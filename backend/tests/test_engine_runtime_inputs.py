"""M1 P0 additive runtime inputs, physical identity, and full historical compatibility."""

from collections import UserDict
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType

import pytest

from app.casepack.loader import load_casepack
from app.casepack.models import Capability, Entity, EventPrecondition, WatchRule
from app.engine import events, graph, metrics, preconditions, technology
from app.engine.state import ArchEdge, ArchNode, StaffPool, TeamState


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "backend/packs/riverside_grocery"
LEGACY_SHA256 = "1b45eb1e1bcdd8ae84d764e271648dd1fe68ab6179b41f50fbe259da1b1afa3a"
HASH_SEEDS = (0, 1, 2, 3, 42, 99)
PROVENANCE = {"source": "AUTHORED", "note": "Independent P0 unit fixture"}


def _node(key="asset", **kwargs):
    fields = dict(
        key=key, roles_filled=("client_access", "transaction_store"), availability=1.0,
        installed_round=0, service_life_rounds=6, serves=("orders", "reports"),
        owns_entities=(("record", "detail"),), placement="on_prem",
    )
    fields.update(kwargs)
    return ArchNode(**fields)


def _state(*nodes, edges=()):
    return TeamState(1, "cost_leadership", tuple(nodes), tuple(edges), (), (), (),
                     StaffPool(2, 2), (), ())


@pytest.fixture(scope="module")
def pack():
    return load_casepack(PACK)


@pytest.fixture
def unit_pack(pack):
    caps = [
        Capability(
            key=key, chain_position="test", required_roles=["client_access", "transaction_store"],
            required_entities=[{"entity": "record", "min_level_of_detail": "detail"}],
            demand_curve=[demand] * 6, demand_unit=unit, provenance=PROVENANCE,
        )
        for key, demand, unit in (("orders", 6000, "order"), ("reports", 80, "report"))
    ]
    rules = [_rule(c.key) for c in caps]
    return pack.model_copy(update={
        "capabilities": caps,
        "entities": [Entity(key="record", levels_of_detail=["detail"], sensitivity="low",
                            provenance=PROVENANCE)],
        "watch_rules": rules,
    })


def _rule(capability):
    return WatchRule(key=f"watch_{capability}", capability=capability,
                     metric="capacity_utilisation", warn_above=0.8, critical_above=0.95,
                     cleared_by=[], provenance=PROVENANCE)


def _event(pack, *capabilities):
    return pack.events[0].model_copy(update={"preconditions": [
        EventPrecondition(type="signal_open", signal=f"watch_{cap}", severity="warning")
        for cap in capabilities
    ]})


def _series():
    return _state(
        _node("start", capacity_by_capability={"orders": 8000, "reports": 100}, owns_entities=()),
        _node("end", capacity_by_capability={"orders": 2000, "reports": 200},
              roles_filled=("transaction_store",)),
        edges=(ArchEdge("start", "end"),),
    )


@pytest.mark.parametrize("cap,demand,ceiling,utilisation", [
    ("orders", 6000, 8000, 0.75), ("reports", 80, 100, 0.8),
])
def test_capacity_single_physical_asset_has_independent_units(unit_pack, cap, demand, ceiling, utilisation):
    state = _state(_node(capacity_by_capability={"orders": 8000, "reports": 100}))
    assert graph.bottleneck_capacity(state, ["asset"], cap) == ceiling
    result = technology.technology(unit_pack, state, cap)
    assert result.sub_factors["capacity"] == 1.0
    assert result.evidence["capacity"] == {"bottleneck": ceiling, "demand": demand}
    assert metrics.capacity_utilisation(state, unit_pack, _rule(cap)) == utilisation
    assert events.failed_node(_event(unit_pack, cap), state, unit_pack) == "asset"


