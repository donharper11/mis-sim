"""Property and pin tests for the 1.4 scoring engine.

Covers invariants I5-I8 (spec section 6) and the Riverside R3 arithmetic pin
(spec 5.7 / section 8 step 2). Run: `python -m pytest tests/test_engine_scoring.py`
or `python tests/test_engine_scoring.py` for a plain-stdlib run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from app.engine import graph as graph_mod
from app.engine.management import firm_management
from app.engine.score import score_capability, score_team
from app.engine.state import ArchEdge, ArchNode, TeamState
from app.seed.demo import load_scenario

TOL = 0.01


def _pack_state():
    return load_scenario("riverside_r3")


# -- The pin (spec 5.7, section 8 step 2) ---------------------------------------

def test_pin_riverside_r3_order_fulfilment():
    pack, state = _pack_state()
    result = score_team(pack, state)
    of = next(c for c in result.capabilities if c.capability == "order_fulfilment")
    # Tech and Org are unchanged by the 1.4 closeout (invariant C1): exact to 1e-6.
    assert abs(of.terms["tech"] - 0.750008) <= 1e-6, of.terms
    assert abs(of.terms["org"] - 0.507003) <= 1e-6, of.terms
    # Mgmt and realised are the NEW computed pins after two real Management inputs
    # (policy_alignment, policy_discipline) were added by the closeout. The prior
    # 0.648006 / 0.246408 are historical baselines, not targets (decision 10/11).
    assert abs(of.terms["mgmt"] - 0.656778) <= 1e-6, of.terms
    assert abs(of.realised - 0.249744) <= 1e-6, of.realised
    assert of.throttle == "org", of.throttle


def test_pin_riverside_r3_is_an_attentive_team():
    # The seed team actively decided all six switches (closeout decision 10): full
    # discipline, and policy_alignment is whatever the frozen formula computes.
    pack, state = _pack_state()
    result = score_team(pack, state)
    of = next(c for c in result.capabilities if c.capability == "order_fulfilment")
    assert of.sub_factors["mgmt"]["policy_discipline"] == 1.0, of.sub_factors["mgmt"]
    assert abs(of.sub_factors["mgmt"]["policy_alignment"] - 0.4676) <= 1e-6


def test_pin_spofs_match_spec_example():
    pack, state = _pack_state()
    result = score_team(pack, state)
    of = next(c for c in result.capabilities if c.capability == "order_fulfilment")
    assert of.spofs == ["wan_link", "hq_firewall", "core_switch", "order_app"], of.spofs


# -- I5 determinism -------------------------------------------------------------

def test_i5_determinism_one_hash_over_100_runs():
    pack, state = _pack_state()
    hashes = set()
    for _ in range(100):
        rec = score_team(pack, state).record()
        blob = json.dumps(rec, sort_keys=True).encode()
        hashes.add(hashlib.sha256(blob).hexdigest())
    assert len(hashes) == 1, f"expected 1 distinct hash, got {len(hashes)}"


# -- I6 across-MOT is a plain product -------------------------------------------

def test_i6_realised_is_plain_product_of_three_terms():
    pack, state = _pack_state()
    firm = firm_management(pack, state)
    for cap in pack.capabilities:
        cs = score_capability(pack, state, cap.key, firm)
        expected = cs.terms["tech"] * cs.terms["org"] * cs.terms["mgmt"]
        assert abs(cs.realised - round(expected, 6)) <= 1e-6, cap.key


# -- I7 a zero in any term zeroes realised --------------------------------------

def test_i7_zero_in_any_term_zeroes_realised():
    pack, state = _pack_state()
    firm = firm_management(pack, state)
    # tech=0: strip every node so no capability can serve.
    no_nodes = replace(state, nodes=(), edges=())
    cs = score_capability(pack, no_nodes, "order_fulfilment", firm)
    assert cs.terms["tech"] == 0.0 and cs.realised == 0.0
    # org=0: remove the primary deployment so the people terms floor to zero.
    no_dep = replace(state, deployments=())
    cs = score_capability(pack, no_dep, "order_fulfilment", firm)
    assert cs.terms["org"] == 0.0 and cs.realised == 0.0


def test_i7_direct_arithmetic():
    # The property at the arithmetic level: any zero term zeroes the product.
    for t, o, m in [(0.0, 0.5, 0.5), (0.5, 0.0, 0.5), (0.5, 0.5, 0.0)]:
        assert t * o * m == 0.0


# -- I8 capacity is min, not sum ------------------------------------------------

def test_i8_adding_a_slow_node_never_raises_capacity():
    pack, state = _pack_state()
    firm = firm_management(pack, state)
    before = score_capability(pack, state, "order_fulfilment", firm).sub_factors["tech"]["capacity"]

    # Add a slow node onto the serving path (in series after the bottleneck): a
    # sum would rise, a min cannot. Wire it between order_app and order_store.
    slow = ArchNode(
        key="slow_relay", roles_filled=("network_path",), availability=0.99,
        installed_round=0, service_life_rounds=6, serves=("order_fulfilment",),
        throughput=1000.0,  # slower than the 7200 bottleneck
    )
    nodes = state.nodes + (slow,)
    edges = state.edges + (ArchEdge("order_app", "slow_relay", "network"), ArchEdge("slow_relay", "order_store", "network"))
    slower_state = replace(state, nodes=nodes, edges=edges)
    after = score_capability(pack, slower_state, "order_fulfilment", firm).sub_factors["tech"]["capacity"]
    assert after <= before, (before, after)


def test_i8_bottleneck_is_min():
    # min(), never sum(): the direct property on the graph helper.
    pack, state = _pack_state()
    of_entity = "order"
    path = graph_mod.serving_path(state, "order_fulfilment", of_entity, "order_line",
                                  ["daily_store_total", "order_header", "order_line"])
    assert path is not None
    caps = [state.node(k).throughput for k in path if state.node(k) and state.node(k).throughput is not None]
    assert graph_mod.bottleneck_capacity(state, path) == min(caps)


# -- graph analysis on a hand-built fixture -------------------------------------

def test_articulation_points_linear_chain():
    """A-B-C-D-E: the interior nodes B, C, D are the articulation points."""
    nodes = tuple(
        ArchNode(key=k, roles_filled=(), availability=1.0, installed_round=0, service_life_rounds=6)
        for k in ("a", "b", "c", "d", "e")
    )
    edges = (ArchEdge("a", "b"), ArchEdge("b", "c"), ArchEdge("c", "d"), ArchEdge("d", "e"))
    st = TeamState(
        round=1, declared_strategy="x", nodes=nodes, edges=edges, deployments=(),
        org_units=(), governance=(), staff=__import__("app.engine.state", fromlist=["StaffPool"]).StaffPool(2.0, 2.0),
        signals=(), decisions=(),
    )
    assert graph_mod.articulation_points(st) == {"b", "c", "d"}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    raise SystemExit(1 if failed else 0)
