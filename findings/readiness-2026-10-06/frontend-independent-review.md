# Independent frontend readiness review

Date: 2026-10-06. Reviewer: `/root/frontend_review`, fresh auditor, not builder or spec author. Reviewed the working tree, not a merged artifact. Read GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS, readiness report/runbook, and the changed frontend/API contracts.

Final verdict: **PASS for the bounded frontend readiness corrections, after independent rework verification.** Five defects were independently reproduced, returned to the builder, and closed by replaying their failing classes. This is not production/class-readiness approval; the host schema/lifecycle, instructor-start, operational performance and observed pilot gates remain separate.

The reviewed working-tree source is pinned in [reviewed-source.sha256](frontend-review/reviewed-source.sha256). Independent frontend lint passed after the final changes. No implementation changes were made by this auditor.

| Finding | Final disposition | Independent closing evidence |
|---|---|---|
| READY-UI-001 | CLOSED locally | Multi-unit communication remains after partial Unit selection plus hiring |
| READY-UI-002 | CLOSED locally | ERP host component uses authored `basic`, returns200, and survives subsequent policy save alongside prior firewall purchase |
| READY-UI-003 | CLOSED locally | Real stale409 retains unsaved slider choice; explicit reload guidance and deliberate recovery restore saved choice |
| READY-UI-004 | CLOSED locally | Successive service purchases retain both service commands |
| READY-UI-005 | CLOSED locally | Delayed post-purchase refresh keeps Close disabled; subsequent policy save succeeds with coherent commands/revision |

Run `node findings/readiness-2026-10-06/frontend-review/closing-check.mjs`: **PASS independent class closure checks**. The same check with `--before` fails against captured original defect evidence. These assertions consume the independently recorded browser/API observations below; the browser probe sources show how to regenerate them on a disposable seed.


## Original findings and evidence (all closed above)

- **READY-UI-001 — Functional, silent communication loss.** Owner: readiness builder. Seed a saved communication for `store_operations` and `finance`. In Infrastructure → People choose a hiring option and Unit `store_operations`, leave Method at Choose, then save. HTTP 200 persists hiring and only the finance communication; the store command disappears. `Controls.jsx:98` filters by selected unit before line 100 verifies a replacement method exists. A single existing unit does not expose this because `runtime_controls.py:245` drops empty replacement categories. Evidence: [before-fix preservation results](frontend-review/preservation-before.json), [browser state](frontend-review/communication-loss.png). The independent script `frontend-review/preservation.mjs` contains the full browser action and API-backed fixture. Closing check: assert its first result `preserved === true` with both units present.
- **READY-UI-002 — Blocking for host component workflow.** Owner: readiness builder. Infrastructure → New Host Platform → On-Premises → create → open → Add a Component → first available placement → Provision returns HTTP 422, `Platform commands are not valid for this round`. `InfrastructurePage.jsx:249` sends `op: buy`, `application`, `config: basic`, and `units`; the runtime command contract uses `buy_application`. Evidence: preservation results entry `component provision`. This stopped the attempted host component → policy-save preservation test; that suspected loss is not claimed as browser-proven. Closing check: same browser action returns 200 and the component appears in the scoped draft; then policy save retains it.
- **READY-UI-003 — UX, stale draft has no recovery action.** Owner: readiness builder. Open Rollout, save a strategy through the same authenticated API to advance the revision, then click Save Changes on the stale Rollout page. API properly refuses 409 `revision_conflict`; the only student message is “The rollout decision could not be saved.” There is no explanation that another save changed the draft or reload/reconcile action. `RolloutSlider.jsx` catch block maps structured detail to this generic string. Evidence: [results](frontend-review/results.json), [stale save screenshot](frontend-review/stale-save.png). Closing check: induce real stale revision and require meaningful recovery guidance/action while preserving the student's draft until a deliberate recovery choice.

## Passing independent browser evidence

[Probe source](frontend-review/probe.mjs) and [results](frontend-review/results.json):

- Real browser student login and authenticated scoped read on the same app origin.
- Navigation to restored Infrastructure Security and People panels.
- Two application training saves preserve both assets' commands.
- Ownership save followed immediately by Rollout save shares the correct revision.
- Policy save followed by hiring shares revisions and preserves existing communication when no unit is being edited.
- Saved data-access policy survives reload.
- Security and Ownership screens checked at 1440, 1280, 1024 and 720 widths; no document overflow. Screenshots inspected at 1280 Security, 720 Security and 1024 Ownership show legible controls without clipping.
- Newly created host with a real attached runtime asset appears in Rollout detail with its actual name, POS label, placement and prices. Modal exposes no mutation inputs or Add Service action.
- Lock through Review disables Security and People save actions.
- Positive probe paths produced zero page/console/HTTP errors; the deliberate stale-save negative produced the expected HTTP 409 and browser resource-error diagnostic, recorded separately. The original failing component workflow produced a real additional HTTP422 defect, now closed after rework.

