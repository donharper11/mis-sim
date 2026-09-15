# Implementation north star

Date: 2026-09-14. Baseline: `952aeac`. Owner: supervising integration agent (Codex).
Execution authorized by the user: preserve the useful core, establish a clear implementation
plan, dispatch bounded agents, and independently audit their work.

## The outcome

A student team inherits a business's IT estate once, makes business decisions for six rounds,
and sees reproducible consequences for cost, people, operational capability, and realised
value. An instructor can run a section without editing a database. A second vertical is
authored as content, with no case-specific engine branches. Every score has a causal trace.

The central acceptance path is:

`initial estate + committed decisions + casepack -> next state -> events -> scores -> explanation`

The production path must never replace the estate with a hand-authored answer each round.
Historical scripted estates remain useful scorer fixtures; they do not prove this path works.

## Authority and the baseline

This document governs the recovery sequence and dispatch gates under the user's instruction.
`GOVERNANCE.md`, `SPEC_PROTOCOL.md`, `QUALITY_PROTOCOL.md`, and `CONTRACTS.md` still govern
implementation. Existing packet IDs in `06-plan-index.md` remain the original product scope.
Recovery handoffs under `handoffs/recovery/` are named follow-ups, not new project phases.
An approved implementation handoff must state every contract it changes; this plan alone is
not permission to invent formulas, rewrite the stack, or expand a builder's assigned scope.

Phases 0–1 have 11 of 47 original packets recorded closed, including the August 22 scripted
calibration gate. That historical ruling stands. It is not a claim of complete simulation
evolution, broad strategy balance, a usable application, or pilot readiness.

Verified at the baseline: 82 pytest tests, all `check_*.py` guards, 44 validator fixtures,
Riverside validation at zero errors/warnings, and the historical calibration score digest.
The React application contains a token-preview page and a 404; auth is a 501 stub.
There are 16 runtime tables, one substantive casepack, and 19 static reference mockups.

Preserve: typed casepacks, validator, pure graph/scoring/event functions, decompositions,
historical fixtures, design tokens, and useful persistence contracts. Change boundaries
only when a concrete workflow or failing business invariant demonstrates the need.

## Delivery milestones and exit evidence

| Milestone | Scope and original packets | Exit evidence |
|---|---|---|
| **M0: trustworthy baseline** | Runtime reproducibility, calibration visibility, scorecard units, current status and ownership (1.4/1.6/1.7 follow-ups) | Fresh declared-dependency environment runs the checks; disposable PostgreSQL migrates and runs six rounds; all rounds of every BSC perspective are visible; score units and limitations are explicit; targeted regressions fail on the original defects. |
| **M1: decision-driven simulation** | Complete the deferred decision mutation and state evolution (1.6-A-002 and the 1.4/1.6 deferrals) | One initial seed followed only by typed decision sheets yields six rounds on the actual persistence path. Purchases, lead times, cancellations, retirement, organisational decisions, ownership and policy have observable costs/effects. No per-round estate seeding. Replay and isolation checks pass. |
| **M2: real platform context** | 2.1–2.5: hierarchy, scope, auth, registry, timing | Two sections bound to different validated pack versions; guarded requests cannot cross scope; migrations/restrictions tested; browser login plus authenticated request on the actual host pair. Scheduling consumes the audited round interface. |
| **M3: first playable loop** | 3.1–3.8 plus the minimum strategy/governance/policy/staffing/challenge controls from 4.1–4.6; minimal instructor round control from 5.3 | A seeded student logs in, sees the estate, decides, locks, advances through an instructor action, and understands the debrief for six rounds. Missing scoring-input controls are not replaced by fixtures. Desktop/tablet screenshots and browser/network diagnostics recorded. |
| **M4: complete deterministic student experience** | Complete 3.x and 4.1–4.6, close field coverage, financial model and data-freshness consumers | Every student input has a cost/preference/scoring/consequence disposition; every score input has a real producer. Coherent/negligent playthroughs and all declared strategies reviewed using decision-driven play. Numeric correctness and pedagogical balance are separate gates. |
| **M5: course operations and teaching support** | Complete 5.1–5.7 and 4.7–4.11, at most two independent tracks | Instructor setup-to-grade-export observed; clone/archive/reset scoped and tested. AI consumes computed state, degrades gracefully, invents no numbers and gives no plan recommendations; 15 adversarial coach probes pass. |
| **M6: portability and pilot** | 6.1–6.2, 7.1–7.3 | A substantive second vertical requires zero engine changes; cohort load, launch audit, deployment/recovery procedure, student manual and observed pilot rehearsal complete. |

