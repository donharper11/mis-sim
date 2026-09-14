# M1 master specification review — RETURN

Date: 2026-09-14. Reviewer: `/root/m1_master_spec_reviewer`, independent of author and builders.
Reviewed exact candidate: `dcb59f54e2ea6cc294a9c0cfffcf470e6e521ead` in `/tmp/mis-sim-m1-author`.
Product source base: `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`. The candidate changes only the master `spec.md` and `verify.md`; its preceding P0 document is separately reviewed. No implementation, repository edit, main/publish action, or delegation was performed by this reviewer.

**Disposition: RETURN. P1–P6 dispatch remains blocked.** This does not reverse the independently reviewed P0 capacity/RTO/BFS contract. The master has two demonstrated contradictions and two incomplete cross-module contracts. Supervisor rulings remain authoritative; the reviewer has not substituted product choices for them.

## Basis and checks performed

Read in full: GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS; design/08; decision-evolution authority, inventory, review, content-basis and content-review; frozen master and verification document; P0 specification. Direct source inspection included complete engine state, organisation, management, ledger, events, metrics, score, rollup and casepack models/loader; graph owner/path/coverage and technology consumers; round models/db and runner event/result/scorecard paths; design/04; original catalog/capability/event/watch and non-policy preference records used below. Source-followup SF-01/SF-02 was a lead, independently checked rather than accepted as proof.

Read-only execution used `PYTHONPATH=backend` and `/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`. No external system claim was made.

Observed:

- Frozen `verify.md` author script was extracted and rerun: all seven advertised defect detections, then PASS. This proves its stated source/math/SQLite examples, not the unbuilt service or the untested whole-game claim.
- Existing focused scorer/round pins: `14 passed in 1.62s` using `pytest -q -p no:cacheprovider` with bytecode writes disabled.
- Preference scalar-leaf counts independently recomputed: catalog 37, platform 52, training 14, services 28; total 131. Frozen table has 10 stakeholders and 33 views. Source weights/tier names and the 13 fund prices were inspected; fund total is 182000. SF-01's 14 platform-weight leaves and SF-02's universe/alias clarification are now explicitly disposed in master lines 688–710.
- Initial recurring cost/load recomputed: source 14200 + starting wages 62000 + inherited connections 2000 = 78200; load 3.7.
- Direct engine probes reproduced both blocking contradictions below.

Browser/auth/migration implementation evidence is N-A to this documentation review. P5 must still prove real PostgreSQL migration, transaction ownership, concurrency and scope isolation; source inspection or the small SQLite author probe is not that evidence.

## SPEC_PROTOCOL §11

| Row | Result | Evidence |
|---|---|---|
| 1. Acceptance maps to a check that can emit the expected result | FAIL | Named test groups are extensive, but the concrete R2 playthrough cannot be accepted under its own affordability rule (MSR-002). The integration row expects isolation that the frozen projection cannot emit (MSR-001). |
| 2. Invariants have observed planted-defect falsification | FAIL | Seven author probes ran as advertised. The entity-route probe validates only source/receiver authoring, not the actual projection spill; the game proof omits the event losses that invalidate its proposed plan. Future builder mutation rows do not establish these two present contract claims. Corrected reference probes must include the actual failure classes below. |
| 3. Fields agree across spec, CONTRACTS, design and models | FAIL | P0 contains no capability/entity visibility field, while master relies on entity-limited visibility and unchanged role scope (MSR-001). Existing ledger price semantics disagree with the new response effect and procurement constraints (MSR-003). Typed publication/delta contracts remain incomplete (MSR-004). Legacy versus production namespaces and M0 scorecard units are otherwise distinguished. |
| 4. One compliant route is written | FAIL for coherence | The sentence is present at master lines 89–94. It cannot simultaneously preserve source role/ownership scope and implement lines 548–551 through the frozen P0 interface. A corrected approved seam can restore a compliant route. |
| 5. New schema downstream checks and vocabulary homes enumerated | FAIL | P1/P2/P3/P4 dependencies are named and P2→P3 sequencing is corrected. The inter-packet DTO fields, canonical array orders and completed-read null path still require author choices; new hiring/communication option display vocabulary has no explicit schema home or named deferred home (MSR-004). |

