# M2 specification reconciliation

**Review date:** 2026-09-15  
**Reviewed base:** `652c28b292630b944562634162d21dc87f174c50` (`build/north-star-foundation`)  
**Method:** read-only comparison of `GOVERNANCE.md`, `SPEC_PROTOCOL.md`, the north star,
`design/06-plan-index.md`, all five Phase 2 specs, the Alembic revisions, the current
backend/frontend tree, and the existing guards/tests.

## Decision

M2 is the correct next milestone, but the five historical specs are **not dispatch-ready as
written**. The useful foundation is present: the typed loader and validator, 16 legacy round
tables with non-null `instance_id`, the versioned M1 run/sheet/checkpoint tables, the lock and
advance methods, and the existing instance-partition canary. The platform entities, foreign
keys to an instance entity, scheduling table/service, auth implementation, registry, and
browser login do not exist.

The immediate dispatch should be a corrected 2.1 hierarchy contract/build. It must first settle
the identity and pack naming seams that the other four specs currently assume differently.

## Current tree facts

The current migration chain is baseline `20260726_0001`, round-runner `20260822_0002`, and
M1 simulation `20260914_0003`. There is no `simulation_instance`, `course`, `section`,
`team`, `enrollment`, `user`, `round_schedule`, or `casepack` registry table. The only
platform API routes are health and the `/api/auth/{path}` 501 stub; the frontend has a token
preview and a 404, with no login route.

The round model has these 16 tables, all with a non-null integer `instance_id`, but none has a
foreign key to a future `simulation_instance`:

```
team_state, arch_node, arch_edge, deployment_org_state, platform_service, org_unit,
it_staff, governance_state, policy_decision, stakeholder_alignment, in_flight,
decision_line, signal, debt_item, tco_forecast, round_result
```

M1 also adds `simulation_run_v1`, `simulation_sheet_v1`, and
`simulation_checkpoint_v1`. Their `instance_id` values are non-null; sheet and checkpoint
have composite foreign keys to `simulation_run_v1`, while the run itself has no instance FK.
The existing round reads use `app.round.snapshot._scoped(...)` and several `session.get(...)`
calls. There is no `ScopedRepo` class.

There is one production pack at `backend/packs/riverside_grocery`, validating 0 errors and 0
warnings. `backend/tests/fixtures/packs/minimal_valid` is a valid second vertical fixture
(`harbour_vet_group`, 4 rounds), but it is not a production pack and is not registered or
bound to a platform section. No registry or pack cache exists. M1's `SimulationService`
stores `pack_key`, `pack_version`, and `pack_digest` on each versioned run and receives a
`RuntimePackV1` directly from a filesystem path.

## Packet-by-packet status

### 2.1 — hierarchy

**True at this base:**

- An Alembic baseline exists and the hierarchy model classes are absent.
- No current application code depends on `Course`, `Section`, `Team`, or `Enrollment`.
- `handoffs/1.6-round-runner/spec.md` does name the runtime tables and requires non-null
  `instance_id`.

**False or stale:**

- The preflight User row is known false: there is no User model. The spec correctly calls this
  a fork, but the user identity fields, role authority, password lifecycle, and ownership
  need to be made an explicit 2.1/2.4 contract before implementation.
- The claim that this is a one-baseline greenfield is stale: the tree already has two later
  migration revisions and M1 tables.
- The seed command `python -m app.seed.demo --cohort` does not exist. The current demo CLI
  accepts `--scenario`, `--with-signals`, and `--full` only, and seeds a single Riverside
  scenario.
- The two-section/two-pack fixture required by the purpose, seed, and DoD does not exist.
- The API route build step has no existing route contract or response shape to guard later.
- The spec names instance columns `scenario_id`/`scenario_version`, while M1's durable run
  contract calls them `pack_key`/`pack_version` and also persists `pack_digest`. The canonical
  names and relationship must be ruled before 2.5 or M1 integration will have two sources of
  pack identity.
- `CONTRACTS.md` says the canonical FK target is `simulation_instance.instance_id`, while the
  2.1 route and model text use a column named `id`. This is an unresolved identifier conflict.

**STOP:** do not dispatch a hierarchy builder until the identity naming, User ownership, pack
identity fields, and concrete seed/API surface are amended in the living contract/spec.

### 2.2 — instance scoping

**True at this base:**

- All 16 1.6 runtime tables have non-null `instance_id`; the three M1 versioned tables do as
  well.
- No FK currently points those columns to `simulation_instance`.
- The round code's existing `_scoped` queries include both instance and team predicates, and
  `backend/tests/check_instance_isolation.py` exercises two isolated instances.

**False or stale:**

- Preflight row 1 is false because 2.1 has not landed.
- The spec's exact runtime list has 13 tables. The actual 1.6 list has 16, omitting
  `governance_state`, `policy_decision`, and `stakeholder_alignment`. This is an explicit
  §7 conflict and a STOP, not an implementation choice.
