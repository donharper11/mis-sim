# M1 P0 — unit-correct engine inputs and deterministic graph paths

Authored under `SPEC_PROTOCOL.md` v1.3. Date: 2026-09-14. Author: `m1_contract_author`.
Base `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`. **Heavy; independent review pending.**
Supervisor approvals M1-R5 in `../authority.md` authorize this bounded seam. P0 is
independently dispatchable after review; it neither completes M1 nor authorizes estate,
organisation, accounting or production-service implementation.

## Basis

[V] Read root GOVERNANCE/QUALITY_PROTOCOL/SPEC_PROTOCOL/CONTRACTS in full; original
1.4 spec/closeout, 1.5 spec/contract, 1.6 spec, design04/07/north-star, decision inventory;
complete `backend/app/engine/{state,graph,catalog,technology,metrics,events,organisation,
management,score,rollup,preconditions,ledger,mathx}.py`, casepack models/loader, round
runner/snapshot/models/actions/db, calibration harness, old seeds, test_engine_scoring,
test_round_pin and Makefile. Extraction covers every changed consumer. No AGENTS found.

[V] `graph.bottleneck_capacity` currently takes min of scalar node.throughput, while
catalog assets serve capabilities with incompatible demand units (order_mgmt: orders and
store_day; ERP: reports and orders). `events.outage_duration` finds authored RTO only when
the physical node key equals the catalog key. `_bfs_path` traverses a neighbor set, so equal
length paths vary with Python hash seed. Existing score formulas are valid and unchanged.

[V] Author reproduced existing diamond path with nodes start/a/b/end and edges
start-a,a-end,start-b,b-end: hash seeds0/1 select a, 2/3 select b. Existing 24-game score
digest is `0e2466975e3ab3eb4ab9deeb931ce85a27032c0423eaa06b98eb113d8c4908d1` under all four.
Full canonical payload digest at this base is
`e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4` (1,656,959 UTF-8 bytes).
Canonicalization: `json.dumps(results,sort_keys=True,separators=(',',':'),allow_nan=False)`.
The full payload check covers evidence/units, not only score_digest's score subset.

## Frozen NEW inputs and semantics

Append two optional fields to frozen ArchNode, preserving positional compatibility:

```python
capacity_by_capability: dict[str, float | None] | None = None
base_rto_hours: float | None = None
```

A missing/None map is the historical scalar path, with precisely existing behavior. A
present map is authoritative. Accept only collections.abc.Mapping containers (not lists of pairs); keys are nonempty
strings (whitespace-only invalid). Python mappings already have unique keys; duplicate
JSON/YAML keys must reject at the future parser boundary before node construction. Values
are finite int/float >=0
(exclude bool) or None. Zero is a real capacity outage; None is no ceiling. An omitted key
in a present map means no ceiling for that transit capability, not the scalar fallback.
Present empty map means no ceilings. A present map together with non-null scalar throughput
raises ValueError: two sources for one ceiling are forbidden. Copy the input map into an
immutable mapping at construction so caller mutation cannot alter a frozen node. The type
annotation may use Mapping; serialized production content remains a JSON object. Reject malformed map containers/keys/values and malformed explicit RTO with ValueError,
including OverflowError from attempted float conversion of an arbitrarily large int; never
coerce strings/bools. No map validation changes the absent-map legacy path. Unknown pack capability keys are the future
runtime projection validator's responsibility: ArchNode has no pack context. No case key
or demand unit is hardcoded.

`base_rto_hours` is explicit finite int/float >0 excluding bool, or None. When present,
`events.outage_duration` uses it. When absent it performs the existing catalog lookup by
failed node key and then the existing8-hour default. Do not add catalog_key or duplicate
RTO lookup state. Production will project this value from validated content; P0 introduces
no caller-facing decision field, DB column, price or RTO calibration change.

Change existing helper with a trailing optional parameter:
`graph.bottleneck_capacity(state,path,capability: str|None=None)`.
With context, use each map's value for that capability if present; otherwise its old scalar.
Return min over finite values, including0; all None=>None. Without context, if any path node
has a present map, raise ValueError; otherwise exact historical behavior. Missing path nodes
retain existing skip behavior. No map value is converted to another demand unit.

