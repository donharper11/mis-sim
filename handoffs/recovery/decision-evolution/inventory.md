# M1 decision-evolution inventory — preparation evidence only

Date: 2026-09-14. Inspected base: `c7283dc27eb0d0bf5178765d81274e5bf66ad546`. This document is the only repository change.
This is **not an approved implementation spec**, interface freeze, formula ruling, or M1 completion claim.
`[V]` means directly inspected executable source or an in-session reproduction below; **OPEN/NEW** means a contract still needs authoring.

Read basis: `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md`, `CONTRACTS.md`, `design/08-implementation-north-star.md`, `design/07-decision-consequence-map.md`, original 1.6 and 2.1–2.5 handoffs;
complete round runner/actions/snapshot/models, relevant casepack models/loader, engine state/organisation/management/ledger, event/precondition extracts, full-game and four archetype seeds.
Extraction is sufficient to inventory these boundaries, **insufficient to dispatch a transition builder**.
No external-system claims, shared databases, service startup, dependency changes, or code/test edits. Quality ladder: source/contract inspection and disposable SQLite probes apply;
build/browser/migration gates are N/A to documentation-only preparation. Independent integration review remains the supervisor's gate.

## Existing input and mutation boundary

- [V] `RoundRunner(session, pack, instance_id, team_id)` is a Python service, not a typed request API.
  The app registers health/auth only; auth is a 501 stub (`backend/app/round/runner.py:43–49`, `backend/app/main.py:30–31`,
  `backend/app/api/auth.py:6–8`). Constructor scope is caller supplied; neither enrollment nor pack-version binding is checked here.
- [V] `write_decision_sheet(round, lines: list[dict])` accepts required `key`, `category` and optional
  `capability`, `capex=0`, `rgt_tag="run"`, `is_maintenance=False`, `action_type`, `target_key`.
  Only these fields are persisted; additional dictionary keys are ignored. Each present category is deleted/replaced;
  absent categories remain, and `[]` deletes nothing
  (`runner.py:90–112`; all unqualified runner references below mean `backend/app/round/runner.py`).
- [V] Validation runs at advance, after sheet writes: category/action membership, nonnegative capex,
  and summed caller capex against that round's authored budget. It does not validate target existence, category/action compatibility,
  option/placement/tier selection, duplicate line keys, capability keys,
  R/G/T tags, exact current round, or affordability against real option costs (`runner.py:116–136`).
- [V] Every category can contribute caller-authored spend to management scoring; none currently
  dispatches a corresponding estate mutation. Advance skips retirements/cancellations and purchases/org/governance deltas,
  then reads that round's persisted estate (`runner.py:288–300`,
  `backend/app/round/snapshot.py:170–175`, `backend/app/engine/management.py:69–135`).

`CONTRACTS.md` fixes twelve categories. Defaults below: `backend/app/round/actions.py:27–58`; an explicit legal action overrides **any** category's default.

| Category today | Action-history default | Missing decision-specific input / mutation |
|---|---|---|
| `platform_service` | none | Service/placement/tier choice; purchase/scale/move; pools and live service state |
| `application` | none | Catalog/placement/configuration choice; purchase/upgrade and deployment creation |
| `integration` | none | Source/destination, edge kind/entity/tier; connect/disconnect |
| `lifecycle` | none | Order or deployment identity; cancel/retire/continue/pause/kill |
| `training` | `add_training` | Deployment plus training-option identity; trained population/effects |
| `process_redesign` | `redesign_process` | Deployment plus process choice; rollout process state |
| `communication` | none | Option, audience, cost and persisted communication/effects |
| `staffing` | none | Hiring/support choice and scope; FTE, load and recurring cost |
| `governance` | none | Named owner/sponsor, priority/project decision; ownership state |
| `policy` | `add_policy` | Policy plus selected value and active decision; policy-state write |
| `event_response` | `fund_response` | Event plus fund/defer/reject and rationale; response consequences |
| `capital_request` | none | Request amount/terms/approval; capital adjustment |

- [V] Closed action vocabulary: `scale_node`, `add_node`, `move_to_cloud`, `add_training`,
  `redesign_process`, `fund_response`, `upgrade_component`, `retire_component`, `add_service_tier`, `add_policy`
  (`backend/app/casepack/checks.py:13–24`). There is no cancel/connect action key;
  **this vocabulary describes signal actions, not an already-designed command union**.