@pytest.mark.parametrize("cap,demand,ceiling,factor,utilisation,failed", [
    ("orders", 6000, 2000, 0.333333, 3.0, "end"),
    ("reports", 80, 100, 1.0, 0.8, "start"),
])
def test_capacity_series_all_consumers_use_primary_capability(unit_pack, cap, demand, ceiling,
                                                            factor, utilisation, failed):
    state = _series()
    assert graph.bottleneck_capacity(state, ["start", "end"], cap) == ceiling
    result = technology.technology(unit_pack, state, cap)
    assert result.sub_factors["capacity"] == factor
    assert result.evidence["capacity"] == {"bottleneck": ceiling, "demand": demand}
    assert metrics.capacity_utilisation(state, unit_pack, _rule(cap)) == utilisation
    other = "reports" if cap == "orders" else "orders"
    assert events.bottleneck_node(state, ["start", "end"], cap) == failed
    assert events.failed_node(_event(unit_pack, cap, other), state, unit_pack) == failed
    pc = EventPrecondition(type="demand_exceeds_capacity", capability=cap, ratio=utilisation)
    assert preconditions.evaluate_precondition(pc, state, unit_pack) is False
    assert preconditions.evaluate_precondition(pc.model_copy(update={"ratio": utilisation - 0.01}),
                                              state, unit_pack) is True


@pytest.mark.parametrize("capacity_map,expected,factor", [
    (None, None, 1.0), ({}, None, 1.0), ({"reports": 100}, None, 1.0),
    ({"orders": None}, None, 1.0), ({"orders": 0}, 0, 0.0),
])
def test_capacity_null_missing_empty_and_zero_consumers(unit_pack, capacity_map, expected, factor):
    state = _state(_node(capacity_by_capability=capacity_map))
    assert graph.bottleneck_capacity(state, ["unknown", "asset"], "orders") == expected
    result = technology.technology(unit_pack, state, "orders")
    assert result.sub_factors["capacity"] == factor
    assert result.evidence["capacity"] == {"bottleneck": expected, "demand": 6000}
    assert metrics.capacity_utilisation(state, unit_pack, _rule("orders")) == 0.0
    failed = "asset" if expected == 0 else None
    assert events.bottleneck_node(state, ["unknown", "asset"], "orders") == failed
    assert events.failed_node(_event(unit_pack, "orders"), state, unit_pack) == failed


def test_capacity_mixed_transit_scalar_and_mapped_nodes():
    state = _state(_node("transit", capacity_by_capability={"reports": 1}, serves=()),
                   _node("scalar", throughput=3000),
                   _node("mapped", capacity_by_capability={"orders": 5000}))
    assert graph.bottleneck_capacity(state, ["transit", "scalar", "mapped"], "orders") == 3000
    assert events.bottleneck_node(state, ["transit", "scalar", "mapped"], "orders") == "scalar"
    assert graph.bottleneck_capacity(state, ["transit", "mapped"], "unknown_capability") is None
    assert events.bottleneck_node(state, ["transit", "mapped"], "unknown_capability") is None


@pytest.mark.parametrize("capacities", [{}, {"orders": None}, {"orders": 0}, {"orders": 8000}])
@pytest.mark.parametrize("fn", [graph.bottleneck_capacity, events.bottleneck_node])
def test_capacity_missing_context_refuses_every_present_map(capacities, fn):
    state = _state(_node("scalar", throughput=0), _node(capacity_by_capability=capacities))
    for kwargs in ({}, {"capability": None}):
        with pytest.raises(ValueError, match="capability"):
            fn(state, ["scalar", "asset"], **kwargs)
    # A mapped node elsewhere in the estate does not invalidate an unrelated scalar path.
    assert fn(state, ["scalar"]) == (0 if fn is graph.bottleneck_capacity else "scalar")


@pytest.mark.parametrize("scalar", [None, 0, 100, -1, float("inf"), True, "unchanged"])
def test_capacity_legacy_scalar_is_not_newly_validated(scalar):
    node = _node(throughput=scalar)
    assert node.capacity_by_capability is None
    assert node.throughput == scalar
    state = _state(node)
    assert graph.bottleneck_capacity(state, ["asset"]) == scalar
    assert graph.bottleneck_capacity(state, ["asset"], "orders") == scalar
    assert events.bottleneck_node(state, ["asset"]) == (None if scalar is None else "asset")


