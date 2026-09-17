"""P0b: exact scoped inputs, shared service failures, and verified repair opportunities."""

from dataclasses import FrozenInstanceError, asdict, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.casepack.loader import load_casepack
from app.casepack.models import Capability, Entity, EventPrecondition, WatchRule
from app.engine import events, graph, ledger, metrics, preconditions, technology
from app.engine.state import (
    ActionRecord, ArchEdge, ArchNode, DeploymentState, EntityAccess, RepairAssessment,
    RepairCandidate, StaffPool, TeamState,
)


ROOT = Path(__file__).resolve().parents[2]
PACK_PATH = ROOT / "backend/packs/riverside_grocery"
LEGACY_SHA = "1b45eb1e1bcdd8ae84d764e271648dd1fe68ab6179b41f50fbe259da1b1afa3a"
PROVENANCE = {"source": "AUTHORED", "note": "Independent P0b interface counterexample"}
CAP = "marketing_sales"
ORDER = ["summary", "detail", "individual"]
SIGNAL = "sec_identity_01"


@pytest.fixture(scope="module")
def pack():
    return load_casepack(PACK_PATH)


@pytest.fixture
def access_pack(pack):
    cap = Capability(
        key=CAP, chain_position="test", required_roles=["client_access", "transaction_store"],
        required_entities=[{"entity": e, "min_level_of_detail": "detail"} for e in ("product", "sale")],
        demand_curve=[1500] * 6, demand_unit="campaigns", agreed_availability=0.99,
        provenance=PROVENANCE,
    )
    return pack.model_copy(update={
        "capabilities": [cap],
        "entities": [Entity(key=e, levels_of_detail=ORDER, sensitivity="low", provenance=PROVENANCE)
                     for e in ("product", "sale")],
        "watch_rules": [WatchRule(key="watch_channel", capability=CAP, metric="capacity_utilisation",
                                 warn_above=0.8, critical_above=0.95, cleared_by=["scale_node"],
                                 provenance=PROVENANCE)],
    })


def node(key, **kwargs):
    fields = dict(key=key, roles_filled=(), availability=1.0, installed_round=1,
                  service_life_rounds=6, serves=(), owns_entities=(), placement="on_prem")
    fields.update(kwargs)
    return ArchNode(**fields)


def state(*nodes, edges=(), **kwargs):
    return TeamState(1, "cost_leadership", tuple(nodes), tuple(edges), (), (), (),
                     StaffPool(2, 0), (), (), **kwargs)


def grant(connection="g1", source="pos", receiver="web", capability=CAP, entity="product"):
    return EntityAccess(connection, source, receiver, capability, entity)


def estate():
    return state(
        node("client", roles_filled=("client_access",), serves=(CAP,), availability=0.99),
        node("pos", roles_filled=("transaction_store",), serves=("store_operations",),
             owns_entities=(("product", "detail"), ("sale", "individual")),
             capacity_by_capability={"store_operations": 6000}, availability=0.96,
             installed_round=-10),
        node("web", serves=(CAP,), capacity_by_capability={CAP: 1125}, availability=0.97,
             base_rto_hours=12),
        edges=(ArchEdge("client", "pos"), ArchEdge("client", "web"),
               ArchEdge("web", "pos", "integration")),
        entity_access=(grant(),),
    )


def route(st, **kwargs):
    return graph.serving_path(st, CAP, "product", "detail", ORDER, **kwargs)


def owners(st, entity="product", level="detail", cap=CAP):
    return graph.owner_nodes(st, cap, entity, level, ORDER)


def entity_evidence(pack, st, entity="product"):
    return technology.technology(pack, st, CAP).evidence["data_adequacy"]["entities"][entity]


def test_access_scope_only_named_entity_original_roles_currency_and_physical_counts(access_pack):
    st = estate()
    original = replace(st, entity_access=None)
    before = technology.technology(access_pack, original, CAP)
    after = technology.technology(access_pack, st, CAP)
    assert owners(st) == ["pos"]
    assert owners(st, "sale") == []
    assert owners(st, cap="customer_insight") == []
    assert st.nodes_serving(CAP) == (st.node("client"), st.node("web"))
    assert after.sub_factors["coverage"] == before.sub_factors["coverage"] == 0.5
    assert after.sub_factors["currency"] == before.sub_factors["currency"] == 1.0
    assert after.evidence["currency"] == {"per_node": {"client": 1.0, "web": 1.0}}
    assert after.sub_factors["data_adequacy"] == 0.5
    assert metrics.data_coverage_gap(st, access_pack, access_pack.watch_rules[0]) == 0.5
    assert entity_evidence(access_pack, st) == {
        "required_level": "detail", "owned_by": ["pos"], "access_via": [asdict(grant())],
    }
    assert entity_evidence(access_pack, st, "sale")["access_via"] == []
    assert len(st.nodes) == 3 and st.node("pos").serves == ("store_operations",)
    pc = EventPrecondition(type="placement_count", placement="on_prem", count=3)
    assert preconditions.evaluate_precondition(pc, st, access_pack)
    assert not preconditions.evaluate_precondition(pc.model_copy(update={"count": 4}), st, access_pack)
    pc = EventPrecondition(type="entity_unowned", entity="sale")
    assert not preconditions.evaluate_precondition(pc, st, access_pack)


