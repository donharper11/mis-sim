# M1 P0b — entity-scoped access and verified repair inputs

Authored under SPEC_PROTOCOL.md v1.3,2026-09-14. Heavy. **NEW review candidate; no
implementation authorized until independent PASS.** Runs after audited P0; P0's frozen
capacity/RTO/BFS contract is unchanged. Root approved these two seam families after
MSR-001/MSR-003 on master dcb59f5; exact semantics below require fresh review.

## Basis, contradiction and scope

[V] Author reread complete engine state/graph/technology/catalog/metrics/preconditions/
events/ledger/organisation/management, original casepack models and Riverside platform,
catalog, watch_rules, obligation_rules, events. Root protocols and original1.4/1.5/1.6
contracts/master readset remain applicable. Source base b7706fb plus audited P0 is the
integration basis; builder receives exact SHA. No AGENTS exists. Extraction covers all
ownership, serving-path, SPOF, blast, failover, capacity, ledger-price/actionability consumers.

[V] `graph.owner_nodes` filters whole nodes by serves then reads every owns_entities;
technology coverage/currency likewise consumes whole serving nodes. Therefore expanding a
POS node's serves for a product integration also exposes sale and POS roles, and a direct
client→POS network path bypasses the receiving ecommerce asset. This violates the granted
entity's scope. Changing owner_nodes alone does not fix mandatory receiver capacity/outage.

[V] `ledger._candidate_costs` lists fund_response and initial-only/free modes as repairs;
`was_actionable` considers capital only. Production prevention does not repair the watch,
and feasible repairs must obey runtime availability/lead/horizon/operating rules. Those old
functions remain exact legacy defaults; production must provide verified repair witnesses.
No score weight/MOT formula, status precedence, metric threshold, entity hierarchy or
legacy fixture is reinterpreted here. Numeric output calibration is outside this packet.

One compliant route: append optional immutable inputs to TeamState, retain exact absent-
input paths, route imported entity access through its receiver and physical integration,
reuse that route for failure exclusions, and let ledger use validated production assessment
witnesses instead of its old generic price list. The pure engine never generates decisions,
prices, DB reads or repair search; P4 is the sole production assessment producer.

## NEW immutable inputs (version1)

Append to frozen TeamState, after all existing/P0-compatible fields:

```python
entity_access: tuple[EntityAccess, ...] | None = None
repair_assessments: tuple[RepairAssessment, ...] | None = None
```

NEW frozen dataclasses:

```python
EntityAccess(connection: str, source: str, receiver: str, capability: str, entity: str)
RepairCandidate(candidate_key: str, capital_cost: int, effective_round: int, affordable: bool)
RepairAssessment(signal: str, checked_round: int, candidates: tuple[RepairCandidate, ...])
```

All string keys nonempty/non-whitespace; counts/costs exact non-bool ints, capital_cost≥0,
rounds≥1, affordable exact bool. A supplied iterable must be tuple/list of the exact record
class, copied to a tuple; arbitrary dictionaries, strings, generators and malformed records
raise ValueError. Duplicate grant tuple `(connection,source,receiver,capability,entity)`
or duplicate assessment.signal/candidate_key within an assessment raises. Grants forbid
source==receiver. No mutable list retained at either layer. Candidate_key is a64-lowercase-
hex SHA256 of canonical candidate commands, not a physical asset key. Record validation
raises ValueError consistently, including nonfinite/overflow/bool numeric rejection.
None is the unchanged historical path. Present empty tuple means production semantics
with no grants/assessments; ledger requires complete watch assessment coverage when used.

Engine structural validation does not replace producer authority. P2 validates each grant
against the immutable content/current live assets: source truly owns entity at original
level, receiver originally serves capability and declares the matching dependency, original
source serves satisfies from_capability, and a live directed integration connection exists.
No transitive grants, no authored role/entity/serves rewrite and no duplicated physical node.
Only the granted entity is visible; level derives from original source ownership. Engine
query also requires both nodes and matching integration edge still live, exact capability/
entity match, receiver.serves containing capability, and source owns the requested level.
A dangling grant is ineffective rather than access to a missing node. Unknown content keys
or unjustified live grants reject in P2; P0b does not receive a pack at node construction.