@pytest.mark.parametrize("container", [[], [("orders", 1)], (), "orders", 1, False])
def test_capacity_invalid_map_container_refuses(container):
    with pytest.raises(ValueError):
        _node(capacity_by_capability=container)


@pytest.mark.parametrize("key", ["", " ", "\t\n", 1, None, False, ("orders",)])
def test_capacity_invalid_map_key_refuses(key):
    with pytest.raises(ValueError):
        _node(capacity_by_capability={key: 1})


INVALID_NUMBERS = [
    pytest.param(True, id="true"), pytest.param(False, id="false"),
    pytest.param("12", id="string"), pytest.param(-1, id="negative"),
    pytest.param(float("nan"), id="nan"), pytest.param(float("inf"), id="infinity"),
    pytest.param(float("-inf"), id="negative_infinity"),
    pytest.param(10 ** 10000, id="overflow"), pytest.param([], id="list"),
    pytest.param({}, id="dict"), pytest.param(1 + 2j, id="complex"),
]


@pytest.mark.parametrize("value", INVALID_NUMBERS)
def test_capacity_invalid_numeric_refuses(value):
    with pytest.raises(ValueError):
        _node(capacity_by_capability={"orders": value})


@pytest.mark.parametrize("capacity_map", [{}, {"orders": None}, {"orders": 100}])
@pytest.mark.parametrize("scalar", [0, 100, False])
def test_capacity_map_and_scalar_refuse_two_sources(capacity_map, scalar):
    with pytest.raises(ValueError):
        _node(capacity_by_capability=capacity_map, throughput=scalar)


@pytest.mark.parametrize("factory", [dict, UserDict, MappingProxyType])
def test_capacity_accepts_mapping_and_preserves_keys(factory):
    node = _node(capacity_by_capability=factory({"orders": 1, "new capability": 2, " spaced ": None}))
    assert dict(node.capacity_by_capability) == {"orders": 1, "new capability": 2, " spaced ": None}


def test_capacity_ties_empty_and_unknown_path_nodes():
    state = _state(_node("b", capacity_by_capability={"orders": 0}),
                   _node("a", capacity_by_capability={"orders": 0}))
    assert events.bottleneck_node(state, ["unknown", "b", "a"], "orders") == "b"
    assert events.bottleneck_node(state, ["a", "b"], "orders") == "a"
    for path in ([], ["unknown"]):
        assert graph.bottleneck_capacity(state, path) is None
        assert events.bottleneck_node(state, path) is None


def test_capacity_disconnected_and_zero_demand_paths(unit_pack):
    state = _series()
    disconnected = replace(state, edges=())
    assert technology.technology(unit_pack, disconnected, "orders").sub_factors["capacity"] == 0
    assert metrics.capacity_utilisation(disconnected, unit_pack, _rule("orders")) == 0
    assert events.failed_node(_event(unit_pack, "orders"), disconnected, unit_pack) is None
    zero_demand = unit_pack.model_copy(update={"capabilities": [
        c.model_copy(update={"demand_curve": [0] * 6}) for c in unit_pack.capabilities
    ]})
    assert metrics.capacity_utilisation(state, zero_demand, _rule("orders")) == 0


@pytest.mark.parametrize("value", INVALID_NUMBERS + [pytest.param(0, id="zero")])
def test_rto_invalid_numeric_refuses(value):
    with pytest.raises(ValueError):
        _node(base_rto_hours=value)


@pytest.mark.parametrize("explicit", [12, 12.0, 0.25])
def test_rto_unique_physical_key_explicit_input(unit_pack, explicit):
    state = _state(_node("unique_physical_id", base_rto_hours=explicit))
    evidence = events.outage_duration(state, "unique_physical_id", "orders", unit_pack)
    assert evidence == {
        "node": "unique_physical_id", "base_rto_hours": explicit, "failover_exists": False,
        "failover_factor": 3.0, "staffing_modifier": 1.0,
        "duration_hours": round(explicit * 3.0, 1), "blast_radius": ["orders"],
    }