def test_access_scope_two_grants_one_owner_and_detached_sorted_provenance(access_pack):
    st = replace(estate(), entity_access=[grant("z"), grant("a")])
    assert owners(st) == ["pos"]
    report = entity_evidence(access_pack, st)
    assert report["access_via"] == [asdict(grant("a")), asdict(grant("z"))]
    report["access_via"][0]["receiver"] = "mutated"
    report["owned_by"].append("mutated")
    assert entity_evidence(access_pack, st)["access_via"] == [asdict(grant("a")), asdict(grant("z"))]
    assert owners(st) == ["pos"]


@pytest.mark.parametrize("change", [
    "source_missing", "receiver_missing", "receiver_membership", "ownership_missing",
    "insufficient_level", "wrong_entity", "wrong_capability", "network_only", "edge_missing",
])
def test_access_scope_invalid_live_grants_have_no_owner_or_evidence(access_pack, change):
    st = estate()
    if change.endswith("_missing") and change.split("_")[0] in ("source", "receiver"):
        removed = "pos" if change == "source_missing" else "web"
        st = replace(st, nodes=tuple(n for n in st.nodes if n.key != removed))
    elif change in ("receiver_membership", "ownership_missing", "insufficient_level"):
        key = "web" if change == "receiver_membership" else "pos"
        values = ({"serves": ()} if change == "receiver_membership" else
                  {"owns_entities": () if change == "ownership_missing" else (("product", "summary"),)})
        st = replace(st, nodes=tuple(replace(n, **values) if n.key == key else n for n in st.nodes))
    elif change in ("wrong_entity", "wrong_capability"):
        st = replace(st, entity_access=(grant(entity="sale") if change == "wrong_entity"
                                        else grant(capability="customer_insight"),))
    else:
        st = replace(st, edges=tuple(replace(e, kind="network") for e in st.edges)
                     if change == "network_only" else st.edges[:2])
    assert owners(st) == []
    assert route(st) is None
    assert entity_evidence(access_pack, st)["access_via"] == []


def test_access_scope_levels_no_transitive_access_and_secondary_needs_no_client_path(access_pack):
    st = estate()
    assert owners(st, level="summary") == ["pos"]
    assert owners(st, level="individual") == []
    assert owners(st, level="unknown") == []
    alien = replace(st.node("pos"), owns_entities=(("product", "alien_level"),))
    st_alien = replace(st, nodes=(st.node("client"), alien, st.node("web")))
    assert owners(st_alien, level="alien_level") == ["pos"]
    assert owners(st_alien, level="detail") == []
    disconnected = replace(st, edges=(ArchEdge("pos", "web", "integration"),))
    assert route(disconnected) is None
    assert owners(disconnected) == ["pos"]
    assert entity_evidence(access_pack, disconnected)["access_via"] == [asdict(grant())]
    transitive = replace(st, nodes=st.nodes + (node("next", serves=("customer_insight",)),),
                         edges=st.edges + (ArchEdge("web", "next", "integration"),),
                         entity_access=st.entity_access + (grant("g2", "web", "next", "customer_insight"),))
    assert owners(transitive, cap="customer_insight") == []
    assert transitive.node("web").owns_entities == ()


def test_access_scope_independent_sources_keep_inconsistency_penalty(access_pack):
    st = estate()
    st = replace(st, nodes=st.nodes + (replace(st.node("pos"), key="another"),),
                 edges=st.edges + (ArchEdge("another", "web", "integration"),),
                 entity_access=(grant(), grant("g2", "another")))
    result = technology.technology(access_pack, st, CAP)
    assert owners(st) == ["another", "pos"]
    assert result.evidence["data_adequacy"]["inconsistent"] == ["product"]
    assert result.sub_factors["data_adequacy"] == 0.425
    st = replace(st, edges=st.edges + (ArchEdge("pos", "another", "integration"),))
    assert technology.technology(access_pack, st, CAP).sub_factors["data_adequacy"] == 0.5


