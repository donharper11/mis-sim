# Independent instructor-start browser review

Date:2026-10-07. Auditor `/root/frontend_review`, not implementation author/builder. Read the accepted instructor-start contract and current UI/API/service implementation, with governance/quality/contracts from earlier independent readiness reviews.

**Final verdict: PASS for the instructor-start technical browser/API walkthrough.** Three independently reproduced UI/API defects were corrected and rechecked. No remaining blocking browser finding in this scope. This seeded technical walkthrough satisfies the user's requested browser acceptance; no live-participant requirement is imposed.

The separate backend audit/full gate still owns transactional initialization, all eligibility cases, generation fencing, concurrency, rollback, and immutable payload equivalence. This is not production deployment approval.

## Finding reconciliation

| ID | Original independently reproduced defect | Final disposition / closing evidence |
|---|---|---|
| START-UI-001 | UI/contract use `/api/instructor/instances/{id}/start-readiness` and `/start`; backend initially registered `/api/instances/{id}/…`. Real404 prevented setup loading. | CLOSED locally. Decorators match accepted paths; fresh full UI walkthrough passed. [Before routes](browser/routes-before.txt), [after](browser/routes-after.txt). |
| START-UI-002 | Confirmation used undefined `modal-card`, so text/buttons displayed transparently over roster rows. | CLOSED locally. Existing `modal-dialog modal-body` styles produce white dialog and legible controls at1440/720px, zero page overflow. [Before](browser/confirmation-before-720.png), [fixed720](browser/confirmation-fixed-720.png), [fixed1440](browser/confirmation-fixed-1440.png). |
| START-UI-003 | “Open round controls” from newly started course5/instance3 loaded default course1, requiring manual reselection. | CLOSED locally. Setup passes selected course/section through router state; final fresh run asserts destination selectors exactly match the course/section just started. [Original mismatch](browser/recheck-results.json), [screenshot](browser/wrong-round-context.png), [final proof](browser/final-results.json). |

Owner for all three: instructor-start builder. Auditor made no implementation edits.

## Final clean replay

The final [independently authored probe](browser/probe.mjs) ran against a second fresh database `mis_sim_browser_instructor_start_final`, API8212/Vite3004. Used actual migrations through0013 then **only** `python -m app.seed.demo --cohort --users`; no readiness/full-game/schedule seed and no direct initialization. Initial earlier audit fixture separately recorded zero `simulation_run_v1` rows. The final seed path creates only platform cohort/identities/bindings, not runtime runs.

[Final results](browser/final-results.json) contain `complete: true`, all workflow assertions passed, and `errors: []`:

- Instructor browser creates a new course, section and pack binding; no-team readiness gives actionable blocked copy and disables Start.
- Through UI, creates two teams, enrolls four existing identities and assigns two per team.
- Readiness becomes true, but strategy selectors have no defaults. Start remains disabled with zero or only one strategy chosen.
- Explicitly chooses Cost Leadership for Team1 and Differentiation for Team2. Screenshots at1440 and720; narrow document overflow0.
- Opens actual confirmation, delays the real POST in the browser, verifies submit/Cancel/context selectors disabled, backdrop ignored, and another click produces no second request. Releases the request:200 and “Simulation started. Round 1 is open.”
- Duplicate start API returns409. Reloaded setup shows active status and round-controls link, with no Start form.
- Student signs in through the actual multi-section chooser to the newly enrolled section. Initial team strategy is `cost_leadership`; capital is400000, matching authored round-one capex (`packs/riverside_grocery/pack.yaml:14`). Live checkpoint0 rows independently show different agreed strategies for both teams: [SQL evidence](browser/checkpoint-strategies.log).
- Student and wrong-course instructor cannot read readiness or start:403 for both endpoints.
- Student changes training, saves through Rollout, and locks through Review.
- Instructor clicks Open round controls: correct new course and section are selected automatically. Actual UI Advance commits round1 and opens round2. Student Debrief reports latest result round1 and displays the result: [screenshot](browser/student-result.png).