def test_rto_explicit_wins_catalog_and_absence_preserves_old_lookup(pack):
    item = next(i for i in pack.catalog if i.key == "next_gen_firewall")
    assert item.base_rto_hours == 4.0
    for explicit, expected in ((12.0, 12.0), (None, 4.0)):
        state = _state(_node(item.key, base_rto_hours=explicit))
        result = events.outage_duration(state, item.key, "store_operations", pack)
        assert result["base_rto_hours"] == expected
        assert result["duration_hours"] == expected * 3.0
    # Lookup did not historically require a physical node to be present.
    assert events.outage_duration(_state(), item.key, "store_operations", pack)["base_rto_hours"] == 4.0


def test_rto_absent_default_and_catalog_without_authored_value(unit_pack):
    item = unit_pack.catalog[0].model_copy(update={"base_rto_hours": None})
    pack = unit_pack.model_copy(update={"catalog": [item]})
    for key in ("unique_physical_id", item.key):
        result = events.outage_duration(_state(_node(key)), key, "orders", pack)
        assert result["base_rto_hours"] == 8.0
        assert result["duration_hours"] == 24.0


@pytest.mark.parametrize("staff,modifier", [(StaffPool(2, 4), 2.0), (StaffPool(0, 4), 4.0)])
def test_rto_explicit_retains_staffing_and_failover_formula(unit_pack, staff, modifier):
    state = _series()
    state = replace(state, nodes=state.nodes + (_node("failed", base_rto_hours=12),),
                    edges=(ArchEdge("start", "end", "failover"),), staff=staff)
    result = events.outage_duration(state, "failed", "orders", unit_pack)
    assert result["base_rto_hours"] == 12
    assert result["failover_exists"] is True
    assert result["failover_factor"] == 1.0
    assert result["staffing_modifier"] == modifier
    assert result["duration_hours"] == 12 * modifier
    assert result["blast_radius"] == []


@pytest.mark.parametrize("factory", [dict, UserDict])
def test_immutable_copies_caller_mapping_and_frozen_fields(factory, unit_pack):
    original = factory({"orders": 8000, "reports": 100})
    node = _node(capacity_by_capability=original, base_rto_hours=12)
    state = _state(node)
    before = technology.technology(unit_pack, state, "orders")
    original["orders"] = 0
    original["new"] = 1
    assert dict(node.capacity_by_capability) == {"orders": 8000, "reports": 100}
    assert technology.technology(unit_pack, state, "orders") == before
    with pytest.raises(TypeError):
        node.capacity_by_capability["orders"] = 0
    with pytest.raises(FrozenInstanceError):
        node.capacity_by_capability = {}
    with pytest.raises(FrozenInstanceError):
        node.base_rto_hours = 8
    copied_node = replace(node, key="another")
    assert copied_node.capacity_by_capability == node.capacity_by_capability
    assert copied_node.capacity_by_capability is not node.capacity_by_capability


def test_physical_asset_counts_once_and_failure_removes_both_capabilities(unit_pack):
    node = _node("physical", capacity_by_capability={"orders": 8000, "reports": 100}, base_rto_hours=12)
    state = _state(node)
    assert len(state.nodes) == 1
    pc = EventPrecondition(type="placement_count", placement="on_prem", count=1)
    assert preconditions.evaluate_precondition(pc, state, unit_pack) is True
    assert preconditions.evaluate_precondition(pc.model_copy(update={"count": 2}), state, unit_pack) is False
    primary = {cap: ("record", "detail", ["detail"]) for cap in ("orders", "reports")}
    assert graph.blast_radius(state, "physical", ["orders", "reports"], primary) == ["orders", "reports"]
    for cap in ("orders", "reports"):
        assert events.failed_node(_event(unit_pack, cap), state, unit_pack) == "physical"
        assert events.outage_duration(state, "physical", cap, unit_pack)["node"] == "physical"
    assert state.nodes == (node,)