M0 gates changes that depend on its unresolved contracts. M1 is the first continuation
checkpoint. M2 may be prepared while M1 is audited, but nothing wires into an unapproved
interface. A minimal second valid pack for M2 is a fixture, not completion of Phase 6.
M3 is a first-playable milestone; the original zero-field-gap gate belongs to M4, after
the original Phase 4 capture controls exist. This resolves the old sequencing contradiction
without silently removing those controls or renumbering the original packets.

The login surface is owned by the M2 auth handoff, using the established design system;
it is included before the browser auth canary is claimed. It is not delegated implicitly to
the component-library packet. Scheduling/unlock policy must agree with the M1 transaction
contract before a scheduling builder is dispatched.

## M1 decomposition: no single "wire up the engine" assignment

These are successive handoffs. Each gets an allowed-file list and frozen interfaces only
after the preceding contract/review is complete.

1. **Decision and transition contract.** Inventory actual casepack options and existing
   snapshot fields. Define typed commands, target identity, prices sourced from content,
   partial updates and explicit removals, allowed round states, ownership, and validation.
   Define one atomic resolution boundary and retry/unlock semantics before implementation.
2. **Estate and investment transitions.** Initialise once; carry the estate forward;
   purchase, arrive, cancel, retire and connect components; derive cost and resource pools.
   No caller may inject the resulting capability score, throughput or arbitrary free cost.
3. **Organisation and governance transitions.** Apply training/process/communication,
   staffing, owner/sponsor, policy, and project continuation decisions. Explicitly define
   adoption, decay and resistance production from content and previous state. An undefined
   formula returns to the contract author; it is never filled in by the builder.
4. **Consequences and accounting.** State which event effects mutate state, which affect
   reporting, and when. Reconcile capex/opex/debt/TCO, affordability, signal clearing and
   rationale consistency against actual committed decisions. Keep partial financial scoring
   labelled until its separate model is implemented and reviewed.
5. **Decision-only regression game.** Migrate the four archetype scenarios to decision-only
   play while retaining the historical snapshot fixtures. Cover all four declared strategies,
   multi-round misses, funded/neglected rollouts, lead times and empty decisions. Inspect the
   four BSC perspectives in every round, not only final realised value.

The M1 gate must demonstrate: invalid or unaffordable input changes no state; locked input
cannot change; failure midway through advance leaves no partial result; a retry does not
double-spend or duplicate effects; one team's actions never affect another's state; and
any permitted reopening invalidates/rebuilds all affected history consistently. Numeric
unit contracts, finite values and bounds are checked independently of snapshot pins.

## Recovery findings and concrete ownership

