# RailDesk — Waitlist Promotion, Cancellation Charges & Settlement Reconciliation

**Track:** Rail ticketing operations | **Language:** Python 3.10+ | **Time:** one-day evaluation

## Scenario
A rail ticketing platform captures payment before a seat is guaranteed. A booking may be
confirmed immediately or placed on a waitlist and promoted later as seats free up. Once the
reservation chart is prepared, the commercial rules change sharply. Passengers cancel at every
stage, cancellation charges depend on how close to departure the request arrives, and settlement
notifications from the payment gateway arrive late, out of order, or more than once.

The service must not over-refund, must not settle the same refund twice, and must not confuse a
partial settlement with a completed one.

This is a simulated, offline project inspired by public rail-ticketing workflows. It is not any
operator's internal software, is not affiliated with Indian Railways or IRCTC, and contains no
real passenger or payment data.

## Required behaviour — the acceptance contract

### 1. Booking lifecycle
Statuses: `CREATED`, `CONFIRMED`, `WAITLISTED`, `CHARTED`, `COMPLETED`, `CANCELLED`.

Valid transitions, and only these:

| From | Event | To |
| --- | --- | --- |
| `CREATED` | `booking_confirmed` | `CONFIRMED` |
| `CREATED` | `waitlisted` | `WAITLISTED` (records `waitlist_position` from the event) |
| `WAITLISTED` | `booking_confirmed` | `CONFIRMED` (clears `waitlist_position`) |
| `CONFIRMED` | `chart_prepared` | `CHARTED` |
| `CHARTED` | `journey_completed` | `COMPLETED` |
| `CREATED`, `CONFIRMED`, `WAITLISTED`, `CHARTED` | `cancel_requested` | `CANCELLED` |

Any other event/status combination, and any unrecognised event type, must leave the booking
state unchanged. A cancellation requested on a `COMPLETED` or already `CANCELLED` booking must
not silently re-cancel it or recompute its charges.

### 2. Idempotency
Every event carries an `event_id`. Replaying an event must not apply it a second time — no
double settlement, no recomputed fee, and no duplicate entry in `processed_event_ids`.

An event with a missing or `None` `event_id` cannot be deduplicated, so it must be **rejected
entirely**: no state change, and it must not be recorded in `processed_event_ids`. An event that
carries a usable `event_id` but is ignored for any other reason (invalid transition, unknown
type, ineligible refund) **is** recorded as processed.

### 3. Cancellation charges
All money is integer paise. Never use floating point for money.

| Condition | Fee |
| --- | --- |
| Chart already prepared (`CHARTED`) | 100% of fare — nothing is refundable |
| 48 hours or more before departure | 5% of fare |
| At least 12 and under 48 hours before departure | 25% of fare |
| Under 12 hours before departure | 50% of fare |

The boundaries are inclusive at the lower edge: exactly 48 hours is the 5% slab, exactly 12 hours
is the 25% slab. The fee is the integer floor of the percentage — `fare_paise * pct // 100` — and
is never rounded up. The fee may never exceed the fare.

### 4. Refund eligibility
`refund_due_paise` is the fare net of the cancellation fee, and is recorded **only** when the
booking was actually paid (`payment_status == "PAID"`). An unpaid booking that gets cancelled
has a zero fee and a zero refund due — no money was collected, so none can be returned.

### 5. Settlement safety
Track `refund_due_paise` and `settled_paise` separately.

A `refund_settled` event applies only when the booking is `CANCELLED`, was paid, and has a
positive `refund_due_paise`. The amount must be a positive integer, and a settlement that would
push `settled_paise` above `refund_due_paise` must be rejected in full — never partially applied
and never clamped. `payment_status` becomes `REFUNDED` only when `settled_paise` exactly equals
`refund_due_paise`, and a booking with nothing due must never be marked `REFUNDED`.

### 6. Waitlist promotion
`promote_waitlist(queue, seats_available)` returns the booking ids promoted, in promotion order:
strictly ascending `position`, ties broken by `booking_id`. It promotes at most
`seats_available` entries and at most the length of the queue, treats a non-positive seat count
as promoting nobody, and **must not mutate the queue it was given**. Calling it twice with the
same inputs must return the same result.

### 7. Reconciliation
`reconcile_settlements(internal, gateway)` compares summaries keyed by `booking_id` and reports
`matched`, `missing_from_gateway`, `missing_from_internal`, `amount_mismatches` and
`status_mismatches`. The mismatch buckets are independent: a record whose amount **and** status
both differ appears in both mismatch buckets and is not matched. Only a record identical on both
sides is matched. Output order must be deterministic and sorted. Neither input list may be
mutated.

A duplicate `booking_id` within one side is a data defect. Decide how you handle it, and justify
your decision in your documentation.