- [V] History is reconstructed from **all** decision rows through the requested round, without a
  per-sheet lock-status filter; `locked_round` is simply the line's round (`snapshot.py:59–67`, `actions.py:47–58`, under `backend/app/round/`).
  Signal matching checks type/capability/time and
  excludes zero-cost training; a still-raising metric prevents clearing. It does not validate the
  target when capability matches, or prove the selected option caused the change
  (`backend/app/engine/ledger.py:232–261,301–325`). A fake training target at cost 1 reaches history (probe A).

## Content and persistent state actually available

| Boundary | [V] Existing fields and shipped options | OPEN / absent producer contract |
|---|---|---|
| Initial estate | `InitialState` contains a round/dashboard/budget/people/review narrative, no nodes/edges/deployments (`backend/app/casepack/models.py:113–126`). Riverside starts this block at **round 3**, with remaining capital 46,000 (`backend/packs/riverside_grocery/pack.yaml:13–41`). | NEW authoritative one-time round-1 estate representation and initialization rule; historical R3 fixture must retain its own identity. |
| Catalog investment | `DeploymentMode`: capex/opex/lead time/bypasses-platform; item roles/serves/sizing/availability/life/staff load/entities/dependencies/people/training/process/RGT/config multipliers (`models.py:182–260`, here and remaining content rows: `backend/app/casepack/models.py`). 14 items, 42 modes; lead-time counts 0:10, 1:26, 2:6. | Price rounding and upgrade delta; quantity/configuration semantics; demand-driver inputs and conversion to capacity; recurring-cost timing. No catalog throughput field. |
| Shared platform | 11 services, 33 placement options; lead-time counts 0:7, 1:25, 2:1. Model has roles, placement prices, `capacity_pct`, staff load, entities (`models.py:284–315`). | Absolute compute/storage supply and capacity conversion are not defined by a utilisation percentage; runtime `PlatformServiceRow` is not consumed by snapshot assembly (`backend/app/round/snapshot.py:120–211`). |
| Support/integration | Support basic/standard/premium costs 20k/50k/100k and FTE 0.6/1.4/2.4; integration basic/advanced/vendor_managed costs 50k/120k/200k (`backend/packs/riverside_grocery/platform.yaml:192–241`). | Which recurring/accounting bucket, effective round, chosen-tier persistence, and technical effects. Integration tiers have only key/cost/provenance. |
| Training/process | Every catalog item offers none/basic/full; cost and coverage exist; 9 of 14 items have a process option with cost/label. Order management training is 0/12k/34k for 0/.6/1 coverage; process 22k (`backend/packs/riverside_grocery/catalog.yaml:65–85`). | Coverage→integer people, accumulation/overlap/repeat training/decay, process choice→state, adoption/resistance transition formulas. `DeploymentOrgStateRow` already stores resulting numbers (`backend/app/round/models.py:89–107`). |
| Communication/staff | Snapshot has deployment adoption/ever-trained, unit resistance, staff FTE/load; no communication state (`backend/app/engine/state.py:64–106`). Support FTE and catalog/platform staff-load attributes exist. | NEW typed communication/hiring options, prices and effects; no such option models in the complete `Casepack` field set (`models.py:542–558`). Support is not an already-defined hiring contract. |
| Governance/strategy | Runtime owner/sponsor are booleans per capability; strategy string plus declaration round live on the team row (`backend/app/round/models.py:30–48,146–155`). Four strategies each author `reopen_cost=80000` (`backend/packs/riverside_grocery/strategies.yaml`). | Named assignee identity, assignment eligibility, project continuation/pause/abandonment lifecycle, strategy revision history/cost/resistance. Strategy has no category or sheet setter. |
| Policy | Six ordinal three-value switches with defaults, one cost/effects map per policy (`backend/packs/riverside_grocery/policies.yaml:48–155`; `models.py:453–503`). Runtime policy/selected/actively-decided exists (`backend/app/round/models.py:158–167`). | Option-specific/repeated-choice charges and effect timing; sheet→row producer; carry chosen state while recording this-round activity. No per-option price/effects shape exists. |
| Preferences | Shipped domains: catalog/platform/training/services/policies. Arbitrary archetype dictionaries/override dictionaries load (`models.py:447–450`; `backend/app/casepack/loader.py:72–81`). | Non-policy alignment is still a precomputed scalar read from rows (`backend/app/round/snapshot.py:181–186`; `backend/seeds/riverside_r3.py:236–255`). Choice→ideal mapping/overrides/caring set must be authored. Policy overrides explicitly raise (`backend/app/engine/management.py:281–295`). |
| Challenges/TCO | 13 events each offer fund/defer/reject with cost/tags; outcome has revenue loss and scorecard map (`models.py:388–407`; sample `backend/packs/riverside_grocery/events.yaml:20–47`). Catalog has true/decoy cost-category lists. | No response selection/rationale/TCO-category capture in the sheet. Event options have no separate outcome payload. TCO forecast and actual are already-supplied integers, merely returned (`runner.py:218–222`). |

