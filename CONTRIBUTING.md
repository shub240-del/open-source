# Evaluation workflow

Fork this repository, create a focused branch, inspect the existing implementation, run
`python -m pytest -q`, and open **one** pull request to the original repository. Do not merge it.

Keep the diff focused. One logical change per commit, with a message that says what changed and
why. Do not commit secrets, credentials, virtual environments or unrelated files.

## Mandatory assessed documentation
Complete these three Markdown files from the templates in this repository:

1. `approach.md` — approach, investigation evidence, experiments, implementation strategy.
2. `challenges.md` — **compulsory**; actual challenges, what you tried, evidence, resolution and
   remaining limitations. If none arose, say so honestly and describe the hardest edge case you
   deliberately tested.
3. `optimizations.md` — optimizations considered or implemented, trade-offs, measured effects
   where measured, and future improvements.

All three are required and together are worth 15 marks (5 each). Empty, generic, copied or
unsupported claims receive no marks for that part. Document the real engineering process and
rationale.

Complete `TESTING.md` and `BOOKING_FLOW_NOTES.md` too, as required by the problem statement.
Reference your documentation from the pull-request description.

## Testing rules
Add regression tests for every fix. Do not delete, skip, weaken or rewrite an existing test to
make it pass, and do not modify the CI workflow to hide a failure. If you believe a test encodes
the wrong expectation, leave it in place and argue the case in `challenges.md`.

## Integrity
AI chatbots, AI coding assistants, generated code or tests, and solution-sharing are prohibited
for this evaluation. Standard non-AI documentation is allowed. Do not submit code you cannot
explain; a short live modification may be requested during the evaluation.
