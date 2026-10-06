# Host activation and reset — dispatch contract

2026-10-06. Author: readiness builder. PROPOSED for independent review before implementation.
Heavy: shared persistence/progression boundary; no scoring/engine calculation change.
Scope0012 is accepted; this successor owns READY-002, not initialization or SQLite archive.

## Verified basis

[V] Manual round control and Scheduler._advance both call SimulationService.advance.
Its locked run transaction writes checkpoint/result and opens n+1, or keeps current_round at
n on final completion. Retry of a committed round returns its original immutable result.
[V] Host create/assignment use instance.current_round, which can lag under scheduled advance.
[V] Host status is presentation metadata, not an engine/scoring input. UI exposes additions
only for pending hosts. Server update/add/remove currently allow active/retired metadata edits.
[V] Reset is limited to setup status. It currently omits host tables and most historical
round tables even though initialize explicitly refuses any existing legacy rows.
[V] Several service tests/harnesses construct explicit minimal table inventories; introducing
host access requires those inventories to include host tables, never a missing-table bypass.

## Frozen behavior

1. Creation remains pending, with created_round = locked run.current_round and
   activated_round = created_round+1. Member assigned_round uses the same locked run pointer.
   `_require_editable` returns its run. It still refuses missing run/sheet, locked round,
   completed run and paused/completed/archived instance. No new command or purchase semantics.
2. On successful first advancement, after setting run.current_round/status but BEFORE commit,
   promote only this instance/team's pending hosts with created_round>=1,
   activated_round=created_round+1 and activated_round<=run.current_round to active.
   Evaluate timing with overflow-safe arithmetic (cast created_round to BIGINT before +1),
   including PostgreSQL INTEGER minimum/maximum fixtures. Null/malformed timing, future,
   active and retired rows are unchanged. The final round does
   not open a hypothetical next round: hosts ordered then remain pending after completion.
   This grouping status does not claim that every purchased member has arrived.
3. Put promotion in the same SimulationService.advance transaction as checkpoint/result,
   behind the same run lock. Shared manual/scheduled behavior; no post-commit duplicate hooks.
   A failed transaction leaves result/run/sheet/host unchanged. Retry returns the same payload
   and does not re-run promotion or mutate prior evidence. No result/checkpoint fields change.
4. Server rename/add/remove requires platform.status=='pending' after authorized parent
   selection and editable-run lock. Active/retired return409; other team/instance remains404
   (403 for forbidden path context), when the own run is editable; the existing editable-run
   guard may return409 first when locked. Creation remains allowed in any editable round, including
   final round; final-round pending is explicitly honest, not silently activated beyond horizon.
5. Historical reconciliation: new data-only migration20261006_0013 after0012 promotes the
   same valid overdue pending rows using the matching scoped run.current_round, including
   completed runs. Hosts without a run, malformed timing, future, active, retired are untouched.
   Reconciliation changes only host.status. It is idempotent, online, SQLite/PostgreSQL portable.
   Downgrade is explicitly a NO-OP on status: it cannot reconstruct which active rows were
   formerly pending. No destructive reversal or claimed lossless semantic rollback. Archive
   CHECK repair remains a separate migration/task. Record exact matching IDs before/after.

## Reset transaction and preservation

Only setup-status instances reset, with existing owner/admin authorization at instructor API.
Refresh/lock instance with PostgreSQL FOR NO KEY UPDATE (compatible with host insert FK key
locks); lock scoped schedule rows in ID order then scoped run rows in team order, matching
scheduler's schedule→run order. Hold locks until caller commits/rolls back. Concurrent host
edit/advance linearizes before reset (its rows then cleared) or observes missing run afterward;
no committed remnant and no cross-instance loss. Do not use instance FOR UPDATE followed by
run lock: that can invert host insertion's run→instance FK lock order. SQLite uses existing
single-writer behavior; do not claim row locks there.

Manual advance final reconciliation also participates: after the per-team service transactions,
roll back any stale async read transaction, then refresh/lock the instance with NO KEY UPDATE
and populate_existing. Under that lock, refresh all scoped runs and compare the exact team-ID
set captured at entry. Missing/replaced scope or any run.advanced_round below target_round
returns409 without writing instance state. Reset that committed between service advance and
this phase therefore leaves setup/round0 and empty runtime intact. If reconciliation commits
first, reset refreshes active/completed status and refuses. No instance lock is held across
per-team synchronous transactions; no inverse instance→schedule/run row lock is introduced.
Read run fields as scalar rows (no stale identity-map state). Current runs must all be completed
or have a single common noncompleted current_round; mixed active rounds return409 without
pointer changes. Derive instance pointer from that authoritative common current_round (or max
completed current_round if all completed), never target_round+1 from stale input. Preserve
paused/archived status if observed at reconciliation; otherwise set active/completed accordingly.
AdvanceOut.round and results describe the requested target; next_round is the reconciled active
round, or null when all runs completed. This does not make the multi-team batch atomic: earlier
team commits survive ordinary later-team failures; reset explicitly clears all of them.
Initialization concurrent with reset is outside this packet; future initialization must use the
same instance lock and must not recreate a run during final reconciliation.