P4's candidate records attest a real effectful legal command bundle that both repairs the
watched condition and emits an action in that rule's original cleared_by vocabulary with
qualifying original commitment time. Real repairs lacking that credit eligibility are
reported separately as repaired_but_uncredited and excluded from these candidates; no
original watch rule or action timestamp is changed. Thus the minimum is over VERIFIED
CREDIT-ELIGIBLE repairs in the bounded catalogue, not every possible physical repair.
The records additionally attest sourced price,
in-game effect date and full affordability check. Engine ledger validates assessment keys
exactly equal pack.watch_rules keys, checked_round==state.round, effective_round between
checked_round and pack.metadata.rounds, and uniqueness. No assessment may silently fall
back to legacy price calculation. P4 persists full commands/price/forecast/metric witnesses
in checkpoint evidence; these compact inputs identify them, not a second editable history.

## NEW one-hop entity route

`graph.owner_nodes` with entity_access=None remains exact legacy. With a tuple, return
sorted de-duplicated physical IDs: original serving owners plus grant sources satisfying
all exact grant predicates above. The receiver is not promoted to owner. `nodes_serving`,
coverage and currency remain original-serving-only; no source roles/age enter a capability
merely through a data grant. Two grants from one source still represent one owner and one
physical placement/failure/cost. Existing inconsistency penalty remains over actual distinct
owners, not grants; two independent owners do not become one merely by sharing a receiver.

Extend serving_path with keyword-only exclusion arguments (default empty frozensets):
`exclude_nodes: frozenset[str]`, `exclude_edges: frozenset[tuple[str,str,str]]`.
Both exclusions accept only frozenset (including the default empty frozenset); None,
list/set/dict/string/generator containers raise ValueError. Node entries must be nonempty,
non-whitespace strings. Edge entries must be exact3-tuples of nonempty string endpoints
and kind network|integration|failover, with distinct endpoints already in lexicographic
order; unsorted/self endpoints, malformed tuples and unknown kinds raise ValueError.
Unknown well-formed node/edge identities are harmless no-ops. Validate before either route
branch. With entity_access=None and both exclusions empty, call the exact legacy path.
With None and any nonempty exclusion, run native-only stable BFS after removing those
nodes/edges; it is an explicit new query operation, never an implicit grant/default change.
No existing caller supplies exclusions, so legacy payload remains byte-identical.

Edge identity is `(min(src,dst),max(src,dst),kind)`, so exclusions remove that physical edge
kind regardless of duplicate entity metadata. Production builder forbids duplicate identical
physical/entity connections; several entities may share a physical integration pair.

For entity_access present, enumerate:
1. Native candidate: stable BFS from original live client_access nodes serving capability
   to original serving owner nodes, after exclusions.
2. For each valid exact grant: stable BFS from those clients to its receiver, excluding the
   grant source as well as requested exclusions; append source using its live receiver→source
   integration edge. The required integration must not be excluded. A source cannot appear
   earlier in the prefix; the resulting physical path is simple and always includes receiver.
Choose minimum `(number_of_nodes,tuple(node_keys))` over candidates; none=>None. No longest
path or cheapest-node preference. A native ownership route remains legal even when an
additional imported route exists. All tuples/lists are detached; no exclusion mutates state.

This route makes receiver throughput/resource factor and availability unavoidable for
imported primary data. P0 capacity lookup compares only the requested capability: a source
with no entry for that capability contributes no ceiling, not its other-unit ceiling.
Source and receiver each contribute reliability once. Secondary-entity ownership adequacy
uses exact live grants as above, matching the existing rule that native ownership does not
itself require a client path. Primary serving failure still produces the existing zero
capacity/reliability; no data-adequacy scoring formula is added.

Add `graph.serving_spofs(state,capability,entity,level,level_order,path)`. For a production
path it examines each interior physical node in path order: remove it and rerun the same
serving_path; mark it a SPOF only if no native or imported alternative remains. Technology
uses this helper only when entity_access is present; legacy spofs_on_path stays unchanged.
Receiver can therefore be a service SPOF even when a physical client→source shortcut exists.
The explicit node_is_spof precondition remains its frozen global physical-articulation
meaning; it has no capability/entity context. Do not silently broaden that predicate.

