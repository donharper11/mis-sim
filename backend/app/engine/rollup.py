"""Firm roll-up: weighted firm score, Balanced Scorecard, stakeholder satisfaction.

The BSC roll-up (design/03) is the presentation frame; it reads the same movements
the MOT engine already produced. Financial figures that need the cost ledger
(capex, opex run-rate, TCO variance) are 1.6's to supply -- the financial
perspective here is the cost-discipline proxy the engine *can* compute, and it is
marked partial in the record rather than fabricated.

Stakeholder satisfaction (spec 5.5, G6 layer 1) consumes realised value in exactly
one direction: alignment x realised value in the capabilities a stakeholder cares
about. It is an output, never fed back into the score -- that keeps the two engines
joined at one point and keeps the causal trace traceable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.casepack.models import Casepack
from app.engine.mathx import clamp, geomean
from app.engine.state import TeamState


@dataclass
class BalancedScorecard:
    financial: float
    customer: float
    internal_process: float
    learning_growth: float
    financial_partial: bool = True
    inputs: dict[str, Any] = field(default_factory=dict)


def firm_score(pack: Casepack, declared_strategy: str, realised: dict[str, float]) -> float:
    """Sum of realised(c) x strategy weight (spec 5.4)."""
    weights: dict[str, float] = {}
    for s in pack.strategies:
        if s.key == declared_strategy:
            weights = dict(s.capability_weights)
            break
    total = 0.0
    for cap, value in realised.items():
        total += value * weights.get(cap, 0.0)
    return round(total, 6)


def balanced_scorecard(
    realised: dict[str, float],
    tech_subs: dict[str, dict[str, float]],
    org_subs: dict[str, dict[str, float]],
    mgmt_subs: dict[str, dict[str, float]],
    weights: dict[str, float],
) -> BalancedScorecard:
    caps = list(realised)

    def wmean(fn) -> float:
        num = 0.0
        den = 0.0
        for c in caps:
            w = weights.get(c, 0.0) or (1.0 / len(caps))
            num += fn(c) * w
            den += w
        return num / den if den else 0.0

    # Customer: availability and unmet demand -> reliability x capacity per cap.
    customer = wmean(lambda c: geomean([tech_subs[c]["reliability"], tech_subs[c]["capacity"]]))
    # Internal process: realised value, coverage, integration, data adequacy.
    internal = wmean(lambda c: geomean([realised[c], tech_subs[c]["coverage"], tech_subs[c]["data_adequacy"]]) if realised[c] > 0 else 0.0)
    # Learning & growth: training, adoption, resistance, governance.
    learning = wmean(lambda c: geomean([
        org_subs[c]["training"] or 0.001,
        org_subs[c]["adoption"] or 0.001,
        org_subs[c]["resistance_inv"] or 0.001,
        mgmt_subs[c]["governance"] or 0.001,
    ]))
    # Financial (partial): the cost-discipline the engine can see without the ledger.
    any_cap = caps[0]
    financial = geomean([
        mgmt_subs[any_cap]["strategic_alignment"] or 0.001,
        mgmt_subs[any_cap]["portfolio_discipline"] or 0.001,
    ])

    return BalancedScorecard(
        financial=round(financial, 6),
        customer=round(customer, 6),
        internal_process=round(internal, 6),
        learning_growth=round(learning, 6),
        financial_partial=True,
        inputs={"perspective_scale": "0..1 computed rollup; multiply by 100 for a headline"},
    )


@dataclass
class StakeholderSatisfaction:
    stakeholder: str
    alignment: float
    realised_in_scope: float
    satisfaction: float
    cares_about: list[str]


def stakeholder_satisfaction(
    state: TeamState, realised: dict[str, float]
) -> list[StakeholderSatisfaction]:
    out: list[StakeholderSatisfaction] = []
    for sa in state.stakeholder_alignments:
        scoped = [realised.get(c, 0.0) for c in sa.cares_about]
        realised_in_scope = sum(scoped) / len(scoped) if scoped else 0.0
        out.append(
            StakeholderSatisfaction(
                stakeholder=sa.stakeholder,
                alignment=round(sa.alignment, 6),
                realised_in_scope=round(realised_in_scope, 6),
                satisfaction=round(clamp(sa.alignment * realised_in_scope), 6),
                cares_about=list(sa.cares_about),
            )
        )
    return out
