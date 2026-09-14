# Recovery execution record

The user authorized the supervising agent to establish a north-star plan, dispatch bounded
agents and audit behind them on 2026-09-14. The plan is
[`../../design/08-implementation-north-star.md`](../../design/08-implementation-north-star.md).
Original main baseline: `952aeac`. Integration branch: `build/north-star-foundation`.
Planning commit: `d4652c1`; reviewed amendments/status reconciliation: `0a3f967`.

## First wave

| Handoff | Builder / isolated branch | Reviewer | Current status |
|---|---|---|---|
| [`runtime/spec.md`](runtime/spec.md) | `runtime_builder`, `build/recovery-runtime`, initial base `d4652c1` | Supervisor (infrastructure author-audit exception declared) | Corrected candidate `ae634456` ACCEPTED and integrated after NS-006 rework; [audit](../../findings/recovery-runtime-2026-09-14.md) |
| [`calibration-report/spec.md`](calibration-report/spec.md) | `report_builder`, `build/recovery-calibration-report`, initial base `d4652c1` | Fresh `report_auditor` plus supervisor integration audit | Candidate `f858b8a` independently ACCEPTED and integrated with shared reconciliation; [audit](../../findings/recovery-calibration-report-2026-09-14.md) |

Each builder received only its named worktree/branch/base, mandatory documents, binding
handoff allowlist/preflight/DoD, no-push/no-deploy/no-main-merge rule, and the instruction to
return undefined semantics or scope expansion to the supervisor. No subdelegation was
authorized. The implementation scopes are the committed specs, not verbal extrapolations.

## Independent plan review

`plan_reviewer`, with no builder context, reviewed the exact planning commit and returned
PASS WITH FINDINGS. Two amendments landed at `0a3f967` and were announced to both builders:

- **RP-001:** scoring reports need an author-independent build auditor under GOVERNANCE
  §6.1 regardless of Light tier. The report handoff now names a fresh reviewer in addition
  to the supervisor; the runtime-only exception is explicitly declared.
- **RP-002:** migration evidence must precede any seed helper that can call `create_all`.
  Runtime checks now inspect the actual Alembic revision, tables and instance columns
  before seeding, and prove a missing-table defect cannot be masked by the seed.

Each builder was authorized to import only its own amended spec from `0a3f967` and record
the change in a separate author-amendment commit. Functional reporting scope was unchanged;
runtime schema-proof acceptance was strengthened. Shared status/contracts/register files
remain the supervisor's integration responsibility.

## Integration rule

Candidate code is not accepted from a progress message. Record its exact SHA, inspect its
diff against the approved scope, rerun behaviour checks, obtain the required independent
audit, then integrate that commit and check the combined tree. Findings and limitations
must be recorded before claiming completion. A failed candidate returns to its builder.
Main and remote publication remain untouched during this bounded first wave.

The next Heavy work is the scorecard units contract and decision-transition contract.
M0 remains open until the scorecard semantics and runtime/report acceptance all pass;
M1–M6 are not implemented by the first wave.
