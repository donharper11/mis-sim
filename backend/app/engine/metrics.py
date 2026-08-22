"""The five watch-rule metrics and the rule evaluator (1.5 contract-spec section 4).

Each metric has the frozen signature `metric(state, pack, rule) -> float | bool` and is pure:
it reads the round-close snapshot before event outcomes are applied. A `threshold` metric
returns an unclipped float; a `presence` metric returns a bool. The `METRICS` registry maps
the five frozen keys to functions; an unknown key raises `UnknownMetricError`, it never
evaluates false (contract-spec section 4.6, decision 2).

Decision 4 (contract-spec section 3): a metric measuring a property of an existing serving
path returns `0.0` -- never raising and never dividing by zero -- when the capability has no
serving path or non-positive capacity. "No path" is a coverage failure scored by 1.4, not an
operational watch signal.
"""

from __future__ import annotations

from typing import Callable

from app.casepack.models import Casepack, WatchRule
from app.engine import catalog, graph
from app.engine.state import TeamState


class UnknownMetricError(Exception):
    """Raised when a watch rule names a metric key outside the frozen `METRICS` registry.

    An unknown metric must raise, never evaluate false (contract-spec section 4.6): a silent
    false would hide a broken pack behind a signal that simply never fires.
    """

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def _serving_path(state: TeamState, pack: Casepack, cap_key: str) -> list[str] | None:
    """The capability's serving path from a client endpoint to its primary record, or None."""
    primary_entity, primary_level, primary_order = catalog.primary_entity(pack, cap_key)
    return graph.serving_path(state, cap_key, primary_entity, primary_level, primary_order)


def capacity_utilisation(state: TeamState, pack: Casepack, rule: WatchRule) -> float:
    """Load on the capability's scarcest resource: raw, unclipped `demand / capacity`.

    Deliberately different from 1.4's clipped, inverted `capacity` sub-factor: this metric
    must be able to express over-saturation above 1.0 (contract-spec section 4.1).
    """
    cap = rule.capability
    demand = catalog.demand_at(pack, cap, state.round)
    if demand == 0:
        return 0.0
    path = _serving_path(state, pack, cap)
    if path is None:
        return 0.0
    bottleneck = graph.bottleneck_capacity(state, path)
    if bottleneck is None or bottleneck <= 0:
        return 0.0
    return round(demand / bottleneck, 4)


def rollout_without_support(state: TeamState, pack: Casepack, rule: WatchRule) -> bool:
    """A live rollout of the capability nobody was trained for and no process was changed for.

    TRUE iff any deployment serving the capability is initiated, not abandoned, has
    `trained_count == 0` and `process == "unchanged"` (contract-spec section 4.2). A
    capability with no deployment is a coverage issue, not "rollout without support" -> FALSE.
    """
    for d in state.deployments_serving(rule.capability):
        if d.initiated and not d.abandoned and d.trained_count == 0 and d.process == "unchanged":
            return True
    return False


def missing_identity_access(state: TeamState, pack: Casepack, rule: WatchRule) -> bool:
    """No live node fills the `identity_access` role for the firm (contract-spec section 4.3).

    Scoped to role presence -- the only grounded signal; per-account provisioning is out of
    scope. An empty node set has no identity node, so it is TRUE.
    """
    for node in state.nodes:
        if "identity_access" in node.roles_filled:
            return False
    return True


def availability_shortfall(state: TeamState, pack: Casepack, rule: WatchRule) -> float:
    """How far realised availability falls below the capability's agreed target.

    `shortfall = max(0.0, agreed_availability - realised)`, where realised is the product of
    node availabilities on the serving path (contract-spec section 4.4). No path -> 0.0.
    """
    cap = rule.capability
    path = _serving_path(state, pack, cap)
    if path is None:
        return 0.0
    realised = graph.path_reliability(state, path)
    agreed = catalog.capability(pack, cap).agreed_availability
    return round(max(0.0, agreed - realised), 4)


def data_coverage_gap(state: TeamState, pack: Casepack, rule: WatchRule) -> float:
    """The share of the capability's required entity-levels it cannot see.

    `gap = unmet_required / total_required`, where a required entity is met iff some serving
    node owns it at a level at least as fine as required (contract-spec section 4.5). Zero
    required entities -> 0.0; no serving path -> 0.0 (decision 4).
    """
    cap = rule.capability
    reqs = catalog.required_entities(pack, cap)
    if not reqs:
        return 0.0
    path = _serving_path(state, pack, cap)
    if path is None:
        return 0.0
    unmet = 0
    for entity_key, level, order in reqs:
        owners = graph.owner_nodes(state, cap, entity_key, level, order)
        if not owners:
            unmet += 1
    return round(unmet / len(reqs), 4)


#: The closed v1 metric vocabulary (1.5 spec section 4, decision 6). Iteration order is fixed.
METRICS: dict[str, Callable[[TeamState, Casepack, WatchRule], float | bool]] = {
    "capacity_utilisation": capacity_utilisation,
    "rollout_without_support": rollout_without_support,
    "missing_identity_access": missing_identity_access,
    "availability_shortfall": availability_shortfall,
    "data_coverage_gap": data_coverage_gap,
}


def metric_value(rule: WatchRule, state: TeamState, pack: Casepack) -> float | bool:
    """Evaluate `rule.metric` against the snapshot; raise `UnknownMetricError` on a bad key."""
    fn = METRICS.get(rule.metric)
    if fn is None:
        raise UnknownMetricError(rule.metric)
    return fn(state, pack, rule)
