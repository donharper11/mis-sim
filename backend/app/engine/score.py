"""The scorer: composes the three terms per capability and rolls the firm up.

    Realised Value = Technology Capability x Organisational Readiness x Management Quality

Multiplication across the three terms, plain product, never a geometric mean
(settled decision 2, invariant I6). A zero in any term zeroes realised value
(invariant I7) -- that is Laudon's complementary-assets argument made mechanical.

Every capability, every round, emits a decomposition record naming which factor
throttled it (spec 5.6). A number without its decomposition is not a deliverable.

CLI: `python -m app.engine.score <scenario>` prints the record and the pinned line.
This module is pure with respect to scoring; the CLI wrapper reads its inputs
through the casepack loader and the seed builder, which live outside the engine
package, so the engine itself performs no I/O (invariant I2).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any

from app.casepack.models import Casepack
from app.engine import technology as tech_mod
from app.engine import organisation as org_mod
from app.engine import management as mgmt_mod
from app.engine import rollup as rollup_mod
from app.engine.state import TeamState


@dataclass
class CapabilityScore:
    capability: str
    realised: float
    terms: dict[str, float]
    throttle: str
    sub_factors: dict[str, dict[str, float]]
    evidence: dict[str, Any]
    spofs: list[str] = field(default_factory=list)


def score_capability(
    pack: Casepack, state: TeamState, cap_key: str, firm: mgmt_mod.FirmManagement
) -> CapabilityScore:
    t = tech_mod.technology(pack, state, cap_key)
    o = org_mod.organisation(state, cap_key)
    m = mgmt_mod.management(state, cap_key, firm)

    tech, org, mgmt = t.value, o.value, m.value
    realised = tech * org * mgmt  # invariant I6: plain product across the three terms

    terms = {"tech": round(tech, 6), "org": round(org, 6), "mgmt": round(mgmt, 6)}
    throttle = min(terms, key=terms.get)  # type: ignore[arg-type]

    return CapabilityScore(
        capability=cap_key,
        realised=round(realised, 6),
        terms=terms,
        throttle=throttle,
        sub_factors={"tech": t.sub_factors, "org": o.sub_factors, "mgmt": m.sub_factors},
        evidence={"tech": t.evidence, "org": o.evidence, "mgmt": m.evidence},
        spofs=t.spofs,
    )


def decomposition_record(cs: CapabilityScore) -> dict[str, Any]:
    """The structure spec 5.6 pins: capability, realised, terms, throttle,
    sub_factors, evidence, spofs."""
    return {
        "capability": cs.capability,
        "realised": cs.realised,
        "terms": cs.terms,
        "throttle": cs.throttle,
        "sub_factors": cs.sub_factors,
        "evidence": cs.evidence,
        "spofs": cs.spofs,
    }


@dataclass
class TeamScore:
    round: int
    capabilities: list[CapabilityScore]
    firm_score: float
    balanced_scorecard: rollup_mod.BalancedScorecard
    stakeholder_satisfaction: list[rollup_mod.StakeholderSatisfaction]

    def record(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "firm_score": self.firm_score,
            "capabilities": [decomposition_record(c) for c in self.capabilities],
            "balanced_scorecard": {
                "financial": self.balanced_scorecard.financial,
                "customer": self.balanced_scorecard.customer,
                "internal_process": self.balanced_scorecard.internal_process,
                "learning_growth": self.balanced_scorecard.learning_growth,
                "financial_partial": self.balanced_scorecard.financial_partial,
            },
            "stakeholder_satisfaction": [
                {
                    "stakeholder": s.stakeholder,
                    "alignment": s.alignment,
                    "realised_in_scope": s.realised_in_scope,
                    "satisfaction": s.satisfaction,
                    "cares_about": s.cares_about,
                }
                for s in self.stakeholder_satisfaction
            ],
        }


def score_team(pack: Casepack, state: TeamState) -> TeamScore:
    firm = mgmt_mod.firm_management(pack, state)
    scores = [score_capability(pack, state, c.key, firm) for c in pack.capabilities]

    realised = {c.capability: c.realised for c in scores}
    tech_subs = {c.capability: c.sub_factors["tech"] for c in scores}
    org_subs = {c.capability: c.sub_factors["org"] for c in scores}
    mgmt_subs = {c.capability: c.sub_factors["mgmt"] for c in scores}

    weights: dict[str, float] = {}
    for s in pack.strategies:
        if s.key == state.declared_strategy:
            weights = dict(s.capability_weights)
            break

    bsc = rollup_mod.balanced_scorecard(realised, tech_subs, org_subs, mgmt_subs, weights)
    fscore = rollup_mod.firm_score(pack, state.declared_strategy, realised)
    sat = rollup_mod.stakeholder_satisfaction(state, realised)

    return TeamScore(
        round=state.round,
        capabilities=scores,
        firm_score=fscore,
        balanced_scorecard=bsc,
        stakeholder_satisfaction=sat,
    )


# --------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------

def _main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.stderr.write("usage: python -m app.engine.score <scenario>\n")
        return 2
    scenario = argv[0]
    # Imported, not read here: the loader and the seed builder live outside the
    # engine package, keeping this module free of I/O (invariant I2).
    from app.seed.demo import load_scenario

    pack, state = load_scenario(scenario)
    result = score_team(pack, state)

    print(json.dumps(result.record(), indent=2))

    target = next((c for c in result.capabilities if c.capability == "order_fulfilment"), None)
    if target is not None:
        t = target.terms
        print("")
        print(
            f"scenario {scenario}: order_fulfilment "
            f"tech {t['tech']:.3f} org {t['org']:.3f} mgmt {t['mgmt']:.3f} "
            f"realised {target.realised:.3f} throttle {target.throttle}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