def test_access_scope_native_owner_present_empty_evidence(access_pack):
    st = estate()
    native = replace(st.node("pos"), serves=(CAP,))
    st = replace(st, nodes=(native, st.node("web"), st.node("client")), entity_access=())
    assert owners(st) == ["pos"]
    assert entity_evidence(access_pack, st)["access_via"] == []
    assert route(st) == ["client", "pos"]


def test_access_path_receiver_and_each_physical_reliability_and_capacity_consumer(access_pack):
    st = estate()
    assert route(st) == ["client", "web", "pos"]
    assert graph.bottleneck_capacity(st, route(st), CAP) == 1125
    assert graph.path_reliability(st, route(st)) == pytest.approx(0.99 * 0.97 * 0.96)
    result = technology.technology(access_pack, st, CAP)
    assert result.evidence["capacity"] == {"bottleneck": 1125, "demand": 1500}
    assert result.sub_factors["capacity"] == 0.75
    assert result.sub_factors["reliability"] == round(0.99 * 0.97 * 0.96, 6)
    assert metrics.capacity_utilisation(st, access_pack, access_pack.watch_rules[0]) == 1.3333
    assert metrics.availability_shortfall(st, access_pack, access_pack.watch_rules[0]) == 0.0681
    event = access_pack.events[0].model_copy(update={"preconditions": [
        EventPrecondition(type="signal_open", signal="watch_channel", severity="warning"),
    ]})
    assert events.failed_node(event, st, access_pack) == "web"
    assert events.bottleneck_node(st, route(st), CAP) == "web"


def test_access_path_real_catalog_product_grant_does_not_expose_pos_sale(pack):
    pos = next(i for i in pack.catalog if i.key == "pos_system_2011")
    web = next(i for i in pack.catalog if i.key == "ecommerce_site")
    source = node("pos", roles_filled=tuple(pos.roles_filled), serves=tuple(pos.serves),
                  owns_entities=tuple((e.entity, e.level_of_detail) for e in pos.owns_entities),
                  capacity_by_capability={"store_operations": 6000})
    receiver = node("web", roles_filled=tuple(web.roles_filled), serves=tuple(web.serves),
                    capacity_by_capability={CAP: 1125})
    st = replace(estate(), nodes=(estate().node("client"), source, receiver))
    result = technology.technology(pack, st, CAP)
    assert result.evidence["serving_path"] == ["client", "web", "pos"]
    assert result.evidence["capacity"]["bottleneck"] == 1125
    assert graph.owner_nodes(st, CAP, "sale", "individual_transaction", []) == []


@pytest.mark.parametrize("change", ["disconnected_receiver", "retired_receiver", "retired_source", "grant_removed", "integration_removed", "wrong_kind"])
def test_access_path_unavailable_receiver_source_or_exact_integration_fails(access_pack, change):
    st = estate()
    if change == "disconnected_receiver":
        st = replace(st, edges=(st.edges[0], st.edges[2]))
    elif change.startswith("retired"):
        removed = "web" if change.endswith("receiver") else "pos"
        st = replace(st, nodes=tuple(n for n in st.nodes if n.key != removed))
    elif change == "grant_removed":
        st = replace(st, entity_access=())
    elif change == "integration_removed":
        st = replace(st, edges=st.edges[:2])
    else:
        st = replace(st, edges=st.edges[:2] + (ArchEdge("web", "pos", "failover"),))
    assert route(st) is None
    result = technology.technology(access_pack, st, CAP)
    assert result.sub_factors["capacity"] == result.sub_factors["reliability"] == 0
    assert metrics.capacity_utilisation(st, access_pack, access_pack.watch_rules[0]) == 0


def test_access_path_native_competes_by_length_then_keys_and_never_repeats_source():
    st = estate()
    # The only prefix to web would traverse source: that may not be reused as the terminal.
    assert route(replace(st, edges=(st.edges[0], st.edges[2]))) is None
    native = node("native", serves=(CAP,), owns_entities=(("product", "detail"),))
    mid = node("a_mid")
    st = replace(st, nodes=st.nodes + (native, mid),
                 edges=st.edges + (ArchEdge("client", "a_mid"), ArchEdge("a_mid", "native")))
    assert route(st) == ["client", "a_mid", "native"]
    # A native route remains legal when imported routes also exist; shortest wins before keys.
    st = replace(st, edges=st.edges + (ArchEdge("client", "native"),))
    assert route(st) == ["client", "native"]
    assert route(st, exclude_nodes=frozenset({"native"})) == ["client", "web", "pos"]
    assert route(replace(st, nodes=tuple(reversed(st.nodes)), edges=tuple(reversed(st.edges)),
                         entity_access=tuple(reversed(st.entity_access)))) == ["client", "native"]


