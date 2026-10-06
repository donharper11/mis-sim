# Independent host-scope browser/API review

Date: 2026-10-06. Auditor: `/root/frontend_review`; not the scope implementation author or builder. Candidate: migration `20261006_0012`, working-tree source hashes in [reviewed-source.sha256](host-scope-browser/reviewed-source.sha256). Governance, quality/spec protocols, CONTRACTS, the bounded host-scope contract, its accepted independent dispatch review, and model/migration/API producers were inspected.

**Verdict: PASS for the bounded browser/API scope acceptance. No new findings.** This does not accept host activation/reset, instructor initialization, assignment ambiguity, production deployment or class readiness. Populated migration/downgrade, malformed-history refusals, SQLite, constraint plants, schema guards and the full gate remain separate backend-auditor obligations.

## Independently executed evidence

Created an empty local PostgreSQL database `mis_sim_browser_host_scope_review` and ran the guarded readiness seed. It migrated through `20261006_0012` and initialized the two-section/four-team cohort. Stopped only this reviewer's old API8212, then relaunched current code against the new database. Browser origin `http://127.0.0.1:3004` proxies to that API; no builder/shared browser database was changed. The previously accepted frontend source hashes still match.

Newly authored [browser probe](host-scope-browser/probe.mjs), run using Node22, completed with `complete: true` and `errors: []` in [results.json](host-scope-browser/results.json):

| Action | Observed result |
|---|---|
| Browser sign-in as owner, teammate, another team in the same section, and another section | All four authenticated same-origin sessions and identity reads succeed |
| Infrastructure navigation → create host → open detail | HTTP200; correct section/team/name/code; normal modal |
| Add actual initialized POS asset through authenticated API | HTTP200; immediate member response; original four response fields preserved |
| Rename owned host; teammate reads populated membership | HTTP200 and renamed host/member visible to the same team |
| Other team supplies owner's `team_id` query | Empty own-team result; cannot select the other team |
| Other team uses populated owner's parent/member IDs to rename/add/remove | All HTTP404 |
| Cross-section session uses owner's instance path to rename/add/remove/list | All HTTP403 |
| Other team and other section read their own rollout | Owner's host assignment is absent |
| Owner removes actual member | HTTP200; member list and rollout assignment immediately empty |
| Owner re-adds real asset and opens Rollout host link | Correct renamed host and POS detail; read-only modal, no Add Service action |
| Owner locks through Review browser action | HTTP200; rename/add/remove now HTTP409; original name/member retained |
| Locked Infrastructure and Rollout at720px | Create action absent; read-only modal/disabled rollout controls; no document overflow |

A separate [cross-context probe](host-scope-browser/cross-context.mjs) supplies the foreign host/member IDs under the attacker's **own authorized instance path**, so the check reaches parent lookup rather than stopping at path authorization. Rename/add/remove all returned HTTP404. [Recorded results](host-scope-browser/cross-context-results.json).

Live PostgreSQL inspection—not ORM metadata alone—confirmed Alembic0012, nonnull member `instance_id`, its direct instance CASCADE FK, member `(platform_id,instance_id)` composite CASCADE FK, and host/team composite scope FK. [Schema log](host-scope-browser/schema.log). The retained actual member has `instance_id=1`, parent instance1, team1; [persisted row](host-scope-browser/member-state.log). Source-hash verification returned OK for all four backend candidate files after testing.

Screenshots: [created](host-scope-browser/created.png), [read-only rollout](host-scope-browser/rollout-readonly.png), [locked720px](host-scope-browser/locked-720.png). The last image was inspected: host/member text and Close are visible without clipped controls.

The probe deliberately expects authorization/lock refusal responses through its authenticated API request client; these are recorded negative assertions, not failed positive browser requests. Browser page/console/HTTP diagnostics on the positive UI paths were empty. Rename/remove are API operations because the current UI has no rename/remove controls, as explicitly allowed by the scope contract.

## Reproduction and boundary

On a fresh disposable seeded database and restarted current API8212:

```bash
/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node findings/readiness-2026-10-06/host-scope-browser/probe.mjs
/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node findings/readiness-2026-10-06/host-scope-browser/cross-context.mjs
sha256sum --check findings/readiness-2026-10-06/host-scope-browser/reviewed-source.sha256
```

No implementation was edited. This browser pass does not separately create an unassigned user or exercise paused/completed runtimes; those remain in the independently reviewed backend scope tests. It verifies the lock guard and real populated cross-team/cross-instance CRUD/projection paths, including IDs presented under the attacker's own authorized context.