`technology.technology` and `metrics.capacity_utilisation` pass their known capability.
`events.bottleneck_node(state,path,capability=None)` adds the same trailing context,
selects the first path node at the computed minimum using the same per-node selection rule,
and `events.failed_node` passes its primary capability. One private shared selection helper
in graph may prevent inconsistent duplicate selection logic; no second scorer is permitted.
Technology capacity remains min/demand/clamp; metric capacity remains demand/min; the existing
zero/no-path rules stay unchanged. Node IDs, serves/ownership, placement counts, event caps,
suppression, blast radius, score weights and MOT equations are untouched.

`_bfs_path` sorts and de-duplicates source keys and sorts each adjacency neighbor set.
Shortest-path ties then choose lexicographic node-key order. Preserve target-set membership
and path length behavior. This applies globally only if the full 24 legacy results and pins
are byte-identical. If sorting changes any historical payload, STOP with the differing
field; do not update a pin or restrict a test to scores merely to pass.

Null/negative cases: None/empty map; missing capability key; zero capacity; int capacities;
bool/string/negative/NaN/infinite values; simultaneous scalar+map; missing context; unknown
physical node (existing behavior); absent/invalid/explicit RTO; multiple equal bottlenecks;
empty source/target and disconnected graphs. Each has a named test below.

One compliant route: append defaulted immutable data fields, share per-node capacity
selection, thread the known capability through the three existing consumers, prefer explicit
RTO only when supplied, and sort BFS traversal. Legacy snapshots supply neither field and
retain their complete output. Pure engine remains I/O-free; no state or scoring input is
produced from a clock, random choice, DB, LLM or casepack identity branch.

## Bounded builder packet

Exact base assigned by supervisor after this spec is reviewed. Allowed code files only:
`backend/app/engine/state.py`, `graph.py`, `technology.py`, `metrics.py`, `events.py`;
NEW `backend/tests/test_engine_runtime_inputs.py`;
NEW `handoffs/recovery/decision-evolution/engine-inputs/dod.md`.
Shared CONTRACTS/design/register edits belong to supervisor at audited integration.
No other engine file, old test/seed, pack value, runner/helper, dependency, migration or UI
edit is authorized. M0 helper extraction stays the later accounting packet.

Required readset: basis above plus this spec and actual complete files in the allowlist.
Before code, report every preflight row:

| PF | Executable check | Expected |
|---|---|---|
| 0 | `git status --porcelain`; `git rev-parse HEAD` | clean and exact assigned base |
| 1 | `rg -n 'def bottleneck_capacity|def bottleneck_node|bottleneck_capacity\(|base_rto_hours|for nxt in adj' backend/app/engine` | only inspected graph/technology/metrics/events capacity callers; scalar and old RTO/BFS seam present |
| 2 | `PYTHONPATH=backend python -m pytest -q backend/tests/test_engine_scoring.py backend/tests/test_round_pin.py` | all pins pass |
| 3 | Run legacy script below and keep JSON outside repo | exact full digest above; 24 results |
| 4 | `rg -n 'bottleneck_capacity|bottleneck_node|ArchNode\(' backend/app backend/seeds backend/tests frontend/src` | inspect every hit; existing omitted-context callers all legacy scalar; no frontend consumer |
| 5 | `make check` | existing suite/guards/44 fixtures pass; no ambient missing dependency |

PF failure stops the dependent edit. New caller or changed base needs supervisor rebase/ruling,
not an expanded builder scope. Preflight facts are falsifiable: missing entry point makes
PF1's explicit inspection fail, wrong pin PF2 fails, changed payload PF3 fails; grep count or
successful command exit alone is not evidence.

Build sequence: fields/helper → three consumers/RTO → BFS sorting → focused tests → legacy
payload equality/full checks → report. The first unit fixture has one physical node serving
orders/reports with capacities8000/100 and demands6000/80; expected capacity1 for both.
A second in-series node with2000/200 yields helper capacity2000 for orders and100
for reports, and rounded technology capacity factors0.333333 and1 respectively. Keeping
one scalar100 instead must fail the orders assertion. Mapped nodes with omitted/None capability context must raise rather than guess;
an explicitly supplied unknown capability means no ceiling under the missing-key rule. Explicit node RTO12 with unique node ID produces base12; absent RTO preserves
old lookup/default. Same asset still counts once under placement_count.

## Acceptance and falsification

NEW test file exposes exactly these independently runnable groups (ordinary pytest tests,
parametrization allowed):