Production `blast_radius` uses the same route: a capability is hit only if its full route
exists before removal and none exists with node excluded. Native and imported alternatives
both count. Legacy None-input path stays untouched, including old empty-path behavior.
Production failover_exists first finds a route with failed node excluded, then removes each
remaining failover-kind physical edge in turn and calls the same route again: true iff at
least one removal destroys all valid routes. No valid surviving route=>false. This preserves
the existing load-bearing-failover definition while respecting required receivers. An
integration edge by itself is never classified failover. Failed-node selection uses the
same production serving path and P0 per-capability bottleneck; outage RTO is still P0's
explicit/legacy precedence. Receiver removal, source removal, grant-edge removal and
alternate-receiver failover all receive independent tests.

Technology entity evidence adds
`evidence["data_adequacy"]["entities"][entity_key]["access_via"]` ONLY when entity_access is
present. Its value is a list of detached `{connection,source,receiver,capability,entity}`
rows satisfying every live-grant predicate and requested level for that exact capability/
entity query. De-duplicate by all5field tuple, then sort by
(connection,source,receiver,capability,entity). No valid grants=>[] even if a native owner
exists. `owned_by` remains de-duplicated actual physical source/owner IDs; two valid
connections to one owner may legitimately yield two provenance rows. With entity_access
None the access_via key is absent, not null or[]. No extra key in legacy results. Metrics already call owner_nodes/
serving_path and inherit exact semantics; update only if a new direct consumer is found.
Preconditions entity_unowned/placement_count continue physical ownership/multiplicity.

## NEW verified assessment seam; unchanged legacy defaults

`advance_ledger` keeps its signature. If state.repair_assessments is None, all old generic
cheapest_effectful_fix/was_actionable behavior remains byte-identical. With assessments:

- Current assessment status is `verified` iff candidates nonempty; otherwise `unassessed`.
  Empty means the bounded producer verified no candidate, never “no repair exists.”
- Current cheapest verified credit-eligible repair is min capital_cost over verified candidates, regardless
  of affordability. Current affordable witness is min `(capital_cost,candidate_key)` among
  affordable=True candidates, or none. These may be different candidates because ongoing
  liabilities differ. Neither fund prevention nor a no-op may be a candidate.
- A newly raised episode stores current cheapest verified credit-eligible cost in the EXISTING
  cheapest_fix_when_raised (None if unassessed), and was_actionable iff an affordable witness
  exists. The initial quote is frozen thereafter, even if later assessed or cheaper.
- For an existing latest open episode, was_actionable becomes prior.was_actionable OR
  current affordable-witness-exists. It never compares the initial generic price against
  available_funds_by_round in the production branch. A later opportunity does not rewrite
  past assessments, the episode's initial quote or first_shown_round.
- Matching real actions, original locked_round, still-raises guard, clear/fire precedence,
  terminal episode immutability and same-round/fired-on-sight projection rules are unchanged.
  Second fire-stamping pass receives the exact same assessment tuple; it does not re-quote.

Full assessment history (including unassessed reasons and candidate witness bodies) is
persisted by P4, outside LedgerSignal's frozen fields. Thus no UI may label None “free” or
“impossible,” and a verified unaffordable repair differs from an unassessed catalogue.
Debt uses the frozen initial quote only when priced; later affordability can change signal
responsiveness opportunity without inventing retroactive priced debt. Master specifies
unpriced exposure reporting. This packet implements no debt ledger or candidate generator.

## Exact packet, preflight and acceptance

Allowed edits: existing backend/app/engine/{state,graph,technology,metrics,events,ledger}.py;
NEW backend/tests/test_engine_production_inputs.py;
NEW handoffs/recovery/decision-evolution/production-inputs/dod.md. No preconditions/scorer/
weights/content/runner/DB/P0test changes. P0's already reviewed behaviors stay intact.
Read every allowed file complete, P0spec, this spec, master/verify and original contracts.

