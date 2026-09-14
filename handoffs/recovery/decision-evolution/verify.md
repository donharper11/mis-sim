# M1 decision-driven simulation — verification and playthrough

Authored under SPEC_PROTOCOL.md v1.3,2026-09-14. Companion to spec.md at the same
commit; Heavy. **Review candidate; no production implementation or M1 completion claimed.**
Author readsets and approved/proposed status are in the master and both engine-input packets.
MSR-001 is addressed by independently reviewed production-inputs/spec.md at2bab351;
MSR-002–004 corrections below remain subject to fresh master review.
All commands run from repository root with declared backend dependencies. Author environment:
`PYTHONPATH=backend /tmp/mis-sim-supervisor-venv-r2cjbjvg/bin/python`. Future builders may
use another explicitly recorded environment. No shared DB or ambient DATABASE_URL is used.

## Pre-flight register and proof obligations

Every packet reports these rows before edits; P0/P0b use their independent registers.
The commands below emit inspected facts, not a ritual exit-code check. A missing source,
field or changed count is a STOP/report against the exact assigned base.

| PF | Command / precise check | Required observation and falsification |
|---|---|---|
| 0 | `git status --porcelain`; `git rev-parse HEAD` | clean/exact supervisor base; deliberately compare against an incorrect SHA and show mismatch |
| 1 | `rg -n 'class Casepack|class CatalogItem|class PlatformService|class TeamState|class ActionRecord|class RoundResult|ALL_TABLES' backend/app/{casepack,engine,round}`; import actual audited predecessor functions from spec§8 | actual existing source names/types; absent predecessor import must fail; P1 inspects both audited P0/P0b field and graph/ledger signatures |
| 2 | Run author probe below, plus own packet's direct original-source parameter assertions |78200/3.7 initial cost/load; actual dependencies, real training/process values,13funds total182000; wrong price/edge/retention rejected |
| 3 | `PYTHONPATH=backend python -m pytest -q backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py`; P0 full24 capture script | existing pins green and full digest e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4; changing non-score event evidence fails full digest |
| 4 | `rg -n 'RoundRunner|build_team_state|ALL_TABLES|EXPECTED_TABLE_COUNT|Base.metadata|_rolled_scorecard|advance\(' backend/app backend/scripts backend/alembic frontend/src` | inspect every production/historical/schema/helper consumer; frontend has no new SimulationService consumer yet. New uninspected consumer stops scope; P5 proves exact migrated schema |
| 5 | `rg -n 'runtime.yaml|simulation|initial_state|unlock|16|38' CONTRACTS.md design/07-decision-consequence-map.md design/08-implementation-north-star.md handoffs/2.3-round-scheduling/spec.md README.md backend/scripts` | identify living-contract/version/count homes, distinguish historical statements; literal deltas applied by supervisor at integration, no blind global replacement |
| 6 | Per-packet selected tests below, source inspections and real defect injection | baseline new behavior absent is not PASS; deliver new actual-interface test with failure/restoration evidence, no self-comparison oracle |

P1 source inventory additionally recursively enumerates131 scalar leaves under original
catalog/platform/training/services preferences defaults/overrides, excluding provenance;
asserts each has exactly one runtime disposition and every live target resolves to a
view. Deleting a disposition or adding a duplicate must fail. It checks original old YAML
SHA256 values against base, allowing only NEW runtime.yaml. Runtime parsing exercises
missing supplement, duplicate YAML key, unknown reference, missing capacity map entry,
zero/nonfinite/bool capacity, config drift, missing numeric provenance/unit, bad response
rationale reference, unknown/nonnull policy override and invalid initial edge. No old loader
may silently return a playable production pack without runtime content.

## Executed author probes

The following script was executed against b7706fb source on2026-09-14. It recomputes
source-backed costs/dependencies and NEW approved formula examples, exercises actual SQLite
transaction behavior, and plants the stated defects. It is a reference/protocol proof,
not a claim that the future SimulationService exists. Candidate tests must invoke actual
implemented interfaces and mutate actual implementation paths; author probes cannot replace
that independent audit. P0's separately executed actual graph/event/hashseed/full-result
probes remain part of the evidence basis.

```bash
PYTHONPATH=backend python - <<'PY'
from decimal import Decimal,ROUND_HALF_UP
from math import floor,ceil
from dataclasses import replace
import sqlite3
from app.casepack.loader import load_casepack
from app.engine.organisation import PROCESS_FIT
p=load_casepack('backend/packs/riverside_grocery')
cat={x.key:x for x in p.catalog};svc={x.key:x for x in p.platform.services}
refs=['pos_system_2011','order_mgmt_v42','accounting_package','store_spreadsheets','order_db_cluster','store_back_office_pc']
services=['client_network','compute_pool','storage_pool','backup_recovery']
def detect(name,fn):
    try: fn()
    except AssertionError: print(name,'defect DETECTED');return
    raise AssertionError(name+' escaped')
def eq(a,b): assert a==b,(a,b)
def initial(integration_opex=1000):
    return sum(cat[k].deployment_modes['on_prem'].opex for k in refs)+sum(svc[k].placement_options['on_prem'].opex for k in services)+31000*p.platform.starting_staff_fte+2*integration_opex
load=sum(cat[k].staff_load for k in refs)+sum(svc[k].staff_load for k in services)+.4
eq(initial(),78200);eq(round(load,6),3.7)
detect('initial actual cost',lambda:eq(initial(0),78200))
def connection(src,dst,entity):
    assert any(x.entity==entity for x in cat[src].owns_entities)
    assert any(x.entity==entity and (x.from_capability is None or x.from_capability in cat[src].serves) for x in cat[dst].must_be_fed_by)
connection('pos_system_2011','order_mgmt_v42','product');connection('order_mgmt_v42','accounting_package','order')
detect('undeclared entity route',lambda:connection('store_spreadsheets','accounting_package','sale'))
def trained(previous,people,coverage,retention=.9):return min(people,max(floor(previous*retention),ceil(people*coverage)))
eq(trained(20,34,.6),21);eq(trained(21,34,0),18)
detect('training without retention',lambda:eq(trained(21,34,0,1),18))
def adoption(previous,trained_count,people,process,staff,resistance,sponsor):
    target=trained_count/people*PROCESS_FIT[process]*sponsor*staff*(1-resistance)
    return round(previous+.35*(target-previous),6)
eq(adoption(0,34,34,'redesigned',1,.2,1),.28)
detect('missing sponsor consequence',lambda:eq(adoption(0,34,34,'redesigned',1,.2,.75),.28))
# Actual horizon schedule from live recurring and a zero-capex one-round hire.
def forecast(hires):
    reserve=0;out=[]
    for r in range(1,7):
        reserve +=100000-initial()-31000*hires*(r>=2);out.append(reserve)
    return out
eq(forecast(0),[21800,43600,65400,87200,109000,130800])
def affordable(hires):assert min(forecast(hires))>=0
affordable(0);detect('unbounded zero-capex hire',lambda:affordable(2))
# Real SQLite transaction shape, deliberately demonstrating catch+commit failure.
def rollback_probe(rollback):
    db=sqlite3.connect(':memory:');db.execute('create table checkpoint(id int primary key)');db.commit()
    try:
        db.execute('begin immediate');db.execute('insert into checkpoint values(1)');raise RuntimeError('after-result')
    except RuntimeError:
        (db.rollback if rollback else db.commit)()
    n=db.execute('select count(*) from checkpoint').fetchone()[0];db.close();return n
eq(rollback_probe(True),0);detect('catch and commit partial write',lambda:eq(rollback_probe(False),0))
funds=[(e.key,next(o.cost for o in e.options if o.key=='fund')) for e in p.events]
eq(len(funds),13);eq(sum(x[1] for x in funds),182000)
detect('response price drift',lambda:eq(sum(x[1] for x in funds)+1,182000))
print('master author content/math/transaction probes PASS; production acceptance still pending')
PY
```

