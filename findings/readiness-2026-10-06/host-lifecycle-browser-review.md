# Independent host lifecycle browser/API review

Date: 2026-10-06. Auditor: `/root/frontend_review`, not the lifecycle author/builder. Read the accepted lifecycle contract and independent contract review, prior governance/quality/contracts, host route, scheduler, manual advance, reset implementation and migration boundary.

**Verdict: PASS for the requested browser/API lifecycle and reset acceptance. No blocking findings in this bounded flow.** This does not substitute for independent backend transaction/rollback/concurrency/migration tests, and does not accept instructor initialization, assignment semantics, archive repair or production readiness.

Candidate source hashes: [reviewed-source.sha256](host-lifecycle-browser/reviewed-source.sha256), covering lifecycle helper, simulation service, platform reset service, host/round-control routes and0013 migration. `sha256sum --check` passed after the browser run.

## Executed workflow

Created a new empty isolated PostgreSQL database `mis_sim_browser_host_lifecycle_review`, ran the readiness seed through actual migration `20261006_0013`, then restarted only this reviewer's API8212 against it. Existing independent Vite3004 proxies to that API. No shared builder database was changed.

The newly authored [browser/API probe](host-lifecycle-browser/probe.mjs) and [database/scheduler helper](host-lifecycle-browser/db_probe.py) completed successfully. [results.json](host-lifecycle-browser/results.json) records `complete: true`, five passing workflow groups, and empty browser page/console/HTTP diagnostics.

1. **Real student/staff browser sessions.** Section A owner, Section B student and owning instructor logged in through the actual same-origin UI. Each student created a pending host through Infrastructure and attached a real initialized application through authenticated API. Both hosts had created round1/activation round2.
2. **Active reset refusal.** Owning instructor called the real reset endpoint for active Section A: HTTP409. Complete snapshots of all inspected scoped/runtime/identity tables before/after were identical.
3. **Manual advancement.** Owning instructor called the real round-control advance API. Round1 committed and returned next round2. Section A host became active; Section B's host/member response remained identical. Student reloaded Infrastructure and saw the active badge and read-only modal with no Add Service or Add Component actions. Rename/add/remove against that active host each returned409. [Active screenshot](host-lifecycle-browser/active-host.png), visually inspected.
4. **Actual scheduler and stale pointer.** The helper created a due Section B schedule and called production `Scheduler.tick` with an explicit aware timestamp. It returned `advanced` with no failures; existing host became active. Live DB snapshot showed presentation `SimulationInstance.current_round=1` while both scoped runs had current round2. The Section B student then created a new host in the browser: created round2, activation round3; API membership assignment stamped round2. This proves the locked run drives host/member timing even while the presentation pointer lags. [Screenshot](host-lifecycle-browser/scheduled-round2-host.png).
5. **Authorized setup reset.** To exercise the contract's setup-only reset of a populated runtime, the test helper explicitly set only the disposable Section A instance's status to setup. This is a fixture step, not a claimed user-facing transition. Owning instructor then called the real reset API:200. All25 inspected runtime tables were empty for Section A; prior nonempty target tables included host, member, two round results, four checkpoints, two runs and four sheets. Section A pointer returned0 and timestamps became null. Pack binding/digest/settings/total rounds, teams, course/section/enrollment and19 user rows were preserved. Every other-scope row remained exactly equal, including hosts/members, real scheduler rows and committed results. Repeating reset returned200 and left the complete snapshot unchanged.

Reset proof retains [before](host-lifecycle-browser/reset-before.json) and [after](host-lifecycle-browser/reset-after.json) snapshots. Every declared table with an `instance_id` column was inspected; tables already empty demonstrate no residue, not populated deletion coverage. Full populated historical/grade inventory, forced rollback and concurrent lock ordering remain obligations of the separate backend audit.

## Reproduction and limits

With a fresh seeded lifecycle-review database and current API8212 running:

```bash
/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node findings/readiness-2026-10-06/host-lifecycle-browser/probe.mjs
sha256sum --check findings/readiness-2026-10-06/host-lifecycle-browser/reviewed-source.sha256
```

The probe uses real manual API and production scheduler entry points; it does not directly call the promotion helper or stub simulation results. Expected409 API refusals are asserted separately from positive browser diagnostics. Successful advancement demonstrates visible activation, not independently proven transaction atomicity under failure; that claim belongs to the backend fault-injection checks.

No implementation changes were made by this auditor. This pass does not exercise final-round nonactivation, malformed historical timing reconciliation, migration downgrade behavior, retired-host mutation, or the PostgreSQL manual-final-reconciliation/reset race. Those are explicitly covered by the bounded backend contract and must pass before overall READY-002 closure.