Delete scoped rows in dependency order: RoundScheduleTeam then RoundSchedule; host members
then hosts; SimulationSheet/Checkpoint then Run; every historical round model in reversed
round_models.ALL_TABLES order (including RoundResult, TeamState, architecture, signals, debt,
TCO and governance); GradeOverride and GradeConfig. Explicit instance predicates everywhere.
Set current_round=0, started_at=None, completed_at=None, leave status=setup. Preserve instance
ID, pack key/version/digest, settings,total_rounds and all course/section/team/enrollment/users.
Repeat reset is harmless. Refuse active/paused/completed/archived reset without any row changes.

## Files and exclusions

Allow new `backend/app/services/host_lifecycle.py` scoped promotion helper if useful;
`app/simulation/service.py`, `app/api/runtime_host_platform.py`, `app/services/platform.py`,
`app/api/runtime_round_control.py` final reconciliation;
new0013 migration; focused tests; existing minimal service/game/portability/round-control and
lifecycle fixture inventories may add required host/model tables only. No weakening assertions,
no schema-existence checks/no ignored missing-table exceptions in production. No new score
factor, casepack branch, API payload shape, provider, initialization, archive or assignment rule.
Docs/CONTRACTS/findings updated; current scope0012 regression pinned to0012 (not future head).

## Required evidence and falsification

| Check | Command/home and failing plant |
|---|---|
| Timing/atomicity/retry/result parity | new test_host_lifecycle.py: successful advance promotes exact due rows, other scope/future/null/malformed/retired unchanged; final horizon; retry full snapshot unchanged; inject exception after promotion to require total rollback; compare payload/checkpoint digests with no-host control run |
| Historical repair | same test module: migrate populated0012→0013 on SQLite and explicit dedicated PostgreSQL, exact status-only delta including completed; rerun same update no additional delta; downgrade leaves statuses and data unchanged |
| Authoritative create/member round and pending-only API | same module or new test_host_lifecycle_api.py: stale instance pointer, run at newer editable round; stamps follow run; active/retired rename/add/remove409; own pending success; foreign IDs404/403 |
| Manual/scheduler parity | existing real test_round_control_api/test_scheduling fixtures extended with host/member; actually invoke both advance entry points, assert identical activation boundary and result bytes |
| Reset scope/inventory/rollback | test_host_lifecycle.py or test_lifecycle_api.py: real populated initialized+legacy+host rows in two scopes; target clears ALL declared runtime tables, preserved identities/digest/roster/settings, other scope byte-identical, repeat reset; rejected statuses exact snapshot; injected failure rolls all changes back |
| PostgreSQL serialization | opt-in dedicated HOST_LIFECYCLE_POSTGRES_URL (strict loopback, prefix mis_sim_verify_host_lifecycle_, destructive fixture isolated from other targets): hold advance/host-edit run lock and attempt reset; release, require linearized cleanup, no deadlock/remnant/cross-instance changes; deterministically pause manual API after last service commit and before reconciliation, commit reset, resume and require409 with setup/round0/empty runtime; reverse order must refuse reset; stale identity-map and newer-run pointer must not regress |
| Browser | fresh seed, student creates pending host; staff advances; student sees active and cannot edit; final browser diagnostics/screenshots. Reset route and scope also independently exercised by API |
| Final gates | make check with separate disposable PostgreSQL scope, lifecycle and concurrency URLs; fresh PG verifier; lint/build; independent backend and browser audit with reviewed source hashes |

At least timing, pending-only write and reset-remnant assertions must be observed failing
against predecessor behavior (via isolated predecessor functions or temporary restored source
copies, never leave mutations). Migration tests must start from actual0012, not create_all.
Failure tests must check persisted state, not only exception text. Add host tables to explicit
fixtures; normal games with no hosts must retain existing deterministic fixture outputs.

Proposed CONTRACTS addition after host scope paragraph: host lifecycle derives from locked
SimulationRun.current_round; pending valid due hosts become active atomically with first
advance, never beyond final current_round; only pending editable hosts mutate; reset clears
all scoped runtime state and timestamps while preserving setup identities/pack/roster. Migration
0013 repairs only valid overdue historical pending statuses; downgrade cannot undo that repair.

DoD: all above pass on final candidate, required PG cases not skipped, both fresh independent
audits ACCEPT. No merge/deployment implied; READY-003 start, READY-AUD-BE-002 archive and
READY-004 performance remain owned separately. Backend model/SQL propagation remains business
metadata and must never alter immutable result/checkpoint values or deterministic engine output.
