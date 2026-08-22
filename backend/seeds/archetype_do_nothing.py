"""Archetype: DO NOTHING -- declares a strategy, then spends nothing (spec section 5.1).

What it must demonstrate: **the floor.** A static minimal estate that ages -- no new nodes,
training stays 0, no owners assigned. As the rounds pass the order system falls behind rising
demand (capacity), the estate ages past its service life (currency, EOL), signals fire unanswered,
and debt accrues. With no training the Organisation term is zero, so realised value floors.

Everything here is authored seed data; the engine computes the terms from it. Nothing is asserted.
"""

from __future__ import annotations

import seeds.archetype_base as base
import seeds.riverside_r3 as r3


class DoNothing(base.Archetype):
    key = "do_nothing"
    label = "Do Nothing"
    instance_id = 11
    team_id = 1
    strategy = "cost_leadership"

    def nodes(self, round: int) -> list[dict]:
        # The R1 estate, frozen. installed_round is kept fixed, so as `round` advances the estate
        # ages (currency falls, nodes pass end-of-life); throughput is kept static, so the order
        # system falls behind the rising demand curve (capacity falls). No node is ever added.
        nodes = [base.node_dict(n) for n in r3._nodes()]
        base.distribute_opex(nodes, 47000)  # opening opex; no new spend raises it
        return nodes

    def deployments(self, round: int) -> list[dict]:
        # The rollouts exist but nobody is ever trained on them: training 0, process unchanged,
        # never trained -> the Organisation term (geomean) is crushed to zero, and follow-through
        # is dragged by deployed-never-trained rollouts.
        return [
            base.deployment_dict(
                d, trained_count=0, process="unchanged", adoption=0.1, ever_trained=False
            )
            for d in r3._deployments()
        ]

    def governance(self, round: int) -> list[dict]:
        return base.governance_dicts(owners=False)  # no owners assigned

    def policy(self, round: int) -> list[dict]:
        return []  # never opened the information-policy screen (policy_discipline at its floor)

    def decision_lines(self, round: int) -> list[dict]:
        return []  # spends nothing


ARCHETYPE = DoNothing()