The prior independent [recheck](browser/recheck.mjs) also changed the team list through real authorized API after confirmation opened, then submitted stale choices. Start409 returned “The team list changed. Refresh and select a strategy for every team.” Both chosen strategies remained selected. [Recorded result](browser/recheck-results.json), [visible guidance](browser/stale-team-error.png). That expected negative response is recorded separately from positive-path diagnostics.

## Evidence and boundaries

Reviewed source hashes in [reviewed-source.sha256](browser/reviewed-source.sha256) cover InstructorSetup, InstructorRoundControl, instructor API and instructor-start service. All matched after the final replay. Independent frontend lint passed. No shared builder database or production state changed.

The final complete run replaced earlier partial harness attempts. Earlier attempts corrected only harness assumptions: create endpoints return201, the registered-pack label also names a region, and navigation/load completion requires waiting before selector assertions. These were not filed as product defects. The three actual defects above were separately evidenced before builder corrections.

Run the probe on a fresh ordinary cohort/users fixture with own API8212/Vite3004:

```bash
/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node findings/instructor-start-2026-10-07/browser/probe.mjs
sha256sum --check findings/instructor-start-2026-10-07/browser/reviewed-source.sha256
```

The script mutates its disposable course/section and assumes deterministic existing user IDs2–5 from the inspected ordinary seed. Multi-section login's expected409 selection response is excluded from unexpected diagnostics; negative role/retry checks use the authenticated request client and assert their expected statuses. This review does not separately create a TA user or exhaust backend invalid-roster/generation-race cases; those remain in the backend gate.

## Final validation-order delta reconciliation

After the browser run, the builder moved the not-ready/status conflict check immediately before authored-strategy validation in `start_instance`. Independently read the final function and reversed only those two adjacent blocks in memory: its SHA256 exactly matched the original browser-reviewed file hash. Thus the service delta is proven to be only this validation precedence change; both UI files and instructor route hashes remain identical.

This preserves409 for a repeat/nonready start even if its supplied strategy is invalid. Eligible starts still validate authored strategies before any initialization write. It does not alter the UI, request/response shapes, successful initialization or the browser-tested valid-choice duplicate refusal. No full browser replay was warranted for this bounded negative-path precedence correction; final negative API verification is owned by the independent backend audit.

Original actually browser-executed hashes are retained in [browser-executed-source.sha256](browser/browser-executed-source.sha256). The [final reviewed hashes](browser/reviewed-source.sha256) now include the inspected delta and all four verify OK. Browser verdict remains PASS, with this source-inspected delta explicitly distinguished from the executed browser candidate.

## Reusable proof entrypoint

The accepted contract's executable home now exists at `frontend/tests/instructor-start-proof.mjs`. It copies the executed independent probe's login/actions/assertions/finalizer **byte-for-byte**; only imports and environment/output initialization differ. The original probe and recorded audit artifacts remain unchanged. The reusable entrypoint requires `MIS_SIM_DISPOSABLE=1`, accepts `MIS_SIM_BASE_URL` (default `http://127.0.0.1:3000`, loopback only) and optional `MIS_SIM_OUT`. Without an explicit output directory it creates a unique directory under the system temp directory and prints its path, so default replays do not overwrite audit evidence.

Runbook command, after fresh migrations and **only** `app.seed.demo --cohort --users` (no runtime initialization):

```bash
MIS_SIM_DISPOSABLE=1 MIS_SIM_BASE_URL=http://127.0.0.1:3000 \
  node frontend/tests/instructor-start-proof.mjs
```

For a chosen artifact location add `MIS_SIM_OUT=/tmp/instructor-start-proof-run`. Use a new disposable database for each replay; fixed audit course/section names and seed identities are intentional fixtures. Node22 `--check` passed. Missing disposable acknowledgment and nonlocal origin were executed and refused before browser launch. Since the workflow body is byte-identical, no additional product/browser rerun was required for this harness-only packaging change.
