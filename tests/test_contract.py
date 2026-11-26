from models import new_booking, new_waitlist_entry
from service import (apply_booking_event, cancellation_fee_paise, promote_waitlist,
                     reconcile_settlements)


def event(event_id, kind, **extra):
    return {"event_id": event_id, "type": kind, **extra}


def paid_cancelled(fare=100000, due=25000):
    booking = new_booking("PNR-1", fare, 1, "CANCELLED")
    booking.update(payment_status="PAID", refund_due_paise=due)
    return booking


# --- lifecycle ---------------------------------------------------------------

def test_confirm_from_created_and_input_is_not_mutated():
    booking = new_booking("PNR-1", 100000)
    out = apply_booking_event(booking, event("e1", "booking_confirmed"))
    assert out["status"] == "CONFIRMED"
    assert booking["status"] == "CREATED"


def test_waitlisted_records_position():
    out = apply_booking_event(new_booking("PNR-1", 100000),
                              event("e1", "waitlisted", position=7))
    assert out["status"] == "WAITLISTED"
    assert out["waitlist_position"] == 7


def test_confirmation_clears_waitlist_position():
    booking = new_booking("PNR-1", 100000, 1, "WAITLISTED")
    booking["waitlist_position"] = 4
    out = apply_booking_event(booking, event("e1", "booking_confirmed"))
    assert out["status"] == "CONFIRMED"
    assert out["waitlist_position"] is None


def test_full_journey_flow():
    booking = new_booking("PNR-1", 100000)
    for e in [event("1", "booking_confirmed"), event("2", "chart_prepared"),
              event("3", "journey_completed")]:
        booking = apply_booking_event(booking, e)
    assert booking["status"] == "COMPLETED"


# --- cancellation fee slabs --------------------------------------------------

def test_fee_slab_boundary_at_48_hours():
    assert cancellation_fee_paise(100000, 48) == 5000
    assert cancellation_fee_paise(100000, 60) == 5000


def test_fee_slab_boundary_at_12_hours():
    assert cancellation_fee_paise(100000, 12) == 25000
    assert cancellation_fee_paise(100000, 47) == 25000


def test_fee_slab_below_12_hours():
    assert cancellation_fee_paise(100000, 2) == 50000


def test_charted_cancellation_forfeits_the_full_fare():
    assert cancellation_fee_paise(100000, 2, charted=True) == 100000


def test_fee_is_integer_floor_never_rounded_up():
    assert cancellation_fee_paise(999, 60) == 49


# --- refund eligibility ------------------------------------------------------

def test_paid_cancellation_records_refund_due_net_of_fee():
    booking = new_booking("PNR-1", 100000, 1, "CONFIRMED")
    booking["payment_status"] = "PAID"
    out = apply_booking_event(booking, event("e1", "cancel_requested",
                                             hours_to_departure=60))
    assert out["status"] == "CANCELLED"
    assert out["cancellation_fee_paise"] == 5000
    assert out["refund_due_paise"] == 95000


def test_unpaid_cancellation_has_no_fee_and_no_refund_due():
    booking = new_booking("PNR-1", 100000, 1, "CONFIRMED")
    out = apply_booking_event(booking, event("e1", "cancel_requested",
                                             hours_to_departure=60))
    assert out["status"] == "CANCELLED"
    assert out["cancellation_fee_paise"] == 0
    assert out["refund_due_paise"] == 0


def test_charted_cancellation_leaves_no_refund_due():
    booking = new_booking("PNR-1", 100000, 1, "CHARTED")
    booking["payment_status"] = "PAID"
    out = apply_booking_event(booking, event("e1", "cancel_requested",
                                             hours_to_departure=2))
    assert out["status"] == "CANCELLED"
    assert out["cancellation_fee_paise"] == 100000
    assert out["refund_due_paise"] == 0


# --- invalid transitions -----------------------------------------------------

def test_cancel_after_completion_is_ignored():
    booking = new_booking("PNR-1", 100000, 1, "COMPLETED")
    booking["payment_status"] = "PAID"
    out = apply_booking_event(booking, event("e1", "cancel_requested",
                                             hours_to_departure=60))
    assert out["status"] == "COMPLETED"
    assert out["refund_due_paise"] == 0


def test_second_cancellation_does_not_recompute_fee():
    booking = new_booking("PNR-1", 100000, 1, "CANCELLED")
    booking.update(payment_status="PAID", cancellation_fee_paise=5000,
                   refund_due_paise=95000)
    out = apply_booking_event(booking, event("e2", "cancel_requested",
                                             hours_to_departure=2))
    assert out["cancellation_fee_paise"] == 5000
    assert out["refund_due_paise"] == 95000


def test_unknown_event_type_changes_nothing():
    booking = new_booking("PNR-1", 100000, 1, "CONFIRMED")
    out = apply_booking_event(booking, event("e1", "teleported"))
    assert out["status"] == "CONFIRMED"
    assert out["refund_due_paise"] == 0


