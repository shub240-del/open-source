"""Helpers for synthetic rail booking records. All data is simulated."""

VALID_STATUSES = ("CREATED", "CONFIRMED", "WAITLISTED", "CHARTED", "COMPLETED", "CANCELLED")
VALID_PAYMENT_STATUSES = ("UNPAID", "PAID", "REFUNDED")


def new_booking(booking_id: str, fare_paise: int, passengers: int = 1,
                status: str = "CREATED") -> dict:
    """Return a fresh booking record."""
    return {
        "booking_id": booking_id,
        "fare_paise": fare_paise,
        "passengers": passengers,
        "status": status,
        "payment_status": "UNPAID",
        "waitlist_position": None,
        "cancellation_fee_paise": 0,
        "refund_due_paise": 0,
        "settled_paise": 0,
        "processed_event_ids": [],
    }


def new_waitlist_entry(booking_id: str, position: int) -> dict:
    """Return a waitlist queue entry."""
    return {"booking_id": booking_id, "position": position}