| Finding / unfinished behaviour | Owner handoff | Gate |
|---|---|---|
| Synchronous PostgreSQL driver missing from requirements; checks rely on ambient dependencies | `recovery/runtime` | M0 |
| Calibration inventory misses `TODO:calibrate`; report hides earlier-round BSC values | `recovery/calibration-report` | M0 |
| 0–1 BSC base receives raw event deltas such as -12; financial partial flag lost at persistence | `recovery/scorecard-contract` then its separately audited implementation | M0 |
| Live decision-to-estate mutation, 1.6-A-002 | `recovery/decision-evolution`, followed by bounded M1 builders | M1 |
| Training decay/adoption/resistance and actual preference-alignment producers | M1 organisation contract and implementation | M1; any richer refinement explicitly recorded for M4 |
| Back-distributed opex and duplicated people-affected seed values, 1.6-A-003/A-004 | M1 estate/cost and organisation handoffs | M1 |
| Data freshness, register G2 | M4 Platform producer + scoring follow-up | M4 |
| Full financial scoring vs the current discipline proxy | M1 accounting contract, M4 scoring follow-up | M4 |
| Numeric-range E00 diagnostics, OS-D1; remaining validator class coverage | M2 registry/validator follow-up | M2 |
| Policy preference overrides; richer communication predicate, CC-D9 | M1 defines supported v1 shape; M4 policy/rollout follow-up for remaining scope | M4 |
| Calibration values, B12/F5/CC-D1/J2 and pack markers | M1/M4 calibration review, each retained with location and owner | M4; playtest refinements may remain explicitly owned |
| Phase 2 table list, preflights, unlock and login dependencies are stale | M2 handoff reconciliation, before its builders | M2 dispatch |
| Original FC-1–FC-6 UI gaps | M3 minimal controls; M4 exhaustive field coverage | M4 |

Historical findings remain in `findings/OPEN-REGISTER.md`. A recovery packet updates its
own findings there at integration after the auditor reproduces the closing checks.
An owner label is not completion. A status moves through **planned → specified → reviewed
→ building → audit → integrated**, and any blocker names the exact dependent work it stops.

## How agents are controlled

- The supervisor owns integration and status. Builders do not merge to `main`, push,
  deploy, tune scoring, change adjacent interfaces, or start another packet on their own.
- At most **two implementation tracks** run at once. Each builder has an isolated Git
  worktree, an exact base commit, an explicit allowed-file list, required read set,
  acceptance commands, and a committed report. Shared integration documents are changed
  by the supervisor after audit to avoid concurrent registry/contract edits.
- Builders first run the preflight. Unexpected files, undefined semantics, inconsistent
  contracts, unavailable dependencies or scope expansion return to the supervisor with
  evidence. They can continue unrelated in-scope work while a question is resolved.
- Heavy work (scoring, transition semantics, cross-module fields) gets an independent
  spec review before coding and an independent build audit. Light work gets one independent
  build audit. A builder never audits its own work. Author/auditor independence follows
  `GOVERNANCE §6.1` at every tier, including reports displaying scoring factors. The
  supervisor reruns and audits agent changes for integration; a fresh build auditor also
  reviews any such work whose spec the supervisor authored. Author-audit is declared only
  for the infrastructure-only exception (no scoring factor or student surface).
- The auditor reads the diff and independently runs behaviour checks on the candidate
  commit. A passing builder report is not evidence by itself. New guards must fail on a
  deliberate regression; changing an expected output to match the implementation is not
  a proof of correct behaviour.
- The supervisor integrates only the audited commit, checks the combined tree, records
  accepted residuals and the next gate, and reports actual progress to the user. Failed
  audit work returns to its builder unless the cause requires a fresh builder under governance.
- No automatic gate asserts "no dominant strategy." Numeric invariants can fail a build;
  pedagogical balance is a separately recorded review of the full evidence.

## First dispatch and the immediate checkpoint

The first implementation wave is deliberately limited to two independent Light handoffs:

| Handoff | Allowed outcome | Explicit non-goals |
|---|---|---|
| `recovery/runtime` | Installable declared dependencies and a reproducible disposable-PostgreSQL verification path | No scorer/runner semantics, auth, hierarchy, deployment, or shared DB writes |
| `recovery/calibration-report` | Live complete marker inventory and every round of every BSC perspective, with factual diagnostics | No changed pack numbers, scoring, strategy claims, persisted payloads, or archetype tuning |

Heavy scorecard/transition contract authoring may proceed while the first-wave builders
finish; no dependent implementation starts before its independent spec review. Those
authors return contracts and open decisions, not speculative implementations. M0
does not pass until its numerical contract and runtime evidence pass too. No later milestone
is claimed merely because these first two handoffs land.

Product decisions reserved for the user: substantive second vertical; whether to include
the optional LLM rationale modifier (default remains no LLM scoring under governance);
reflection grading; pedagogical balance and material departures from the product design.
Routine implementation choices inside an approved contract belong to the supervisor.