| Tests selected with `-k` | Required observable result | Deliberate regression that must fail |
|---|---|---|
| `capacity` | per-unit examples; None/empty/missing/zero; all invalids; scalar compatibility; missing context refuses | read scalar for mapped node or omit capability from one consumer |
| `rto` | unique-ID explicit12; catalog-key old lookup; absent default8; invalids reject | ignore explicit RTO |
| `immutable` | mutate original dict after node construction; snapshot capacity unchanged | retain caller's dict reference |
| `physical` | one mapped node counts one placement and fails as one identity | duplicate node for second capability |
| `hashseed` | subprocess seeds0,1,2,3,42,99 all print start,a,end on diamond; fixed bottleneck evidence | revert sorted neighbor traversal; original base is already a failing specimen |
| `legacy` | full results equal captured base and digest above; original pins green | change one stored event point/status/evidence value before comparison |

Planted-defect proof is performed on a disposable copy, then restored; record failing
command/output and passing restored result. It is not enough to assert that a test would
fail or to change expected values. Numeric checks reach `make check` through pytest.
The independent auditor reruns the focused tests and one defect per group, full payload
comparison and `make check` on the exact candidate; no self-audit substitutes.

Legacy capture from repository root (declared environment, disposable SQLite only):

```bash
PYTHONPATH=backend python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,json
from app.casepack.loader import load_casepack
from app.calibrate.harness import run_calibration
with TemporaryDirectory(prefix='m1-p0-legacy-') as d:
    _, results=run_calibration(load_casepack('backend/packs/riverside_grocery'),db_url=f'sqlite:///{d}/game.db')
    assert sum(map(len,results.values())) == 24
    blob=json.dumps(results,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert hashlib.sha256(blob).hexdigest() == 'e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4'
    capture=Path(d).parent / ('m1-p0-legacy-' + Path(d).name + '.json')
    capture.write_bytes(blob)
    print(capture,len(blob),hashlib.sha256(blob).hexdigest())
PY
```


## Author prebuild evidence (computed probes, not production implementation)

The executable below invokes inspected graph/event/precondition consumers on independently
constructed unit-specific scalar fixtures, then plants real wrong-unit/min-to-sum/RTO/
physical-identity/alias/traversal/payload defects. Each is observed failing its assertion.
The proposed BFS ordering is evaluated only in memory/subprocesses; no repository source
is changed. The map-copy probe proves the construction mechanism, not a yet-unbuilt
ArchNode field. Candidate tests must still invoke the NEW fields/context and plant code
regressions; this prebuild evidence never claims those interfaces already exist.