Counts above were recomputed by loading the shipped pack; mode-count reproduction is included in probe A.
`ConfigTier.compute_multiplier` is an actual schema field, not a throughput formula. Platform `capacity_pct=100/70` describes compute/storage **used**
(`backend/packs/riverside_grocery/platform.yaml:45–73`); neither interpretation is silently changed here.

- [V] Nodes are full **per-round** rows with roles/availability/life/serves/throughput/entities/placement/opex, but no catalog key,
  configuration tier, retirement round, or deployment relationship. Edges store only src/dst/kind; deployment rows separately hold catalog key and people (`backend/app/round/models.py:54–107`).
  Technology consumes supplied throughput via serving-path bottleneck (`backend/app/engine/technology.py:93–115`).
- [V] Arrival is the one estate-creation path: an externally inserted `InFlightRow` carries catalog key, ordered/arrival round,
  capex, arbitrary node JSON and `materialised`; runner reads that JSON, **not** the catalog key/price. It inserts only a node in the exact arrival round,
  creates no deployment/edge, marks even an empty payload materialised, and supplies defaults (`backend/app/round/models.py:185–199`;
  `runner.py:140–166`). No sheet path inserts an order or calculates arrival round.
- [V] Policy scoring and policy-gated event consequences do work when policy rows are supplied:
  missing choices resolve to defaults/false, explicit retention of default can count as active
  (`backend/app/engine/management.py:192–231,363–390`; `backend/app/engine/events.py:61–80`).
  Generic policy `effects` have no transition consumer in the runner; training/adoption/resistance are
  supplied state read by `backend/app/engine/organisation.py:44–84`, not simulated there.

## Accounting, chronology, and failure boundaries

- [V] `CONTRACTS.md` says: “One home, and it is `initial_state.budget.capital_remaining`.” Runtime funds instead recompute each round's capex budget minus its decision-line capex;
  no carryover, refund, opex deduction, capital-request addition, or cash decrement is implemented
  (`backend/app/round/snapshot.py:39–56`; `runner.py:129–136,368–373`). These two contexts need an explicit seam.
- [V] Opex is a sum of supplied node contributions (`runner.py:170–174`); the seeds distribute authored
  targets across nodes (`backend/seeds/riverside_full.py:39–44,80–89`). Debt inserts a positive cheapest
  fix for actionable newly raised, uncleared signals; no retirement/payment settlement path exists (`runner.py:204–216`). The supplied debt ratio is debt/(debt+committed spend)
  by capability (`backend/app/round/snapshot.py:70–97`); this inventory does not replace it.
- [V] Event iteration builds outcome/evidence records, then rebuilds the same persisted estate for the authoritative rescore;
  it does not remove the failed node or debit `revenue_loss` from cash
  (`runner.py:310–339,359–373`). The approved recovery scorecard contract owns score units; **no score-unit/interface change is proposed here**.
- [V] `lock(r)` directly overwrites the highest-lock pointer; `is_locked(r)` means pointer ≥ r. There is no sequential-round/pack-round range check or actor check. `unlock(r)` deletes only result r,
  rewinds team pointers, and retains estate/arrivals/debt/signals and later results (`runner.py:53–86`).
- [V] Advance flushes arrivals, debt and signal rows **before** checking for an existing result (`runner.py:291,342,365–366,397–408`). No runner transaction/rollback/savepoint or concurrent advance
  guard exists. `session_for` closes sessions but does not define an atomic round transaction (`backend/app/round/db.py:47–56`).
  Caller rollback can protect the transaction; catching then committing can persist partial mutations (B/C), not an automatic commit.