Observed output: initial actual cost, undeclared entity route, training without retention,
missing sponsor consequence, unbounded zero-capex hire, catch-and-commit partial write,
response price drift each printed `defect DETECTED`; then
`master author content/math/transaction probes PASS; production acceptance still pending`.
A positive assertion initially caught an incorrect author total191000; the verified source
sum is182000. The final script above uses that corrected independent table total.

## Successor author evidence for MSR-001–004

All following blocks were executed on2026-09-15 with the declared environment against the
unchanged author source base. The P0b reference/original-consumer probes are frozen in its
separate accepted spec; no duplicate engine algorithm is authorized here. Extract a Python
block below to a temporary file and run `PYTHONPATH=backend python <file>` from repository
root. Each is an executable reference claim, not proof of the unbuilt production service.

### MSR-003: status-only eligibility and bounded repair exclusions

This block calls the actual original ledger, all11 precondition branches and all13 event
gates. Its explicit temporary unassessed-price stub is the prebuild analogue of complete
empty P0b assessment inputs; the builder must test that actual new input instead. The
legacy debt_above branch is tested only to establish quote independence; production v1
rejects that content as specified. Cost comparisons use actual identity prices, and the
separate horizon check prevents interpreting the hypothetical cost comparison as a legal
R6 purchase. It demonstrates no ledger/state mutation and detects status deletion, held-fund
eligibility ignoring a real repair, a held-defer exemption despite a changed policy arm,
capital-only feasibility, postgame arrival, initial-only free purchase and no-op repair. It does not claim exhaustive catalogue search coverage.

```python
"""Actual precondition/ledger reference checks, not the unbuilt repair producer."""
from dataclasses import replace
from app.casepack.loader import load_casepack
from app.casepack.models import EventPrecondition
from app.engine import ledger,events
from app.engine.preconditions import evaluate_precondition
from app.engine.state import ArchNode,TeamState,StaffPool,ActionRecord,PolicyDecisionState
p=load_casepack('backend/packs/riverside_grocery');svc=next(x for x in p.platform.services if x.key=='central_sign_on');rule=next(x for x in p.watch_rules if x.key=='sec_identity_01')
state=TeamState(1,'cost_leadership',(),(),(),(),(),StaffPool(2,3.7),(),(),available_funds_by_round=(100000,),debt_ratio_by_capability={})
rich=ledger.advance_ledger((),state,p)
empty_quotes=tuple(replace(x,was_actionable=False,cheapest_fix_when_raised=None) for x in rich)
pcs=[EventPrecondition(**d) for d in [
 {'type':'signal_open','signal':rule.key,'severity':'critical'},
 {'type':'demand_exceeds_capacity','capability':'order_fulfilment','ratio':1},
 {'type':'adoption_below','capability':'order_fulfilment','ratio':.5},
 {'type':'staffing_over','ratio':1}, {'type':'debt_above','capability':'order_fulfilment','ratio':.5},
 {'type':'node_is_spof','node':'absent'}, {'type':'entity_unowned','entity':'user_account'},
 {'type':'placement_count','placement':'on_prem','count':1},
 {'type':'policy_contradiction','policy':p.policies[0].key,'other_policy':p.policies[1].key},
 {'type':'sponsor_unassigned','capability':'order_fulfilment'}, {'type':'round_equals','round':1}]]
assert len(pcs)==11
assert [evaluate_precondition(pc,state,p,rich) for pc in pcs]==[evaluate_precondition(pc,state,p,empty_quotes) for pc in pcs]
def eligible(s,rows):return tuple(e.key for e in p.events if events._satisfiable(e,s,p,rows))
assert eligible(state,rich)==eligible(state,empty_quotes)
assert 'ransomware_on_finance' in eligible(state,empty_quotes)
# Existing status consumer under an explicit unassessed quote stub is the prebuild analogue
# of P0b complete empty assessments. It MUST NOT call candidate enumeration.
original=ledger.cheapest_effectful_fix;calls=[]
def unassessed(rule,pack):calls.append(rule.key);return None
try:
 ledger.cheapest_effectful_fix=unassessed
 status=ledger.advance_ledger((),state,p)
 assert eligible(state,status)==eligible(state,rich)
 assert all(x.cheapest_fix_when_raised is None and not x.was_actionable for x in status)
 node=ArchNode('r1_identity',tuple(svc.roles_filled),.99,2,6,tuple(c.key for c in p.capabilities),owns_entities=tuple((x.entity,x.level_of_detail) for x in svc.owns_entities),placement='on_prem')
 repaired=replace(state,round=2,nodes=(node,),action_history=(ActionRecord('add_node',1,'firm_infrastructure','central_sign_on',25000),),available_funds_by_round=(100000,100000))
 before=repr(rich);repaired_status=ledger.advance_ledger(rich,repaired,p)
 assert repr(rich)==before and repaired.available_funds_by_round==(100000,100000)
 assert 'ransomware_on_finance' not in eligible(repaired,repaired_status)
 assert any(x.key==rule.key and x.status=='cleared' for x in repaired_status)
 # A held zero-cost defer must also remain eligible: this real policy choice closes its arm.
 held_defer={'event':'unlogged_system_change','option':'defer','rationale_tag':'cost_containment'}
 held_event=next(e for e in p.events if e.key==held_defer['event'])
 held_option=next(o for o in held_event.options if o.key==held_defer['option'])
 assert held_option.cost==0 and held_defer['rationale_tag'] in held_option.tags
 assert events._satisfiable(held_event,state,p,status)
 policy=next(x for x in p.policies if x.key=='access_logging')
 defer_state=replace(state,policy_decisions=(PolicyDecisionState(policy.key,policy.options[-1],True),))
 defer_status=ledger.advance_ledger((),defer_state,p)
 assert not events._satisfiable(held_event,defer_state,p,defer_status)
finally:ledger.cheapest_effectful_fix=original

def detect(name,fn):
 try:fn()
 except AssertionError:print(name,'defect DETECTED');return
 raise AssertionError(name+' escaped')
def equal(a,b):assert a==b,(a,b)
detect('empty ledger loses status',lambda:equal(eligible(state,()),eligible(state,status)))
detect('held fund ignores actual repair',lambda:equal(eligible(repaired,repaired_status),eligible(state,status)))
detect('held defer eligibility exemption',lambda:equal(events._satisfiable(held_event,defer_state,p,defer_status),True))
# The same source identity repair has different genuine capital/operating affordability.
# An R6 hypothetical immediate-effect cost comparison uses the exact source prices;
# the separate real one-round lead rejects ALL newly committed R6 identities.
def affordable(mode):
 cost=svc.placement_options[mode]
 return cost.capex<=100000 and 100000-98000-cost.opex>=0
assert affordable('on_prem') and not affordable('saas')
detect('capital-only repair affordability',lambda:equal(svc.placement_options['saas'].capex<=100000,affordable('saas')))
assert 6+svc.placement_options['on_prem'].lead_time_rounds>p.metadata.rounds
detect('postgame repair witness',lambda:equal(6+svc.placement_options['on_prem'].lead_time_rounds<=p.metadata.rounds,True))
assert next(x for x in p.catalog if x.key=='pos_system_2011').deployment_modes['on_prem'].capex==0
# Runtime initial-only qualification is explicit; source zero price is not purchase authority.
purchasable={'pos_system_2011':set(next(x for x in p.catalog if x.key=='pos_system_2011').deployment_modes)-{'on_prem'}}
detect('free incumbent quote',lambda:equal('on_prem' in purchasable['pos_system_2011'],True))
assert ledger.evaluate(rule,repaired,p) is None
assert ledger.matching_clear_actions(rule,rule.capability,repaired,1,2,p)==(1,('add_node',))
# An already-present identity is a no-op baseline and cannot verify removal of a watch.
detect('already-live no-op repair',lambda:equal(ledger.evaluate(rule,repaired,p) is not None,True))
print('all11 preconditions and13 event gates quote-independent PASS; status/repair negatives PASS')
```

