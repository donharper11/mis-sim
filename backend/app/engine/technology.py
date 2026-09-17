"""Technology Capability -- computed from the graph, no judgement (spec 5.1).

Technology uses an authored weighted average for partial evidence. A capability
with no serving path remains a hard zero; once a path exists, capacity, reliability,
data and currency gaps reduce the term proportionally rather than erasing it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.casepack.models import Casepack
from app.engine import catalog, graph
from app.engine.mathx import clamp, weighted_mean
from app.engine.state import TeamState


#: O2 default: a missing required role floors coverage at 0.3, not 0. A true zero
#: would make the whole capability zero and hide the Org/Mgmt signal, which is the
#: lesson; the student still sees the missing role prominently.
COVERAGE_FLOOR = 0.3

#: A required entity held by two or more serving nodes with no integration edge
#: between them is a data-inconsistency risk (the "two systems disagree about
#: inventory" problem). Each such entity multiplies data adequacy by (1 - this).
#: Hard-coded v1 (O1 lineage); revisit after 1.7.
INCONSISTENCY_PENALTY = 0.15

# Technology evidence weights. Capacity and data adequacy carry the most weight
# because they determine whether a live path can serve useful business work.
TECHNOLOGY_WEIGHTS = {
    "coverage": 0.20,
    "capacity": 0.25,
    "reliability": 0.20,
    "data_adequacy": 0.25,
    "currency": 0.10,
}


@dataclass
class TechResult:
    value: float
    sub_factors: dict[str, float]
    evidence: dict[str, Any] = field(default_factory=dict)
    spofs: list[str] = field(default_factory=list)


def _coverage(pack: Casepack, state: TeamState, cap_key: str) -> tuple[float, list[str]]:
    roles = catalog.required_roles(pack, cap_key)
    serving = state.nodes_serving(cap_key)
    frac, missing = graph.coverage_fraction(roles, serving)
    if missing:
        return max(frac, COVERAGE_FLOOR), missing
    return frac, missing


def _has_integration_edge(state: TeamState, a: str, b: str) -> bool:
    for e in state.edges:
        if e.kind == "integration" and {e.src, e.dst} == {a, b}:
            return True
    return False


def _data_adequacy(pack: Casepack, state: TeamState, cap_key: str) -> tuple[float, dict[str, Any]]:
    reqs = catalog.required_entities(pack, cap_key)
    serving = state.nodes_serving(cap_key)
    satisfied = 0
    penalty_product = 1.0
    detail: dict[str, Any] = {"entities": {}, "inconsistent": []}
    for entity_key, level, order in reqs:
        owners = graph.owner_nodes(state, cap_key, entity_key, level, order)
        ok = len(owners) >= 1
        if ok:
            satisfied += 1
        detail["entities"][entity_key] = {"required_level": level, "owned_by": owners}
        if state.entity_access is not None:
            detail["entities"][entity_key]["access_via"] = [
                asdict(grant) for grant in graph.valid_entity_access(state, cap_key, entity_key, level, order)
            ]
        if len(owners) >= 2:
            # Owned by two-plus nodes: penalise unless every pair is integrated.
            integrated = all(
                _has_integration_edge(state, owners[i], owners[j])
                for i in range(len(owners))
                for j in range(i + 1, len(owners))
            )
            if not integrated:
                penalty_product *= 1.0 - INCONSISTENCY_PENALTY
                detail["inconsistent"].append(entity_key)
    ratio = satisfied / len(reqs) if reqs else 1.0
    return clamp(ratio * penalty_product), detail


def _currency(state: TeamState, cap_key: str) -> tuple[float, dict[str, Any]]:
    serving = [n for n in state.nodes_serving(cap_key) if n.service_life_rounds > 0]
    if not serving:
        return 1.0, {}
    per_node: dict[str, float] = {}
    total = 0.0
    for n in serving:
        age = state.round - n.installed_round
        c = clamp(1.0 - age / n.service_life_rounds)
        per_node[n.key] = round(c, 4)
        total += c
    return total / len(serving), {"per_node": per_node}


def technology(pack: Casepack, state: TeamState, cap_key: str) -> TechResult:
    coverage, missing_roles = _coverage(pack, state, cap_key)

    primary_entity, primary_level, primary_order = catalog.primary_entity(pack, cap_key)
    path = graph.serving_path(state, cap_key, primary_entity, primary_level, primary_order)

    evidence: dict[str, Any] = {}
    spofs: list[str] = []

    if path is None:
        # No path from a client endpoint to the record: capacity is 0 and the
        # capability cannot serve (spec 5.1). Coverage is already floored.
        capacity = 0.0
        reliability = 0.0
        evidence["serving_path"] = None
    else:
        demand = catalog.demand_at(pack, cap_key, state.round)
        bottleneck = graph.bottleneck_capacity(state, path, cap_key)
        capacity = clamp((bottleneck / demand) if bottleneck is not None else 1.0)
        reliability = graph.path_reliability(state, path)
        spofs = (
            graph.spofs_on_path(state, path) if state.entity_access is None
            else graph.serving_spofs(state, cap_key, primary_entity, primary_level, primary_order, path)
        )
        evidence["serving_path"] = path
        evidence["capacity"] = {"bottleneck": bottleneck, "demand": demand}

    data_adequacy, data_detail = _data_adequacy(pack, state, cap_key)
    if state.data_freshness is not None:
        raw_adequacy = data_adequacy
        data_adequacy = min(data_adequacy, state.data_freshness.coverage)
        data_detail["freshness"] = {
            "coverage": state.data_freshness.coverage,
            "statuses": {entity: status for entity, status in state.data_freshness.statuses},
            "raw_data_adequacy": raw_adequacy,
        }
    currency, currency_detail = _currency(state, cap_key)

    sub_factors = {
        "coverage": round(coverage, 6),
        "capacity": round(capacity, 6),
        "reliability": round(reliability, 6),
        "data_adequacy": round(data_adequacy, 6),
        "currency": round(currency, 6),
    }
    value = 0.0 if path is None else weighted_mean(sub_factors, TECHNOLOGY_WEIGHTS)

    if missing_roles:
        evidence["missing_roles"] = missing_roles
    evidence["data_adequacy"] = data_detail
    if currency_detail:
        evidence["currency"] = currency_detail

    return TechResult(value=round(value, 6), sub_factors=sub_factors, evidence=evidence, spofs=spofs)
