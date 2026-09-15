# MIS Simulation — current battlecard

Updated 2026-09-14 against baseline `952aeac`. Current execution plan:
[`design/08-implementation-north-star.md`](design/08-implementation-north-star.md).
Read governance, quality, spec and field contracts before implementing an assigned handoff.

## The product

Undergraduate MIS teams inherit a company's IT estate and manage it for six rounds.
The decision hierarchy is strategy → platform → components → rollout, with ownership,
information policy, staffing, challenges and a review/lock/debrief loop around it.

`Realised Value = Technology Capability × Organisational Readiness × Management Quality`

The interface speaks business: what does it cost, who does it affect, and what happens
if it fails? The engine computes scores and causal evidence; AI may explain, role-play
and teach, but may not score or advise on the team's plan. Every persona number comes
from engine state. Stakeholder satisfaction uses realised value, not just purchases.

## What exists

| Area | Evidence-backed status |
|---|---|
| Foundation | FastAPI/React scaffold, migrations, semantic tokens, local IBM Plex fonts, 19 static reference mockups |
| Content | One substantive Riverside pack: 7 capabilities, 14 catalog items, 8 entities, 8 watch rules, 13 events, 4 strategies, 14 stakeholders, 6 policy switches and 6 obligation rules |
| Engine | Pure graph/scoring functions, policy scoring, event/precondition model, signal episodes, explanatory decompositions; audited optional capability-specific capacity/RTO inputs and deterministic paths |
| Persistence | 16 runtime tables, instance-scoped snapshots, lock/advance, arrivals, result and ledger persistence |
| Calibration | Four scripted archetypes × six rounds; all perspectives now visible in every round, 38 live marker sites and raw scale diagnostics; all scripts declare Cost Leadership; August ruling retained |
| Verification | M1 P6 integration: 652 pytest tests, all guards, 44 fixtures; complete historical payloads preserved, plus 16 decision games/96 persisted reports and matching hash-seed digests. M0's actual PostgreSQL migrations/16 tables/six results and all 96 reconciled BSC values remain the baseline; Riverside zero errors/warnings |
| Application | React token-preview page and 404 only; auth remains 501; student/instructor workflows unbuilt |

The original packet count is **11 of 47 recorded closed**. Phase 1 closure covers the
audited scripted-state model with accepted deferrals. It does not prove a decision-driven
game, balance across all strategies, a usable application, or readiness for a cohort.

**M0 is complete** on `build/north-star-foundation`: reporting (`94b85e7`), runtime
(`4adafd8`) and the independently audited scorecard candidate (`ad5de38`). Scores now
apply integer event points to normalized bases once and retain versioned base/delta/partial
status. All other fields across 24 scripted results and historical result rows are preserved.
Main remains at the historical baseline. [Evidence and limits](handoffs/recovery/README.md).

**M1 is complete.** Its bounded capacity/RTO/path packet passed a fresh build audit at
`7dbb4c8`, and its entity-access/verified-repair packet passed at `1729a89`; both are
integrated on the recovery branch. [P0 audit](findings/recovery-engine-inputs-2026-09-14.md)
and [P0b audit](findings/recovery-production-inputs-2026-09-15.md). The corrected master
contract passed independent Heavy review at `bee3977`, closing the four returned findings.
[Master review](handoffs/recovery/decision-evolution/master-review-2.md). P1 typed content
and runtime validation passed independent audit at `e4f4757` and is integrated in the
current recovery branch. [P1 audit](findings/recovery-content-types-2026-09-15.md). P2
estate passed independent audit at `b4bfec9` and is now integrated. [P2 audit](findings/recovery-estate-2026-09-15.md).
P3 organisation passed independent audit at `2c42f24` and is now integrated. [P3 audit](findings/recovery-organisation-2026-09-15.md).
P4 consequences passed independent audit at `f43ea7f8` and is now integrated. It adds
pure accounting, consequence resolution, repairs, preview challenges, prevention, debt/TCO
and the shared M0 scorer adapter. [P4 audit](findings/recovery-consequences-2026-09-15.md).
P5 persistence passed independent audit at `58a75669` and is now integrated. It adds the
three canonical simulation tables, strict 19-table migration verification and fresh
transaction service operations. [P5 audit](findings/recovery-persistence-2026-09-15.md).
P6 games passed independent audit at `3855188` and is integrated. It loads the frozen
typed six-round fixture through `SimulationService`; final evidence covers 16 games,
96 persisted reports, fresh-scope determinism, causal archetype differences and hash-seed
stability. The nullable-command persistence and no-op/pending-liability affordability fixes
are integrated in `3c2bb51`, `e2356e7`, `3624f2` and `8ef2411`. [P6 audit](findings/recovery-games-2026-09-15.md).

