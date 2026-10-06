# Independent contract review — readiness follow-up

Date: 2026-10-06. Reviewer: `/root/contract_review`, independent of author; no implementation performed. Reviewed original `next-contract.md` (78 lines) against working tree at HEAD `0a535ba23e2571bbb2fd691d52afb62a0a874977`. This is a preimplementation review, not a runtime audit. No shared database was modified.

## Verdict

**RETURN TO AUTHOR before builder dispatch.** The proposal correctly identifies unresolved decisions and does not pretend to approve them. It is a useful backlog boundary, but not yet the dispatch specification required by SPEC_PROTOCOL §11. Scope integrity can be dispatched independently after the author freezes the narrow decisions below; activation, initialization, reset, assignment semantics and performance need not block that packet when explicitly excluded and owned.

## Findings and exact closing requirements

- **NCR-001 — scope migration is underspecified (owner: author).** `next-contract.md:25–34` does not define deletion behavior, parent candidate key, replacement versus retention of old FKs, downgrade, or full invalid-history cases. `models/host_platform.py:29–85` has no `(id, instance_id)` unique constraint; `models/platform.py:110–111` already has `uq_team_instance_identity(id, instance_id)`. Freeze named parent/member constraints, migration failure before writes for orphan members, orphan host instance/team, and mismatched host/team instance; preserve every existing field and ID on valid rows. Specify PostgreSQL transactional rejection and whether SQLite support means migration execution or metadata/create_all only. Closing check: author supplies exact constraint/action table and executable disposable PostgreSQL preservation, invalid-history and downgrade checks; final audit independently runs them.
- **NCR-002 — scope consumers and compatibility are not enumerated (owner: author).** Member construction is `api/runtime_host_platform.py:255`; member removal currently performs an unscoped `session.get` at line284; selectin relationships occur at lines128/243; rollout joins at `api/runtime_rollout.py:168–171`. A parent composite FK must not leave ambiguous or single-column ORM relationship joins. Freeze public request/response shapes (no required client instance field), retain team selection and round locks, and identify every production/test constructor. Closing check: explicit scoped SQL/load/delete and write-path tests, plus browser CRUD and rollout projection using a real persisted member; planted removal of member scope or join must fail the designated guard/test.
- **NCR-003 — canary inventory and proof are not dispatch-ready (owner: author).** `tests/check_instance_scope_schema.py:14–40` intentionally guards nineteen original runtime tables and historical migration declarations. Newer grading, scheduling and host tables have different deletion rules; `RoundScheduleTeam` has a composite instance-bearing parent FK rather than a direct instance FK (`models/scheduling.py:55–70`). Freeze the exact added inventory and expected FK behavior per table instead of silently repairing unrelated schemas. Closing check: existing nineteen-table regression stays green; new reachable-from-`make check` guard fails when member scope/nullability/composite FK is deliberately removed; PostgreSQL proves mismatched member/parent and host/team rejection for inserts and updates.
- **NCR-004 — proposal acceptance mixes independent products (owner: author).** `next-contract.md:59–62` requires instructor start, lifecycle advance and reset although lines39–50 leave their behavior unresolved. No implementer can satisfy those acceptance rows without making author decisions. Closing check: narrow scope packet has its own DoD and browser playthrough, while remaining items have named future ownership and no implied approval. Map every scope acceptance row to a specific command/test and add one concrete compliant implementation route, per SPEC_PROTOCOL §11.

## Factual clarifications

- CONTRACTS `instance_id` entry requires a nonnullable instance FK and scoped reads/writes. It does **not** prescribe RESTRICT globally. RESTRICT belongs to the original nineteen-table migration/guard; host and grading instance FKs currently CASCADE. My preliminary message overstated the CONTRACTS rule; this report corrects it. Choosing RESTRICT for host/member is an author decision that requires deletion-ripple tests, not compliance with an already-existing global restrictive rule.
- Team's composite candidate key already exists; no Team unique-constraint addition is required merely to reference `(id, instance_id)`.
- `InstanceService.delete` always rejects direct instance deletion (`services/platform.py:160–170`). Section deletion deletes teams and instance through ORM (`:91–110`). If host/member direct FKs change to RESTRICT while host/team and member/host remain CASCADE, verify real flush/cascade ordering on section deletion with populated metadata; do not infer it from statement order.
- Reset retains host and member rows because it deletes neither table and preserves teams (`services/platform.py:414–461`). This is an existing residue, not a requirement to couple reset implementation to the scope migration.
- Initialization is currently non-idempotent: `SimulationService.initialize` rejects any existing legacy/runtime rows and commits one team's run/checkpoint/sheet in its own transaction (`simulation/service.py:261–297`). An atomic batch wrapper cannot simply call it repeatedly and claim all-or-nothing behavior. Strategy requires a valid key; the Strategy screen submits `declare_strategy` to an existing sheet (`api/runtime_controls.py:231–234`). Initial strategy, replay reconciliation and partial-batch semantics must be authored before start dispatch. Calling initialization Light before those decisions are inspected may understate its scoring/contract impact.
- Host creation stamps `max(instance.current_round, 1)` and next-round activation (`api/runtime_host_platform.py:182–195`); manual advancement explicitly tolerates scheduler leaving the instance pointer stale (`api/runtime_round_control.py:114–119`). A future lifecycle contract must choose the authoritative round and shared transactional boundary, not merely update status from the presentation pointer.
- Assignment ambiguity is real: Infrastructure resolves `source_key` OR concrete asset `id` (`frontend/src/pages/InfrastructurePage.jsx:330,348`); rollout maps one asset key by ascending member ID with later assignment overwriting earlier (`api/runtime_rollout.py:171–178`). Preserve these semantics in a scope-only packet; do not introduce uniqueness by deployment, cleanup duplicate assignments, or reinterpret catalog keys.