### 8. Robustness
Empty input, missing fields, unknown ids, unknown event types and duplicates must all be handled
without corrupting state. `apply_booking_event` returns an updated copy and never mutates its
input booking.

## Setup
```
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```

## Repository reading checklist
Before editing anything, read `README.md` and `STUDENT_START_HERE.md`, then inspect the whole
repository: `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `service.py`, `models.py`,
`fixtures.py`, `main.py`, every file under `tests/`, `data/README.txt`, and the workflow files
under `.github/workflows/`.

The synthetic dataset is in `data/records.json`: 120 internal bookings, 132 gateway settlement
records, 190 event examples and a 21-entry waitlist queue, plus an edge-case catalog. Read
`data/README.txt` for the schema and the intentional anomalies. The offline demo uses
`fixtures.py`; the JSON file is additional investigation and test material.

**Run the baseline test suite before editing anything and record the actual result.** Do not
delete, skip or weaken tests to make CI green.

## Work to submit
- Run the starter tests and read the source before editing.
- Treat the acceptance contract above as authoritative. Investigate failing tests, trace each
  one to a root cause, and fix the underlying behaviour. Do not hard-code fixture output and do
  not patch symptoms test by test.
- Add regression tests for every fix, and document at least five edge cases in `TESTING.md`.
- Submit **one** pull request against the original repository containing code, tests, a
  root-cause summary and known limitations. **Do not merge it.**
- Complete `BOOKING_FLOW_NOTES.md` with one real event sequence, the expected state after each
  event, your assumptions, and at least three edge cases.

## Mandatory problem-solving documentation — all three required
Complete these at the repository root and include them in your pull request. Code alone is not a
complete submission. Start from the templates; a blank or generic file scores zero.

- `approach.md` (5 marks) — your baseline test result, the code and data flow you traced, your
  hypotheses, the experiments you ran, your implementation strategy and why you chose it.
- `challenges.md` (5 marks, **compulsory**) — concrete obstacles or confusing behaviour, what you
  tried, evidence from tests and logs, how you resolved it, and anything left unresolved. If you
  did not get stuck, say so honestly and describe the hardest edge case you deliberately tested.
  Do not invent a struggle.
- `optimizations.md` (5 marks) — optimizations considered or implemented, why you chose or
  rejected each, correctness/readability/performance trade-offs, and future improvements.
  Separate measured improvements from unmeasured ideas.

Be concrete and evidence-based. Never claim a test passed unless you ran it.

## Optional stretch work
Pick at most one, only after the core contract passes: export an awaiting-settlement CSV report;
detect out-of-order events from a timestamp field; or summarise bookings by status.

## Testing and CI
Several visible tests are expected to fail on the untouched starter, because key behaviours are
incomplete or wrong. The exact initial count is not given to you — measure it yourself. GitHub
Actions runs on push and pull request. A red check before your fixes is expected. Do not remove,
skip, weaken or bypass tests, and do not edit CI to hide failures.

## Final submission checklist
- [ ] I read this statement, `STUDENT_START_HERE.md`, `README.md`, the contribution guide, every
      source file, the dataset notes, every visible test and the CI workflow.
- [ ] I installed dependencies, recorded the untouched baseline from `python -m pytest -q`, and
      ran `python -m main`.
- [ ] I fixed root causes, not symptoms, and added regression tests. I did not delete, skip,
      weaken or bypass any existing test, and did not edit CI to hide failures.
- [ ] I completed `approach.md`, `challenges.md` and `optimizations.md` with my own evidence.
- [ ] I completed `TESTING.md` with the real Python version, the commands I ran, the test summary
      and at least five edge cases showing input, expected behaviour, actual result and evidence.
- [ ] I completed `BOOKING_FLOW_NOTES.md`.
- [ ] I reviewed my diff, kept the change focused, and committed no secrets or unrelated files.
- [ ] I opened **one** pull request from my fork to this repository, filled in the PR template,
      and **did not merge it**.
- [ ] I checked the PR's CI result and documented any remaining failures honestly.
- [ ] I can explain every change independently and make a small live modification on request.

## Individual-work policy
AI chatbots, AI coding assistants, generated patches or tests, and asking another person to write
or debug the solution are prohibited. Ordinary non-AI documentation is allowed. Do not upload
challenge code or data to external services. You must be able to explain your code and make a
small live change if asked.

## Rubric — 100 marks
- Codebase understanding and booking-state flow: 10
- Root-cause analysis and correctness: 20
- Transitions, idempotency, charge and settlement safety: 25
- Regression tests and edge cases: 15
- Code quality and maintainability: 5
- Required problem-solving documentation: 15 (approach 5, challenges 5, optimizations 5)
- Pull request, booking-flow notes and live explanation: 10

The three process documents are assessed for specific, honest, evidence-based technical
reflection, not for writing style.