PF0 clean/exact assigned post-P0 SHA. PF1 `rg -n 'owner_nodes|serving_path|spofs_on_path|blast_radius|failover_exists|cheapest_effectful_fix|was_actionable' backend/app backend/tests`:
inspect every hit and record which path consumes context/quote; new uninspected hit stops.
PF2 original pins+P0focused tests pass; PF3 P0full24 capture exact e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4.
PF4 author computed probe below passes and detects each planted defect. PF5 `make check`.

Named pytest groups and concrete falsification:

| -k | Acceptance | Real code defect to plant and observe failing |
|---|---|---|
| access_scope | product grant exposes product only; no sale/role/currency leak; one owner for two grants; levels exact, no transitive grant | union source.serves or add receiver as owner |
| access_path | physical shortcut cannot skip receiver; mapped receiver1125/campaigns constrains path; other-unit source6000/store_day ignored; disconnected/retiredreceiver/removedgrant fail | route directly to source or ignore integration kind |
| access_failure | receiver is service SPOF; source/receiver removal blast; alternate receiver survives only via load-bearing failover; removals pure | call raw physical BFS during failover/blast |
| assessment | None legacy; complete checked-round/key enforcement; cost0 realcandidate vs unassessedNone; cheapestunaffordable distinctaffordablewitness; lateropportunity preservesinitialquote | include fund; fallback empty assessment tolegacyprice; recomputeinitialquote |
| immutable | copied tuples, malformedcontainers/records/keys/bool/dates/costs rejected; no aliases | retain supplied list or accept bool cost |
| legacy | all24fullJSON/pins/P0tests byte-identical; no added access evidence whenNone | add empty access_via to every old report |

Builder and fresh auditor execute actual input interfaces and each planted code regression
on disposable copies, then restore and rerun focused tests/makecheck. Author probes establish
the numeric/route counterexample before these new fields exist; they do not replace actual
candidate tests. No browser/migration/auth rung applies to pure P0b. Review PASS and audited
build of P0b are required before dependent P1+ dispatch; P0alone does not authorize it.

Supervisor literal CONTRACTS addition on audited integration:

> **Production engine inputs v1.** Optional TeamState entity_access grants expose one
> original source-owned entity to one declared receiving capability through a mandatory
> live receiver/integration path. Ownership, roles, serves, currency membership and physical
> identity remain original. Per-entity access provenance lives at
> TechResult.evidence.data_adequacy.entities[entity].access_via under this packet's exact
> sorted/valid-grant/production-empty/legacy-omitted contract. Serving capacity, SPOF, blast and failover queries use the same
> exclusions, so receiver failure cannot be bypassed by an unrelated physical shortcut.
> Optional repair_assessments replace legacy generic actionability estimates only for
> production. A verified candidate has real effect/price/horizon/affordability evidence;
> unassessed means no candidate verified in the bounded catalogue, not no repair exists.
> Episode initial quotes/timestamps remain frozen, and later verified opportunities update
> only current/persistent actionability. Absent optional inputs preserve exact legacy24
> results. Simulation projection/consequence preparation are sole production producers.

Supervisor appends this subsection to design/07-decision-consequence-map.md:

> ### Entity access and assessed repair opportunity
> An integration grants only its named data, not every role or record held by its source.
> Imported data must pass through the live receiving system. Runtime repair assessments
> use bounded verified choices and distinguish a priced repair, an affordable repair and
> an unassessed possibility. Historical generic repair-price examples remain fixture-only.


## Executed author reference probe

This standalone prototype combines actual source owners/roles, graph BFS/bottleneck/
reliability consumers, live watch predicates, price rows and the old false quote with the
NEW explicitly described route/candidate rules. It is not production implementation.
It runs only in memory; the new candidate input interfaces are still builder deliverables.