def test_access_path_stable_grant_and_source_ties_detached_results():
    st = estate()
    alt = replace(st.node("web"), key="a_receiver")
    st = replace(st, nodes=st.nodes + (alt,),
                 edges=st.edges + (ArchEdge("client", "a_receiver"), ArchEdge("pos", "a_receiver", "integration")),
                 entity_access=(grant(), grant("z", receiver="a_receiver")))
    expected = ["client", "a_receiver", "pos"]
    assert route(st) == expected
    route(st).append("mutated")
    assert route(st) == expected
    st = replace(st, nodes=tuple(reversed(st.nodes)), edges=tuple(reversed(st.edges)),
                 entity_access=tuple(reversed(st.entity_access)))
    assert route(st) == expected
    source = node("a_client", roles_filled=("client_access",), serves=(CAP,))
    st = replace(st, nodes=st.nodes + (source,), edges=st.edges + (ArchEdge("a_client", "a_receiver"),))
    assert route(st) == ["a_client", "a_receiver", "pos"]


def test_access_failure_receiver_service_spof_despite_physical_shortcut(access_pack):
    st = estate()
    assert graph.spofs_on_path(st, route(st)) == []
    assert graph.serving_spofs(st, CAP, "product", "detail", ORDER, route(st)) == ["web"]
    assert technology.technology(access_pack, st, CAP).spofs == ["web"]
    pc = EventPrecondition(type="node_is_spof", node="web")
    assert not preconditions.evaluate_precondition(pc, st, access_pack)
    primary = {CAP: ("product", "detail", ORDER)}
    for key in ("client", "pos", "web"):
        assert route(st, exclude_nodes=frozenset({key})) is None
        assert graph.blast_radius(st, key, [CAP], primary) == [CAP]
    assert graph.blast_radius(st, "unknown", [CAP], primary) == []
    disconnected = replace(st, entity_access=())
    assert graph.blast_radius(disconnected, "web", [CAP], primary) == []
    assert events.outage_duration(st, "web", CAP, access_pack) == {
        "node": "web", "base_rto_hours": 12, "failover_exists": False, "failover_factor": 3.0,
        "staffing_modifier": 1.0, "duration_hours": 36.0, "blast_radius": [CAP],
    }


def alternate_estate():
    st = estate()
    return replace(st, nodes=st.nodes + (replace(st.node("web"), key="backup"),),
                   edges=st.edges + (ArchEdge("client", "backup", "failover"),
                                    ArchEdge("backup", "pos", "integration")),
                   entity_access=st.entity_access + (grant("g2", receiver="backup"),))


def test_access_failure_alternate_receiver_requires_load_bearing_failover(access_pack):
    st = alternate_estate()
    snapshot = (st.nodes, st.edges, st.entity_access)
    assert route(st, exclude_nodes=frozenset({"web"})) == ["client", "backup", "pos"]
    assert events.failover_exists(st, "web", CAP, access_pack)
    assert not events.failover_exists(st, "pos", CAP, access_pack)
    assert not events.failover_exists(st, "backup", CAP, access_pack)
    assert technology.technology(access_pack, st, CAP).spofs == []
    assert graph.blast_radius(st, "web", [CAP], {CAP: ("product", "detail", ORDER)}) == []
    assert route(st, exclude_nodes=frozenset({"web"}),
                 exclude_edges=frozenset({("backup", "client", "failover")})) is None
    # A parallel network edge survives an exclusion of the same pair's failover kind.
    parallel = replace(st, edges=st.edges + (ArchEdge("backup", "client", "network"),))
    assert not events.failover_exists(parallel, "web", CAP, access_pack)
    assert route(parallel, exclude_nodes=frozenset({"web"}),
                 exclude_edges=frozenset({("backup", "client", "failover")})) == ["client", "backup", "pos"]
    assert (st.nodes, st.edges, st.entity_access) == snapshot
    assert events.outage_duration(st, "web", CAP, access_pack)["duration_hours"] == 12.0


