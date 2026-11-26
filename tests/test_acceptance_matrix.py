"""Parametrized acceptance matrix for the RailDesk contract."""
import pytest

from models import new_booking, new_waitlist_entry
from service import (apply_booking_event, cancellation_fee_paise, promote_waitlist,
                     reconcile_settlements)


def event(event_id, kind, **extra):
    return {"event_id": event_id, "type": kind, **extra}


TRANSITIONS = [
    ("CREATED", "booking_confirmed", "CONFIRMED"),
    ("CREATED", "waitlisted", "WAITLISTED"),
    ("WAITLISTED", "booking_confirmed", "CONFIRMED"),
    ("CONFIRMED", "chart_prepared", "CHARTED"),
    ("CHARTED", "journey_completed", "COMPLETED"),
    ("CREATED", "chart_prepared", "CREATED"),
    ("CREATED", "journey_completed", "CREATED"),
    ("CONFIRMED", "waitlisted", "CONFIRMED"),
    ("CONFIRMED", "journey_completed", "CONFIRMED"),
    ("COMPLETED", "chart_prepared", "COMPLETED"),
    ("COMPLETED", "booking_confirmed", "COMPLETED"),
    ("CANCELLED", "booking_confirmed", "CANCELLED"),
    ("CANCELLED", "chart_prepared", "CANCELLED"),
]


@pytest.mark.parametrize("status,kind,expected", TRANSITIONS)
def test_transition_matrix(status, kind, expected):
    booking = new_booking("PNR-1", 100000, 1, status)
    out = apply_booking_event(booking, event("e1", kind, position=1))
    assert out["status"] == expected


CANCEL_MATRIX = [
    ("CREATED", True),
    ("CONFIRMED", True),
    ("WAITLISTED", True),
    ("CHARTED", True),
    ("COMPLETED", False),
    ("CANCELLED", False),
]


@pytest.mark.parametrize("status,cancellable", CANCEL_MATRIX)
def test_cancellation_eligibility_matrix(status, cancellable):
    booking = new_booking("PNR-1", 100000, 1, status)
    booking["payment_status"] = "PAID"
    out = apply_booking_event(booking, event("e1", "cancel_requested",
                                             hours_to_departure=60))
    assert out["status"] == ("CANCELLED" if cancellable else status)


FEE_MATRIX = [
    (200000, 120, False, 10000),
    (200000, 48, False, 10000),
    (200000, 47.9, False, 50000),
    (200000, 24, False, 50000),
    (200000, 12, False, 50000),
    (200000, 11.5, False, 100000),
    (200000, 0, False, 100000),
    (200000, 120, True, 200000),
    (200000, 0, True, 200000),
]


@pytest.mark.parametrize("fare,hours,charted,expected", FEE_MATRIX)
def test_fee_slab_matrix(fare, hours, charted, expected):
    assert cancellation_fee_paise(fare, hours, charted=charted) == expected


@pytest.mark.parametrize("fare", [1, 7, 99, 101, 999, 123457])
def test_fee_never_exceeds_fare_and_stays_integral(fare):
    for hours in (0, 12, 48, 100):
        fee = cancellation_fee_paise(fare, hours)
        assert isinstance(fee, int)
        assert 0 <= fee <= fare


@pytest.mark.parametrize("event_id", ["e1", "pay-001", "0"])
def test_payment_replay_matrix(event_id):
    booking = new_booking("PNR-1", 100000)
    e = event(event_id, "payment_captured")
    twice = apply_booking_event(apply_booking_event(booking, e), e)
    assert twice["payment_status"] == "PAID"
    assert twice["processed_event_ids"] == [event_id]


@pytest.mark.parametrize("malformed", [
    {"type": "payment_captured"},
    {"event_id": None, "type": "payment_captured"},
    {"event_id": None, "type": "cancel_requested", "hours_to_departure": 60},
])
def test_events_without_usable_id_are_rejected(malformed):
    booking = new_booking("PNR-1", 100000, 1, "CONFIRMED")
    booking["payment_status"] = "PAID"
    out = apply_booking_event(booking, malformed)
    assert out["processed_event_ids"] == []
    assert out["status"] == "CONFIRMED"
    assert out["refund_due_paise"] == 0