Observed: all seven planted defects printed DETECTED, then all11/all13 independence PASS.
P0b's actual matching_clear_actions probe separately proves an add_service_tier repair of
cust_data_01 cannot receive credit; the master witness catalogue must retain that class as
repaired_but_uncredited. The candidate P4 suite must additionally mutate real preparation to
double-apply a grant/training retention, bypass held-sheet conflicts, recurse into repair
search during status-only checking, or publish disposable ledger rows; every mutant fails.

### MSR-004: explicit views, source joins and collection order

The following constructs initialized, edited draft, locked and completed representative
views from actual source records. It is a serialization/shape reference, not a complete
initial topology, legal six-round state or preview-event proof. It covers every root state
field, exact view/asset/action record keys, actual price/source joins and representative
collection ordering. All remaining nested invariants listed in the master still require
actual P1/P5 tests. A dict with correct-looking fields but an unjoined command is rejected.

```python
"""Reference serialization/view checks; not a production-state transition."""
from copy import deepcopy
from hashlib import sha256
import json
from app.casepack.loader import load_casepack
p=load_casepack('backend/packs/riverside_grocery')
STATE_KEYS=set('strategy strategy_declared_round assets connections projects hiring_orders staff_hires support rollouts unit_resistance governance primary policies capital_balance operating_reserve cost_ledger technical_debt signal_ledger action_history available_funds_by_round event_history response_history tco_forecasts repair_assessment_history unpriced_signal_exposures'.split())
VIEW_KEYS=set('version pack_identity current_round status checkpoint_round checkpoint_digest state sheet'.split())
SHEET_KEYS=set('version round revision locked_revision commands preview'.split())
ASSET_KEYS=set('id source_kind source_key placement config units installed_round retired_round'.split())
ACTION_KEYS=set('id source_round source_command effect_round record'.split())
ACTION_RECORD_KEYS=set('action_type locked_round capability target_key cost'.split())
def exact(obj,keys):assert type(obj)is dict and set(obj)==keys,(set(obj),keys)
def same(a,b):assert a==b,(a,b)
def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def act(source_round,key,target,cap,cost):
    record={'action_type':'add_training','locked_round':source_round,'capability':cap,'target_key':target,'cost':cost}
    return {'id':digest([source_round,key,source_round,'add_training',cap,target]),'source_round':source_round,'source_command':key,'effect_round':source_round,'record':record}
source_commands={(1,'train_order'):{'asset':'initial_order_mgmt_v42','option':'full'},(2,'train_pos'):{'asset':'initial_pos_system_2011','option':'basic'}}
actions=[act(1,'train_order','order_mgmt_v42','order_fulfilment',34000),act(2,'train_pos','pos_system_2011','store_operations',next(x for x in p.catalog if x.key=='pos_system_2011').training_options['basic'].cost)]
def canonical(st):
    st=deepcopy(st)
    st['action_history'].sort(key=lambda a:(a['effect_round'],a['source_round'],a['source_command'],a['record']['action_type'],a['record']['capability'] or '',a['record']['target_key'] or ''))
    st['cost_ledger'].sort(key=lambda x:(x['round'],x['kind'],x['source']))
    st['staff_hires'].sort(key=lambda x:(x['arrival_round'],x['order_id']))
    st['technical_debt'].sort(key=lambda x:(x['opened_round'],x['signal'],x['episode_id']))
    st['tco_forecasts'].sort(key=lambda x:(x['ordered_round'],x['asset_id']))
    return st
cat={x.key:x for x in p.catalog};asset={'id':'initial_order_mgmt_v42','source_kind':'catalog','source_key':'order_mgmt_v42','placement':'on_prem','config':'core','units':1,'installed_round':0,'retired_round':None}
st={k:[] for k in STATE_KEYS}
st.update(strategy='cost_leadership',strategy_declared_round=0,assets={asset['id']:asset},connections={},projects={},hiring_orders={},rollouts={},governance={},primary={},policies={},unit_resistance={},support={'tier':None,'covered_assets':[]},capital_balance=0,operating_reserve=0)
service_by_key={x.key:x for x in p.platform.services}
for source in ['pos_system_2011','accounting_package','store_spreadsheets','order_db_cluster','store_back_office_pc']:
    key='initial_'+source;st['assets'][key]={**asset,'id':key,'source_key':source}
for source in ['client_network','compute_pool','storage_pool','backup_recovery']:
    key='initial_'+source;st['assets'][key]={**asset,'id':key,'source_kind':'service','source_key':source,'config':None}
st['projects']={k:{'id':k,'asset_id':k,'source_kind':a['source_kind'],'source_key':a['source_key'],'placement':a['placement'],'config':a['config'],'units':1,'ordered_round':0,'paid_capex':0,'remaining_lead':0,'status':'arrived','replacement_target':None,'tco_categories':[]} for k,a in st['assets'].items()}
st['rollouts']={k:{'trained_count':int(.6*cat[a['source_key']].people_affected.count),'adoption':.6,'process':'partial' if cat[a['source_key']].process_option else 'unchanged','ever_trained':True,'lifecycle':'active'} for k,a in st['assets'].items() if a['source_kind']=='catalog'}
primary={'order_fulfilment':'initial_order_mgmt_v42','store_operations':'initial_pos_system_2011','financial_reporting':'initial_accounting_package'}
st['primary']={c.key:primary.get(c.key) for c in p.capabilities}
st['governance']={c.key:{'owner':None,'sponsor':None} for c in p.capabilities}
st['policies']={x.key:{'selected':x.default,'actively_decided':False} for x in p.policies}
st['unit_resistance']={x.people_affected.org_unit:.2 for x in p.catalog}
def check_state(s):
    exact(s,STATE_KEYS)
    assert type(s['assets']) is dict
    for key,a in s['assets'].items():
        exact(a,ASSET_KEYS);assert key==a['id']
        source=(cat if a['source_kind']=='catalog' else service_by_key);assert a['source_key'] in source
        item=source[a['source_key']]
        assert a['placement'] in (item.deployment_modes if a['source_kind']=='catalog' else item.placement_options)
        assert a['config'] in item.config_tiers if a['source_kind']=='catalog' else a['config'] is None
        assert key in s['projects'] and s['projects'][key]['asset_id']==key
    assert all(x is None or x in s['assets'] for x in s['primary'].values())
    seen=set()
    for a in s['action_history']:
        exact(a,ACTION_KEYS);exact(a['record'],ACTION_RECORD_KEYS)
        assert (a['source_round'],a['source_command']) in source_commands
        command=source_commands[(a['source_round'],a['source_command'])];target=s['assets'][command['asset']]['source_key']
        assert target==a['record']['target_key'] and a['record']['cost']==cat[target].training_options[command['option']].cost
        assert a['id'] not in seen;seen.add(a['id'])
        assert a['record']['locked_round']==a['source_round']
        assert a['id']==digest([a['source_round'],a['source_command'],a['effect_round'],a['record']['action_type'],a['record']['capability'],a['record']['target_key']])
PREVIEW_KEYS=set('version round normalized_commands arrivals retirements expiries capital_available capital_spend capital_remaining operating_runrate operating_forecast challenges repair_assessments prevented_events would_fire cost_entries warnings'.split())
def preview():
    return {'version':1,'round':1,'normalized_commands':[],'arrivals':[],'retirements':[],'expiries':[],'capital_available':400000,'capital_spend':0,'capital_remaining':400000,'operating_runrate':78200,'operating_forecast':[{'round':1,'opening':0,'allowance':100000,'recurring':78200,'closing':21800}],'challenges':[],'repair_assessments':[],'prevented_events':[],'would_fire':[],'cost_entries':[],'warnings':[]}
def view(status,revision=0):
    completed=status=='completed';state=deepcopy(st)
    if completed:state['available_funds_by_round']=[0]*6
    sheet=None if completed else {'version':1,'round':1,'revision':revision,'locked_revision':revision if status=='locked' else None,'commands':[],'preview':preview()}
    return {'version':1,'pack_identity':{'key':p.metadata.pack_key,'version':p.metadata.pack_version,'digest':'a'*64},'current_round':6 if completed else 1,'status':status,'checkpoint_round':6 if completed else 0,'checkpoint_digest':digest(canonical(state)),'state':state,'sheet':sheet}
def check_view(v):
    exact(v,VIEW_KEYS);check_state(v['state'])
    assert v['checkpoint_digest']==digest(canonical(v['state']))
    if v['status']=='completed':assert v['current_round']==v['checkpoint_round']==6 and v['sheet'] is None
    else:
        exact(v['sheet'],SHEET_KEYS);exact(v['sheet']['preview'],PREVIEW_KEYS);assert v['current_round']==v['sheet']['round']==1
        assert type(v['sheet']['commands'])is list and type(v['sheet']['revision'])is int
        assert v['sheet']['locked_revision']==(v['sheet']['revision'] if v['status']=='locked' else None)
    assert len(v['state']['available_funds_by_round'])==v['checkpoint_round']
def detect(name,fn):
    try:fn()
    except (AssertionError,ValueError,TypeError):print(name,'defect DETECTED');return
    raise AssertionError(name+' escaped')
for name,v in [('initialized',view('draft')),('draft',view('draft',1)),('locked',view('locked',1)),('completed',view('completed'))]:check_view(v);print(name,'view PASS')
ordered=deepcopy(st);ordered['action_history']=actions
ordered['cost_ledger']=[{'round':2,'kind':'training','source':'r2_train_pos','asset':'initial_pos_system_2011','capability':'store_operations','category':'training','capital_delta':-8000,'operating_delta':0},{'round':1,'kind':'training','source':'r1_train_order','asset':'initial_order_mgmt_v42','capability':'order_fulfilment','category':'training','capital_delta':-34000,'operating_delta':0}]
reversed_state=deepcopy(ordered);reversed_state['action_history'].reverse();reversed_state['cost_ledger'].reverse()
check_state(ordered);check_state(reversed_state)
assert digest(canonical(ordered))==digest(canonical(reversed_state))
detect('unsorted action serialization',lambda:same(digest(ordered),digest(reversed_state)))
bad=view('draft');bad['extra']=1;detect('unknown view field',lambda:check_view(bad))
bad=view('draft');del bad['checkpoint_round'];detect('absent required view field',lambda:check_view(bad))
bad=view('draft');bad['sheet']['commands']=None;detect('forbidden null commands',lambda:check_view(bad))
bad=deepcopy(ordered);bad['action_history'].append(deepcopy(actions[0]));detect('ambiguous duplicate action',lambda:check_state(bad))
bad=deepcopy(ordered);bad['action_history'][0]['source_command']='invented';detect('unjoined source command',lambda:check_state(bad))
bad=deepcopy(st);bad['assets'][asset['id']]['source_key']='foreign_catalog';detect('invalid asset reference',lambda:check_state(bad))
bad=view('completed');bad['sheet']=view('locked',1)['sheet'];detect('completed editable sheet',lambda:check_view(bad))
print('MSR004 representative shape/order/view reference PASS')
```

