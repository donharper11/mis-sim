# Independent instructor-start contract review

2026-10-06 · Reviewer `/root/contract_review`, independent of author/build.
Reviewed `instructor-start-contract.md` against the inspected initialization, hierarchy,
reset, manual progression, scheduler, strategy and authorization contracts. No implementation
or replacement spec authored.

## Initial verdict: RETURN TO AUTHOR

The proposed explicit instructor-selected per-team strategy preserves existing scoring while
making the initial choice visible. Atomic session-owned initialization, exact team selection,
all25-runtime-table residue rejection, authored horizon equality and explicit duplicate409
are coherent choices. The section→instance setup serialization rule addresses the earlier
roster/binding race. One generation boundary remains blocking.

- **START-PR-001 — final generation check happens after stale mutation (Blocking; owner:
  author).** Contract lines78–82 checks `started_at` only at manual API final reconciliation.
  `api/runtime_round_control.py:143–162` calls `service.lock` and `service.advance` separately
  for each team. `simulation/service.py` lock/advance validate scoped run, round and sheet
  revision, with no start-generation input. Pause an old request before lock, between lock
  and advance, or before a later team; reset/start recreates the same IDs/round1/revision0;
  resume the old request. It can mutate the NEW run before its final409. The requested
  after-last-service-commit test cannot expose this. Required author closure: generation
  validation within the relevant service mutation transaction, after its scoped run lock,
  without introducing run→instance lock inversion; explicit distinction between an expected
  NULL legacy generation and omitted compatibility argument; manual/scheduler producer
  scope; deterministic tests at all three barriers with complete new-generation snapshot
  preservation. Final reconciliation fencing remains necessary but is insufficient alone.

## Smaller dispatch clarifications

- Freeze the exact active-student predicate and precedence: Enrollment role/is_active and
  User role/is_active are distinct (`models/platform.py:21–33,128–147`). The phrases “every
  active student enrollment,” “inactive students ignored” and “invalid user roles refused”
  need one consistent rule for active enrollment with inactive or non-student User. Include
  missing user/cross-scope negatives, and decide whether inactive malformed rows are ignored.
- `SimulationInstance.pack_digest` is nullable (`models/platform.py:89`). Readiness must
  represent the absent pin without response-validation failure; declare nullable response
  fields and blocked-reason behavior explicitly. GET remains read-only; it must not reuse
  the SQLite no-op write lock intended for POST/mutators.
- Map gates to named new backend test/browser homes and executable commands, and provide
  the exact living CONTRACTS insertion, as the prior accepted scope/lifecycle packets do.
  Planned tests need final observed failing/restored proof; this preimplementation review
  does not assert they exist or have run.

## Adjacent generation risk needing explicit scope ownership

Standalone round-control lock/reopen, student controls/review writes and host edits also
have round/revision/ID reuse across reset/start. The service has `patch_sheet`, `lock`,
`reopen` and `advance`; host edits use their own run lock. Capturing an old request's instance
snapshot and validating it within its actual mutation transaction can protect in-flight
requests. A stale browser tab issuing a new request *after* reset is a different problem:
the server sees the new generation unless the client sends a generation token. That requires
an API/client contract beyond the current frozen payloads. Author must explicitly choose
which in-flight mutation surfaces are fenced here and retain a named residue for any excluded
class. Do not claim universal generation-safe writes based only on an advance fence. This
review does not automatically require a new client generation-token feature in this packet.

No objection to the selected no-default instructor strategy workflow, provided any explicit
user steering received before implementation is honored. Initialization remains Heavy and
requires independent implementation/browser audit; the preceding lifecycle full gate must
finish before this packet is dispatched, as the proposed contract already states.

## Re-review — ACCEPT for dispatch

2026-10-06 · Reviewer `/root/contract_review`.
Reviewed final proposed contract SHA-256
`a05bda5b6c640ad7e23dc11ddf2a1f69ba0fe1b3498ced8ee446eaabf9eddc62`.
**ACCEPT the bounded instructor-start contract for dispatch once the preceding lifecycle
full gate is complete**, as required by its header. This supersedes the initial RETURN
verdict; it is not implementation or merge acceptance.

**START-PR-001 is resolved at specification level.** `patch_sheet`, `lock`, `reopen` and
`advance` check the originally captured timestamp after acquiring the scoped run lock and
before mutation/retry, using a fresh scalar read without an inverse instance row lock.
Explicit expectedNone is distinct from an omitted legacy argument. All existing production
mutation callers are enumerated: student platform/components/rollout/controls/review, host
metadata's equivalent guard, staff lock/reopen/advance and the actual scheduler operation.
Timestamp normalization, scheduler capture timing and final manual reconciliation fencing
are specified. The named tests now cover before-lock, between-lock/advance, later-team and
final-response barriers, all HTTP mutation homes, and complete new-generation snapshots.

A new request from an already stale tab is explicitly a separate client-token problem,
retained under `READY-START-CLIENT` with platform/API ownership. The contract makes no broader
claim and freezes current client payloads; no silent generation-token migration is implied.

Other review items are resolved: eligibility explicitly filters both enrollment and User
activity/role; invalid active student-user linkage blocks; only actual TA enrollments are
excluded (Enrollment's vocabulary is student/ta). Missing pack_digest has a nullable readiness
response. Strategy labels use the actual authored `Labels.strategies` field with formatted-key
fallback. New backend/API/concurrency/browser test homes, commands, DoD report and exact
CONTRACTS insertion are written.

SPEC_PROTOCOL §11 consistency passes for dispatch: acceptance maps to named executable homes;
atomicity/status/generation claims have deliberate-failure and snapshot checks; models/API
vocabulary and docs agree; the section→instance/session-owned initialization route is feasible;
and downstream setup mutations plus all generation-fence producers/consumers are enumerated.
The explicit strategy selection, conflict-on-duplicate rule, strict clean-runtime requirement,
no implicit schedule creation and authored-horizon equality do not contradict the inspected
existing service/scoring contracts. The public legacy initialize behavior remains frozen.

Implementation audit must independently verify actual SQLite/PostgreSQL migrations and start
transactions, each25-table residue refusal, all eligibility/auth/body cases, setup mutation
serialization, reset/start and generation barriers, no unscoped/no-fence production caller,
legacy initialize parity, predecessor mutation sensitivity and a real browser start/student/
advance flow. This review has not executed those future checks and does not bless a builder
substituting smaller test coverage. An explicit user change to pre-start strategy selection
still supersedes the proposed default before implementation, as the author states.
