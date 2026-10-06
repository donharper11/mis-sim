# Independent lifecycle contract review

2026-10-06 · Reviewer `/root/contract_review`, not author or builder.
Spec: `host-lifecycle-contract.md`. Reviewed against current advance, scheduler, host APIs,
reset/instructor API, runtime models, lifecycle/game/service fixture inventories and existing
scope0012 regression. No implementation performed or replacement specification authored.

## Initial verdict: RETURN TO AUTHOR

The activation boundary, final horizon, pending-only edits and status-only historical
migration/no-op downgrade are coherent. The proposed shared advance hook fits the existing
single-run transaction and retry boundary. Reset's proposed schedule→run ordering and
NO KEY UPDATE choice address the host insertion FK lock inversion. One cross-transaction
boundary remains unresolved before dispatch.

- **HLC-001 — manual advance can overwrite a completed reset (Blocking; owner: author).**
  Spec lines50–57 promise reset/advance linearization but only serialize against the run
  transaction. `api/runtime_round_control.py:158–176` calls `SimulationService.advance`
  in its own transaction, then later updates `SimulationInstance.current_round/status`
  in the async request transaction. The reset can hold the instance lock, wait for advance's
  run lock, clear the just-committed run/result/host rows and commit; afterward the already
  executing manual request can write `active`/next_round back onto the reset instance.
  This is not covered by merely holding a run lock in the required PostgreSQL test. Freeze
  a compatible fence/reconciliation rule for the manual endpoint's final instance write,
  add that code home to the allowlist if needed, and test a real request paused after the
  service commit but before final instance reconciliation. Expect a setup round0 instance
  with no runtime remnants after reset wins, and no stale later pointer/status rewrite.
  Include the reverse ordering: committed instance activation must make reset refuse.
  Closing check: a deterministic two-transaction/request PostgreSQL test with those barriers
  fails under predecessor behavior and passes under the frozen solution.
- **HLC-002 — malformed timing needs an overflow-safe evaluation boundary (Functional;
  owner: author).** Spec lines27–29/40–43 says malformed host timing remains untouched.
  `models/host_platform.py` stores unconstrained Integer timing fields. A literal SQL
  `created_round + 1` may overflow for legal historical Integer data, so one malformed row
  can abort reconciliation or advance instead of remaining untouched. Independently ran
  `psql -h 127.0.0.1 -p 44535 -U readiness -d postgres -c 'SELECT 2147483647::integer + 1'`;
  result: `ERROR: integer out of range`. Author must freeze overflow-safe evaluation or an
  explicit malformed-input alternative consistent with the unchanged-row promise. Closing
  check: extreme historical timing rows plus valid due rows on actual PostgreSQL and SQLite;
  only the valid due rows change, no transaction abort. Do not rely on WHERE evaluation order.

## Factual/verification clarifications

- Actual class is `Scheduler` (`app/scheduling/service.py:74`), not `SchedulingService`.
  Its leased production service calls lock/check a schedule in
  `SimulationService._verify_schedule_claim`, then acquire the run. Manual no-claim service
  calls acquire the run only; scheduler orchestration also commits participant metadata
  separately. Preserve that distinction when describing the locking proof.
- Foreign-ID404 statements need an explicit precedence/context. Existing host API calls
  `_require_editable` before selecting the authorized parent. A caller with a locked own
  run gets409 before a foreign parent can be tested; a forbidden path context gets403 first.
  Preserving that ordering is valid, but do not require universal404 for every foreign-ID
  request while also declaring those guards unchanged.
- The reset instructor API already verifies ownership, commits on success and rolls back
  exceptions (`api/instructor.py:917–941`). Reset must refresh its already-loaded instance
  under lock; a bare locking SELECT without refreshing the identity-mapped object can keep
  stale status. The spec's explicit “refresh/lock” wording correctly calls for this.