Observed: four view states PASS, eight planted shape/order/reference defects DETECTED, then
MSR004 representative shape/order/view reference PASS. Hiring/communication display labels
belong explicitly to the M3 labels.yaml/UI vocabulary boundary; the M1 headless guide uses
machine keys. This is the label-owner disposition, not a rendered-label claim.

### MSR-002: full source-backed event and budget forecast

This reference forecasts all16 six-round accepted plans, including exact physical IDs,
explicit arrival connections, literal runtime capacities, source prices, training decay,
policy arms, all eligible original event losses and O2 slot release after prevention.
It uses a temporary one-hop path reference only to feed existing metrics/ledger/events;
P0b remains the separately tested authoritative path contract. The script does not run
score_team, simulate adoption/management scores, implement persistence, or certify repair
quotes. Original legacy quotes are used solely for watch status, justified by the preceding
independence probe. The real P6 gate must run the complete production reducers/service.

The 100-hire overspender proposal is deliberately unaffordable and its authored accepted
fallback is empty; the reference verifies the liability failure, while only P5/P6 can prove
actual typed refusal and unchanged database state. No failed choice silently becomes valid.

```python
"""Read-only reference event/cost forecast, not a production runner/scorer implementation."""
from dataclasses import replace
from math import floor,ceil
from app.casepack.loader import load_casepack
from app.engine import graph,ledger,events
from app.engine.state import ArchNode,ArchEdge,DeploymentState,TeamState,StaffPool,ActionRecord,PolicyDecisionState
p=load_casepack('backend/packs/riverside_grocery');cat={x.key:x for x in p.catalog};services={x.key:x for x in p.platform.services};event={x.key:x for x in p.events}
initial_cat=['pos_system_2011','order_mgmt_v42','accounting_package','store_spreadsheets','order_db_cluster','store_back_office_pc']
initial_svc=['client_network','compute_pool','storage_pool','backup_recovery']
original_owner=graph.owner_nodes;original_path=graph.serving_path;original_capacity=graph.bottleneck_capacity
CAPS={};GRANTS=[];CURRENT=None
def bfs(st,sources,targets,excluded=()):
    st=replace(st,nodes=tuple(n for n in st.nodes if n.key not in excluded))
    return graph._bfs_path({k:sorted(v) for k,v in graph._adjacency(st).items()},sorted(sources),set(targets))
def grants(st,cap,entity,level,order):
    out=[]
    for src,dst,ent in GRANTS:
        a=st.node(src);b=st.node(dst)
        if a and b and ent==entity and cap in b.serves and any(x==entity and graph._level_ok(l,level,order) for x,l in a.owns_entities):out.append((src,dst))
    return out
def owners(st,cap,entity,level,order):return sorted(set(original_owner(st,cap,entity,level,order)+[a for a,b in grants(st,cap,entity,level,order)]))
def paths(st,cap,entity,level,order):
    global CURRENT
    CURRENT=cap;sources=[n.key for n in st.nodes_serving(cap) if n.is_client_access];out=[]
    native=bfs(st,sources,original_owner(st,cap,entity,level,order))
    if native:out.append(native)
    for a,b in grants(st,cap,entity,level,order):
        prefix=bfs(st,sources,[b],[a])
        if prefix:out.append(prefix+[a])
    return min(out,key=lambda x:(len(x),tuple(x))) if out else None
def capacity(st,path,*args):
    vals=[CAPS.get(k,{}).get(CURRENT) for k in path];vals=[v for v in vals if v is not None]
    return min(vals) if vals else None
graph.owner_nodes=owners;graph.serving_path=paths;graph.bottleneck_capacity=capacity

def physical(source):return {'centraline_im7':'r1_warehouse','central_sign_on':'r1_identity','customer_database':'r3_customer'}.get(source,'initial_'+source)
def run(archetype,strategy,omit_identity_prevention=False):
    global CAPS,GRANTS
    active={k:('catalog','on_prem',0) for k in initial_cat};active.update({k:('service','on_prem',0) for k in initial_svc})
    network=[(a,'client_network') for a in active if a!='client_network'];integrations=[('pos_system_2011','order_mgmt_v42','product'),('order_mgmt_v42','accounting_package','order')]
    roll={k:[floor(.6*cat[k].people_affected.count),'partial' if cat[k].process_option else 'unchanged'] for k in initial_cat}
    prior=();fired_before=set();capital=operating=0;actions=[];rows=[];fundhistory=[]
    paired=archetype in {'balanced','all_tech_no_org'};org=archetype=='balanced'
    for r in range(1,7):
        capital+=p.metadata.budget.capex_per_round[r-1];capital_spend=0
        if archetype=='overspender' and r==1:
            attempted=[sum(100000-78200-(100*31000 if q>=2 else 0) for q in range(1,t+1)) for t in range(1,7)]
            assert min(attempted)<0  # declared rejected100-hire proposal; explicit empty fallback
            assert not any(k=='it_generalist' for k in active)
        # Exact fixed accepted choices. Pending orders do not appear before arrival.
        if paired and r==1:capital_spend+=services['central_sign_on'].placement_options['on_prem'].capex
        if paired and r==2:
            for key,kind,mode in [('centraline_im7','catalog','saas'),('central_sign_on','service','on_prem')]:
                active[key]=(kind,mode,r)
                if kind=='catalog':roll[key]=[0,'unchanged']
                actions.append(ActionRecord('add_node',1,'firm_infrastructure' if kind=='service' else 'order_fulfilment',key,25000 if kind=='service' else 0))
            network.extend([('centraline_im7','client_network'),('central_sign_on','client_network')]);integrations.append(('pos_system_2011','centraline_im7','product'));capital_spend+=50000
        if paired and r==4:
            active['customer_database']=('catalog','saas',r);roll['customer_database']=[0,'unchanged'];network.append(('customer_database','client_network'));integrations.append(('pos_system_2011','customer_database','sale'));capital_spend+=50000
            actions.append(ActionRecord('add_node',3,'customer_insight','customer_database',0))
        for key in roll:roll[key][0]=floor(roll[key][0]*.9)
        if org:
            training={1:[('order_mgmt_v42','full')],2:[('centraline_im7','full')],4:[('customer_database','full')],5:[('centraline_im7','basic')],6:[('order_mgmt_v42','full'),('customer_database','full')]}.get(r,[])
            process={1:'order_mgmt_v42',2:'centraline_im7',5:'customer_database'}.get(r)
            for key,opt in training:
                o=cat[key].training_options[opt];roll[key][0]=max(roll[key][0],ceil(cat[key].people_affected.count*o.coverage));capital_spend+=o.cost;actions.append(ActionRecord('add_training',r,cat[key].serves[0],key,o.cost))
            if process:roll[process][1]='redesigned';capital_spend+=cat[process].process_option.cost
            capital_spend+={1:4000,2:4000,5:2500}.get(r,0)
        # Unit-correct proposed capacity profiles; prove platform resources are ample here.
        CAPS={};nodes=[];draw_compute=draw_storage=0.;opex=62000+1000*len(integrations)
        drivers={'transactions':[80000,90000,100000,110000,120000,130000][r-1],'orders':p.capabilities[0].demand_curve[r-1],'stores':8,'reporting_periods':1,'sku_count':12000,'customer_records':[10000,12500,15000,18000,22000,26000][r-1]}
        for key,(kind,mode,installed) in active.items():
            item=cat[key] if kind=='catalog' else services[key];price=(item.deployment_modes if kind=='catalog' else item.placement_options)[mode];opex+=price.opex
            serves=tuple(item.serves) if kind=='catalog' else tuple(c.key for c in p.capabilities)
            nodes.append(ArchNode(physical(key),tuple(item.roles_filled),item.availability if kind=='catalog' else .99,installed,item.service_life_rounds if kind=='catalog' else 6,serves,None,tuple((x.entity,x.level_of_detail) for x in item.owns_entities),mode))
            profiles={'order_mgmt_v42':{'order_fulfilment':8000,'store_operations':6000},'pos_system_2011':{'store_operations':6000},'centraline_im7':{'order_fulfilment':7500},'accounting_package':{'financial_reporting':100},'store_spreadsheets':{'store_operations':None,'financial_reporting':None},'order_db_cluster':{'order_fulfilment':7500,'store_operations':5250},'store_back_office_pc':{'store_operations':None},'customer_database':{'customer_insight':1250,'service':375}}
            caps=profiles[key] if kind=='catalog' else {c:None for c in serves}
            CAPS[physical(key)]=caps
            if kind=='catalog' and not price.bypasses_platform:
                size=item.sizing;d=drivers[size.driver];draw_compute+=size.base.compute+size.per_unit.compute*d/size.per_unit.per;draw_storage+=size.base.storage_gb+size.per_unit.storage_gb*d/size.per_unit.per
        assert draw_compute<=12 and draw_storage<=5000
        deployments=tuple(DeploymentState(physical(k),k,cat[k].people_affected.org_unit,cat[k].people_affected.count,t,process,0,t>0,tuple(cat[k].serves)) for k,(t,process) in roll.items())
        edges=tuple([ArchEdge(physical(a),physical(b)) for a,b in network]+[ArchEdge(physical(a),physical(b),'integration') for a,b,e in integrations]);GRANTS=[(physical(a),physical(b),e) for a,b,e in integrations]
        funds=[]
        if paired and r==1:
            funds=['ransomware_on_finance','phishing_on_staff_accounts','unlogged_system_change']
            if omit_identity_prevention:funds.remove('ransomware_on_finance')
        capital_spend+=sum(next(o.cost for o in event[k].options if o.key=='fund') for k in funds)
        capital-=capital_spend;assert capital>=0
        state=TeamState(r,strategy,tuple(nodes),edges,deployments,(),(),StaffPool(2,3.7),(),(),policy_decisions=tuple(PolicyDecisionState(x.key,x.default,org and r in {1,3,6}) for x in p.policies),action_history=tuple(actions),available_funds_by_round=tuple(fundhistory+[capital]))
        # This old ledger quote is used only for actual watch/fire status; no actionability claim.
        newledger=ledger.advance_ledger(prior,state,p)
        for k in funds:assert events._satisfiable(event[k],state,p,newledger) and k not in fired_before,(r,k,'ineligible fund')
        # Full pending/current liability forecast for newly increasing choices, before unknown events.
        if paired and r in {1,2,3,4}:
            future=[];reserve=operating
            for q in range(r,7):
                liab=78200
                if q>=2:liab+=9100+1500
                if r>=2 and q>=2:liab+=1000
                if r>=3 and q>=4:liab+=7300
                if r>=4 and q>=4:liab+=1000
                reserve+=100000-liab;future.append(reserve)
            assert min(future)>=0,(archetype,strategy,r,'unaffordable planned recurring',future)
        deck=p.model_copy(update={'events':[e for e in p.events if e.key not in funds]})
        fired,_=events.resolve_events(state,deck,newledger,already_fired=frozenset(fired_before));loss=sum(event[k].outcomes.revenue_loss or 0 for k in fired)
        signalkeys=frozenset(pc.signal for k in fired for pc in event[k].preconditions if pc.type=='signal_open')
        prior=ledger.advance_ledger(newledger,state,p,fired_signals=signalkeys);fired_before.update(fired);operating+=100000-opex-loss;fundhistory.append(capital)
        rows.append((r,opex,loss,operating,tuple(fired),capital_spend,capital))
    return rows
try:
    result={}
    for archetype in ['balanced','all_tech_no_org','do_nothing','overspender']:
        for strategy in [x.key for x in p.strategies]:
            rows=run(archetype,strategy);result[(archetype,strategy)]=rows
            print(archetype,strategy,'opex',[x[1] for x in rows],'loss',[x[2] for x in rows],'reserve',[x[3] for x in rows],'capital_spend',[x[5] for x in rows],'capital_close',[x[6] for x in rows],'fired',[x[4] for x in rows])
    assert sum(map(len,result.values()))==96
    try:run('balanced','cost_leadership',omit_identity_prevention=True)
    except AssertionError as e:print('removed ransomware prevention defect DETECTED',e)
    else:raise AssertionError('missing prevention escaped')
    print('all96 planned source-backed event/cost rounds PASS; no production/scoring claim')
finally:
    graph.owner_nodes=original_owner;graph.serving_path=original_path;graph.bottleneck_capacity=original_capacity
```

