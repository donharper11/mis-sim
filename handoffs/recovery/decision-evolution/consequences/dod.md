# P4 consequences DoD

This packet implements the pure consequence seam from the decision evolution
specification.  The six-file scope is:

- `backend/app/simulation/accounting.py`
- `backend/app/simulation/consequences.py`
- `backend/app/simulation/repairs.py`
- `backend/app/round/runner.py` (mechanical `rolled_scorecard` delegation only)
- `backend/tests/test_simulation_consequences.py`
- this file

The implementation consumes the audited P1, P2 and P3 DTOs, keeps preparation
detached, quotes integer money with authored allowances and recurring liabilities,
emits effect-only action envelopes, records event/response evidence, and delegates
scorecard conversion to the existing `RoundRunner._rolled_scorecard` helper.  It
does not persist state or modify the casepack.