- Minimum fixture ripple is real: `test_simulation_games.py:31` creates only round/simulation
  tables, `test_simulation_service.py:28` and `test_simulation_portability.py:157` enumerate
  their tables, `test_round_control_api.py:37–48` and `test_lifecycle_api.py:44–59` likewise.
  `run_game` requires an already-migrated engine rather than creating tables itself
  (`simulation/games.py:203–209`). Do not change the production harness to create missing
  tables or bypass the new host access. The explicit fixture-only allowance is appropriate.
- Reverse `round_models.ALL_TABLES` plus schedule/host/simulation/grading rows covers the
  current declared runtime inventory. Existing `reset_instance` only deletes a subset, so
  the specified two-instance all-table residue test is necessary, not a duplicate test.
- Spec must record candidate hashes and exact executed failing/green plants; this review
  is preimplementation and does not claim planned checks already ran. Separate final backend
  and browser audits remain mandatory.

No request to settle initialization, archive migration or asset-assignment semantics is
introduced by this review. Those exclusions remain valid.

## Re-review — ACCEPT for dispatch

2026-10-06 · Reviewer `/root/contract_review`.
Reviewed revised lifecycle contract SHA-256
`58c240a76024c3d0a9e28f8665a29057c3932af42a48eac2cf893bc0e05ed5ac`.
**ACCEPT the bounded lifecycle/reset build for dispatch.** This supersedes the initial
RETURN verdict for the revised document. It is not implementation or merge acceptance.

- **HLC-001 resolved at specification level.** Final manual reconciliation now rolls back
  stale reads, refreshes and locks the instance with NO KEY UPDATE, reads fresh scalar run
  fields, checks the exact entry participant set and advancement floor, and refuses vanished
  reset state before writing instance fields. Holding this instance lock makes the two
  reset/manual-final-write orderings decisive; no run/schedule row lock is taken here, and no
  instance lock spans synchronous per-team calls. Reconciliation derives its pointer from
  current run evidence, detects mixed active rounds, preserves paused/archived status and
  explicitly keeps existing per-team partial-commit semantics. The allowlist and PostgreSQL
  test requirement now include the real endpoint paused between service commit and final
  reconciliation, reverse ordering, stale identity map and newer-run evidence.
- **HLC-002 resolved at specification level.** Both shared promotion and historical
  reconciliation use the same timing predicate with `created_round` widened to BIGINT before
  incrementing. Integer minimum/maximum fixtures are expressly required. This satisfies
  unchanged malformed rows without relying on SQL predicate evaluation order.
- Actual `Scheduler` name and foreign-ID rejection precedence are corrected. Concurrent
  initialization is explicitly excluded and assigned a future instance-lock obligation;
  the packet does not claim protection against an unimplemented run-recreation protocol.

SPEC_PROTOCOL §11 consistency: each behavior maps to a named test home/browser path; timing,
write guards and reset residues have required predecessor-failure plants; field vocabulary,
status/migration rules and CONTRACTS change agree; a feasible common advance transaction plus
separate fenced manual reconciliation route exists; downstream endpoint, migration, fixture
inventory, contract and scope0012 regression homes are enumerated. No unresolved product
choice remains in the bounded text that the implementer must silently decide.

The concurrency claim is scoped to existing host edits, service advances and manual final
reconciliation. As with today's scheduler, a presentation pointer may lag a later independent
scheduled advance; the frozen reconciliation reads an authoritative scalar snapshot, and
cannot promise an eternally current pointer after its transaction ends. This does not reopen
or alter the author's stated contract.

Required final audit evidence remains unexecuted at this preimplementation stage: actual
PostgreSQL lock/barrier tests in both orders (including schedule→run ordering), migration
0012→0013 on both databases, extreme timing rows, status-only historical snapshots/no-op
downgrade, all-runtime-table reset preservation/rollback, deterministic result/checkpoint
parity, observed failing/restored plants, full checks and independent browser acceptance.
Initialization, SQLite archive repair, asset assignment semantics and release readiness remain
outside this acceptance.