Observed: all96 accepted source event/cost rounds PASS. Removing the R1 ransomware prevention
choice produced an R2 operating forecast `[-80000,-69800,-59600,-49400,-39200]` and the
expected assertion failure. This defect is detected without weakening affordability.
R1 training retention makes the inherited two-person order DB fully untrained, so the two
warehouse events add12000 for cost_leadership/intimacy; R1 identity prevention alone would
release an O2 slot for unlogged_system_change, hence its explicit third response. All raw
fired-event keys, costs and balances print per round for independent inspection.

For both paired plans, recurring costs are `[78200,89800,89800,98100,98100,98100]`.
Balanced capital spend/close are `[146000,110000,0,68000,28500,52000]` /
`[254000,404000,624000,776000,947500,1095500]`; all_tech_no_org spend/close are
`[86000,50000,0,50000,0,0]` / `[314000,524000,744000,914000,1114000,1314000]`.

| Strategy | Paired event losses R1–R6 | Paired operating close R1–R6 |
|---|---|---|
| cost_leadership |12000,0,18000,0,0,0|9800,20000,12200,14100,16000,17900|
| differentiation / focus_strategy |0,0,18000,9000,0,0|21800,32000,24200,17100,19000,20900|
| customer_supplier_intimacy |12000,0,0,9000,0,0|9800,20000,30200,23100,25000,26900|