## Blocking findings

### MSR-001 — Entity integration expands unrelated entities and roles, and can bypass the receiver

Owner: master author + supervisor; affected gate: approved integration input seam before P1/P2.

Master `spec.md:544–552` prescribes extending `source.serves` by every receiver capability, but says this applies “for that validated entity” and performs no source-role expansion. `backend/app/engine/graph.py:67–82` reads **all** `owns_entities` for each node returned by `nodes_serving(capability)`; `state.py` implements that filter using only `serves`. `technology.py:35–42` likewise counts all source roles. P0 explicitly leaves serves/ownership unchanged and supplies only capacity/RTO fields. There is no representation for the promised entity-only access.

A legal POS→ecommerce product integration, projected exactly as the master prescribes, also makes POS sale data visible to marketing_sales and adds POS roles there. This is not a possible implementation mistake: it follows from the frozen fields and existing consumers.

Reproduction from product source root:

```bash
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python - <<'PY'
from app.casepack.loader import load_casepack
from app.engine.state import ArchNode,TeamState,StaffPool
from app.engine import graph
p=load_casepack('backend/packs/riverside_grocery'); c={x.key:x for x in p.catalog}
src,dst=c['pos_system_2011'],c['ecommerce_site']
assert any(x.entity=='product' and x.from_capability in src.serves for x in dst.must_be_fed_by)
n=ArchNode('initial_pos_system_2011',tuple(src.roles_filled),src.availability,0,
 src.service_life_rounds,tuple(dict.fromkeys([*src.serves,*dst.serves])),
 owns_entities=tuple((x.entity,x.level_of_detail) for x in src.owns_entities))
s=TeamState(1,'cost_leadership',(n,),(),(),(),(),StaffPool(2,0),(),())
print(graph.owner_nodes(s,'marketing_sales','sale','individual_transaction',[]))
print(sorted({r for n in s.nodes_serving('marketing_sales') for r in n.roles_filled}))
assert graph.owner_nodes(s,'marketing_sales','sale','individual_transaction',[]) == []
PY
```

Observed output: `['initial_pos_system_2011']`, `['pos_app', 'transaction_store']`, then AssertionError. The same class affects all multi-entity/role sources, not just POS.

The path also needs an explicit receiver rule: `graph.serving_path` finds any client-to-owner path through global undirected adjacency. An initial network→POS edge can supply the imported path without traversing ecommerce, so receiver capacity/resource loss may not constrain it. Merely filtering owner visibility still leaves that defect.

Closing checks: corrected independently reviewed seam must ship executable source-backed reference probes and later candidate tests selected by `pytest -q backend/tests/test_simulation_estate.py -k integration`. They must assert: only the selected entity becomes accessible; unrelated roles/entities stay absent; ownership identity stays the source; one physical source/receiver each; valid receiver path participates in capacity/reliability; zero/unavailable/retired receiver or disconnect removes usable imported access; no transitive access. Each omission must fail a planted-defect run. The source probe above is the current failure witness, not a demand to alter P0 silently.

Minimal coherent alternatives for authority, not reviewer-selected implementation:

1. Add a separately reviewed immutable entity-access sidecar identifying connection/source/receiver/entity/capability. Keep physical nodes' original serves/roles/owns_entities unchanged. Teach the existing entity/path consumers to resolve that access while retaining source ownership provenance and requiring a live receiver path. Freeze how receiver capacity/reliability and multiple access paths participate; update every technology/metric/event path consumer and preserve legacy defaults/results.
2. Add separate per-capability **accessible entity** input on the receiver, explicitly distinct from owned entities, with source/connection provenance and corresponding graph lookup/path semantics. It must not create a second system of record or erase duplicate-owner penalties. This has the same need for reviewed consumer changes.

Duplicated physical facets, broad whole-node serves expansion, or annotating evidence without changing consumer semantics are not coherent fixes under the supervisor's retained ruling.

### MSR-002 — Concrete balanced/no-org games fail at round 2

Owner: master/verification author; affected gate: P6 plan and §11 acceptance.

