# M2 dispatch record — first bounded packet

Date: 2026-09-15
Supervisor base: `376d54c` (`build/north-star-foundation`)
Milestone: M2 — real platform context

## Boundary

M2 starts with packet **2.1, Course → Section → SimulationInstance → Team →
Enrollment**. This packet establishes the hierarchy that every later M2 packet
depends on. It does not implement instance guards (2.2), scheduling (2.3), auth
(2.4), casepack registration (2.5), instructor UI, or changes to the audited
simulation transition service.

The historical 2.x specs were reconciled at `handoffs/recovery/m2-spec-reconciliation.md`.
The supervisor's identity amendment is committed at this base in
`handoffs/recovery/m2-contract-amendment.md`. In particular, the
canonical instance primary key is `simulation_instance.instance_id`, and the
canonical pack identity is `(pack_key, pack_version)`; the historical
`scenario_id`/`scenario_version` wording is not used.

The current M1 tree has 19 runtime tables: the 16 legacy round-state tables and
`simulation_run_v1`, `simulation_sheet_v1`, and `simulation_checkpoint_v1`.
Their `instance_id` values are non-null integers but deliberately have no
`simulation_instance` foreign key yet. Packet 2.1 creates that referenced
hierarchy; packet 2.2 will add the complete FK and repository guard after the
actual table list is frozen.

## Exact base and allowed paths

The builder starts from `c95892b`. The allowed implementation paths are:

* `backend/app/models/platform.py` (new hierarchy and minimal `User` model)
* `backend/app/services/platform.py` (new thin CRUD services)
* `backend/app/api/platform.py` (new unprotected CRUD routes for this packet)
* `backend/alembic/versions/20260915_0004_platform_hierarchy.py` (new migration)
* `backend/alembic/env.py` (register the new model metadata)
* `backend/app/main.py` (include the platform router)
* `backend/app/seed/demo.py` (add the deterministic `--cohort` hierarchy seed)
* `backend/requirements.txt` (declare the async SQLite test driver used by the
  async service tests)
* `backend/tests/test_platform_hierarchy.py` (new focused tests and planted
  invariant checks)
* `handoffs/2.1-hierarchy/dod.md` (builder evidence only)

No other path may change. In particular, do not edit `backend/app/round/`,
`backend/app/simulation/`, casepack content/loader/validator, auth, frontend,
or existing migrations. Do not add runtime foreign keys or a scheduler in this
packet.

## Required behavior

Implement the five-level hierarchy and the minimal `User` FK target from the
2.1 spec: integer primary keys; one instance per section; `settings` JSON;
`status` in `setup|active|paused|completed`; team rows carrying both
`section_id` and `instance_id`; enrollment uniqueness per user/section and
nullable team assignment. Resolution belongs to 2.5. The corrected contract uses
`pack_key` and `pack_version` on the instance, with `instance_id` as its primary
key. The cohort seed is structural and may use pack keys without resolving or
validating them; registry binding belongs to 2.5.

Services must provide create/read operations and narrow deletion rules. A
section cannot silently erase live runtime state. Routes are intentionally
unprotected until 2.4, but must use the service layer and must not accept or
invent runtime state.

The migration must pass upgrade → downgrade → upgrade on a disposable database.
Focused tests must prove the hierarchy constraints, duplicate-instance refusal,
team instance/section requirements, enrollment uniqueness, and that no runtime
table is read by these services. The existing M1 tests and guards remain the
regression baseline.

## Stop conditions

Stop and report with evidence if the builder encounters a table-name conflict,
an existing `User` model, an async/sync session boundary that requires changing
an unlisted file, or any ambiguity about deletion semantics. Do not resolve a
spec/code conflict by guessing.

## Gates

This is platform plumbing, so it gets build plus an independent audit. The
supervisor integrates only an audited candidate. Packet 2.2 is blocked until
the builder's exact table list and migration are independently checked; 2.3–2.5
remain blocked on the hierarchy.