def test_access_failure_native_and_imported_alternatives_both_survive(access_pack):
    st = estate()
    native = node("native", serves=(CAP,), owns_entities=(("product", "detail"),))
    st = replace(st, nodes=st.nodes + (native,), edges=st.edges + (ArchEdge("client", "native"),))
    primary = {CAP: ("product", "detail", ORDER)}
    for key in ("native", "web", "pos"):
        assert graph.blast_radius(st, key, [CAP], primary) == []
    assert route(st, exclude_nodes=frozenset({"pos"})) == ["client", "native"]
    assert route(st, exclude_nodes=frozenset({"native", "web"})) is None
    assert not events.failover_exists(st, "web", CAP, access_pack)


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("kwargs", [
    {"exclude_nodes": None}, {"exclude_nodes": []}, {"exclude_nodes": set()},
    {"exclude_nodes": {}}, {"exclude_nodes": "web"},
    {"exclude_edges": None}, {"exclude_edges": []}, {"exclude_edges": set()},
    {"exclude_edges": {}}, {"exclude_edges": "web"},
    {"exclude_nodes": frozenset({""})}, {"exclude_nodes": frozenset({" \t"})},
    {"exclude_nodes": frozenset({1})}, {"exclude_nodes": frozenset({None})},
    {"exclude_edges": frozenset({("web", "pos", "integration")})},
    {"exclude_edges": frozenset({("pos", "pos", "integration")})},
    {"exclude_edges": frozenset({("pos", "web", "other")})},
    {"exclude_edges": frozenset({("pos", "web")})},
    {"exclude_edges": frozenset({("pos", "web", "integration", "extra")})},
    {"exclude_edges": frozenset({("", "web", "integration")})},
    {"exclude_edges": frozenset({("pos", 1, "integration")})},
    {"exclude_edges": frozenset({"pos"})},
])
def test_access_failure_total_exclusion_validation_before_both_branches(legacy, kwargs):
    st = state(entity_access=None if legacy else ())
    with pytest.raises(ValueError):
        route(st, **kwargs)


@pytest.mark.parametrize("field", ["exclude_nodes", "exclude_edges"])
def test_access_failure_generator_exclusions_refused(field):
    with pytest.raises(ValueError):
        route(estate(), **{field: (x for x in ())})


def test_access_failure_exact_edge_kinds_unknown_identities_and_native_exclusions():
    st = estate()
    assert route(st, exclude_nodes=frozenset({"unknown"}),
                 exclude_edges=frozenset({("absent_a", "absent_b", "integration")})) == route(st)
    assert route(st, exclude_edges=frozenset({("pos", "web", "network")})) == route(st)
    assert route(st, exclude_edges=frozenset({("pos", "web", "integration")})) is None
    native = replace(st, nodes=tuple(replace(n, serves=(CAP,)) if n.key == "pos" else n for n in st.nodes),
                     entity_access=None)
    assert route(native) == ["client", "pos"]
    assert route(native, exclude_edges=frozenset({("client", "pos", "network")})) == ["client", "web", "pos"]
    assert route(native, exclude_nodes=frozenset({"pos"})) is None
    assert route(native, exclude_edges=frozenset({("pos", "web", "integration")})) == ["client", "pos"]


def candidate(cost=0, effective=1, affordable=True, key="a"):
    return RepairCandidate(key * 64, cost, effective, affordable)


def assessed(pack, st=None, candidates=(), signal=SIGNAL):
    st = state() if st is None else st
    return replace(st, repair_assessments=tuple(
        RepairAssessment(rule.key, st.round, tuple(candidates) if rule.key == signal else ())
        for rule in pack.watch_rules
    ))


def signal_row(rows, key=SIGNAL):
    return next(row for row in reversed(rows) if row.key == key)


def test_assessment_none_preserves_generic_quote_and_funds(pack):
    st = state(available_funds_by_round=(1000000,))
    rule = next(r for r in pack.watch_rules if r.key == SIGNAL)
    row = signal_row(ledger.advance_ledger((), st, pack))
    quote = ledger.cheapest_effectful_fix(rule, pack)
    assert row.cheapest_fix_when_raised == quote
    assert row.was_actionable == ledger.was_actionable(quote, st.available_funds_by_round, range(1, 2))
    assert ledger.advance_ledger((), replace(st, repair_assessments=None), pack) == (row,)