```bash
PYTHONPATH=backend python - <<'PY'
from dataclasses import replace
from types import SimpleNamespace
from collections import deque
from app.casepack.loader import load_casepack
from app.engine import graph,metrics
from app.engine.ledger import cheapest_effectful_fix,was_actionable,LedgerSignal
from app.engine.state import ArchNode,ArchEdge,TeamState,StaffPool,DeploymentState
p=load_casepack('backend/packs/riverside_grocery');items={x.key:x for x in p.catalog}
def eq(a,b):assert a==b,(a,b)
def detect(name,f):
    try:f()
    except AssertionError:print(name,'defect DETECTED');return
    raise AssertionError(name+' escaped')
def state(nodes,edges):return TeamState(1,'cost_leadership',tuple(nodes),tuple(edges),(),(),(),StaffPool(2,0),(),())
pos=items['pos_system_2011'];web=items['ecommerce_site']
owner=ArchNode('pos',tuple(pos.roles_filled),pos.availability,0,pos.service_life_rounds,tuple(pos.serves),None,tuple((e.entity,e.level_of_detail) for e in pos.owns_entities))
receiver=ArchNode('web',tuple(web.roles_filled),web.availability,0,6,tuple(web.serves),1125)
client=ArchNode('client',('client_access',),.99,0,6,('marketing_sales',))
s=state([client,owner,receiver],[ArchEdge('client','pos'),ArchEdge('client','web'),ArchEdge('web','pos','integration')])
grants=[('g1','pos','web','marketing_sales','product')]
def live_grants(st,entity,removed=frozenset(),removed_edges=frozenset()):
    out=[]
    for g in grants:
        _,source,dst,cap,ent=g;n=st.node(source);r=st.node(dst)
        edge=tuple(sorted((source,dst)))+('integration',)
        if ent!=entity or cap!='marketing_sales' or source in removed or dst in removed:continue
        if not n or not r or cap not in r.serves or not any(e==entity for e,_ in n.owns_entities):continue
        if edge in removed_edges:continue
        if not any(e.kind=='integration' and {e.src,e.dst}=={source,dst} for e in st.edges):continue
        out.append(g)
    return out
def route(st,removed=frozenset(),removed_edges=frozenset()):
    candidates=[]
    for _,source,dst,_,_ in live_grants(st,'product',removed,removed_edges):
        nodes=[n for n in st.nodes if n.key not in removed and n.key!=source]
        edges=[e for e in st.edges if tuple(sorted((e.src,e.dst)))+(e.kind,) not in removed_edges]
        prefix_state=replace(st,nodes=tuple(nodes),edges=tuple(edges))
        # Existing BFS consumes sorted adjacency iterables and sorted sources.
        adj={k:sorted(v) for k,v in graph._adjacency(prefix_state).items()}
        prefix=graph._bfs_path(adj,['client'],{dst})
        if prefix:candidates.append(prefix+[source])
    return min(candidates,key=lambda x:(len(x),tuple(x))) if candidates else None
path=route(s);eq(path,['client','web','pos'])
eq(graph.bottleneck_capacity(s,path),1125)
eq(round(graph.path_reliability(s,path),6),round(.99*web.availability*pos.availability,6))
eq(live_grants(s,'sale'),[])
leaky=replace(s,nodes=(client,replace(owner,serves=(*owner.serves,'marketing_sales')),receiver))
detect('unrelated entity exposure',lambda:eq(graph.owner_nodes(leaky,'marketing_sales','sale','individual_transaction',[]),[]))
raw=graph._bfs_path(graph._adjacency(s),['client'],{'pos'})
detect('receiver shortcut',lambda:eq(raw,path))
eq(route(s,{'web'}),None);eq(route(s,{'pos'}),None)
eq(route(s,removed_edges={('pos','web','integration')}),None)
detect('ignored receiver failure',lambda:eq(graph._bfs_path(graph._adjacency(s,exclude='web'),['client'],{'pos'}),None))
# A second real receiver gives one source owner and a load-bearing failover route.
r2=replace(receiver,key='web2');s2=replace(s,nodes=(*s.nodes,r2),edges=(*s.edges,ArchEdge('client','web2','failover'),ArchEdge('web2','pos','integration')))
grants.append(('g2','pos','web2','marketing_sales','product'))
eq(sorted({g[1] for g in live_grants(s2,'product')}),['pos'])
eq(route(s2,{'web'}),['client','web2','pos'])
eq(route(s2,{'web'},{('client','web2','failover')}),None)
detect('double owner for two grants',lambda:eq([g[1] for g in live_grants(s2,'product')],['pos']))
# A real source-backed witness distinguishes cheapest verified credit-eligible and affordable repair.
service=next(x for x in p.platform.services if x.key=='central_sign_on')
base=state([],[])
rule=next(x for x in p.watch_rules if x.key=='sec_identity_01')
assert metrics.missing_identity_access(base,p,rule)
assert not metrics.missing_identity_access(replace(base,nodes=(ArchNode('identity',tuple(service.roles_filled),.99,5,6),)),p,rule)
def candidate(mode,round=5,live=False):
    price=service.placement_options[mode];effect=round+price.lead_time_rounds
    if live or effect>6:return None
    reserve=0
    for r in range(round,7):reserve+=100000-98000-(price.opex if r>=effect else 0)
    return (mode,price.capex,effect,price.capex<=50000 and reserve>=0)
rows=[candidate(k) for k in service.placement_options];rows=[r for r in rows if r]
eq(min(r[1] for r in rows),0)
eq(min((r[1],r[0]) for r in rows if r[3]),(25000,'on_prem'))
detect('capital-only affordability',lambda:eq(min((r[1],r[0]) for r in rows if r[1]<=50000),(25000,'on_prem')))
eq(candidate('on_prem',6),None);eq(candidate('on_prem',5,True),None)
rule2=next(x for x in p.watch_rules if x.key=='wh_rollout_01').model_copy(update={'cleared_by':['fund_response']})
legacy=cheapest_effectful_fix(rule2,p)
eq(legacy,6000);eq(was_actionable(legacy,(6000,),range(1,2)),True)
# Production bounded catalogue excludes prevention before metric-effect verification.
deployment=DeploymentState('warehouse','centraline_im7','warehouse',34,0,'unchanged',0,False,('order_fulfilment',))
rollout_state=replace(base,deployments=(deployment,))
assert metrics.rollout_without_support(rollout_state,p,rule2)
# Removing a funded event from its deck does not mutate the rollout state.
production=[o for e in p.events for o in e.options if o.key=='fund'
            and not metrics.rollout_without_support(rollout_state,p,rule2)]
fake_fund_state=replace(rollout_state,deployments=(replace(deployment,trained_count=21),))
detect('fund fabricated training',lambda:eq(metrics.rollout_without_support(fake_fund_state,p,rule2),True))
eq(production,[])
detect('prevention treated as repair',lambda:eq(legacy,None))
old=LedgerSignal('x',1,'firm_infrastructure','missing_identity_access','presence',1,'critical','open',1,cheapest_fix_when_raised=None)
later=replace(old,was_actionable=old.was_actionable or any(r[3] for r in rows))
eq((later.cheapest_fix_when_raised,later.was_actionable),(None,True))
detect('rewritten initial quote',lambda:eq(replace(later,cheapest_fix_when_raised=min(r[1] for r in rows)).cheapest_fix_when_raised,None))
print('production input source-backed reference probes PASS')
# Run after the preceding production-input reference block in the same namespace.
def exclusions(nodes,edges):
    if type(nodes) is not frozenset or type(edges) is not frozenset:raise ValueError('container')
    valid=lambda x:isinstance(x,str) and bool(x.strip())
    if any(not valid(k) for k in nodes):raise ValueError('node key')
    for e in edges:
        if type(e) is not tuple or len(e)!=3:raise ValueError('edge tuple')
        a,b,k=e
        if not valid(a) or not valid(b) or not a<b or k not in {'network','integration','failover'}:raise ValueError('edge key')
def checked_route(st,nodes=frozenset(),edges=frozenset(),native=False):
    exclusions(nodes,edges)
    if not native:return route(st,nodes,edges)
    st=replace(st,nodes=tuple(n for n in st.nodes if n.key not in nodes),edges=tuple(e for e in st.edges if tuple(sorted((e.src,e.dst)))+(e.kind,) not in edges))
    return graph._bfs_path({k:sorted(v) for k,v in graph._adjacency(st).items()},['client'],{'pos'})
for n,e in [(None,frozenset()),(set(),frozenset()),(frozenset(),None),(frozenset({''}),frozenset()),(frozenset(),frozenset({('a','b')})),(frozenset(),frozenset({('b','a','network')})),(frozenset(),frozenset({('a','b','bad')})),(frozenset(),frozenset({('a','a','network')}))]:
    try:exclusions(n,e)
    except ValueError:pass
    else:raise AssertionError('invalid exclusions accepted')
eq(checked_route(s,nodes=frozenset({'missing'})),['client','web','pos'])
eq(checked_route(s,nodes=frozenset({'web'})),None)
eq(checked_route(s,nodes=frozenset({'pos'}),native=True),None)
detect('ignored native exclusion',lambda:eq(checked_route(s,native=True),None))
try:exclusions(None,frozenset())
except ValueError:print('null exclusion rejected PASS')
else:raise AssertionError('null coerced')
def must_reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('invalid value silently accepted')
detect('coerced null exclusion',lambda:must_reject(lambda:exclusions(frozenset(),frozenset())))
def entity_evidence(st,present):
    native=graph.owner_nodes(st,'marketing_sales','product','sku',[])
    row={'required_level':'sku','owned_by':native}
    if present:
        valid=live_grants(st,'product');row['owned_by']=sorted(set(native+[x[1] for x in valid]))
        row['access_via']=[dict(zip(('connection','source','receiver','capability','entity'),g)) for g in sorted(set(valid))]
    return {'evidence':{'data_adequacy':{'entities':{'product':row}}}}
expected_row={'required_level':'sku','owned_by':['pos'],'access_via':[{'connection':'g1','source':'pos','receiver':'web','capability':'marketing_sales','entity':'product'}]}
actual=entity_evidence(s,True)
eq(actual['evidence']['data_adequacy']['entities']['product'],expected_row)
wrong_home={'required_level':'sku','owned_by':['pos']}
detect('wrong access evidence home',lambda:eq(wrong_home,expected_row))
raw={**expected_row,'access_via':[dict(zip(('connection','source','receiver','capability','entity'),g)) for g in grants]}
detect('dangling grant in evidence',lambda:eq(raw,expected_row))
legacy=entity_evidence(s,False)['evidence']['data_adequacy']['entities']['product']
eq(legacy,{'required_level':'sku','owned_by':[]})
detect('legacy empty evidence key',lambda:eq({**legacy,'access_via':[]},legacy))
validrow=entity_evidence(s2,True)['evidence']['data_adequacy']['entities']['product']
detect('noncanonical evidence order',lambda:eq({**validrow,'access_via':list(reversed(validrow['access_via']))},validrow))
empty=entity_evidence(replace(s,edges=()),True)['evidence']['data_adequacy']['entities']['product']
eq(empty,{'required_level':'sku','owned_by':[],'access_via':[]})
print('P0b exclusion/evidence reference probes PASS')
from app.engine.ledger import matching_clear_actions
from app.engine.state import ActionRecord
customer_rule=next(x for x in p.watch_rules if x.key=='cust_data_01')
integration_action=ActionRecord('add_service_tier',1,'customer_insight','customer_database',50000)
integration_state=replace(base,action_history=(integration_action,))
eq(matching_clear_actions(customer_rule,'customer_insight',integration_state,1,1,p),(None,()))
mislabelled=replace(integration_state,action_history=(replace(integration_action,action_type='upgrade_component'),))
detect('integration falsely relabelled for credit',lambda:eq(matching_clear_actions(customer_rule,'customer_insight',mislabelled,1,1,p),(None,())))
print('original clearing vocabulary reference PASS')
PY
```

Author executed2026-09-14: unrelated entity exposure, receiver shortcut, ignored receiver
failure, duplicate owner, capital-only affordability, fabricated fund training, prevention
as repair, and rewritten initial quote were each DETECTED, then all probes PASS. Actual
candidate tests additionally validate the input containers and all excluded-edge/failure
paths, and retain exact legacy24 payload proof.

P0BSR-001/002 closure evidence: the same executable block additionally rejects8 malformed
exclusion cases, observes native exclusion, coerced-null, wrong-home, dangling-grant,
legacy-empty-key and reversed-evidence-order mutants failing, and proves production-empty
access_via[]. Author reran combined block successfully2026-09-14.

Supervisor credit-eligibility clarification (2026-09-15): assessment/debt quote terminology
is limited to verified credit-eligible repairs. The reference above invokes actual
matching_clear_actions and detects a relabelled integration action that would fabricate
credit. No new compact input field or scoring rule is added.