- The required `ScopedRepo` does not exist. The current protection is a helper plus caller
  discipline; `session.get` also bypasses that proposed repository abstraction.
- The specified path `backend/tests/test_instance_isolation.py` does not exist. The current
  executable is `backend/tests/check_instance_isolation.py`.
- The current canary uses two instances of the **same** Riverside pack and does not create
  sections, users, or real registered pack versions. It proves partitioning of seeded rows,
  not the M2 two-section/different-pack gate.
- The spec does not mention the three M1 `simulation_*_v1` tables. They are runtime state
  and must be included or explicitly excluded with a justified direct/composite-FK rule.

**STOP:** the 13-vs-16 table contradiction and the missing M1 table decision must be resolved
before any FK migration or repository refactor is dispatched.

### 2.3 — round scheduling

**True at this base:**

- `RoundRunner.lock(round)` and `RoundRunner.advance(round)` exist.
- The 1.6 O3 decision is recorded: resolution happens at advance, not lock.
- No `round_schedule` table, scheduler, deadline reader, or timing API currently exists.
- No APScheduler or Celery dependency is present, so a separate entrypoint is necessary.

**False or stale:**

- `simulation_instance.settings` is absent because 2.1 is absent.
- The proposed route calls `lock(instance, round)` and `advance(instance, round)`, but the
  actual runner requires `(session, pack, instance_id, team_id)` and operates one team at a
  time. A schedule row is per instance/round, so the spec must define how it enumerates teams,
  handles a partial lock/advance, and resolves a pack for each team.
- The route step's second pass tests “round not yet advanced,” but the schedule model in §5.1
  does not list an `advanced_at` or equivalent state. This is an internal spec contradiction.
- “Management command” is not a framework concept in this FastAPI tree. The concrete command,
  process invocation, timezone policy, and retry/transaction behaviour are unspecified.
- The dependency list is stale: the spec says 2.2's `ScopedRepo` is already present and
  preflight row 5 expects it, but it is absent.

**STOP:** scheduling semantics must be rewritten around the real team-level runner and a
concrete clock/entrypoint contract before dispatch.

### 2.4 — auth, roles, route protection

**True at this base:**

- `backend/app/api/auth.py` is the 501 catch-all stub.
- `python-jose`, `passlib[bcrypt]`, `bcrypt`, and `python-multipart` are pinned.
- `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES` exist in config.
- There is no frontend login implementation yet, and no current route outside the stub relies
  on its 501 response.
- The preflight correctly predicts that a User model must be created or extended; it is absent.

**False or stale:**

- Enrollment is absent, so the proposed `get_current_instance` resolution route cannot yet
  be implemented.
- The historical spec says the login screen is out of scope until 3.1 and marks browser UI
  N-A. The north star now explicitly assigns the login surface to M2 auth and requires it
  before the auth canary. This must be amended in 2.4; 3.1 must not inherit an implicit auth
  deliverable.