Frozen `verify.md:185–199` requires balanced and all_tech_no_org to share the listed acquisitions/integrations. Round 1 buys Centraline SaaS but provides neither identity nor funded response. The initial estate has no identity (`spec.md:311–315`). Original `events.yaml:66–80,110–124` fires ransomware (100000 loss) and phishing (30000) for all four strategies. They are the first two eligible identity events under the unchanged cap. Thus R1 operating reserve is `100000−78200−130000 = −108200`.

The R2 sheet adds a basic integration with recurring 1000, while the prior Centraline order adds 9100. R2 projected close is `−108200+100000−78200−9100−1000 = −96500`. The integration raises per-round future liability, so `spec.md:737–745` necessarily rejects it. No expected refusal/fallback is authored for this step. Funding one-off training despite a deficit, as newly ruled, does not authorize the recurring integration.

Reproduction (isolating the known identity condition; other signals cannot remove its separate capability slots):

```bash
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python - <<'PY'
from app.casepack.loader import load_casepack
from app.engine.state import TeamState,StaffPool
from app.engine.ledger import advance_ledger
from app.engine.events import resolve_events
p=load_casepack('backend/packs/riverside_grocery'); by={e.key:e for e in p.events}
for strategy in [x.key for x in p.strategies]:
 s=TeamState(1,strategy,(),(),(),(),(),StaffPool(2,3.7),(),(),available_funds_by_round=(340000,))
 fired,_=resolve_events(s,p,advance_ledger((),s,p))
 loss=sum(by[k].outcomes.revenue_loss or 0 for k in fired)
 r1=100000-78200-loss; r2=r1+100000-78200-9100-1000
 print(strategy,fired,loss,r1,r2)
 assert r2>=0, 'R2 increases recurring liability but candidate forecast is negative'
PY
```

Observed first strategy: `('ransomware_on_finance','phishing_on_staff_accounts') 130000 -108200 -96500`, then AssertionError. The authored affinity lists are identical across all four.

Closing checks: author concrete revised typed templates with explicit identity/prevention/reducing decisions or declared refusals/fallbacks, preserving the intended identical-technology comparison. Before dispatch, run a full source-backed reference forecast including actual events and demonstrate all planned accepted rounds are eligible. After build: `pytest -q backend/tests/test_simulation_games.py -k 'decision_only or cross_effects'`; all 16×6 rounds must pass, and removing the necessary solvency decision must fail without changing rules or expectations. The affordability rule itself must not be weakened to rescue the template.

### MSR-003 — Legacy “effectful fix” prices need an explicit production disposition

Owner: supervisor/master author; affected gate: P4 actions, actionability and debt.

`spec.md:787` makes funded responses non-clearing, temporary prevention only; lines 799–801 call original `advance_ledger` unchanged. `ledger.py:160–211` still includes funded options as effectful repair prices, every catalog mode irrespective of v1 initial-only restrictions, and no operating/horizon feasibility. This feeds `was_actionable`, responsiveness denominator and the master debt estimate. New actual integration repair actions are `add_service_tier`, while e.g. `cust_data_01` only lists add_node/upgrade_component/add_policy, so a genuine integration repair has a natural-lapse/no-credit disposition unless explicitly resolved.

Current Riverside minima were independently printed: all zero except wh_rollout_01=3000. Therefore I do **not** claim the response exclusion changes today's Riverside minimum. The mismatch is the claimed meaning of a generic production quote and its unsupported null path, not a fabricated changed pin.

Executable falsifier for the response-only supported action vocabulary:

```bash
PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python - <<'PY'
from app.casepack.loader import load_casepack
from app.casepack.models import WatchRule
from app.engine.ledger import cheapest_effectful_fix,was_actionable
p=load_casepack('backend/packs/riverside_grocery')
d=next(x for x in p.watch_rules if x.key=='wh_rollout_01').model_dump()
d['cleared_by']=['fund_response']; rule=WatchRule.model_validate(d)
quote=cheapest_effectful_fix(rule,p)
print(quote,was_actionable(quote,(6000,),range(1,2)))
assert quote is None, 'v1 prevention cannot repair this watch condition'
PY
```

