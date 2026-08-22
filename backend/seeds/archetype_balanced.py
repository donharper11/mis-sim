"""Archetype: BALANCED -- a coherent strategy, proportionate Tech/Org/Mgmt, acts on signals
(spec section 5.1).

What it must demonstrate: **the intended good play.** It should score best. This is exactly the
``seeds/riverside_full.py`` six-round playthrough (cost leadership): a scaled estate, training that
keeps pace, and ``scale_node`` / ``add_training`` / ``fund_response`` / ``add_node`` action lines
that clear signals before they fire. Reusing that proven playthrough (rather than re-authoring it)
keeps the "good play" identical to the one the round-runner already ships and the 1.4 pin depends
on -- it runs here on its own ``(instance_id, team_id)``.

Everything here is authored seed data; the engine computes the terms from it. Nothing is asserted.
"""

from __future__ import annotations

import seeds.archetype_base as base
import seeds.riverside_full as full


class Balanced(base.Archetype):
    key = "balanced"
    label = "Balanced"
    instance_id = 13
    team_id = 1
    strategy = full.STRATEGY  # cost_leadership -- the coherent riverside_full playthrough

    def nodes(self, round: int) -> list[dict]:
        return full._nodes_for_round(round)

    def deployments(self, round: int) -> list[dict]:
        return full._deployments_for_round(round)

    def governance(self, round: int) -> list[dict]:
        return base.r3_governance_dicts()  # the exact riverside_full / 1.4-pin governance shape

    def policy(self, round: int) -> list[dict]:
        return base.attentive_policy_dicts()  # opened the policy screen, decided every switch

    def decision_lines(self, round: int) -> list[dict]:
        return full._decision_lines_for_round(round)

    def tco(self, round: int) -> list[dict]:
        return full._tco_forecasts_for_round(round)


ARCHETYPE = Balanced()
