# RailDesk — Open-Source Evaluation starter

Simulated rail-ticketing back office: booking lifecycle, waitlist promotion, cancellation
charges and payment-gateway settlement reconciliation. All records in this repository are
synthetic. Not affiliated with any rail operator or ticketing service.

**Start here: [STUDENT_START_HERE.md](STUDENT_START_HERE.md)** — it is the reading checklist for
this evaluation. The acceptance contract and rubric live in
[STUDENT_PROBLEM_STATEMENT.md](STUDENT_PROBLEM_STATEMENT.md).

## Setup

```
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```

Python 3.10 or newer.

## Layout

| Path | What it is |
| --- | --- |
| `service.py` | Booking lifecycle, charges, waitlist and reconciliation logic |
| `models.py` | Record shapes and constructors |
| `fixtures.py` | Synthetic records for the offline demo |
| `main.py` | Offline demo entry point |
| `tests/` | Visible test suite — the acceptance contract in executable form |
| `data/` | Larger synthetic dataset and its schema notes |

Several visible tests fail on the untouched starter. That is expected. Measure the baseline
yourself before changing anything, fix root causes rather than symptoms, and do not weaken tests.