```bash
PYTHONPATH=backend python - <<'PY'
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace, MappingProxyType
import hashlib,json,os,subprocess,sys
from app.casepack.loader import load_casepack
from app.calibrate.harness import run_calibration
from app.engine import graph,events,preconditions
from app.engine.state import ArchNode,TeamState,StaffPool

def detected(label,check):
    try: check()
    except AssertionError: print(label,'planted defect DETECTED'); return
    raise AssertionError(label+' escaped')
def equal(a,b): assert a==b,(a,b)
p=load_casepack('backend/packs/riverside_grocery')
def state(nodes): return TeamState(1,'cost_leadership',tuple(nodes),(),(),(),(),StaffPool(2,0),(),())
# Independent unit-specific scalar projections exercise existing min and event consumers.
profiles=[{'orders':8000,'reports':100},{'orders':2000,'reports':200}]
def capacities(project=lambda x,c:x[c]):
    out=[]
    for cap,demand in [('orders',6000),('reports',80)]:
        nodes=[ArchNode(str(i),(),.99,0,6,throughput=project(x,cap)) for i,x in enumerate(profiles)]
        minimum=graph.bottleneck_capacity(state(nodes),['0','1'])
        out.append((minimum,round(min(1,minimum/demand),6)))
    return out
expected=[(2000,.333333),(100,1)]
equal(capacities(),expected)
detected('wrong unit',lambda:equal(capacities(lambda x,c:x['reports']),expected))
original=graph.bottleneck_capacity
graph.bottleneck_capacity=lambda s,path:sum(s.node(k).throughput for k in path)
detected('min changed to sum',lambda:equal(capacities(),expected))
graph.bottleneck_capacity=original
# Existing event consumer receives explicit authored12 via its legacy catalog source.
item=p.catalog[0].model_copy(update={'base_rto_hours':12.0})
p12=p.model_copy(update={'catalog':[item,*p.catalog[1:]]})
n=ArchNode(item.key,(),.99,0,6,placement='on_prem')
equal(events.outage_duration(state([n]),n.key,'store_operations',p12)['duration_hours'],36.0)
p8=p12.model_copy(update={'catalog':[item.model_copy(update={'base_rto_hours':8.0}),*p.catalog[1:]]})
detected('wrong RTO',lambda:equal(events.outage_duration(state([n]),n.key,'store_operations',p8)['duration_hours'],36.0))
pc=SimpleNamespace(type='placement_count',placement='on_prem',count=2)
equal(preconditions.evaluate_precondition(pc,state([n]),p,()),False)
detected('duplicated physical node',lambda:equal(preconditions.evaluate_precondition(pc,state([n,replace(n,key='facet')]),p,()),False))
def copy_probe(copy):
    original={'orders':8000}; frozen=copy(original); original['orders']=1
    return frozen['orders']
equal(copy_probe(lambda x:MappingProxyType(dict(x))),8000)
detected('retained map alias',lambda:equal(copy_probe(lambda x:x),8000))
# Execute inspected BFS in new subprocesses; apply ONLY the proposed ordering in memory.
source=Path('backend/app/engine/graph.py').read_text()
sorted_source=source.replace('for s in sources:', 'for s in sorted(set(sources)):').replace('for nxt in adj[cur]:','for nxt in sorted(adj[cur]):')
def paths(src):
    code=src+"\nprint(_bfs_path({'start':{'a','b'},'a':{'start','end'},'b':{'start','end'},'end':{'a','b'}},['start'],{'end'}))"
    return [subprocess.check_output([sys.executable,'-c',code],env={**os.environ,'PYTHONHASHSEED':str(seed)},text=True).strip() for seed in [0,1,2,3,42,99]]
wanted=["['start', 'a', 'end']"]*6
equal(paths(sorted_source),wanted)
detected('unordered BFS',lambda:equal(paths(source),wanted))
with TemporaryDirectory(prefix='m1-p0-author-proof-') as d:
    _,result=run_calibration(p,db_url=f'sqlite:///{d}/legacy.db')
    digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    expected_hash='e4260be4986ac085483f84434b6abe8352f83d347083299b2794084f38f4dcd4'
    equal(digest(result),expected_hash)
    changed=json.loads(json.dumps(result));first=next(iter(changed.values()))
    # Full-report change outside the score digest is still detected.
    first[0]['suppressed_events'].append({'key':'injected','reason':'cap','capability':None})
    detected('changed legacy evidence',lambda:equal(digest(changed),expected_hash))
print('all computed prebuild probes PASS')
PY
```

Author output on2026-09-14: wrong unit, min changed to sum, wrong RTO, duplicated physical
node, retained map alias, unordered BFS and changed legacy evidence each printed
`planted defect DETECTED`, followed by `all computed prebuild probes PASS`. Original
source/state is restored between probes; subprocess source has no filesystem mutation.

Definition of done in builder dod.md: PF0–5; each test group above; failing/restored mutation
evidence; legacy24 full digest and old pins; `make check`; `git diff --check`; allowed-file
check; independent audit pending/complete with exact candidate. Ladder1/2 and pure runtime
apply; migrations, DB isolation, browser/auth/UX/screenshots N-A because P0 adds no DB or
UI. No claim that production capacity, RTO or M1 simulation is implemented by this seam alone.

Supervisor living-contract delta on audited integration (literal text; supervisor owns the
shared files):

Append to CONTRACTS.md engine input contracts:

> **M1 engine inputs v1.** ArchNode may carry an immutable
> `capacity_by_capability` mapping and positive finite `base_rto_hours`. An absent capacity
> map preserves historical scalar throughput. A present map forbids scalar throughput;
> finite nonnegative entries are unit-specific ceilings, zero is an outage, and None or an
> omitted key means no ceiling for that capability. Graph, technology, metrics and event
> bottleneck consumers must pass capability context for mapped nodes. The runtime projection
> is the sole production producer and validates pack capability keys. Explicit RTO wins;
> absence retains historical catalog-key lookup and8-hour fallback. One physical node keeps
> one placement/failure identity. This adds no scorecard-v1 field or scoring formula.

Append this new final subsection to design/07-decision-consequence-map.md:

> ### M1 deterministic engine input contract

> **M1 deterministic paths.** Serving-path BFS visits unique source keys and adjacency
> neighbors in lexicographic node-key order. Equal-length paths therefore have a stable
> cross-process tie-break. Adoption of this tie-break requires byte-identical canonical
> historical24 RoundResult payloads and unchanged R3 pins. New mapped capacities are compared
> only within the requested capability; incidental transit with no map entry has no ceiling.
