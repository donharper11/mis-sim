# P3 organisation final amended audit — PASS

Candidate: `2c42f24cb3361afc8670994ce447bfa2d8d4bc36`
Base: `9e226c3`
Worktree: `/tmp/mis-sim-m1-p3-organisation-v1`
Audit date: 2026-09-15

## Decision

**PASS.** The final amended candidate resolves the prior four findings and the repeated
held-support no-op defect. Direct P3 contract probes and all inherited gates passed.

## Scope and integrity

`HEAD` matched the requested candidate. The worktree was clean, `git diff --check
9e226c3..2c42f24cb3361afc8670994ce447bfa2d8d4bc36` passed, and the exact amended diff
contains only:

```text
backend/app/simulation/organisation.py
backend/app/simulation/types.py
backend/tests/test_simulation_organisation.py
handoffs/recovery/decision-evolution/organisation/dod.md
```

The `types.py` change is limited to the authorized `OrgDeltaV1.hiring_orders` and
`OrgDeltaV1.staff_hires` fields. No candidate or root files were modified.

## Direct contract results

- Training retention, coverage ceilings, none/full behavior, process partial/full/revert
  pricing and exact `PROCESS_FIT` passed.
- Catalog-only arrival shocks, scoped communication/resistance, bounded adoption with
  sponsor/no sponsor, and one-time strategy change cost/round/shock passed.
- Hire order carry-forward, round-2 arrival, capacity increase, `-31000` wage entry,
  and pre-arrival cancellation passed.
- Support scope/capacity and empty coverage passed. Repeating identical held basic
  support in a later round returned **no support charge and no support effect**; changing
  support remains effectful.
- Internal owner and permitted sponsor joins, primary serving/retired joins, duplicate
  assignment/primary conflicts, six policy activity states, 10 preference rows and 33
  views passed.
- Strict bool/float/NaN/out-of-range round checks, malformed references, DTO joins and
  detached outputs passed.

## Gates and mutation/restoration

- Focused P3 tests: **7 passed**.
- Combined P3/P2/P1/P0/legacy pins: **338 passed**.
- Supervisor `make check` with `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin`: **635 passed**,
  all guards green.
- Riverside validator: **0 errors, 0 warnings**.
- Disposable mutation removing strict round validation failed the strict-round test
  (`1 failed, 6 deselected`).
- Disposable mutation removing the held-support no-op guard failed the staffing/support
  test (`1 failed, 6 deselected`).
- Candidate worktree remained clean after all checks.