def test_assessment_unassessed_never_calls_generic_price_or_funds(pack, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("production assessment fell back to legacy repair logic")
    monkeypatch.setattr(ledger, "cheapest_effectful_fix", forbidden)
    monkeypatch.setattr(ledger, "was_actionable", forbidden)
    st = assessed(pack, state(available_funds_by_round=(1000000,) * 6))
    row = signal_row(ledger.advance_ledger((), st, pack))
    assert row.cheapest_fix_when_raised is None and not row.was_actionable
    next_st = assessed(pack, replace(st, round=2))
    assert signal_row(ledger.advance_ledger((row,), next_st, pack)).cheapest_fix_when_raised is None


@pytest.mark.parametrize("candidates,quote,actionable", [
    ((), None, False), ((candidate(),), 0, True), ((candidate(0, affordable=False),), 0, False),
    ((candidate(4, affordable=False), candidate(9, key="b")), 4, True),
    ((candidate(4, affordable=False), candidate(9, affordable=False, key="b")), 4, False),
])
def test_assessment_zero_none_and_cheapest_independent_of_affordable_witness(pack, candidates, quote, actionable):
    st = assessed(pack, state(available_funds_by_round=(1000000,) * 6), candidates)
    row = signal_row(ledger.advance_ledger((), st, pack))
    assert row.cheapest_fix_when_raised == quote
    assert row.was_actionable is actionable
    # A supplied witness already attests full affordability, even with no residual capital array.
    assert ledger.advance_ledger((), replace(st, available_funds_by_round=()), pack) == (row,)


def test_assessment_affordable_witness_tie_break_and_cost_minimum(pack):
    values = (candidate(1, affordable=False), candidate(8, key="c"), candidate(8, key="b"), candidate(9, key="d"))
    assessment = RepairAssessment(SIGNAL, 1, values)
    assert ledger._affordable_witness(assessment) == candidate(8, key="b")
    row = signal_row(ledger.advance_ledger((), assessed(pack, candidates=values), pack))
    assert row.cheapest_fix_when_raised == 1 and row.was_actionable


@pytest.mark.parametrize("initial", [None, 90])
def test_assessment_later_opportunity_preserves_initial_quote_and_timestamps(pack, initial):
    candidates = () if initial is None else (candidate(initial, affordable=False),)
    first = signal_row(ledger.advance_ledger((), assessed(pack, candidates=candidates), pack))
    st2 = assessed(pack, replace(state(), round=2), (candidate(7, 2),))
    second = signal_row(ledger.advance_ledger((first,), st2, pack))
    assert second.cheapest_fix_when_raised == initial
    assert second.first_shown_round == 1 and second.episode_id == 1
    assert second.was_actionable and not first.was_actionable
    third = signal_row(ledger.advance_ledger((second,), assessed(pack, replace(state(), round=3)), pack))
    assert third.was_actionable and third.cheapest_fix_when_raised == initial
    assert not ledger.project_signal_state((second,), current_round=1)[0].actionable
    assert ledger.project_signal_state((second,), current_round=2)[0].actionable


@pytest.mark.parametrize("change", ["empty", "missing_nonraising", "extra", "stale", "future", "early_effect", "late_effect"])
def test_assessment_complete_coverage_checked_round_and_horizon_enforced(pack, change):
    st = assessed(pack, replace(state(), round=2))
    entries = list(st.repair_assessments)
    if change == "empty":
        entries = []
    elif change == "missing_nonraising":
        entries = [a for a in entries if a.signal != "wh_rollout_01"]
    elif change == "extra":
        entries.append(RepairAssessment("unknown", 2, ()))
    else:
        index = next(i for i, a in enumerate(entries) if a.signal == "wh_rollout_01")
        entries[index] = replace(entries[index], **(
            {"checked_round": 1 if change == "stale" else 3} if change in ("stale", "future")
            else {"candidates": (candidate(1, 1 if change == "early_effect" else pack.metadata.rounds + 1),)}
        ))
    st = replace(st, repair_assessments=entries)
    with pytest.raises(ValueError):
        ledger.advance_ledger((), st, pack)


def test_assessment_horizon_boundaries_empty_watch_pack_and_nonraising_assessments(pack):
    st = assessed(pack, candidates=(candidate(1, pack.metadata.rounds),))
    assert signal_row(ledger.advance_ledger((), st, pack)).was_actionable
    empty_pack = pack.model_copy(update={"watch_rules": []})
    assert ledger.advance_ledger((), state(repair_assessments=()), empty_pack) == ()
    st = assessed(pack, state(node("id", roles_filled=("identity_access",))), (candidate(),))
    assert ledger.advance_ledger((), st, pack) == ()


def test_assessment_prevention_and_noop_are_not_silently_credit_eligible(pack):
    rule = next(r for r in pack.watch_rules if r.key == "wh_rollout_01")
    response_only = rule.model_copy(update={"cleared_by": ["fund_response"]})
    response_pack = pack.model_copy(update={"watch_rules": [response_only]})
    rollout = DeploymentState("live", "warehouse_system", "warehouse", 10, 0, "unchanged", 0, False,
                              (rule.capability,), rule.capability)
    st = replace(state(available_funds_by_round=(1000000,) * 6), deployments=(rollout,))
    old = ledger.advance_ledger((), st, response_pack)[0]
    assert old.cheapest_fix_when_raised == 6000 and old.was_actionable
    production = assessed(response_pack, st, signal=rule.key)
    current = ledger.advance_ledger((), production, response_pack)[0]
    assert current.cheapest_fix_when_raised is None and not current.was_actionable
    # Empty candidates also prevents initial/free modes from becoming a generic fallback.
    ordinary = ledger.advance_ledger((), assessed(pack, st, signal=rule.key), pack)
    assert all(row.cheapest_fix_when_raised is None and not row.was_actionable for row in ordinary)


def test_assessment_still_raises_no_false_clear_original_actions_and_credit_clock(pack):
    initial = signal_row(ledger.advance_ledger((), assessed(pack, candidates=(candidate(20),)), pack))
    action = ActionRecord("add_node", 2, "firm_infrastructure", "identity", 20)
    st = assessed(pack, replace(state(), round=2, action_history=(action,)), (candidate(1, 2),))
    still_open = signal_row(ledger.advance_ledger((initial,), st, pack))
    assert still_open.status == "open" and still_open.cleared_round is None
    fixed = replace(st, nodes=(node("identity", roles_filled=("identity_access",)),))
    cleared = signal_row(ledger.advance_ledger((initial,), fixed, pack, frozenset({SIGNAL})))
    assert (cleared.status, cleared.cleared_round, cleared.fire_round, cleared.cleared_by) == (
        "cleared", 2, 2, ("add_node",))
    assert cleared.cheapest_fix_when_raised == 20 and cleared.first_shown_round == 1
    assert ledger.project_signal_state((cleared,), 2)[0].acted_before_fire
    assert fixed.action_history[0].locked_round == 2
    for invalid_action in (replace(action, locked_round=0), replace(action, locked_round=3),
                           replace(action, capability=CAP), replace(action, action_type="scale_node")):
        lapsed = signal_row(ledger.advance_ledger((initial,), replace(fixed, action_history=(invalid_action,)), pack))
        assert lapsed.status == "cleared" and lapsed.cleared_round is None
        assert not ledger.project_signal_state((lapsed,), 2)[0].acted_before_fire


def test_assessment_terminal_history_second_fire_pass_and_fired_on_sight_projection(pack):
    st = assessed(pack, candidates=(candidate(50),))
    first = ledger.advance_ledger((), st, pack)
    stamped = ledger.advance_ledger(first, st, pack, frozenset({SIGNAL}))
    row = signal_row(stamped)
    assert row.status == "fired" and row.fire_round == row.first_shown_round == 1
    assert row.cheapest_fix_when_raised == 50 and row.was_actionable
    assert len(stamped) == 1
    assert ledger.project_signal_state(stamped)[0].actionable
    assert not ledger.project_signal_state(stamped, 2)[0].actionable
    later = assessed(pack, replace(state(), round=2), (candidate(1, 2),))
    recurrence = ledger.advance_ledger(stamped, later, pack)
    assert recurrence[0] is row
    assert recurrence[1].episode_id == 2 and recurrence[1].first_shown_round == 2
    assert recurrence[1].cheapest_fix_when_raised == 1
    fixed = replace(later, nodes=(node("identity", roles_filled=("identity_access",)),))
    assert ledger.advance_ledger(stamped, fixed, pack) == stamped


def test_immutable_all_records_and_two_tuple_layers_are_copied_and_frozen(pack):
    grants = [grant()]
    candidates = [candidate()]
    assessment = RepairAssessment(SIGNAL, 1, candidates)
    assessments = [assessment]
    st = state(entity_access=grants, repair_assessments=assessments)
    grants.clear()
    candidates.clear()
    assessments.clear()
    assert st.entity_access == (grant(),)
    assert st.repair_assessments == (RepairAssessment(SIGNAL, 1, (candidate(),)),)
    assert type(st.entity_access) is type(st.repair_assessments) is type(assessment.candidates) is tuple
    for obj, field, value in ((st, "entity_access", ()), (grant(), "source", "other"),
                              (candidate(), "capital_cost", 1), (assessment, "candidates", ())):
        with pytest.raises(FrozenInstanceError):
            setattr(obj, field, value)
    assert replace(st).entity_access == st.entity_access


@pytest.mark.parametrize("field", ["entity_access", "repair_assessments", "candidates"])
@pytest.mark.parametrize("value", [{}, "text", 1, False, [None], [{}], ["record"]])
def test_immutable_container_and_exact_record_validation(field, value):
    with pytest.raises(ValueError):
        if field == "candidates":
            RepairAssessment(SIGNAL, 1, value)
        else:
            state(**{field: value})


def test_immutable_generators_wrong_classes_and_none_candidate_container_rejected():
    for field in ("entity_access", "repair_assessments"):
        with pytest.raises(ValueError):
            state(**{field: (v for v in ())})
    for value in (None, (v for v in ()), (grant(),)):
        with pytest.raises(ValueError):
            RepairAssessment(SIGNAL, 1, value)
    with pytest.raises(ValueError):
        state(entity_access=(RepairAssessment(SIGNAL, 1, ()),))
    class DerivedAccess(EntityAccess):
        pass
    with pytest.raises(ValueError):
        state(entity_access=(DerivedAccess("g", "s", "r", "c", "e"),))


@pytest.mark.parametrize("field", ["connection", "source", "receiver", "capability", "entity"])
@pytest.mark.parametrize("value", ["", " \t\n", None, 1, False])
def test_immutable_entity_access_keys(field, value):
    with pytest.raises(ValueError):
        replace(grant(), **{field: value})


@pytest.mark.parametrize("value", ["", " \t", None, 1, False])
def test_immutable_assessment_signal_key(value):
    with pytest.raises(ValueError):
        RepairAssessment(value, 1, ())


@pytest.mark.parametrize("key", ["", " ", "a" * 63, "a" * 65, "A" * 64, "g" * 64, None, 1])
def test_immutable_candidate_identity_is_lowercase_sha256(key):
    with pytest.raises(ValueError):
        RepairCandidate(key, 0, 1, True)


INVALID_NUMBERS = [
    pytest.param(True, id="bool_true"), pytest.param(False, id="bool_false"),
    pytest.param(1.0, id="float"), pytest.param(-1, id="negative"), pytest.param(None, id="none"),
    pytest.param("1", id="string"), pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="inf"), pytest.param(float("-inf"), id="negative_inf"),
    pytest.param(10 ** 10000, id="overflow"), pytest.param([], id="list"),
]