## Smallest independently dispatchable boundary

Repair database and query instance integrity for the two existing host tables, with a populated reversible migration, explicit ORM relationships, matching CRUD/rollout scope, preserved response/assignment/status behavior and an additive schema guard. No new score factor or casepack field. Required evidence: PostgreSQL valid-row preservation and invalid insert/update/history negatives; SQLite supported path with foreign-key enforcement enabled; parent/team/instance deletion actions; authenticated two-instance/two-casepack and same-instance cross-team probes; unassigned student probes; unchanged locked/paused/completed behavior; real-browser create/rename/add/remove/rollout; clean diagnostics and screenshots; `make check`; independent final audit. An exclusion dependency search must show lifecycle/engine code does not consume the new member field.

This report does not author the replacement contract or settle its new deletion policy. Live PostgreSQL constraints were not queried by this reviewer; that remains a required author/builder preflight, not an asserted external fact.

## Re-review 1 — bounded host-scope contract

Reviewed `host-scope-contract.md` as supplied after the original review. The schema/API decisions now provide a coherent narrow implementation route: preserve CASCADE, reuse Team identity key, add host identity key, backfill member scope, replace old single-column FKs, preserve payloads and assignment/lifecycle semantics. NCR-001's author decisions and NCR-004's scope separation are resolved in this text. The original proposal remains historical, not dispatch authority.

**Dispatch verdict: RETURN for a small verification appendix.** Remaining requirements are precise and do not require new product decisions:

1. Add named new test/guard commands and a preflight/DoD mapping (SPEC_PROTOCOL §§5–6,11). Include insert **and update** mismatch cases; identify the browser script and exact seed command/environment. `frontend/tests/host-platform-proof.mjs` presently covers create, authenticated-request attach, rollout view, lock and denied rename, but not successful rename/remove; map those to a new API check or add an explicit playthrough.
2. Include executable/planned mutation proof for the guard/query invariants, separately from bad-data constraint rejection: remove member scope/composite FK or scoped predicate, run the named closing test, require nonzero, restore, require green. A database rejecting a bad row proves the FK, not that the schema/query guard would catch an omitted FK/filter.
3. Supply the exact living CONTRACTS insertion and candidate evidence/DoD rows. No new vocabulary is needed; freeze that fact explicitly. Reference inspected source paths/line anchors and name preflight checks for the live migration-head claim, rather than leaving the current `[V]` assertions uncited.

These are NCR-002/003/004 closure details; they do not reopen the settled CASCADE decision or require lifecycle/start implementation.

## Re-review 2 — dispatch acceptance

**ACCEPT FOR THE BOUNDED HOST-SCOPE BUILD**, 2026-10-06, reviewer `/root/contract_review`.
Reviewed revised `host-scope-contract.md`, SHA-256
`c6da305e6a7ddb1a41ffd0d8d8e7cf308ee8257f8b01adfd4fda384d83e7c401`.
This supersedes Re-review 1's dispatch verdict for that document only; the original broad
`next-contract.md` remains an unsettled umbrella, not implementation authorization.

The added appendix maps acceptance to named migration/API/guard test homes, insert and
update negatives on both databases, separate guard/query mutation sensitivity, a concrete
migration/ORM route, exact living CONTRACTS text and a DoD. Existing browser proof plus
explicit API rename/remove acceptance matches the current UI, which has no rename/remove
controls. The reproducible fresh seed and local browser server instructions already exist
in `docs/readiness-runbook.md:24–70`; use that isolated setup for the named browser command.
Original findings NCR-001 through NCR-004 are resolved **at specification level** by the
bounded contract and its appendix; none is a claim that runtime defects are fixed.

SPEC_PROTOCOL §11 consistency outcomes:

1. Acceptance rows map to concrete test/guard/browser code homes: PASS.
2. Invariants specify bad-data negatives and independent guard/query falsification: PASS
   for dispatch definition. Builder/auditor must record observed failing plants and restored
   green checks; this review does not claim future tests were run.
3. Field shape/deletion behavior reconciles with models and living CONTRACTS via explicit
   proposed migration/text: PASS. Live PostgreSQL preflight still must be recorded before DDL.
4. One compliant migration/query implementation route is written: PASS.
5. Host-only guard and downstream CRUD/rollout/ORM consumers are enumerated, no new public
   vocabulary/response field is introduced, historical nineteen-table guard stays intact: PASS.

Required independent implementation audit remains open. It must verify populated PostgreSQL
and SQLite upgrade/downgrade/re-upgrade, every invalid-history refusal, constraints and query
scope plants, CASCADE preservation, authenticated/browser flow and final candidate evidence.
Do not mark activation, reset, instructor initialization, assignment ambiguity, or release
readiness closed with this acceptance.
