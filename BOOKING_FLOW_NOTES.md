# Booking flow notes

## 1. One real event sequence
Take a single booking through a realistic sequence of events and record the state after each one.
Use a sequence you actually ran, not an imagined one.

| # | Event (type, event_id, fields) | status | payment_status | cancellation_fee_paise | refund_due_paise | settled_paise |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | (initial) |  |  |  |  |  |
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |

Note anywhere the actual state differed from what you expected before running it, and what that
told you.

## 2. The state machine as implemented
List every transition the code allows after your changes, and which events are ignored from which
states. State explicitly what happens to an event that is ignored.

## 3. Assumptions
Every decision you made where the contract was silent or ambiguous, and the reasoning. Example
shape: "An event with no `event_id` is rejected and not recorded, because X."

## 4. Edge cases — at least three
For each: the input, the expected state after it, the actual state, and where it is tested.

### Edge case 1
### Edge case 2
### Edge case 3

## 5. Money handling
How integer paise are preserved end to end, where rounding happens, and what guarantees the
totals never drift.