@pytest.mark.parametrize("field", ["capital_cost", "effective_round", "checked_round"])
@pytest.mark.parametrize("value", INVALID_NUMBERS)
def test_immutable_counts_are_exact_finite_nonbool_ints(field, value):
    with pytest.raises(ValueError):
        if field == "checked_round":
            RepairAssessment(SIGNAL, value, ())
        else:
            replace(candidate(), **{field: value})


@pytest.mark.parametrize("value", [0, 1, None, "true", [], {}])
def test_immutable_affordable_is_exact_bool(value):
    with pytest.raises(ValueError):
        replace(candidate(), affordable=value)


def test_immutable_duplicates_dates_self_grant_and_valid_general_keys():
    for field in ("effective_round", "checked_round"):
        with pytest.raises(ValueError):
            if field == "effective_round":
                replace(candidate(), effective_round=0)
            else:
                RepairAssessment(SIGNAL, 0, ())
    with pytest.raises(ValueError):
        replace(grant(), receiver="pos")
    with pytest.raises(ValueError):
        state(entity_access=[grant(), grant()])
    with pytest.raises(ValueError):
        state(repair_assessments=[RepairAssessment(SIGNAL, 1, ()), RepairAssessment(SIGNAL, 2, ())])
    with pytest.raises(ValueError):
        RepairAssessment(SIGNAL, 1, (candidate(), candidate(1)))
    general = EntityAccess("connection 1", " original source ", "receiving-system", "Capability 1", "Entity 1")
    assert state(entity_access=[general]).entity_access == (general,)