- [V] Full game wipes all 16 runtime tables for one instance/team, inserts estate and decisions **each** round, then commits all six
  (`backend/seeds/riverside_full.py:176–245`). Archetypes use the same pattern
  (`backend/seeds/archetype_base.py:192–248`); all four declare cost leadership. Reset-based replay proves fixture determinism,
  not retry safety or one-estate state evolution. Probe A yields 9→0 nodes.

## Conflicting/stale assumptions to carry forward without resolving

1. 1.6 §5.2/DoD says decision application and order completed, but code explicitly uses seeded deltas. Historical `1.6-A-002` is a ruled deferral;
   north-star M1 now owns it (`findings/OPEN-REGISTER.md:498,553`).
2. 1.6 O1 permits result invalidation/re-advance; 2.3 §5.2 repeats invalidation, while §5.4 says unlock after advance is refused.
   Actual code permits it. Scheduling needs a ruling on one shared contract.
3. 2.2 §5.1 lists 13 runtime tables; actual `ALL_TABLES` has 16, adding governance/policy/alignment (`backend/app/round/models.py:303–308`). Current keys have no FKs.
   `CONTRACTS.md` still labels instance scoping prospective and policy persistence deferred despite these implemented rows.
4. 2.1 assumes no existing data/one Alembic revision; fixtures/runtime migration now exist. Its proposed instance pointer overlaps today's team pointer.
   2.5 proposes bind-before-round-1 and immutable pack-version registry; today the runner accepts an arbitrary pack object.
5. Design07 §2/§3.5 policy-is-inert and §4 “54 of 75 zero lead times” are historical: policy scoring/gating is live and the shipped 75 modes have 17 zeroes.
   Its “content, not engineering” / end-to-end follow-through statements do not establish current mutation producers.
6. 2.4 excludes login UI to 3.1 while the north star assigns it to M2 auth. No authorization claim follows from the runner's “Instructor-only” unlock docstring.
7. 1.6 §5.2 pseudocode passes fired **event** keys to `fired_signals`; actual `runner.py:188–200,328–330` maps them to signal keys.
   `findings/1.6-round-runner-2026-08-22.md`, Observation 1, already rules the actual binding correct; retain that ruling, do not revive the stale pseudocode.

## Smallest first M1 contract to author

Author the **decision validation and atomic round-transition boundary** first (Heavy), as north-star M1 item 1 requires, before any estate/org builder is dispatched.
Names/shapes for new commands, revision identity and initial estate are **NEW**; this inventory assigns none. Required decisions, owned by that author/supervisor:

| OPEN | Exact decision the contract must settle |
|---|---|
| D1 Identity/input | Typed operation set and target namespaces; catalog vs placed node vs rollout vs order; uniqueness/duplicates; scoped references; permitted unknown/extra/null values; derived versus student-authored tags. |
| D2 Sheet editing | Category replacement versus line updates; explicit removals/empty category; ordering/conflicts within a sheet; pre-validation before deletion; draft/committed history and actor authorization boundary. |
| D3 Initial/carry state | Round numbering, one authoritative initial estate, mapping into persisted nodes/deployments, historical fixture separation, per-round carry-forward, deterministic ordering and versioned pack/strategy identity. |
| D4 Lifecycle | Purchase/zero-delay arrival timing against existing step order; pending-order persistence; cancellations/refunds; retire/upgrade/move replacement; edge cleanup; continue/pause/kill and scoring disposition. |
| D5 Price/resources | Content-backed option price and rounding; capex/opex effectiveness dates; support/integration pricing; resource/throughput conversion and missing authored inputs; forbid caller-injected outcomes/free prices. |
| D6 Organisation | Training coverage/count/decay, process transitions, adoption/resistance and communication formulas/parameters, staff load/FTE production, catalog-derived affected people, primary deployment, owner/sponsor identity. Undefined formulas return to author before dependent build. |
| D7 Policy/preferences | Persistent selection versus per-round active decision, explicit default retention, cost/effects, supported v1 preferences and overrides, non-policy alignment/caring-set producer; preserve frozen policy score behavior unless explicitly reviewed. |
| D8 Money/consequences | Affordability funds authority and carryover; capital requests; debt lifecycle; TCO forecasts/actuals; fund/defer/reject/rationale and event mutation versus reporting; signal credit tied to effective validated actions. |
| D9 Atomicity/replay | One resolution transaction and failure rollback, already-advanced behavior, concurrent calls, retry identity, lock immutability, permitted reopening and dependent-history invalidation/rebuild, team versus section advance ownership. |
| D10 Acceptance | One initial estate + six decision-only sheets; invalid/unaffordable/no-op inputs; arrival/cancellation and negligent rollout; failure/retry/reopen and cross-team isolation proofs. Preserve historical fixtures without treating their numeric pins as transition formulas. |