# --- idempotency -------------------------------------------------------------

def test_replayed_event_is_applied_once():
    booking = new_booking("PNR-1", 100000)
    e = event("e1", "payment_captured")
    once = apply_booking_event(booking, e)
    twice = apply_booking_event(once, e)
    assert twice["payment_status"] == "PAID"
    assert twice["processed_event_ids"] == ["e1"]


def test_replayed_settlement_does_not_double_count():
    booking = paid_cancelled(due=25000)
    e = event("s1", "refund_settled", amount_paise=10000)
    once = apply_booking_event(booking, e)
    twice = apply_booking_event(once, e)
    assert twice["settled_paise"] == 10000


def test_event_without_an_event_id_is_ignored_and_not_recorded():
    booking = new_booking("PNR-1", 100000)
    out = apply_booking_event(booking, {"type": "payment_captured"})
    assert out["payment_status"] == "UNPAID"
    assert out["processed_event_ids"] == []


def test_ignored_event_is_still_recorded_when_it_has_an_id():
    booking = new_booking("PNR-1", 100000, 1, "COMPLETED")
    out = apply_booking_event(booking, event("e9", "cancel_requested",
                                             hours_to_departure=60))
    assert out["processed_event_ids"] == ["e9"]


# --- settlement safety -------------------------------------------------------

def test_settlement_must_be_positive():
    booking = paid_cancelled(due=25000)
    for amount in (0, -500):
        out = apply_booking_event(booking, event("s1", "refund_settled",
                                                 amount_paise=amount))
        assert out["settled_paise"] == 0


def test_settlement_cannot_exceed_refund_due():
    booking = paid_cancelled(due=25000)
    out = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=30000))
    assert out["settled_paise"] == 0
    assert out["payment_status"] == "PAID"


def test_partial_settlement_stays_partial():
    booking = paid_cancelled(due=25000)
    out = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=10000))
    assert out["settled_paise"] == 10000
    assert out["payment_status"] == "PAID"


def test_full_settlement_marks_refunded():
    booking = paid_cancelled(due=25000)
    out = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=25000))
    assert out["settled_paise"] == 25000
    assert out["payment_status"] == "REFUNDED"


def test_booking_with_no_refund_due_is_never_marked_refunded():
    booking = new_booking("PNR-1", 100000, 1, "CONFIRMED")
    booking["payment_status"] = "PAID"
    out = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=1000))
    assert out["settled_paise"] == 0
    assert out["payment_status"] == "PAID"


# --- waitlist ----------------------------------------------------------------

def test_waitlist_promotes_in_ascending_position_order():
    queue = [new_waitlist_entry("PNR-C", 3), new_waitlist_entry("PNR-A", 1),
             new_waitlist_entry("PNR-B", 2)]
    assert promote_waitlist(queue, 2) == ["PNR-A", "PNR-B"]


def test_waitlist_promotion_does_not_mutate_the_queue():
    queue = [new_waitlist_entry("PNR-A", 1), new_waitlist_entry("PNR-B", 2)]
    before = [dict(e) for e in queue]
    promote_waitlist(queue, 1)
    assert queue == before


def test_waitlist_promotion_is_bounded_by_seats_and_queue_length():
    queue = [new_waitlist_entry("PNR-A", 1)]
    assert promote_waitlist(queue, 5) == ["PNR-A"]
    assert promote_waitlist(queue, 0) == []
    assert promote_waitlist([], 3) == []


# --- reconciliation ----------------------------------------------------------

def test_reconcile_reports_status_mismatch_separately():
    report = reconcile_settlements(
        [{"booking_id": "A", "amount_paise": 100, "status": "CANCELLED"}],
        [{"booking_id": "A", "amount_paise": 100, "status": "COMPLETED"}])
    assert report["status_mismatches"] == ["A"]
    assert report["matched"] == []


def test_reconcile_reports_amount_and_status_mismatch_in_both_buckets():
    report = reconcile_settlements(
        [{"booking_id": "A", "amount_paise": 100, "status": "CANCELLED"}],
        [{"booking_id": "A", "amount_paise": 90, "status": "COMPLETED"}])
    assert report["amount_mismatches"] == ["A"]
    assert report["status_mismatches"] == ["A"]
    assert report["matched"] == []


def test_reconcile_reports_missing_records_on_each_side():
    report = reconcile_settlements(
        [{"booking_id": "A", "amount_paise": 100, "status": "CANCELLED"}],
        [{"booking_id": "B", "amount_paise": 50, "status": "CANCELLED"}])
    assert report["missing_from_gateway"] == ["A"]
    assert report["missing_from_internal"] == ["B"]


def test_reconcile_matches_identical_records():
    record = {"booking_id": "A", "amount_paise": 100, "status": "CANCELLED"}
    report = reconcile_settlements([record], [dict(record)])
    assert report["matched"] == ["A"]


def test_empty_reconciliation_returns_empty_buckets():
    assert all(v == [] for v in reconcile_settlements([], []).values())