Do_nothing and overspender's empty fallback both spend zero capital and pay78200 recurring
per round. Final operating close is−59200(cost),−47200(differentiation/focus),−41200(intimacy).
The full six-round vectors print above; unavoidable negative operating cash does not block
empty advances. These are feasibility/evidence checks, not expected score pins or balance
claims. Any production mismatch must be explained and corrected by author/supervisor;
builders cannot change event losses, affordability or these decisions to hide it.

## Actual candidate tests and mutation evidence

Each named file/group is a required builder deliverable, runnable as
`PYTHONPATH=backend python -m pytest -q backend/tests/<file> -k '<group>'`.
The groups may contain several ordinary/parametrized tests; they must assert the observable
state/result/DB facts below, not simply that a helper was called. Each row includes a real
implementation defect to plant on a disposable candidate copy, observe failing, then restore.
Every packet runs its focused file and `make check` once after fixes; further runs need a
new change or unresolved failure. No expectation may be weakened to preserve a false PASS.

| Packet/file and `-k` group | Required positive and negative observations | Plant that must fail |
|---|---|---|
| P1 test_simulation_content.py `strict` | typed12categories; full union rejects arbitrary price/state/action/unknown/null/bool;[]clear vs omitted preserved; key48/asset64 limits; unsupported capital request | allow extra fields or coerce bool/int |
| P1 `content` | exact profiles/initial refs/units/provenance; all4strategies;131leaf dispositions/33views/13responses; immutable semantic digest bound to private copy; formatting change same digest, semantic change different | remove capacity/provenance/disposition; mutate original Casepack after binding |
| P1 `checkpoint` | full nested state validates identity/joins/limits; invalid digest/missing field/nonfinite refuses, output detached | retain nested mutable reference or accept unknown JSON field |
| P2 test_simulation_estate.py `initial` | exactly one initial estate,14200 base recurring/78200 incl wages/integrations,3.7load; source roles/entities preserved; all new IDs unique; no historicalR3seed | distribute47000 target or copy seed-only roles |
| P2 `arrival` | lead0 immediate, lead1 next round, lead2 second round; only then nodes/rollout/opex/effect; six-round bound; due-cancel beforearrival | materialize on commitment or after finalround |
| P2 `lifecycle` | cancellation/kill sunk, terminal neverresume; pause countdown/last-feasible expiry; replacements old live untilarrival/sameidentity; identical config nocharge/noreset; retire edge/support/primary cleanup | refund sunkcapex; resetcurrency on no-op; train cancelled/pendingorder |
| P2 `integration` | exact P0b grants; source ownership/roles/serves unchanged; only named entity accessible, one-hop mandatory receiver path/capacity/reliability, disconnect/exclusion reversal; no undeclared customer→ecommerce route | broad serves union, shortcut bypassing receiver, transitive grant or duplicate physical facets |
| P2 `resources` | unitqty<=8, sourceprice/config rounding, mode bypass, live/pending/retired draw/supply/opex/load once; zero supply gives0 and noNaN | use capacity_pct supply or duplicate multicap draw |
| P3 test_simulation_organisation.py `training_process` |34people basicceil21, next untouchedfloor18; none0noeffect/action; fullcount bounds; partial/full/revert prices and exact PROCESS_FIT | accumulate basic beyondcoverage or charge repeated process |
| P3 `adoption_resistance` | approved examples; no sponsor.75, communication changes only correct unit, arrivals shock; bounded6dp; paused/pending no rollouttraining; strategychangeonce80k | count servicearrival as user shock or leave adoption caller-authored |
| P3 `staff_governance` | +1hirelead1/wage31k, support scopedload cap, staffing_factorzero cases; identifiedinternalowner/executivefinance sponsor; mergedcarry primary asset unique | grant supportcredit on emptycoverage; duplicate primaryrollout |
| P3 `policy_preferences` | all6switches live selection/activity; helddefault explicit counts; absenceinactive; sourcepolicy staffload intensity;10rows33views weights/caring scopes; exact null/nointerest/unsupporteddispositions | persist actively_decided acrossrounds; double-countpolicy in nonpolicy scalar |
| P4 test_simulation_consequences.py `money` | every source charge and allowance reconciles balances; pendinghirerunaway blocked, retirementmayrestoreaffordability, no postgamegrant; empty/reducing worksnegative; quote=advance cost/arrival/events | omit future hire wage or doublecharge recurring |
| P4 `actions_signals` | only effective actions enterhistory with originalcommitmenttime; cancelled/noop/prepaid/noeffectneverclear; positive trainingcost real; same-round responsewindow exclusion; prior terminalepisode unchanged | emit purchaseaction early or fake training forfund6000 |
| P4 `repair_assessments` | bounded catalogue witnesses repair original metric and match original-cleared_by/timewindow; no response/freeincumbent/no-op/postgame quote; fullcapital/operating feasibility; current prior+sheet preparation once; uncredited integration and unassessed/null explicitly reported; initialquote frozen/later affordable opportunity OR only; same-target conflicts and heldfund status-only check | publish price-only opportunity, mutate prior/grant twice, classify uncredited integration as upgrade, recursively invoke quote during status check |
| P4 `responses` | all13price/tag/effect paths; final-all-cost eligibility; prevent expires/noalready_fired/no signalcredit; laterunfundedfires; otherdeckorder/caps same; uneligiblefund atomicerror | markprevented fired or validatebeforefinalcosts |
| P4 `debt_tco` | one positive priced debt/episode or distinct unpriced exposure, frozencrediteligible initialquote, actualclearing/lapse settlement, no cashrefund, ratio0/0; productiondebt_above refuses; TCOselectedtrue/decoy/missing distinction, fixedforecast/realtimeactual, cancellation/retirement, no calleramounts | accrue sameepisode eachround or count paidforecast as expense |
| P4 `scorecard_legacy` | mechanically shared M0 helper, core/MOT unchanged, all24historicalpayloadbytes and pins exact; events affect only agreedscorecard fields/accounting | alter eventpointconversion or pureweights |
| P5 test_simulation_service.py `editing` | init/read detachedstate; initdraftrevision0/digestnull, lock canonicaldigest, completecurrentN/sheetnull; every declared collection order/source-actionjoin; occupiedlegacy/newscope refused; partial[]/empty map semantics; fullvalidation beforedraftwrite; strict revisions/lock/current/legalrounds; no implicit scope | delete existing category before validating replacement |
| P5 `rollback` | capture full all-table scope dump; inject errors after estate preparation, resultinsert, checkpointinsert and beforecommit; EVERY dumpbyte unchanged including revisions/pointers; new connection seesnone | catch thencommit insert; persist estimate duringpreview |
| P5 `retry_reopen` | repeated lock idempotent; currentlockedreopen retainscommands incrementsrevision; old advancedreopen rejects; matchingcurrent/oldadvanceretry returns samebytes no newcost/state/result | recompute retry or clear oldresults onreopen |
| P5 `concurrency` | real distinctconnections: simultaneousmatchingadvances one result/checkpoint, equalreturn; mismatchedrevision loses; edit/lock/reopen/advance serialize; racinginit one success | remove runrow lock or SQLite BEGIN IMMEDIATE |
| P5 `isolation` | same teamID differentinstances and differentteams sameinstance; foreignreference/invalid/rollback/retry cannot change any other scoped dump; packmismatchfails | omit either scopedpredicate from read/write |
| P5 test_postgres_runtime_check.py `schema` | actual Alembic emptyDBupgrade oldbaseline→newrevision; exact19models+versiontable; old16 stillrecognized; missing/extra/wrongconstraint fails | loosen tableequality to subset or omit modelmetadataimport |
| P6 test_simulation_games.py `decision_only` | each of16archetype/strategy games initializes once and advances6typed sheets; no producer seeds/inflightpayload/callerprices; all96reports finite and persist acrossnew serviceobjects | seed perround, calllegacyrunner, or accept fabricatedscore |
| P6 `determinism` | fullcanonical96results/checkpoints match rerun freshscopes withonlyscopeIDs normalized; subprocess PYTHONHASHSEED0/2 representative branchinggame equal | sort byprocesshash or consume wallclock/random |
| P6 `cross_effects` | balanced vs identical-tech/noorg plan changes trained/process/adoption/Orginputs; edited purchase changesonlycausalstate/cost; overspender refusedunchanged then emptysheetadvances | satisfy game via fixed reportfixtures or hardcodedarchetypename |