## The important unfinished boundary

The scripts author a replacement post-decision estate each round. The runner scores that
state; it does not yet apply the complete student decision set to the previous estate.
Training decay, adoption/resistance evolution and general stakeholder-alignment inputs still
need real producers. The Financial scorecard is a partial discipline proxy, although
capex/opex/debt/TCO records exist. Distinct data freshness and full policy overrides remain
deferred. See the north-star ownership table and `findings/OPEN-REGISTER.md`.

The first meaningful product checkpoint is **one initial estate followed only by real
decision sheets for six rounds**, with coherent costs, timing, consequences and explanations.
Historical scorer fixtures remain useful regression evidence; they are not that checkpoint.

## Current delivery order

1. **M0 — trustworthy baseline — COMPLETE:** declared dependencies, disposable PostgreSQL
   proof, complete calibration visibility, explicit scorecard units and owned gaps.
2. **M1 — decision-driven simulation:** typed commands, actual state transitions, atomic
   advance/retry semantics, organisational evolution, accounting and decision-only playthroughs.
3. **M2 — platform:** hierarchy, guarded scope/auth, pack versions and scheduling. A login
   surface is included before the browser auth canary; a minimal second pack proves isolation.
4. **M3 — first playable browser loop:** required input controls, student review/debrief and
   instructor advance, through six rounds on real state.
5. **M4 — complete deterministic student experience:** all input capture, real producers,
   financial/freshness follow-ups and balance review across declared strategies.
6. **M5 — course operations and AI:** complete instructor workflow, grades/export/lifecycle,
   grounded personas, interviews, concept coach and debrief narration.
7. **M6 — second vertical and pilot:** content portability, cohort load, launch/recovery
   audit, manual and observed rehearsal.

Original packet IDs and full scope remain in `design/06-plan-index.md`. Milestones group
work around user outcomes and include the old deferrals; they do not erase the history.

## How a builder starts

The supervisor supplies one exact branch/base commit and isolated worktree, one approved
handoff, an allowed-file list, preflight checks and acceptance evidence. At most two
implementation tracks run. Do not infer an assignment from this overview or start a later
milestone because a nearby file looks ready. No `git add -A`, pushing, deployment or main
merge by builders. Undefined semantics and scope changes return to the supervisor.

Heavy contracts/scoring work gets independent spec review and build audit. Every builder's
work is independently checked before integration. The supervisor records the candidate SHA,
reproduced evidence, remaining findings and next gate. Browser evidence is required when
there is a browser workflow; seed-based headless evidence is appropriate for the engine.

## References and open product decisions

- Design intent: `design/02-traceability-matrix.md`, `design/04-decisions-g1-g6.md`,
  `design/07-decision-consequence-map.md`. A tick in the traceability matrix may mean an
  identified design path, not an implemented runtime path.
- Shared fields: `CONTRACTS.md`; historical audits and owned deferrals: `findings/`.
- Reference systems and locations: `GOVERNANCE.md §4.1`. Inspect current source before
  porting; old availability/version claims are not current verification.
- Product decisions reserved for the user: substantive second vertical, optional LLM
  rationale modifier, reflection grading, and pedagogical balance. The market/competitor
  layer remains deliberately deferred.
