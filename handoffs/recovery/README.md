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

## Decision-evolution continuation — P0/P0b accepted

M1 P0 capacity/RTO inputs were independently audited and integrated at `1079b612`.
P0b entity-scoped access and verified repair inputs were independently audited and
integrated at `1729a896`; the combined candidate passed 604 tests, all guards and 44
fixtures, preserved the complete historical24 payload, and detected/restored 13 real
source mutations. [P0b audit](../../findings/recovery-production-inputs-2026-09-15.md).
The builder disclosed P0B-BLD-001, a preflight read-order deviation; its exact-base replay
passed, but the replay does not erase the original procedural residue.

The corrected M1 master transition contract passed independent Heavy review at `bee3977`;
MSR-001–004 are closed at specification level. [Master review](decision-evolution/master-review-2.md).
P1 typed content and runtime binding passed independent audit at `e4f4757` and is integrated
in the current recovery branch. It adds the strict command/runtime/checkpoint boundary and
immutable Riverside pack binding; the packet passed `618` full-gate tests, all guards and
the zero-error Riverside validator. [P1 audit](../../findings/recovery-content-types-2026-09-15.md).
P2 estate passed independent audit at `b4bfec9` and is integrated in the current recovery
branch. It supplies initial estate/lifecycle, resource and physical projection behavior;
the packet passed `628` full-gate tests, all guards and the zero-error Riverside validator.
[P2 audit](../../findings/recovery-estate-2026-09-15.md). P3 organisation is now the next
dispatchable packet. M1 remains unfinished until organisation, consequences, persistence
and decision-only game packets pass their independent audits.

## First-wave acceptance and cleanup

- Reporting candidate `f858b8a` was independently accepted by `report_auditor`, then
  integrated with living-spec/register reconciliation at **`94b85e7`**.
- Initial runtime candidate `d68d892` returned for NS-006: shared dotenv keys prevented
  settings import and exposed fixture values in the traceback. Supervisor scope amendment
  `6a6c707` authorized the one-line configuration correction and subprocess regressions.
  Corrected candidate `ae634456` passed re-audit, integrated at **`4adafd8`**.
- Supervisor combined-tree checks: **132 pytest tests**, every guard and **44 fixtures**,
  `pip check`, and actual PostgreSQL migrations/16 scoped tables/six persisted rounds.
  Refusal and missing-table-before-seed checks also passed on the combined checkout.
- All supervisor-created disposable databases were dropped. The runtime builder then
  dropped its two retained verification databases, stopped its isolated cluster on
  `127.0.0.1:53883`, confirmed `pg_ctl status` reports no server, and removed that cluster,
  dummy dotenv directory and its two venvs. Logs remain as evidence; no shared service
  was touched. The supervisor's fresh verification venv remains available under `/tmp`.

Audit details and durable reproduction commands are linked above. Historical builder
DoDs record their candidate-ready state; these acceptance records supersede their
pending-audit status without rewriting the historical evidence.

## Next reviewed handoff

`scorecard_author` delivered the Heavy [scorecard contract](scorecard-contract/spec.md)
on an isolated branch, with no implementation permission. Fresh reviewer `report_auditor`
returned two concrete gaps at `6caf40b`; the author corrected them at `0716eb9` and the
reviewer passed all five spec checks. [Review and authority ruling](scorecard-contract/review.md)
accept R1–R4 and specify the next dispatch prerequisites. No scorecard builder was launched
before that review, and no scorecard code is included in this first wave.

That was the first-wave checkpoint. The following continuation supersedes its pending
scorecard status; historical candidate evidence remains unchanged.

## Scorecard continuation — M0 accepted

The user's “Can we proceed?” authorized the next reviewed packet. Builder
`scorecard_builder` received the exact base `c7283dc`, five-file allowlist and no
subdelegation in [dispatch.md](scorecard-contract/dispatch.md). It completed all six
preflights before edits. Code/tests were frozen at `5f5b09e`; final candidate `ad5de38`
adds only the [DoD](scorecard-contract/dod.md). Fresh `scorecard_auditor` independently
reviewed and verified the build; the supervisor separately checked its complete diff,
24 persisted results against pre-edit captures, and a new PostgreSQL database.

The accepted correction uses integer event points, bounded 0–1 output and versioned
base/delta/partial-status evidence. Balanced R1 Financial is **0.696932**; the firm score
remains **0.35825**. Every other field across all 24 results is unchanged. The full score
digest changes because it continues to include the corrected BSC values; old evidence
and old unversioned payloads are preserved. Shared §7 contracts and the NS-003 register
closure accompany integration. **311 tests, all guards and 44 fixtures pass.**
[Independent audit and supervisor evidence](../../findings/recovery-scorecard-2026-09-14.md).

**M0 is complete on `build/north-star-foundation`.** No main merge, push or deployment.
The Financial proxy, scripted estates, transaction/retry gaps and all later product
milestones retain their explicit limits. Current code and documentation were integrated
together only after audit acceptance. The combined checkout passed the full gate;
its five builder files and eight contract documents match the accepted candidate and
auditor hashes exactly. All disposable audit databases and the private scorecard
cluster/password were removed after verification; non-secret evidence is retained.

## M1 preparation

In parallel, `decision_inventory` had permission for one new documentation file and no
implementation or formula design. Candidate `0f08674` was independently reproduced by
the supervisor and integrated with its review/register update at `54c1ead`.
[Inventory](decision-evolution/inventory.md) and [review](decision-evolution/review.md)
record concrete transition failures and D1–D10 contract decisions. No M1 interface has
passed spec review. The next assignment is its Heavy decision/atomic-transition contract;
M1's five bounded stages remain those in the north star. M1–M6 remain unfinished.