## Reproduction — existing code, in-memory SQLite only

Run from `backend/` on the inspected base with declared backend dependencies. A/B/C invoke no production seed CLI;
they use isolated in-memory state as diagnostic reproductions, not new tests or closing criteria for an unapproved contract.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from collections import Counter
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.casepack.loader import load_casepack
from app.round.db import create_all
from app.round import models as m, snapshot as snap
from app.round.runner import RoundRunner, LockStateError
import seeds.riverside_full as full
p = load_casepack(Path('packs/riverside_grocery'))
for label, items, attr in [('catalog', p.catalog, 'deployment_modes'),
                           ('platform', p.platform.services, 'placement_options')]:
    modes = [v for item in items for v in getattr(item, attr).values()]
    print(label, len(items), len(modes), dict(Counter(v.lead_time_rounds for v in modes)))
def setup():
    e = create_engine('sqlite:///:memory:')
    create_all(e)
    s = Session(e)
    s.add(m.TeamStateRow(instance_id=1, team_id=1, current_round=1,
                        declared_strategy='cost_leadership'))
    s.flush()
    return e, s, RoundRunner(s, p, 1, 1)
e, s, r = setup()  # A: bogus selection, empty patch, no carry-forward
full._seed_round_estate(s, p, 1)
r.write_decision_sheet(1, [dict(key='fake', category='training', capex=1,
    capability='order_fulfilment', target_key='does_not_exist')])
r.write_decision_sheet(1, [])
before = snap.build_team_state(s, 1, 1, 1, p)
r.lock(1)
r.advance(1)
after = snap.build_team_state(s, 1, 1, 1, p)
print('A action', snap.action_history(s, 1, 1, 1)[-1])
print('A training unchanged', before.deployments == after.deployments)
r.lock(2)
r.advance(2)
print('A nodes', len(after.nodes), len(snap.build_team_state(s, 1, 1, 2, p).nodes))
s.close()
e.dispose()
e, s, r = setup()  # B: late duplicate refusal and incomplete rewind
for n in (1, 2):
    full._seed_round_estate(s, p, n)
    r.lock(n)
    r.advance(n)
count = lambda model: s.scalar(select(func.count()).select_from(model))
print('B debt before', count(m.DebtItemRow))
try: r.advance(2)
except LockStateError as exc: print('B refusal', exc)
print('B debt after', count(m.DebtItemRow))
s.commit()  # demonstrates that catching this Python error does not force rollback
r.unlock(1)
print('B remaining results', list(s.scalars(select(m.RoundResult.round))))
print('B signal/debt rows', count(m.SignalRow), count(m.DebtItemRow))
s.close()
e.dispose()
e, s, r = setup()  # C: arrival flushed before a later scoring-input failure
order = m.InFlightRow(instance_id=1, team_id=1, key='probe_arrival',
    catalog_key='unknown', ordered_round=0, arrival_round=1,
    node_payload={'roles_filled': ['network_path']})
s.add(order)
s.add(m.PolicyDecisionRow(instance_id=1, team_id=1, round=1,
                          policy='unknown', selected='unknown'))
r.lock(1)
try: r.advance(1)
except ValueError as exc: print('C failure', exc)
s.commit()
print('C materialised/nodes/result', order.materialised,
      list(s.scalars(select(m.ArchNodeRow.key))), s.get(m.RoundResult, (1, 1, 1)))
s.close()
e.dispose()
PY
```

Observed: catalog `14 42 {0:10,1:26,2:6}`; platform `11 33 {1:25,0:7,2:1}`.
A: fake target retained as `add_training`, cost 1; training unchanged `True`; nodes `9 0`.
B: debt rows `1 → 3` despite duplicate-result refusal; unlock(1) retains result `[2]`, 8 signal rows,
3 debt rows. C: unknown-policy error leaves committed `True ['probe_arrival'] None`.
These outputs describe the inspected implementation; M1 authoring must determine the replacement guarantees.