## Progress

2026-09-14: first bounded implementation wave integrated on `build/north-star-foundation`.
Reporting (`94b85e7`) passed an author-independent audit; runtime (`4adafd8`) passed the
supervisor's independent build audit after a shared-dotenv defect was returned and fixed.
Combined verification: **132 pytest tests, all guards and 44 fixtures**, fresh declared
dependencies, and real disposable PostgreSQL migration plus six committed round results.
See [execution record and audits](../handoffs/recovery/README.md).

2026-09-14 continuation: **M0 COMPLETE on the integration branch.** The reviewed
scorecard implementation (`5f5b09e`, final candidate `ad5de38`) passed fresh independent
build audit and supervisor reproduction. Combined verification: **311 pytest tests, all
guards and 44 fixtures**; real PostgreSQL migrations and six committed v1 results. All
96 BSC values follow the approved points-to-fraction rule; every other payload field
across 24 results, pure-scoring code, pack values, seeds and historical pins is preserved.
Financial remains explicitly partial. Shared contracts and NS-003 close with integration.
See the [scorecard audit](../findings/recovery-scorecard-2026-09-14.md).

**M1 underway; milestone unfinished.** P0's capability-capacity/RTO input seam and stable
paths passed a fresh build audit at `7dbb4c8` and are integrated. P0b's scoped entity-access
and verified-repair input seam passed independent build audit at `1729a89` and is integrated.
Combined P0b verification is **604 tests, all guards and 44 fixtures**, with complete
historical24 payloads byte-identical. [P0 audit](../findings/recovery-engine-inputs-2026-09-14.md)
and [P0b audit](../findings/recovery-production-inputs-2026-09-15.md).
The master contract corrections passed independent Heavy review at `bee3977`; MSR-001–004
are closed at specification level. [Master review 1](../handoffs/recovery/decision-evolution/master-review-1.md)
and [master review 2](../handoffs/recovery/decision-evolution/master-review-2.md).
P1 typed content and runtime binding passed independent audit at `e4f4757` and is
integrated in the current recovery branch. [P1 audit](../findings/recovery-content-types-2026-09-15.md).
P2 estate passed independent audit at `b4bfec9` and is integrated. [P2 audit](../findings/recovery-estate-2026-09-15.md).
P3 organisation passed independent audit at `2c42f24` and is integrated. [P3 audit](../findings/recovery-organisation-2026-09-15.md).
P4 consequences passed independent audit at `f43ea7f8` and is integrated. [P4 audit](../findings/recovery-consequences-2026-09-15.md).
P5 persistence passed independent audit at `58a75669` and is integrated. [P5 audit](../findings/recovery-persistence-2026-09-15.md).
P6 games passed independent audit at `3855188` and is integrated. The frozen fixture now
executes through `SimulationService`; nullable command persistence, no-op affordability and
pending-hire refusal are covered by the predecessor corrections. The final evidence covers
16 games, 96 persisted reports, fresh-scope determinism, cross-effects and hash-seed stability.
[P6 audit](../findings/recovery-games-2026-09-15.md).

The independently reproduced
[inventory](../handoffs/recovery/decision-evolution/inventory.md) identifies invalid-target
acceptance, absent carry-forward, late duplicate-advance refusal, incomplete rewind and
caller-committable partial writes. D1–D10 must be resolved in the Heavy decision and
transition contract, then independently reviewed before estate/organisation builders start.
**M1 is complete after audited P6 integration.** Broader product work begins at M2; the
decision-driven simulation boundary is now the maintained foundation.
Main and remote publication remain untouched.

**M2 has started.** The pre-dispatch platform reconciliation and identity amendment are
committed at `376d54c`; packet 2.1 (hierarchy, identity foundation, unprotected CRUD seam,
and deterministic cohort seed) was accepted at `5d6b573` after independent audit
(`b140f91`). The combined tree passes 662 tests and all guards. Instance scoping, registry,
auth/login, and scheduling remain separate M2 packets with amended contracts; none is
implicitly included in 2.1.
