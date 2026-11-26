# Student start here — RailDesk

This is the reading checklist for the evaluation. Read these before editing code. You are
responsible for understanding the starter code, the dataset, the tests and the required
submission files.

## 1. Read the problem statement first
- [Markdown problem statement](STUDENT_PROBLEM_STATEMENT.md) — the source of truth, including
  the full acceptance contract and the rubric.

## 2. Read the workflow and integrity rules
- [README and setup](README.md)
- [Contribution and pull-request workflow](CONTRIBUTING.md)
- [Pull-request checklist](.github/PULL_REQUEST_TEMPLATE.md)

## 3. Mandatory Markdown files — all three are graded
- [approach.md](approach.md) — approach, experiments, evidence, decisions (5 marks)
- [challenges.md](challenges.md) — **COMPULSORY**; real obstacles, evidence, resolution (5 marks)
- [optimizations.md](optimizations.md) — optimizations, trade-offs, future work (5 marks)

Also submit:
- [TESTING.md](TESTING.md) — real commands, real results, at least five edge cases
- [BOOKING_FLOW_NOTES.md](BOOKING_FLOW_NOTES.md) — one event sequence, assumptions, three edge cases

These must reflect work you actually did. Do not invent problems or measurements.

## 4. Inspect the codebase — do not read only the problem statement
- `service.py` — the logic under evaluation
- `models.py` — record shapes
- `fixtures.py` and everything in `data/` — synthetic examples
- `main.py` — the offline demo path
- every file in `tests/` — read the assertions and understand what each one protects
- `requirements-dev.txt`, `pyproject.toml` — environment and tooling
- `.github/workflows/` — what CI runs on push and pull request
- `.gitignore` — what must not be committed

Do not change a test to hide a defect. Add regression tests for your fixes.

## 5. Run, investigate, submit
1. Python 3.10+ and Git.
2. `python -m pip install -r requirements-dev.txt`
3. `python -m pytest -q` — **record the actual baseline result before editing.**
4. `python -m main`
5. Trace each failure to a root cause. Do not hard-code fixture output.
6. Re-run tests after meaningful changes and record actual results in your notes.
7. Open one pull request from your fork to the original repository. Do not merge it.
8. Be ready to explain the implementation and make a small live change.

## Evaluation overview
Total **100 marks**. The rubric in the problem statement awards **15 marks for the three
mandatory process documents** and **15 for regression tests and edge cases**. Correctness, state
safety, the pull request and your live explanation are also assessed.

Challenge context: rail ticketing operations — booking lifecycle, waitlist promotion,
cancellation charge slabs, idempotency and settlement reconciliation.
