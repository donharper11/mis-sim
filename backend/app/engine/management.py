"""Management Quality -- computed from the pattern of decisions (spec 5.3).

mgmt(c) = geomean(governance, strategic_alignment, portfolio_discipline,
                  signal_responsiveness, follow_through, stakeholder_alignment,
                  policy_alignment, policy_discipline)

Nothing in the catalog raises any of these (invariant I4). Tech is bought, Org is
funded, this term is earned. O3 hybrid default: governance and stakeholder
alignment are per capability; strategic alignment, portfolio discipline, signal
responsiveness, follow-through, and (added by the 1.4 closeout) policy alignment
and policy discipline are firm-wide and apply identically to each.

The 1.4 closeout added the last two sub-factors, closing the deliberately paused
information-policy path (register F4/E2): `policy_alignment` scores the team's
information-policy switch choices against stakeholder ideals as an asymmetric
ordinal distance over `PolicyOption.options` (design/07 3.5b), and
`policy_discipline` charges a team for leaving switches undecided. The existing six
inputs and their formulas are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any

from app.casepack.models import Casepack, Strategy
from app.engine.mathx import clamp, geomean
from app.engine.state import TeamState

#: Information-policy discipline floor (1.4 closeout decision 7). A team that never
#: opens the policy screen still scores this rather than zeroing the whole Management
#: term and hiding every other lesson. Hard-coded v1 calibration constant; 1.7's
#: harness owns revisiting it.
POLICY_DISCIPLINE_FLOOR = 0.25


@dataclass
class FirmManagement:
    """The firm-wide sub-factors, computed once per round.

    `policy_alignment` and `policy_discipline` are NEW frozen fields added by the
    1.4 closeout; the four above them are unchanged.
    """

    strategic_alignment: float
    portfolio_discipline: float
    signal_responsiveness: float
    follow_through: float
    policy_alignment: float
    policy_discipline: float
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
    pa, pa_ev = policy_switch_alignment(pack, state)
    pdis, pdis_ev = policy_discipline(pack, state)
    return FirmManagement(
        strategic_alignment=round(sa, 6),
        portfolio_discipline=round(pd, 6),
        signal_responsiveness=round(sr, 6),
        follow_through=round(ft, 6),
        policy_alignment=round(pa, 6),
        policy_discipline=round(pdis, 6),
        evidence={
            "strategic_alignment": sa_ev,
            "portfolio_discipline": pd_ev,
            "signal_responsiveness": sr_ev,
            "follow_through": ft_ev,
            "policy_alignment": pa_ev,
            "policy_discipline": pdis_ev,
        },
    )


def _governance(state: TeamState, cap_key: str) -> float:
    g = state.governance_for(cap_key)
    if g is None:
        return 0.0
    return (int(g.owner_assigned) + int(g.sponsor_assigned)) / 2.0


def _resolve_policy_decisions(
    pack: Casepack, state: TeamState
) -> dict[str, tuple[str | None, bool]]:
    """Resolve each pack policy to `(selected_value, actively_decided)`.

    Runtime `policy_decisions` win; any pack policy absent from them resolves to its
    authored `default` with `actively_decided=False` (closeout decision 6). Every
    broken scoring input raises before a score is returned (decision 9): a duplicate
    runtime decision, an unknown policy key, a selected value outside a policy's
    declared options, or a policy that needs a default for the null path and has none.
    """
    by_key = {p.key: p for p in pack.policies}
    resolved: dict[str, tuple[str | None, bool]] = {}
    seen: set[str] = set()

    for d in state.policy_decisions:
        if d.policy in seen:
            raise ValueError(f"duplicate runtime policy decision for {d.policy!r}")
        seen.add(d.policy)
        pol = by_key.get(d.policy)
        if pol is None:
            raise ValueError(f"policy decision references unknown policy {d.policy!r}")
        if pol.options and d.selected not in pol.options:
            raise ValueError(
                f"policy {d.policy!r} selected {d.selected!r} is not one of its "
                f"options {list(pol.options)}"
            )
        resolved[d.policy] = (d.selected, bool(d.actively_decided))

    for pol in pack.policies:
        if pol.key in resolved:
            continue
        if pol.options and pol.default is None:
            raise ValueError(
                f"policy {pol.key!r} declares options but has no default for the null "
                f"path (an untouched switch cannot resolve)"
            )
        resolved[pol.key] = (pol.default, False)

    return resolved


def _asymmetric_alignment(
    team_index: int, ideal_index: int, span: int
) -> tuple[float, str]:
    """The frozen ordinal formula (closeout decision 2). `span = n - 1`.

    `t == i` -> 1.0; `t < i` (more permissive than asked) pays the full normalized
    distance; `t > i` (stricter than asked) pays half. Overshooting an ideal always
    costs less than ignoring it by the same number of ordinal steps.
    """
    if team_index == ideal_index:
        return 1.0, "match"
    if span <= 0:
        # A single-option switch cannot express a distance; a mismatch is impossible
        # but is scored as a full miss rather than silently passing.
        return 0.0, ("too_permissive" if team_index < ideal_index else "stricter")
    if team_index < ideal_index:
        return clamp(1.0 - (ideal_index - team_index) / span), "too_permissive"
    return clamp(1.0 - 0.5 * (team_index - ideal_index) / span), "stricter"


def policy_switch_alignment(
    pack: Casepack, state: TeamState
) -> tuple[float, dict[str, Any]]:
    """Firm-wide information-policy preference alignment (spec 5.5 policy path).

    For every actual stakeholder in `pack.stakeholders`, resolve its archetype's
    policy-preference row; for every `by_decision` preference, score the team's
    chosen option against the stakeholder's ideal with the frozen asymmetric ordinal
    formula, and aggregate as a weighted arithmetic mean where
    `effective_weight = archetype.weight * by_decision[policy].weight` (decision 3).

    Stakeholders whose archetype has no policy row, and policies no stakeholder holds
    a view on, are absent from numerator and denominator -- not neutral rows. Total
    weight zero -> alignment 1.0 with `preferences: 0`. A preference naming an unknown
    policy or an ideal outside that policy's options raises (decision 9).
    """
    resolved = _resolve_policy_decisions(pack, state)
    by_key = {p.key: p for p in pack.policies}
    pref_domain = pack.preferences.get("policies")

    numerator = 0.0
    total_weight = 0.0
    rows: list[dict[str, Any]] = []

    if pref_domain is not None:
        for sh in pack.stakeholders:
            arow = pref_domain.defaults_by_archetype.get(sh.archetype)
            if not arow:
                continue  # archetype holds no policy view -> excluded (decision 3)
            arch_weight = float(arow.get("weight", 0.0))
            by_decision = arow.get("by_decision", {}) or {}
            for policy_key, pref in by_decision.items():
                pol = by_key.get(policy_key)
                if pol is None:
                    raise ValueError(
                        f"stakeholder {sh.key!r} preference names unknown policy "
                        f"{policy_key!r}"
                    )
                options = list(pol.options)
                ideal = pref["ideal_posture"]
                if ideal not in options:
                    raise ValueError(
                        f"stakeholder {sh.key!r} ideal_posture {ideal!r} for policy "
                        f"{policy_key!r} is not one of its options {options}"
                    )
                selected, _active = resolved[policy_key]
                if selected not in options:
                    raise ValueError(
                        f"team selection {selected!r} for policy {policy_key!r} is not "
                        f"one of its options {options}"
                    )
                team_index = options.index(selected)
                ideal_index = options.index(ideal)
                alignment, direction = _asymmetric_alignment(
                    team_index, ideal_index, len(options) - 1
                )
                weight = arch_weight * float(pref.get("weight", 0.0))
                numerator += alignment * weight
                total_weight += weight
                rows.append({
                    "stakeholder": sh.key,
                    "archetype": sh.archetype,
                    "policy": policy_key,
                    "selected": selected,
                    "ideal": ideal,
                    "team_index": team_index,
                    "ideal_index": ideal_index,
                    "direction": direction,
                    "alignment": round(alignment, 6),
                    "weight": round(weight, 6),
                })

    if total_weight == 0.0:
        return 1.0, {"preferences": 0, "total_weight": 0.0, "alignment": 1.0, "rows": []}

    value = numerator / total_weight
    return round(value, 6), {
        "preferences": len(rows),
        "total_weight": round(total_weight, 6),
        "alignment": round(value, 6),
        "rows": rows,
    }


def policy_discipline(
    pack: Casepack, state: TeamState
) -> tuple[float, dict[str, Any]]:
    """Firm-wide active information-policy discipline (closeout decision 7).

    Eligible policies `P` = pack policies with non-empty options; decided `D` = those
    actively decided in runtime state. `discipline = FLOOR + (1 - FLOOR) * |D|/|P|`,
    or 1.0 when there are no eligible policies. The floor keeps ignoring the screen
    costly without zeroing the whole Management term.
    """
    resolved = _resolve_policy_decisions(pack, state)
    eligible = [p.key for p in pack.policies if p.options]
    if not eligible:
        return 1.0, {
            "eligible": 0, "actively_decided": 0,
            "floor": POLICY_DISCIPLINE_FLOOR, "ratio": 1.0, "undecided": [],
        }
    decided = [k for k in eligible if resolved[k][1]]
    undecided = [k for k in eligible if not resolved[k][1]]
    ratio = len(decided) / len(eligible)
    value = POLICY_DISCIPLINE_FLOOR + (1.0 - POLICY_DISCIPLINE_FLOOR) * ratio
    return round(value, 6), {
        "eligible": len(eligible),
        "actively_decided": len(decided),
        "floor": POLICY_DISCIPLINE_FLOOR,
        "ratio": round(ratio, 6),
        "undecided": undecided,
    }


def _stakeholder_alignment(state: TeamState, cap_key: str) -> tuple[float, dict[str, Any]]:
    # Capability-rollout dimension only, and UNCHANGED by the 1.4 closeout (decision
    # 1, invariant C8): the consumed `StakeholderDecisionAlignment.alignment` scalar
    # is a rollout-alignment input, not a policy-options computation. The
    # information-policy-switch dimension is now scored separately and firm-wide by
    # `policy_switch_alignment`; the `policy_switch_dimension: deferred` marker below
    # stays byte-identical and still reads true of THIS per-capability scalar, which
    # deliberately excludes policy switches.
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
        "policy_alignment": firm.policy_alignment,
        "policy_discipline": firm.policy_discipline,
    }
    value = geomean(list(sub_factors.values()))
    # Firm-wide policy factors are computed once (firm_management) and applied
    # identically to every capability; their evidence rides along unchanged per
    # capability. Existing per-capability `stakeholder_alignment` evidence is
    # byte-identical (invariant C8); the two policy keys are the only additions.
    evidence: dict[str, Any] = {
        "stakeholder_alignment": stake_ev,
        "policy_alignment": firm.evidence.get("policy_alignment", {}),
        "policy_discipline": firm.evidence.get("policy_discipline", {}),
    }
    return MgmtResult(value=round(value, 6), sub_factors=sub_factors, evidence=evidence)
