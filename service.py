"""RailDesk booking lifecycle, cancellation charges and settlement reconciliation.

All records are synthetic. See STUDENT_PROBLEM_STATEMENT.md for the acceptance
contract that this module is required to satisfy.
"""
from copy import deepcopy

FEE_SLABS = ((48, 5), (12, 25), (0, 50))


def cancellation_fee_paise(fare_paise: int, hours_to_departure: float,
                           charted: bool = False) -> int:
    """Return the cancellation fee in integer paise."""
    pct = 50
    for threshold, slab_pct in FEE_SLABS:
        if hours_to_departure > threshold:
            pct = slab_pct
            break
    fee = fare_paise * pct // 100
    if charted and fee > fare_paise:
        fee = fare_paise
    return fee


def apply_booking_event(booking: dict, event: dict) -> dict:
    """Return an updated copy of booking after applying a single event."""
    out = deepcopy(booking)
    out.setdefault("payment_status", "UNPAID")
    out.setdefault("waitlist_position", None)
    out.setdefault("cancellation_fee_paise", 0)
    out.setdefault("refund_due_paise", 0)
    out.setdefault("settled_paise", 0)
    out.setdefault("processed_event_ids", [])

    event_id = event.get("event_id")
    kind = event.get("type")

    if kind == "payment_captured":
        out["payment_status"] = "PAID"
    elif kind == "booking_confirmed" and out.get("status") in ("CREATED", "WAITLISTED"):
        out["status"] = "CONFIRMED"
        out["waitlist_position"] = None
    elif kind == "waitlisted" and out.get("status") == "CREATED":
        out["status"] = "WAITLISTED"
        out["waitlist_position"] = event.get("position")
    elif kind == "chart_prepared" and out.get("status") == "CONFIRMED":
        out["status"] = "CHARTED"
    elif kind == "journey_completed" and out.get("status") == "CHARTED":
        out["status"] = "COMPLETED"
    elif kind == "cancel_requested":
        fee = cancellation_fee_paise(
            out.get("fare_paise", 0),
            event.get("hours_to_departure", 0),
            charted=out.get("status") == "CHARTED",
        )
        out["status"] = "CANCELLED"
        out["waitlist_position"] = None
        out["cancellation_fee_paise"] = fee
        out["refund_due_paise"] = out.get("fare_paise", 0) - fee
    elif kind == "refund_settled":
        out["settled_paise"] += event.get("amount_paise", 0)
        if out["settled_paise"] >= out.get("refund_due_paise", 0):
            out["payment_status"] = "REFUNDED"

    out["processed_event_ids"].append(event_id)
    return out


def promote_waitlist(queue: list[dict], seats_available: int) -> list[str]:
    """Return the booking ids promoted off the waitlist, in promotion order."""
    promoted = []
    while seats_available > 0 and queue:
        entry = queue.pop()
        promoted.append(entry.get("booking_id"))
        seats_available -= 1
    return promoted


def reconcile_settlements(internal: list[dict], gateway: list[dict]) -> dict:
    """Compare internal and gateway settlement summaries keyed by booking_id."""
    left = {r.get("booking_id"): r for r in internal}
    right = {r.get("booking_id"): r for r in gateway}
    report = {
        "matched": [],
        "missing_from_gateway": [],
        "missing_from_internal": [],
        "amount_mismatches": [],
        "status_mismatches": [],
    }
    for key in sorted(set(left) | set(right), key=lambda x: str(x)):
        if key not in right:
            report["missing_from_gateway"].append(key)
        elif key not in left:
            report["missing_from_internal"].append(key)
        else:
            a, b = left[key], right[key]
            if a.get("amount_paise") != b.get("amount_paise"):
                report["amount_mismatches"].append(key)
            else:
                report["matched"].append(key)
    return report
