"""Runtime semantics for all eleven event-precondition types (contract-spec section 6).

Each type is total: it returns a bool, or -- for the two inputs 1.6 has not yet supplied --
raises `MissingRoundInputError` rather than silently reading FALSE. Boundary direction is
frozen per type (strict `>`, strict `<`, `>=`, or `==` as the table specifies). The reference pack uses
only `signal_open`; the other ten are exercised by synthetic fixtures.
"""

from __future__ import annotations

from app.casepack.models import Casepack, EventPrecondition
from app.engine import graph, metrics
from app.engine.management import _resolve_policy_decisions
from app.engine.state import TeamState

_SEVERITY_RANK: dict[str, int] = {"warning": 0, "critical": 1}


class MissingRoundInputError(Exception):
    """Raised when a precondition needs a 1.6 round-evolution input the snapshot does not carry.

    Never a silent FALSE: a precondition that cannot be evaluated must say so, not read as
    unmet (contract-spec section 6, `debt_above` / `placement_count`).
    """


def _capacity_utilisation(pc: EventPrecondition, state: TeamState, pack: Casepack) -> float:
    # A synthetic threshold rule so the shared metric body computes demand / capacity.
    from app.casepack.models import WatchRule

    rule = WatchRule(
        key="_pc", capability=pc.capability, metric="capacity_utilisation", cleared_by=[],
        provenance={"source": "AUTHORED", "note": "synthetic precondition probe"},
    )
    return float(metrics.capacity_utilisation(state, pack, rule))


def _policy_contradiction(pc: EventPrecondition, state: TeamState, pack: Casepack) -> bool:
    """Two switches on opposite halves of their ordinal spread (contract-spec section 6.1).

    The `< 2`-option guard runs BEFORE any division, so a one-option (`n == 0`) or legacy
    zero-option policy can never divide by zero -- it returns FALSE (no expressible spread of
    positions cannot be a contradiction).
    """
    by_key = {p.key: p for p in pack.policies}
    pol_a = by_key.get(pc.policy)
    pol_b = by_key.get(pc.other_policy)
    if pol_a is None or pol_b is None:
        return False
    if len(pol_a.options) < 2 or len(pol_b.options) < 2:
        return False  # guard: no division on n == 0
    resolved = _resolve_policy_decisions(pack, state)
    sel_a, _ = resolved[pol_a.key]
    sel_b, _ = resolved[pol_b.key]
    i_a = list(pol_a.options).index(sel_a)
    i_b = list(pol_b.options).index(sel_b)
    n_a = len(pol_a.options) - 1
    n_b = len(pol_b.options) - 1
    a_permissive = (i_a / n_a) < 0.5
    b_permissive = (i_b / n_b) < 0.5
    return a_permissive != b_permissive


def evaluate_precondition(
    pc: EventPrecondition, state: TeamState, pack: Casepack, ledger: tuple = ()
) -> bool:
    """Evaluate one precondition against the round-close snapshot and open ledger."""
    t = pc.type

    if t == "signal_open":
        required = _SEVERITY_RANK[pc.severity]
        for s in ledger:
            if s.key == pc.signal and s.status == "open" and _SEVERITY_RANK[s.severity] >= required:
                return True
        return False

    if t == "demand_exceeds_capacity":
        return _capacity_utilisation(pc, state, pack) > pc.ratio

    if t == "adoption_below":
        dep = state.primary_deployment(pc.capability)
        if dep is None:
            return False
        return dep.adoption < pc.ratio

    if t == "staffing_over":
        if state.staff.staff_fte == 0:
            return True  # any load over zero capacity is over
        return (state.staff.load_fte / state.staff.staff_fte) > pc.ratio

    if t == "debt_above":
        if state.debt_ratio_by_capability is None:
            raise MissingRoundInputError("debt_ratio_by_capability")
        return state.debt_ratio_by_capability.get(pc.capability, 0.0) > pc.ratio

    if t == "node_is_spof":
        return pc.node in graph.articulation_points(state)

    if t == "entity_unowned":
        for node in state.nodes:
            for owned_entity, _level in node.owns_entities:
                if owned_entity == pc.entity:
                    return False
        return True

    if t == "placement_count":
        if all(n.placement is None for n in state.nodes) and state.nodes:
            raise MissingRoundInputError("placement")
        count = sum(1 for n in state.nodes if n.placement == pc.placement)
        return count >= pc.count

    if t == "policy_contradiction":
        return _policy_contradiction(pc, state, pack)

    if t == "sponsor_unassigned":
        gov = state.governance_for(pc.capability)
        if gov is None:
            return True  # no governance row -> unsponsored
        return not gov.sponsor_assigned

    if t == "round_equals":
        return state.round == pc.round

    raise KeyError(f"unknown precondition type {t!r}")