- The token rules for instructors/admins (“resolve from the route's section context”) have no
  section route contract, and the spec does not define how a staff token selects or is checked
  against a section/instance. This is a scope/security ambiguity.

**STOP:** reconcile login ownership with the north star and define staff section context,
Enrollment lookup, token claims, route paths, and the browser host pair before dispatch.

### 2.5 — casepack registry

**True at this base:**

- The typed loader exists and Riverside loads.
- The validator CLI exists, returns exit 1 for an ERROR fixture, accepts `--json`, and returns
  Riverside as 0 errors/0 warnings.
- A second valid vertical exists as a test fixture: `minimal_valid` validates clean as
  `harbour_vet_group`.
- `pack_key` is snake case and `pack_version` is semver in the typed schema.

**False or stale:**

- The specified preflight command `python -m app.casepack.loader <path>` is not a loader demo;
  the module has no `__main__` invocation and returns without parsing (apart from a runtime
  warning). The preflight must call the function or the existing validator/CLI explicitly.
- `simulation_instance.scenario_id` and `scenario_version` do not exist.
- No `casepack` table, registry service, register/list command, cache, bind operation, or
  `docs/casepack-operations.md` exists.
- `backend/packs` has only Riverside. The valid second pack is test-fixture content, not the
  “two real packs registered and bound” seed required by the spec.
- M1's `SimulationService` reads a `RuntimePackV1` from a path and pins its digest on the run;
  the registry spec does not say how registry rows produce that object, how the digest is
  checked, or how the existing service is changed without creating a second pack source.
- The spec's “nothing out of scope reads packs from disk” claim is incomplete: demo,
  calibration, and simulation-content entrypoints still accept/load filesystem paths. Their
  status and migration path to the registry must be named rather than hidden by a narrow grep.

**STOP:** define registry-to-`RuntimePackV1`/digest integration, production versus fixture
second-pack policy, and the filesystem immutability/read path before dispatch.

## Cross-packet blockers and required amendments

The following living-spec amendments are required before implementation dispatch:

1. **Canonical platform identity.** Choose the actual primary-key column name for the instance
   and use it consistently with `CONTRACTS.md`, all FK targets, token claims, and route
   parameters. Choose one canonical pack tuple (`pack_key`, `pack_version`, `pack_digest` or
   renamed equivalents) and map the historical `scenario_*` wording to it.
2. **Runtime table inventory.** Replace 2.2's 13-table list with the verified 16-table 1.6
   inventory and add a ruling for `simulation_run_v1`, `simulation_sheet_v1`, and
   `simulation_checkpoint_v1`. State whether each gets a direct instance FK or is covered by
   a composite parent FK, and require all reads/writes in both `app.round` and `app.simulation`
   to satisfy the scope guard.
3. **Hierarchy contract.** Define User creation/ownership, course/section/instance/team
   cardinalities, enrollment roles and uniqueness, concrete API route/response shapes, delete
   semantics, and the reproducible cohort seed. The seed must include two sections, two
   validated pack versions, teams, and users, or the M2 gate cannot be exercised.
4. **Repository/isolation contract.** Either introduce the proposed `ScopedRepo` and migrate
   all current `session.get`/select paths, or amend the spec to a different enforceable guard.
   Name the actual canary path and make it run two different validated packs with real state;
   retain the existing same-pack check as a regression.
5. **Scheduling contract.** Define per-team versus per-instance lock/advance semantics,
   partial-failure/idempotency rules, `advanced_at` (or its replacement), grace/deadline
   timezone semantics, and one concrete manually runnable entrypoint whose only clock read is
   at the boundary.
6. **Auth/browser contract.** Move the design-system login surface into 2.4 per the north
   star. Define student and staff section context, route guards, token claims, error/status
   states, same-host auth canary, and the exact boundary handed to 3.1.
7. **Registry contract.** Define registry row-to-loader-to-`RuntimePackV1` construction,
   digest pinning, registration path policy, cache scope, duplicate/version behaviour, instance
   binding, and whether the existing `minimal_valid` fixture becomes the M2 second-pack seed.
   Include the open validator class item OS-D1/numeric-range coverage in the registry preflight
   and closing checks; do not silently treat “validator invokes” as proof that the full gate is
   covered.
8. **Living-document and audit updates.** Amend `CONTRACTS.md`, the relevant 2.x specs, and
   the M2 handoff/DoD together. Each schema-contract packet needs the independent spec review
   required by `GOVERNANCE.md §6.2` before a builder is dispatched; each builder still needs a
   fresh independent audit.

## Recommended bounded order

1. **Supervisor amendment/review packet (no implementation):** apply the eight rulings above
   and record the exact M2 gate, allowlists, and acceptance commands. This closes the current
   NS-005 reconciliation work.
2. **Corrected 2.1 hierarchy:** build the platform entities, User identity foundation, and
   two-section cohort fixture. This is the first implementation packet and the dependency for
   every request guard.
3. **2.2 scoping/isolation:** add the complete FK set and enforceable repository/read guards;
   prove the two sections on different validated packs with real state. This is a schema
   contract and should be dispatched with Heavy review/audit.
4. **2.5 registry:** register/validate/cache/bind the two packs and integrate the registry
   with M1's pack identity and digest. It can run in parallel with 2.2 only after 2.1's naming
   contract is accepted.
5. **2.4 auth plus login surface:** implement token/dependency guards and the M2 browser login
   route against the completed hierarchy and scope contract; run the same-host auth canary.
6. **2.3 scheduling:** implement schedule persistence and fixed-time ticking against the real
   team-level runner and registry, then verify lock/advance idempotency and the seeded cohort.
7. **M2 integration gate:** run both sections on different registered pack versions, assert
   zero cross-scope access, verify migration restrictions and reversibility, and reproduce the
   browser login plus authenticated request on the actual app/API host pair. Do not claim M2
   complete from isolated packet tests alone.

## Evidence commands used

```text
git rev-parse HEAD
find backend/alembic/versions -maxdepth 1 -type f
rg -n 'simulation_instance|Course|Section|Enrollment|round_schedule|ScopedRepo' backend/app backend/alembic backend/tests
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend python - <<'PY'
from app.round import models as m
from app.simulation import models as sm
print([x.__tablename__ for x in m.ALL_TABLES])
print([x.__tablename__ for x in (sm.SimulationRunV1, sm.SimulationSheetV1, sm.SimulationCheckpointV1)])
PY
cd backend && PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=. python bin/validate_casepack packs/riverside_grocery
cd backend && PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=. python bin/validate_casepack tests/fixtures/packs/minimal_valid
```

No application, test, spec, or shared document was changed by this reconciliation.