@pytest.mark.parametrize("amount", [-5000, -1, 0])
def test_invalid_settlement_amounts_are_ignored(amount):
    booking = new_booking("PNR-1", 100000, 1, "CANCELLED")
    booking.update(payment_status="PAID", refund_due_paise=50000)
    out = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=amount))
    assert out["settled_paise"] == 0
    assert out["payment_status"] == "PAID"


@pytest.mark.parametrize("first,second,expected", [
    (20000, 20000, 40000),
    (30000, 30000, 30000),
    (50000, 1, 50000),
    (49999, 1, 50000),
])
def test_settlements_never_exceed_due(first, second, expected):
    booking = new_booking("PNR-1", 100000, 1, "CANCELLED")
    booking.update(payment_status="PAID", refund_due_paise=50000)
    one = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=first))
    two = apply_booking_event(one, event("s2", "refund_settled",
                                         amount_paise=second))
    assert two["settled_paise"] == expected
    assert two["settled_paise"] <= 50000


@pytest.mark.parametrize("status,payment_status,due,allowed", [
    ("CANCELLED", "PAID", 50000, True),
    ("CANCELLED", "UNPAID", 50000, False),
    ("CANCELLED", "PAID", 0, False),
    ("CONFIRMED", "PAID", 50000, False),
    ("COMPLETED", "PAID", 50000, False),
    ("CHARTED", "PAID", 50000, False),
])
def test_settlement_eligibility_matrix(status, payment_status, due, allowed):
    booking = new_booking("PNR-1", 100000, 1, status)
    booking.update(payment_status=payment_status, refund_due_paise=due)
    out = apply_booking_event(booking, event("s1", "refund_settled",
                                             amount_paise=1000))
    assert out["settled_paise"] == (1000 if allowed else 0)


@pytest.mark.parametrize("seats,expected", [
    (0, []),
    (1, ["PNR-A"]),
    (2, ["PNR-A", "PNR-B"]),
    (3, ["PNR-A", "PNR-B", "PNR-C"]),
    (9, ["PNR-A", "PNR-B", "PNR-C"]),
])
def test_waitlist_promotion_matrix(seats, expected):
    queue = [new_waitlist_entry("PNR-B", 2), new_waitlist_entry("PNR-C", 3),
             new_waitlist_entry("PNR-A", 1)]
    assert promote_waitlist(queue, seats) == expected


def test_waitlist_promotion_is_repeatable():
    queue = [new_waitlist_entry("PNR-B", 2), new_waitlist_entry("PNR-A", 1)]
    assert promote_waitlist(queue, 1) == promote_waitlist(queue, 1)


@pytest.mark.parametrize("left_status,right_status", [
    ("CANCELLED", "COMPLETED"),
    ("CONFIRMED", "CANCELLED"),
    ("CHARTED", "CONFIRMED"),
])
def test_status_mismatch_matrix(left_status, right_status):
    report = reconcile_settlements(
        [{"booking_id": "X", "amount_paise": 100, "status": left_status}],
        [{"booking_id": "X", "amount_paise": 100, "status": right_status}])
    assert report["status_mismatches"] == ["X"]
    assert report["matched"] == []


@pytest.mark.parametrize("n", [1, 5, 25])
def test_reconciliation_is_deterministic_and_sorted(n):
    ids = [f"PNR-{i:03d}" for i in range(n)]
    records = [{"booking_id": i, "amount_paise": 100, "status": "CANCELLED"} for i in ids]
    report = reconcile_settlements(list(reversed(records)), records)
    assert report["matched"] == sorted(ids)


def test_reconciliation_does_not_mutate_inputs():
    internal = [{"booking_id": "A", "amount_paise": 100, "status": "CANCELLED"}]
    gateway = [{"booking_id": "A", "amount_paise": 100, "status": "CANCELLED"}]
    snapshot = ([dict(r) for r in internal], [dict(r) for r in gateway])
    reconcile_settlements(internal, gateway)
    assert (internal, gateway) == snapshot


@pytest.mark.parametrize("kind", ["booking_confirmed", "chart_prepared",
                                  "cancel_requested", "refund_settled", "nonsense"])
def test_input_booking_is_never_mutated(kind):
    booking = new_booking("PNR-1", 100000, 1, "CONFIRMED")
    booking["payment_status"] = "PAID"
    before = dict(booking)
    apply_booking_event(booking, event("e1", kind, hours_to_departure=60,
                                       amount_paise=1000))
    assert booking == before
