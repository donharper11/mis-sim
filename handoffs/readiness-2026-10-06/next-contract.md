# Next readiness contract — host-platform scope and lifecycle

Prepared 2026-10-06; **proposal for independent review, not an approved schema change**.
Risk: Heavy for the scope/FK contract. Instructor initialization tier must be settled after
its strategy/scored-state semantics are specified (not assumed Light).
The scope-only successor `host-scope-contract.md` has passed independent dispatch review
(`contract-independent-review.md`); this umbrella proposal still leaves lifecycle/start open.
Current acceptance evidence is in `../../docs/readiness-2026-10-06.md`.

## Verified basis and unresolved boundary

- [V] `backend/app/models/host_platform.py`: `HostPlatform` has `instance_id` and `team_id`;
  `HostPlatformMember` has only `platform_id`. The new member table does not satisfy
  `CONTRACTS.md`'s non-null runtime `instance_id` rule.
- [V] `backend/tests/check_instance_scope_schema.py` intentionally guards the original
  19-table inventory. It does not guard host-platform membership or newer runtime tables.
- [V] `backend/app/api/runtime_host_platform.py`: creation writes pending status and an
  `activated_round`. No production advancement path currently promotes these rows to active.
- [V] `backend/app/services/platform.py::reset_instance`: explicit deletion inventory
  omits both host-platform tables. Existing member rows can survive reset.
- [V] `backend/app/api/runtime_round_control.py`: advancement refuses teams without a
  `SimulationRunV1`. No instructor API invokes `SimulationService.initialize`; setup and
  clone therefore do not by themselves produce a playable game. The new disposable seed
  provides an operator rehearsal route, not production onboarding.

## Proposed scope contract

1. Add non-null `HostPlatformMember.instance_id`, backfilled from its existing parent.
   Use a composite FK to `(host_platform.id, host_platform.instance_id)` and a direct
   instance FK. Preserve existing IDs and member rows. Refuse orphaned/inconsistent input
   before enforcing the constraint; do not silently delete it.
2. Ensure parent platform/team belongs to the same instance, enforced by a composite
   relationship with `Team` after inspecting its actual unique constraints.
3. All member creation/query/deletion/relationship paths include instance scope. Retain
   student team selection and locked-round guards. Preserve existing response fields.
4. Extend the scope/schema canary to the current runtime inventory without deleting the
   historical 19-table regression. Verify real PostgreSQL migrations and SQLite test support.
5. Add constraints for valid member kinds and unambiguous deployment assignment only after
   resolving catalog-key versus concrete-asset semantics. Today both forms exist. The next
   author must define that migration/compatibility boundary explicitly.

## Lifecycle and initialization decisions to settle

- Define when a pending host becomes operational relative to round advance and authored
  asset arrival. The UI currently claims an operational platform cannot be edited; this
  needs one explicit server rule applied to both scheduler and manual paths.
- Define whether resetting a setup instance clears all host/member metadata; recommended:
  clear it with runtime rows while preserving course, roster and pack binding.
- Add an instructor-owned start/initialize action for setup instances. Recommended:
  initialize every eligible team atomically or report per-team reconciliation explicitly,
  verify pinned pack digest, refuse empty teams/invalid pack, and make retries idempotent.
  Do not infer a student strategy; reconcile `initialize`'s strategy argument with the
  Strategy screen before specifying the production start command.

## Required preflight and closing evidence

- Inspect the actual PostgreSQL host/member/team constraints and migration head.
- Plant mismatched member/parent instance and mismatched parent/team instance; both must
  fail at the database boundary. Re-run cross-team, cross-section and unassigned-student API
  probes with a real member row, including rename/add/remove/rollout projection.
- Migrate a populated pre-change database and compare all retained identities/rows.
- Initialize through the instructor browser, sign in as an assigned student, make a choice,
  lock and advance; no out-of-band DB edits. Repeat start to prove retry behavior.
- Advance by manual API and scheduler; verify host status at the same boundary. Reset a
  disposable setup instance and prove no host/member remnants in it or cross-instance loss.
- Re-run `make check`, PostgreSQL verifier and browser proofs. Independent review must
  precede schema implementation; a fresh auditor must verify the final candidate.

The user authorized prioritizing remaining work. This document makes the next contract
reviewable without silently inventing missing lifecycle or assignment semantics.


## Performance follow-up evidence

The readiness profile shows 82,445,652 calls for one full round-one `SimulationService.read`,
with 16.806s cumulative in the pack's defensive-copy getter. The existing bounded harness
snapshot in `backend/app/simulation/games.py` is an inspectable starting point, not automatic
permission to weaken immutability. A proposed optimization must keep operation-local content
isolated, preserve pack/checkpoint digests and byte-equivalent preview/result payloads, and
prove that mutating any returned view cannot affect another team, call or cached pack.
Profile evidence: `../../findings/readiness-2026-10-06/profile.log`.