All original tests/seeds/old YAML hashes stay protected. NEW toy content used to reach
isolated event gates is explicitly test-only, scoped to the narrow condition, and never a
second substantive playable vertical. Production Riverside event-response smoke tests must
include real decision-produced prior states for rollout, policy and capacity challenges;
pure all13option coverage may use validated canonical fixtures from the same reducer.
At least one non-Riverside renamed thin test bundle exercises generic content-driven keys;
no engine/simulation branch may contain a Riverside asset/event/archetype key outside the
fixture/content/game-template files. `rg -n 'riverside|grocer|centraline|warehouse_rollout_gap'
backend/app/engine backend/app/simulation` must yield only documented fixture/template
entries in games.py, never reducers. The game templates select decisions; reducers never
branch on archetype.

## PostgreSQL and schema evidence

P5 receives an explicit supervisor-provisioned disposable PostgreSQL URL and recorded
psycopg2 driver environment. It must invoke Alembic on that URL, inspect actual schema,
run the existing script's exact verifier and new simulation checks, and close/drop only
that disposable database. It may not use shared/external database credentials from local
.env files. SQLite file-backed independent-connection tests supplement PostgreSQL tests;
in-memory SQLite cannot prove its writer-lock behavior. Root has a private old-baseline
capture of17tables including migration and6legacy results; use it only for comparison,
never as authorization to modify that database. Record actual new migration head,
19+1table set, PK/FK/null constraints and query/results, with secrets redacted. Test timeout
or DB failure must produce rollback evidence and no false successful advancement.

## Headless student playthrough and decision templates

The production consumer is `SimulationService`, exercised by NEW games.run_game and the
headless guide. It calls initialize once, then patch/lock/advance; it may read detached state
and preview, but may never write DB tables, seed estates, pass scorer inputs or author costs.
Fixture JSON contains only typed commands and expected refusal codes. The runner records
an unchanged DB digest after a refused candidate, then applies the explicitly authored
fallback; no silent budget-driven substitution of plans.

Four archetypes run under each of cost_leadership, differentiation,
customer_supplier_intimacy and focus_strategy. The balanced and all_tech_no_org plans share
the exact acquisition/integration/primary/response commands; the latter omits training,
process, communication, owner/sponsor assignment, policy and hire commands. It retains
set_primary so it is the same technology comparison. No numeric score ordering is a required balance
claim. The concrete six-round plan is:

| Round | Balanced decisions (source prices only) | EXPECT in student language |
|---|---|---|
|1| buy centraline_im7/saas/core key warehouse tco[integration,training]; buy central_sign_on/on_prem/units1 key identity; fund ransomware_on_finance/compliance, phishing_on_staff_accounts/strategic_priority, unlogged_system_change/compliance; train initial_order_mgmt_v42 full; process it redesigned; assign order_fulfilment owner operations/sponsor senior_management; communicate store_operations change_champions; explicitly retain all6default policies | Warehouse and identity orders are pending; three temporary responses prevent current identity/change losses; training/process benefit the existing order system. Capital spend146000. |
|2| connect initial_pos_system_2011→r1_warehouse integration/product/basic; connect initial_client_network→r1_warehouse network; connect initial_client_network→r1_identity network; primary order_fulfilment=r1_warehouse; train r1_warehouse full; process redesigned; communicate warehouse change_champions | Warehouse and identity arrive once and are explicitly connected; the warehouse receives rollout support. Recurring total89800; capital spend110000. |
|3| buy customer_database/saas/core key customer tco[data_migration,policy,training]; retain policies explicitly | Customer purchase is pending; no early customer rollout or clearing credit. |
|4| connect initial_pos_system_2011→r3_customer integration/sale/basic; network initial_client_network→r3_customer; primary customer_insight=r3_customer; train it full; assign insight owner marketing/sponsor senior_management | Customer system is live and trained; source records and actual cost explain its contribution. |
|5| communicate marketing_sales feedback_loops; process r3_customer redesigned; train r1_warehouse basic | Communication affects its named unit; training restores basic coverage without stacking into full. |
|6| train initial_order_mgmt_v42 full; train r3_customer full; retain all6policydefaults explicitly | Sixth report closes the run; state/history are immutable and fully inspectable. |

The executable typed recipe below freezes every key/field and the accepted/fallback fixture
shape. Its generated JSON contains decisions only; source prices never enter commands.
All lines have distinct48-character-safe command keys and canonical source key spelling. If a unit name above differs from actual catalog org_unit,
PF2 stops and author corrects the template before build (never guess a new unit). Other
categories are omitted, except an initial empty map for a deliberately empty sheet. A
set_primary may move the prior primary for that capability but cannot leave one asset
primary under two capabilities. All primary references follow actual arrivals.

The exact fixture shape is a list of four `{archetype,rounds}` records, with six rows of
`{attempt:SheetPatchV1|null,expected_error:SimulationError.code|null,accepted:SheetPatchV1}`.
Attempt is used only for the explicit overspender refusal; every accepted patch follows
master§2. P6 serializes the following deterministic recipe, never the source forecast state:

```python
"""Frozen typed plan recipe: commands only; no estate, prices or score inputs."""
from app.casepack.loader import load_casepack
p=load_casepack('backend/packs/riverside_grocery')
def cmd(key,op,**fields):return {'key':key,'op':op,**fields}
def policy_lines():return [cmd('policy_'+x.key,'set_policy',policy=x.key,selected=x.default) for x in p.policies]
def network(key,dst):return cmd(key,'connect',src='initial_client_network',dst=dst,kind='network',entity=None,tier=None)
plans=[
 [cmd('warehouse','buy_application',catalog='centraline_im7',placement='saas',config='core',primary_for=None,tco_categories=['integration','training']),
  cmd('identity','buy_service',service='central_sign_on',placement='on_prem',units=1),
  cmd('train_order','train',asset='initial_order_mgmt_v42',option='full'),
  cmd('process_order','set_process',asset='initial_order_mgmt_v42',choice='redesigned'),
  cmd('owner_order','assign',capability='order_fulfilment',owner='operations',sponsor='senior_management'),
  cmd('champions','communicate',org_unit='store_operations',option='change_champions'),
  cmd('prevent_ransom','respond',event='ransomware_on_finance',option='fund',rationale_tag='compliance'),
  cmd('prevent_phishing','respond',event='phishing_on_staff_accounts',option='fund',rationale_tag='strategic_priority'),
  cmd('prevent_change','respond',event='unlogged_system_change',option='fund',rationale_tag='compliance'),*policy_lines()],
 [cmd('warehouse_feed','connect',src='initial_pos_system_2011',dst='r1_warehouse',kind='integration',entity='product',tier='basic'),network('warehouse_network','r1_warehouse'),network('identity_network','r1_identity'),
  cmd('primary_order','set_primary',capability='order_fulfilment',asset='r1_warehouse'),
  cmd('train_warehouse','train',asset='r1_warehouse',option='full'),cmd('process_warehouse','set_process',asset='r1_warehouse',choice='redesigned'),cmd('champions','communicate',org_unit='warehouse',option='change_champions')],
 [cmd('customer','buy_application',catalog='customer_database',placement='saas',config='core',primary_for=None,tco_categories=['data_migration','policy','training']),*policy_lines()],
 [cmd('customer_feed','connect',src='initial_pos_system_2011',dst='r3_customer',kind='integration',entity='sale',tier='basic'),network('customer_network','r3_customer'),
  cmd('primary_customer','set_primary',capability='customer_insight',asset='r3_customer'),cmd('train_customer','train',asset='r3_customer',option='full'),cmd('owner_customer','assign',capability='customer_insight',owner='marketing',sponsor='senior_management')],
 [cmd('feedback','communicate',org_unit='marketing_sales',option='feedback_loops'),cmd('process_customer','set_process',asset='r3_customer',choice='redesigned'),cmd('train_warehouse','train',asset='r1_warehouse',option='basic')],
 [cmd('train_order','train',asset='initial_order_mgmt_v42',option='full'),cmd('train_customer','train',asset='r3_customer',option='full'),*policy_lines()]]
category={'buy_application':'application','buy_service':'platform_service','connect':'integration','train':'training','set_process':'process_redesign','assign':'governance','set_primary':'governance','communicate':'communication','set_policy':'policy','respond':'event_response','hire':'staffing'}
org_ops={'train','set_process','communicate','assign','set_policy','hire'}
def patch(lines):
 groups={}
 for line in lines:groups.setdefault(category[line['op']],[]).append(line)
 return {'version':1,'replace_categories':{k:sorted(v,key=lambda x:x['key']) for k,v in sorted(groups.items())}}
def recipe(archetype):
 rounds=[]
 for r,balanced in enumerate(plans,1):
  accepted=balanced if archetype=='balanced' else [x for x in balanced if x['op'] not in org_ops] if archetype=='all_tech_no_org' else []
  attempt=patch([cmd('hire_'+str(i),'hire',option='it_generalist') for i in range(100)]) if archetype=='overspender' and r==1 else None
  rounds.append({'attempt':attempt,'expected_error':'unaffordable' if attempt else None,'accepted':patch(accepted)})
 return {'archetype':archetype,'rounds':rounds}
fixtures=[recipe(a) for a in ['balanced','all_tech_no_org','do_nothing','overspender']]
assert all(len(f['rounds'])==6 for f in fixtures)
for f in fixtures:
 for row in f['rounds']:
  lines=[x for rows in row['accepted']['replace_categories'].values() for x in rows]
  assert len({x['key'] for x in lines})==len(lines) and all(len(x['key'])<=48 for x in lines)
  for x in lines:
   assert not {'price','cost','score','state'}&set(x)
   if x['op']=='respond':assert x['rationale_tag'] in next(o for e in p.events if e.key==x['event'] for o in e.options if o.key==x['option']).tags
for r in range(6):
 b=[x for rows in fixtures[0]['rounds'][r]['accepted']['replace_categories'].values() for x in rows if x['op'] not in org_ops]
 t=[x for rows in fixtures[1]['rounds'][r]['accepted']['replace_categories'].values() for x in rows]
 assert sorted(b,key=lambda x:x['key'])==sorted(t,key=lambda x:x['key'])
print('four6-round typed recipes and paired technology/response equality PASS')
```

Observed: four6-round typed recipes and paired technology/response equality PASS. The
actual P1 command parser and P5 preview must accept each accepted patch on its carried state;
this prebuild source check does not claim those future APIs already exist.

Do_nothing has empty patches in all6rounds. EXPECT: inherited estate persists, training
fades, demand and operating costs progress, negligence may produce real signals/events;
it is not reseeded into better states. Overspender attempts100 hires with unique keys at
R1 (future liabilities fail), then explicit empty fallback; R2–R6 empty. EXPECT: rejection
changes no draft, money, people or history, while the fallback yields a complete game.
Additionally attempt a purchase arriving afterR6 atR6: typed arrival_after_game_end,
unchanged state; fallback empty still resolves.

Student action sequence for each plan: (1) Start with chosen strategy, EXPECT visible
initial estate/cash. (2) Enter round choices, EXPECT price/arrival/affordability preview.
(3) Replace training category with[], EXPECT other categories preserved; restore the
chosen valid category. (4) Submit an invalid foreign asset, EXPECT unchanged draft/state.
(5) Lock then attempt edit, EXPECT locked; reopen current unadvanced sheet, EXPECT retained
choices/newrevision; relock. (6) Advance, EXPECT exactly one persisted report and carried
estate. (7) Retry, EXPECT exactly the same report/cost. (8) Repeat throughR6, EXPECT complete
history. (9) Attempt reopen/advance stale revision, EXPECT refusal/unchanged history.
These are headless Python interactions; browser/auth/accessibility/screenshots N-A for M1.

## Definition of Done and report format

Builder/auditor report fills one row per item PASS/FAIL/DEVIATION/N-A with exact command,
output/artifact and candidate SHA; no blanket “tested” prose. For rows not yet implemented
write PENDING, never N-A. Final supervisor report retains remaining M2/M3/M4 limitations.

| Item | Required evidence |
|---|---|
| D1/D2 typed input/editing | P1 strict plus P5 editing/rollback; malformed/unauthorized-target-shapedinput changes nothing, no authUI claim |
| D3 initial/carry | P2initial + P6decision_only; exactly one init, six decisions, detached readstate |
| D4 lifecycle | P2arrival/lifecycle, horizon/expiry boundary, no prepaidrollout/refund/noopreset |
| D5 price/resources | P1content/P2resources, onephysicalcharge/load, quote/actual matching |
| D6 org/governance | P3allgroups, source populations and namedstakeholdergroups, no multicapprimary |
| D7 policy/preferences | P3policy_preferences,33views/131dispositions and explicitunsupportedtable |
| D8 accounting/consequences | P4money/actions_signals/repair_assessments/responses/debt_tco; nofakecost/credit/score;13fundprices182000 |
| D9 persistence | P5rollback/retry_reopen/concurrency/isolation and real PostgreSQL migration/schema |
| D10 complete game |16games×6rounds=96results, fourstrategies; deterministicfullpayload/checkpoint reruns |
| Regression | old pins, exacthistorical24payloadhash, M0v1 untouched, makecheck; no seed/testexpectation rewrite |
| Integration/doc ripple | literal CONTRACTS/design/scheduling note, actual19+1schema report, actualruntime.yaml calibrationinventory |
| Scope/quality | readset/PF0–6, realplantfail+restoration, exactallowlist+gitdiffcheck, fresh independentaudit |
| Honest limitations | marketing customer integration/role gap and unsupportedpreference/policyvectors; fullFinancialM4, no pedagogicalbalanceclaim; M2auth/scheduling andM3browser |

Review candidate authority is not implementation authority. A fresh independent master
spec review must PASS before any P1+ builder dispatch. P0 and P0b have separately reviewed
contracts; passing those alone does not fulfill this master.
