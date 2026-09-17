# M5 instructor operations audit

Date: 2026-09-18  
Commit audited: `6cf144f` (`feat: add bounded instructor setup workspace`)  
Contract: [instructor-ops-contract.md](./instructor-ops-contract.md)  
Result: **FAIL**

The commit stays within the allowed implementation files and the ordinary focused and
regression tests pass, but the bounded handoff's team-invariant, setup-state, and browser
acceptance gates are not closed.

## Findings

### F-01 — assignment max is not concurrency-safe on the SQLite test backend; no PostgreSQL proof

Severity: high  
Contract references: acceptance 7 and 8

`EnrollmentService.assign_team` locks the target `Team` with `with_for_update()` before
counting members (`backend/app/services/platform.py:287-302`). SQLite ignores that clause.
With `team_size_max=1`, two simultaneous PATCH requests assigning two different enrollments
to the same team both returned `200`, and a follow-up query found two persisted members:

```text
concurrent [(200, {... "enrollment_id": 1, "team_id": 1}),
            (200, {... "enrollment_id": 2, "team_id": 1})]
persisted_count 2
```

The handoff explicitly requires the losing transaction to receive `409` and the persisted
roster to remain valid. The commit adds no concurrency test and no disposable PostgreSQL
run. The target lock may serialize the max check on PostgreSQL, but the required evidence is
absent; the source team is also not locked when moving a member, so concurrent moves can
violate `team_size_min` even on PostgreSQL.

### F-02 — unassigning can leave a team below `team_size_min`

Severity: high  
Contract reference: roster/team-assignment contract and acceptance 7

The minimum-size check is guarded by `if team_id is not None`
(`backend/app/services/platform.py:281-286`). Sending the documented `null` unassignment
therefore skips the check. In an adversarial API run with `team_size_min=2`, one member was
assigned to a team and then unassigned; the response was `200` and the team was left empty.
The mutation boundary must either reject that operation or apply an explicit setup policy
that preserves the minimum invariant.

### F-03 — extra enrollment-state route mutates an active roster

Severity: high  
Contract references: bounded setup-state scope and out-of-scope runtime mutation

The commit adds `PATCH /api/sections/{section_id}/enrollments/{enrollment_id}/state`
(`backend/app/api/instructor.py:300-315`) and permits `is_active`/`role` changes through
`EnrollmentService.update` (`backend/app/services/platform.py:307-315`). That service never
checks the section's simulation instance status. With an `active` instance, the endpoint
returned `200` and deactivated an enrollment, while the existing create and team-assignment
paths correctly reject roster changes outside `setup`. This route is extra functionality
outside the recommended bounded API and can alter a live roster after setup has ended.

### F-04 — section creation accepts impossible team bounds

Severity: medium  
Contract reference: team-size and max-team constraints at the mutation boundary

`SectionIn` (`backend/app/api/platform.py:46-53`) and `SectionService.create`
(`backend/app/services/platform.py:65-70`) do not validate positive `max_teams` or the
relationship `1 <= team_size_min <= team_size_max`. A direct instructor request with
`max_teams=0, team_size_min=0, team_size_max=0` returned `201` and persisted the invalid
section. Later team operations reject the bounds, leaving an unusable setup instead of
rejecting the setup mutation.

### F-05 — browser acceptance proof is missing

Severity: release gate  
Contract reference: acceptance 9 and the packet-completion statement

There is no browser test, screenshot, console/network capture, or other browser proof in
commit `6cf144f`. Frontend lint/build pass, but that does not demonstrate staff login,
role-gated navigation, pack selection, team creation, seeded-student assignment, student
denial, or clean browser logs. The M5 handoff says API-only success does not close this gate.

## Checks run

* `git show --stat --find-renames 6cf144f` and the commit diff: implementation is limited to
  the handoff's allowed backend/frontend files; no migration, engine, scoring, casepack
  content, or student-page edits were found.