def test_legacy_evidence_omits_access_key_and_old_positional_inputs_work(access_pack):
    st = estate()
    native = replace(st.node("pos"), serves=(CAP,))
    st = replace(st, nodes=(st.node("client"), native, st.node("web")), entity_access=None)
    detail = technology.technology(access_pack, st, CAP).evidence["data_adequacy"]["entities"]
    assert all("access_via" not in row for row in detail.values())
    assert state().entity_access is None and state().repair_assessments is None
    assert owners(st) == ["pos"] and route(st) == ["client", "pos"]


def test_legacy_full24_payload_bytes_and_supervisor_capture(tmp_path):
    destination = tmp_path / "full24.json"
    db_url = "sqlite:///" + str(tmp_path / "full24.db")
    code = f'''
import json
from pathlib import Path
from app.casepack.loader import load_casepack
from app.calibrate.harness import run_calibration
_, results = run_calibration(load_casepack({str(PACK_PATH)!r}), db_url={db_url!r})
assert sum(map(len, results.values())) == 24
Path({str(destination)!r}).write_bytes(json.dumps(results, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
'''
    subprocess.check_call([sys.executable, "-c", code], cwd=ROOT,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "backend"), "PYTHONHASHSEED": "42"})
    blob = destination.read_bytes()
    assert len(blob) == 1657267 and hashlib.sha256(blob).hexdigest() == LEGACY_SHA
    assert sum(map(len, json.loads(blob).values())) == 24
    if os.environ.get("M1_P0_LEGACY_BASELINE"):
        assert blob == Path(os.environ["M1_P0_LEGACY_BASELINE"]).read_bytes()
