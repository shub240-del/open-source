RailDesk dataset v1 - all records are synthetic. Not any operator's real data; no real
passenger, card or payment information.

FILE
  records.json - a single JSON object with these top-level keys:

    counts              record counts, for a quick sanity check
    internal_bookings   120 booking records as the platform sees them
    gateway_settlements 132 settlement summaries as the payment gateway reports them
    events              190 lifecycle events, in arrival order
    waitlist_queue      21 waitlist entries, deliberately NOT in position order
    edge_case_catalog   plain-language list of the anomalies planted in this data

SCHEMAS
  internal_bookings[]
    booking_id            string, "PNR-nnnn"
    train_no              string
    fare_paise            integer paise - never a float, never rupees
    passengers            integer, 1..4
    status                CREATED | CONFIRMED | WAITLISTED | CHARTED | COMPLETED | CANCELLED
    payment_status        UNPAID | PAID | REFUNDED
    waitlist_position     integer, or null when the booking is not waitlisted
    cancellation_fee_paise, refund_due_paise, settled_paise   integer paise
    processed_event_ids   list of event ids already applied to this booking
    hours_to_departure    float, included so slab boundaries can be exercised

  gateway_settlements[]
    booking_id, amount_paise (integer paise), status

  events[]
    event_id    string - MAY BE ABSENT on some records, deliberately
    booking_id  string - may reference a booking that does not exist
    type        payment_captured | booking_confirmed | waitlisted | chart_prepared |
                journey_completed | cancel_requested | refund_settled, plus some
                unrecognised types
    position            present on waitlisted events
    hours_to_departure  present on cancel_requested events
    amount_paise        present on refund_settled events; some are zero or negative

  waitlist_queue[]
    booking_id, position

INTENTIONAL ANOMALIES
  Read edge_case_catalog in the JSON for the full list. In summary, the data contains slab
  boundary values at exactly 48.0 and exactly 12.0 hours, fares where a percentage does not
  divide into whole paise, duplicate events, events with no event_id at all, unknown event
  types, events pointing at unknown bookings, settlements that are negative, zero, or larger
  than the amount due, bookings missing from each side of the reconciliation, records where the
  amount matches but the status does not, records where both differ, a duplicate booking_id on
  the internal side, and a waitlist queue that is shuffled and contains a repeated position.

NOTES
  The offline demo in main.py uses fixtures.py, not this file. records.json is additional
  investigation and test material - use it to find cases the visible tests do not cover.
  Do not upload this data to external services.
