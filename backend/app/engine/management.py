"""Management Quality -- computed from the pattern of decisions (spec 5.3).

mgmt(c) = geomean(governance, strategic_alignment, portfolio_discipline,
                  signal_responsiveness, follow_through, stakeholder_alignment)

Nothing in the catalog raises any of these (invariant I4). Tech is bought, Org is
funded, this term is earned. O3 hybrid default: governance and stakeholder
alignment are per capability; strategic alignment, portfolio discipline, signal
responsiveness and follow-through are firm-wide and apply identically to each.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any

from app.casepack.models import Casepack, Strategy
from app.engine.mathx import clamp, geomean
from app.engine.state import TeamState


@dataclass
class FirmManagement:
    """The four firm-wide sub-factors, computed once per round."""

    strategic_alignment: float
    portfolio_discipline: float
    signal_responsiveness: float
    follow_through: float
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class MgmtResult:
    value: float
    sub_factors: dict[str, float]
    evidence: dict[str, Any] = field(default_factory=dict)


def _strategy(pack: Casepack, key: str) -> Strategy:
    for s in pack.strategies:
        if s.key == key:
            return s
    raise KeyError(f"strategy {key!r} not in pack")


def _spend_by_capability(state: TeamState) -> dict[str, float]:
    spend: dict[str, float] = {}
    for d in state.decisions:
        if d.capability is None:
            continue
        spend[d.capability] = spend.get(d.capability, 0.0) + d.capex
    return spend


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = sqrt(sum(v * v for v in a.values()))
    nb = sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return clamp(dot / (na * nb))


def _strategic_alignment(pack: Casepack, state: TeamState) -> tuple[float, dict[str, Any]]:
    strat = _strategy(pack, state.declared_strategy)
    spend = _spend_by_capability(state)
    value = _cosine(spend, dict(strat.capability_weights))
    return value, {"spend_by_capability": spend, "weights": dict(strat.capability_weights)}


def _portfolio_discipline(pack: Casepack, state: TeamState) -> tuple[float, dict[str, Any]]:
    strat = _strategy(pack, state.declared_strategy)
    spend = _spend_by_capability(state)
    total = sum(spend.values())

    # Concentration: Herfindahl of spend shares vs the strategy's expected value.
    if total > 0:
        hhi = sum((v / total) ** 2 for v in spend.values())
    else:
        hhi = 0.0
    expected = strat.expected_concentration
    concentration_score = clamp(1.0 - (abs(hhi - expected) / expected if expected else 0.0))

    # R/G/T mix vs target: 1 - total-variation distance between the two mixes.
    tag_spend: dict[str, float] = {"run": 0.0, "grow": 0.0, "transform": 0.0}
    grand = 0.0
    for d in state.decisions:
        if d.rgt_tag in tag_spend:
            tag_spend[d.rgt_tag] += d.capex
            grand += d.capex
    if grand > 0:
        actual = {k: v / grand for k, v in tag_spend.items()}
    else:
        actual = {k: 0.0 for k in tag_spend}
    target = {k.value: v for k, v in strat.target_rgt_mix.items()}
    tv = 0.5 * sum(abs(actual[k] - target.get(k, 0.0)) for k in tag_spend)
    rgt_score = clamp(1.0 - tv)

    # Maintenance floor: run-tagged / maintenance spend against the floor.
    maint = sum(d.capex for d in state.decisions if d.is_maintenance)
    maint_ratio = (maint / total) if total > 0 else 0.0
    floor = strat.maintenance_floor_pct
    maintenance_score = clamp(maint_ratio / floor) if floor > 0 else 1.0

    value = geomean([concentration_score, rgt_score, maintenance_score])
    detail = {
        "concentration": {"hhi": round(hhi, 4), "expected": expected, "score": round(concentration_score, 4)},
        "rgt": {"actual": {k: round(v, 4) for k, v in actual.items()}, "target": target, "score": round(rgt_score, 4)},
        "maintenance": {"ratio": round(maint_ratio, 4), "floor": floor, "score": round(maintenance_score, 4)},
    }
    return value, detail


def _signal_responsiveness(state: TeamState) -> tuple[float, dict[str, Any]]:
    actionable = [s for s in state.signals if s.actionable]
    if not actionable:
        return 1.0, {"actionable": 0, "acted": 0}
    acted = sum(1 for s in actionable if s.acted_before_fire)
    return acted / len(actionable), {"actionable": len(actionable), "acted": acted}


def _follow_through(state: TeamState) -> tuple[float, dict[str, Any]]:
    initiated = [d for d in state.deployments if d.initiated]
    if not initiated:
        return 1.0, {"initiated": 0}
    abandoned = sum(1 for d in initiated if d.abandoned)
    never_trained = sum(1 for d in initiated if not d.abandoned and not d.ever_trained)
    value = clamp(1.0 - (abandoned + never_trained) / len(initiated))
    return value, {
        "initiated": len(initiated),
        "abandoned": abandoned,
        "deployed_never_trained": never_trained,
    }


def firm_management(pack: Casepack, state: TeamState) -> FirmManagement:
    sa, sa_ev = _strategic_alignment(pack, state)
    pd, pd_ev = _portfolio_discipline(pack, state)
    sr, sr_ev = _signal_responsiveness(state)
    ft, ft_ev = _follow_through(state)
    return FirmManagement(
        strategic_alignment=round(sa, 6),
        portfolio_discipline=round(pd, 6),
        signal_responsiveness=round(sr, 6),
        follow_through=round(ft, 6),
        evidence={
            "strategic_alignment": sa_ev,
            "portfolio_discipline": pd_ev,
            "signal_responsiveness": sr_ev,
            "follow_through": ft_ev,
        },
    )


def _governance(state: TeamState, cap_key: str) -> float:
    g = state.governance_for(cap_key)
    if g is None:
        return 0.0
    return (int(g.owner_assigned) + int(g.sponsor_assigned)) / 2.0


def policy_switch_alignment(*_args: Any, **_kwargs: Any) -> float:
    """DEFERRED HOOK -- the information-policy-switch dimension of stakeholder
    alignment (spec 5.5, the by_decision / ideal_posture path over
    `PolicyOption.options`).

    PAUSED by the coordinator mid-build (2026-08-21): whether alignment against a
    policy's `ideal_posture` is an exact match or a distance along the options
    ordering -- and whether `PolicyOption.options` is ordinal or unordered -- is
    being reworked and independently re-audited. The design/07 section 3.5b
    "options is ordinal / distance" ruling is UNSETTLED and must NOT be encoded
    here. This hook exists so the policy path is a visible hole, never a silent
    guess: it is not called by the scoring path, and if it is called it raises
    rather than contribute a number.

    `_stakeholder_alignment` below scores only the capability-rollout dimension of
    section 5.5 (alignment x realised value in the capabilities a stakeholder cares
    about); it does not read `PolicyOption.options` at all.
    """
    raise NotImplementedError(
        "policy-switch alignment (spec 5.5 ideal_posture over PolicyOption.options) "
        "is paused pending rework and re-audit; do not encode an interpretation here"
    )


def _stakeholder_alignment(state: TeamState, cap_key: str) -> tuple[float, dict[str, Any]]:
    # Capability-rollout dimension only. The information-policy-switch dimension is
    # the deferred `policy_switch_alignment` hook above and is deliberately NOT
    # folded in -- the consumed `StakeholderDecisionAlignment.alignment` scalar is a
    # rollout-alignment input, not a policy-options computation.
    caring = [sa for sa in state.stakeholder_alignments if cap_key in sa.cares_about]
    if not caring:
        return 1.0, {"stakeholders": [], "policy_switch_dimension": "deferred"}
    value = sum(sa.alignment for sa in caring) / len(caring)
    return clamp(value), {
        "stakeholders": [(sa.stakeholder, round(sa.alignment, 4)) for sa in caring],
        "policy_switch_dimension": "deferred",
    }


def management(
    state: TeamState, cap_key: str, firm: FirmManagement
) -> MgmtResult:
    governance = _governance(state, cap_key)
    stakeholder, stake_ev = _stakeholder_alignment(state, cap_key)

    sub_factors = {
        "governance": round(governance, 6),
        "strategic_alignment": firm.strategic_alignment,
        "portfolio_discipline": firm.portfolio_discipline,
        "signal_responsiveness": firm.signal_responsiveness,
        "follow_through": firm.follow_through,
        "stakeholder_alignment": round(stakeholder, 6),
    }
    value = geomean(list(sub_factors.values()))
    evidence: dict[str, Any] = {"stakeholder_alignment": stake_ev}
    return MgmtResult(value=round(value, 6), sub_factors=sub_factors, evidence=evidence)