Observed `6000 True`, then AssertionError. This is a typed unit fixture for the lookup, not a claim that the modified whole pack passed the production validator.

Closing check: choose explicitly between (a) a separately reviewed production candidate-price seam with preserved legacy behavior, or (b) a clearly bounded retained legacy proxy with approved naming/limitations and refusal of unsupported content. Freeze response-only, initial-only, already-live/no-op, late-arrival and operating-deficit cases, plus proper integration repair credit/disposition. Execute those reference cases before review; later run `pytest -q backend/tests/test_simulation_consequences.py -k 'actions_signals or debt_tco'` with false-actionability mutants. No builder may silently relabel a temporary response as training or change the legacy scorer/ledger contract.

### MSR-004 — Strict inter-packet shapes and completed/null ordering paths remain undefined

Owner: master author; affected gate: P1 DTO freeze and dependent P2–P5.

Concrete unresolved choices at this exact candidate:

- `spec.md:929–939`: EstateDeltaV1/OrgDeltaV1 “effect_candidates” has no record schema. ResourceViewV1 describes concepts but no exact keys/container/ranges for the per-placement and per-asset records. P1 owns DTOs, and P2/P3 are forbidden from amending them, so a builder must invent a shared interface.
- `spec.md:414` requires every array to sort by `(round,key)`, but StaffHire has `arrival_round,order_id`, Debt `opened_round,signal,episode_id`, ActionRecord `locked_round,action_type,capability,target_key,cost`, and Tco `ordered_round,asset_id` (`spec.md:443–462`, `state.py:117–135`). These cannot follow the specified tuple as written. Effect actions also lack a frozen unique join back to their source command when several commitments share type/capability/round.
- `spec.md:119–120,480–489`: final advance creates no next sheet, yet RunViewV1 always contains `sheet` without a completed-case null/last-sheet rule or final current_round value. Missing/null fields otherwise reject. Initial sheet revision and sheet digest canonical input are also not fully stated.
- Runtime hiring/communication schemas at lines 258–260 contain no label field, while no explicit M3 vocabulary home is assigned. Only unit labels have a home. Machine-code errors can legitimately remain headless, but §11 still requires the downstream label/vocabulary ownership to be enumerated.

Closing check: supply exact nested records, per-array sort/identity rules and complete initialized/draft/locked/completed view examples, plus a schema/consumer/label-owner table. Add a directly executable reference-contract probe that constructs all four view states, canonicalizes reversed input collections to identical expected bytes, and rejects unknown fields, absent required fields, forbidden nulls, ambiguous duplicate actions and invalid references. Show each corresponding planted defect fails. Later candidate commands: `pytest -q backend/tests/test_simulation_content.py -k checkpoint` and `pytest -q backend/tests/test_simulation_service.py -k 'editing or retry_reopen'`. The author owns these choices before P1; they are not reviewer or builder discretion.

## Retained strengths and scope checks

The candidate has useful, concrete lifecycle rules: lead-time arrival, due cancellation before rollout, sunk costs, replacement keeping the old asset live, no-op replacement preserving currency, final-horizon rejection and paused expiry. It separates capital from operating reserve, carries committed pending liabilities, permits capital-funded non-increasing-liability choices during deficits, retains partial Financial status, and keeps technical debt distinct from cash. Training decay, count rounding, process charges, resistance/adoption, support scope, assignment identity and policy activity are specified without new scorer equations. Their named positive/negative builder gates remain required.

Event prevention price/rationale, fire-once exclusions, original deck order and point conversion are explicit. Debt settlement and frozen TCO forecasts have stated homes. The review findings concern whether the promised inputs and examples can actually satisfy those rules; no tuning or balance verdict was performed.

P2→P3 dependency sequencing and explicit projection staff/alignment inputs are coherent. The new migration and three-table checkpoint authority preserve the historical 16-table fixture path. P5's instruction to update runtime documentation at master line 1038 must be assigned to an exact allowed path or explicitly to supervisor integration when dispatch is prepared. It is not a blanket permission to edit undocumented files.

Re-review must name a new exact SHA, rerun corrected reference probes, reconcile each stable finding above, and inspect any new engine/schema seam against its complete consumers. This report does not authorize a dependent builder.
