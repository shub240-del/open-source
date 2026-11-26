"""Synthetic records for the offline demo only."""
from models import new_booking, new_waitlist_entry


def sample_bookings():
    return [
        new_booking("PNR-4401", 185000, 2, "CONFIRMED"),
        new_booking("PNR-4402", 92500, 1, "WAITLISTED"),
        new_booking("PNR-4403", 240000, 3, "CHARTED"),
    ]


def sample_gateway_settlements():
    return [
        {"booking_id": "PNR-4401", "amount_paise": 185000, "status": "CONFIRMED"},
        {"booking_id": "PNR-4402", "amount_paise": 92500, "status": "CANCELLED"},
        {"booking_id": "PNR-4404", "amount_paise": 56000, "status": "COMPLETED"},
    ]


def sample_internal_settlements():
    return [
        {"booking_id": b["booking_id"], "amount_paise": b["fare_paise"],
         "status": b["status"]}
        for b in sample_bookings()
    ]


def sample_waitlist():
    return [new_waitlist_entry("PNR-4402", 1), new_waitlist_entry("PNR-4405", 2),
            new_waitlist_entry("PNR-4406", 3)]