def test_physical_explicit_spof_binding_keeps_authored_identity(unit_pack):
    state = _series()
    event = _event(unit_pack, "orders").model_copy(update={"preconditions": [
        EventPrecondition(type="node_is_spof", node="start"),
        EventPrecondition(type="node_is_spof", node="end"),
    ]})
    assert events.failed_node(event, state, unit_pack) == "start"
    assert events.failed_node(event.model_copy(update={"preconditions": []}), state, unit_pack) is None


def _child(code, seed):
    env = {**os.environ, "PYTHONHASHSEED": str(seed), "PYTHONPATH": str(ROOT / "backend")}
    return subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env=env, text=True)


@pytest.mark.parametrize("seed", HASH_SEEDS)
def test_hashseed_diamond_stable_path_and_bottleneck_evidence(seed):
    output = _child('''
import json
from app.engine import graph, events
from app.engine.state import ArchNode, StaffPool, TeamState
adj = {'start': {'a', 'b'}, 'a': {'start', 'end'}, 'b': {'start', 'end'}, 'end': {'a', 'b'}}
path = graph._bfs_path(adj, ['start'], {'end'})
nodes = tuple(ArchNode(k, (), 1.0, 0, 6, capacity_by_capability={'orders': 10 if k in ('a', 'b') else None}) for k in adj)
state = TeamState(1, 'x', nodes, (), (), (), (), StaffPool(2, 2), (), ())
print(json.dumps([path, events.bottleneck_node(state, path, 'orders'), graph.bottleneck_capacity(state, path, 'orders'), graph._bfs_path(adj, ['b', 'a', 'b'], {'end'})]))
''', seed)
    assert json.loads(output) == [["start", "a", "end"], "a", 10, ["a", "end"]]


def test_hashseed_bfs_empty_disconnected_shortest_and_target_ties():
    adj = {"start": {"b", "a"}, "a": {"end"}, "b": {"end"}, "end": set(), "isolated": set()}
    assert graph._bfs_path(adj, [], {"end"}) is None
    assert graph._bfs_path(adj, ["unknown"], {"end"}) is None
    assert graph._bfs_path(adj, ["start"], set()) is None
    assert graph._bfs_path(adj, ["start"], {"isolated"}) is None
    assert graph._bfs_path(adj, ["start"], {"b", "a"}) == ["start", "a"]
    assert graph._bfs_path(adj, ["start", "end", "end"], {"end"}) == ["end"]
    # Lexicographic order resolves equal distances; a shorter path still wins.
    adj["start"].add("end")
    assert graph._bfs_path(adj, ["start"], {"end"}) == ["start", "end"]


def test_legacy_full_24_payloads_across_six_hashseeds(tmp_path):
    blobs = []
    for seed in HASH_SEEDS:
        capture = tmp_path / f"legacy-{seed}.json"
        database = tmp_path / f"legacy-{seed}.db"
        _child(f'''
import json
from pathlib import Path
from app.casepack.loader import load_casepack
from app.calibrate.harness import run_calibration
_, results = run_calibration(load_casepack({str(PACK)!r}), db_url={'sqlite:///' + str(database)!r})
assert sum(map(len, results.values())) == 24
Path({str(capture)!r}).write_bytes(json.dumps(results, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
''', seed)
        blob = capture.read_bytes()
        assert len(blob) == 1657267
        assert hashlib.sha256(blob).hexdigest() == LEGACY_SHA256
        blobs.append(blob)
    assert all(blob == blobs[0] for blob in blobs)
    # Optional independent preflight capture makes the candidate audit a direct byte comparison.
    baseline = os.environ.get("M1_P0_LEGACY_BASELINE")
    if baseline:
        assert blobs[0] == Path(baseline).read_bytes()


def test_legacy_positional_constructor_compatibility():
    node = ArchNode("old", ("client_access",), 0.99, 1, 6,
                    ("orders",), 8000, (("record", "detail"),), "cloud")
    assert (node.serves, node.throughput, node.owns_entities, node.placement) == (
        ("orders",), 8000, (("record", "detail"),), "cloud")
    assert node.capacity_by_capability is None
    assert node.base_rto_hours is None