* `SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=. pytest -q tests/test_instructor_setup_api.py tests/test_auth_guards.py tests/test_platform_hierarchy.py`
  — **14 passed**.
* `SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=. pytest -q` — **717 passed**, 39
  deprecation warnings.
* `npm run lint` — **passed**.
* `npm run build` — **passed** (Vite emitted only the existing large-chunk warning).
* Adversarial API probes covered minimum-size unassignment, active-instance state mutation,
  invalid section bounds, and concurrent assignment at `team_size_max=1`; outputs are
  recorded under the findings above.

No source files were modified by this audit.

## A5 re-audit — correction commit `946a851`

Date: 2026-09-18  
Verdict: **FAIL — residual concurrency evidence and browser gate**

The correction commit closes F-02, F-03, and F-04 from the original audit:

* The `assign_team` minimum-size check now runs for `team_id=None`; a sole-member
  unassignment returned `409`.
* The out-of-scope `/enrollments/{id}/state` route and its unguarded service method were
  removed; the same request now returns `404`.
* `SectionIn` rejects zero and inverted bounds with `422`, and the service rejects invalid
  bounds before persistence.

Focused correction tests pass: `4 passed, 1 skipped`. The skip is the new PostgreSQL test,
which requires an explicitly supplied `M5_POSTGRES_URL`.

F-01 remains unresolved as an acceptance/evidence issue. The correction locks the section
parent before assignment (`backend/app/services/platform.py:277-301`), which should
serialize assignments on PostgreSQL, and adds a real two-connection PostgreSQL test.
However, the test is skipped in the normal environment and the attempted local check with
`postgresql+asyncpg://mis_sim:mis_sim@127.0.0.1:5438/mis_sim` failed authentication. A fresh
SQLite race still produced two `200` responses and `persisted_count 2` for a team capped at
one, because SQLite ignores `FOR UPDATE`. Therefore the required concurrency proof is not
closed by this commit.

The browser proof remains outstanding for the root audit: no staff/student Playwright run,
console/network capture, or browser artifact was added by `946a851`.

Commands run for A5:

* `SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=. pytest -q tests/test_instructor_setup_api.py`
  — **4 passed, 1 skipped**.
* Adversarial API probes — bounds `422/422`; sole-member unassign `409`; active state route
  `404`.
* SQLite two-connection assignment probe — **both 200, persisted count 2**.
* `M5_POSTGRES_URL=... pytest -q tests/test_instructor_setup_api.py::test_assignment_concurrency_postgres_serializes_team_max`
  — could not connect: PostgreSQL rejected the repository credentials.

## A6 re-audit — projection, selection race, and browser proof

Date: 2026-09-18  
Corrections: `35f4968`, `9ec2156`

The setup aggregate projection and frontend selection behavior are now corrected.

* `35f4968` projects initialized teams as the aggregate's `TeamSummary` shape while
  preserving the detailed team endpoint. The initialized-section regression passes.
* `9ec2156` prevents stale asynchronous setup loads from overwriting a newer course or
  section selection. A delayed-response Playwright race probe kept the user's newer
  selection.
* A seeded browser flow logged in as staff, opened `/instructor/setup`, selected Section C,
  exercised the pack/team/roster controls, saved `/tmp/m5-instructor-setup.png`, and then
  verified that a student session is redirected from the protected instructor route to
  `/login`. No unexpected page errors or failed requests were observed. The login flow's
  expected `409` section-choice and `403` authorization responses are handled by the UI.

Focused validation after the corrections: `31 passed, 1 skipped`; frontend lint and build
pass; `git diff --check` passes. The opt-in PostgreSQL concurrency proof remains skipped
without a working `M5_POSTGRES_URL`, and SQLite still cannot prove row-lock semantics.
Therefore the bounded browser/UI and API projection gates pass, while the overall setup
slice remains open until production-database concurrency evidence is captured.