## Reproduction and limits

Created a new disposable database `mis_sim_browser_review_frontend` in the existing local isolated PostgreSQL cluster at `127.0.0.1:44535`, then ran `backend/scripts/seed_readiness_demo.py --database-url <local URL>`. It migrated through `20261004_0011` and printed `Ready: two sections, four round-one teams`. Own API uses 8212, own Vite 3004; no shared builder browser team was changed. Node executable: `/home/ubuntu/.nvm/versions/node/v22.23.2/bin/node`.

The executable browser probes are newly authored from inspected interfaces. Builder scripts were read for environment conventions but were not used as the independent proof. Native select label matching was corrected in the harness, and one temporary Vite config module-resolution issue was fixed before the successful run; neither is counted as a product defect.

This bounded audit does not repeat six-round competent/negligent pedagogical acceptance, production-host checks, the backend test suite, or schema/lifecycle review; those are separate reviewer/gate work. No implementation changes made by this auditor.

## Additional independent finding and re-review

- **READY-UI-004 — Functional, successive service purchase loss.** Owner: readiness builder. New host → Add Service → Standby copy for outages/on-prem → Provision200, then Add Service → Central sign-on/on-prem → Provision200. The first saved `buy_service` vanished; only `central_sign_on` remained. Original `InfrastructurePage.jsx:134` sent a one-command replacement category. Evidence: [before-fix commands](frontend-review/services-before.json), [probe](frontend-review/services.mjs). Closing check: require both service keys after the second save.

On the builder's subsequent corrections, independently re-ran the exact failing action classes. Multi-unit partial People entry now retains both commands, and two successive services now retain both `central_sign_on` and `failover_cluster`. Component/policy and stale-conflict checks were still pending at that intermediate point and are now closed as recorded above. Evidence files retain the before-fix outputs separately; this is class-level rechecking, not acceptance of builder evidence.

Re-review of READY-UI-002 after the first correction still returns 422, now `invalid_reference` / `config`. The only Section A firmwide item is `erp_suite`, whose authored config tiers are `basic`, `mid`, `advanced` (`backend/packs/riverside_grocery/catalog.yaml:413`); the corrected adapter guessed `core`. At that intermediate revision this remained blocking; `preservation-config-failure.json` retains that failure. Final closure above supersedes it. Section B has no available firmwide card, so the component workflow was re-run in Section A.

READY-UI-003 now passes a separately authored [real-conflict probe](frontend-review/conflict.mjs): initial slider 50 → unsaved 100 → other save advances revision → save409 retains100 and explains reload/discard → deliberate Reload latest decisions restores50. [Recorded result](frontend-review/conflict-results.json).

- **READY-UI-005 — Functional, close-during-provision race.** Owner: readiness builder. With authored configuration selected, the component mutation returns 200. Immediately closing the modal, opening Security, and saving policies returns 409 `revision_conflict`. The component handler still awaits member assignment and platform GET before `handlePlatformDataUpdated` invalidates controls; the user can use the stale sibling before that point. Independent script observed real 200 followed by real 409; [purchase output at failure](frontend-review/preservation-close-race.json). Closing check: attempt Close during a delayed post-purchase refresh; either it is unavailable until refresh completes or sibling controls remain unavailable until a coherent command/revision snapshot is loaded. A completed-operation wait was checked separately; the final delayed-refresh test, rather than that wait alone, closes this race.


## Final replay details

The final [preservation browser probe](frontend-review/preservation.mjs) uses a scoped application-category reset in the disposable team before replay so previous audit purchases do not hide the catalog card. It then saves firewall/security, provisions ERP through the real modal, delays the subsequent platform GET by two seconds, verifies Close is disabled, attempts Close, and saves Security immediately after the completed close. [Results](frontend-review/preservation-results.json) record HTTP200 for the authored ERP purchase, `closeBlocked: true`, and identical before/after application commands (`erp_suite/basic` plus `next_gen_firewall/core`). The successful completed-operation flow was also observed separately before the deliberate-delay race test.

The authored configuration is obtained from the existing scoped Components choices; no backend/API schema change was required. The additional Close/X/backdrop/Cancel blocking is verified by source inspection at `InfrastructurePage.jsx:417`, `:432`, `:529`, `:551`, and catalog handlers, with browser proof for the Close path under delayed refresh. Other dismissal paths were not separately clicked in the browser.

Final source files: `Controls.jsx`, `InfrastructurePage.jsx`, `RolloutSlider.jsx`, hashes in the linked manifest. All closing checks were run against this source. The ordinary route/viewport/modal/lock evidence predates the last narrow provisioning/conflict corrections; those changed paths were independently replayed after their correction. No claim is made that every route or six-round teaching scenario was re-run after each narrow patch.
