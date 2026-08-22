"""Archetype: ALL TECH, NO ORG -- buys the best of everything, funds zero training, assigns no
owners (spec section 5.1).

What it must demonstrate: **the sim's central lesson.** High Technology, collapsed Organisation.
The estate is rich and always current (fresh nodes, ample capacity), so the Technology term is
high; but with no training on any rollout the Organisation term is zero, and with no owners the
governance sub-factor of Management is zero -- and a plain product across the three terms zeroes
realised value. Capability bought without the complementary organisational assets delivers nothing
(Laudon), shown from a script.

Everything here is authored seed data; the engine computes the terms from it. Nothing is asserted.
"""

from __future__ import annotations

import seeds.archetype_base as base
import seeds.riverside_r3 as r3


class AllTechNoOrg(base.Archetype):
    key = "all_tech_no_org"
    label = "All Tech, No Org"
    instance_id = 12
    team_id = 1
    strategy = "cost_leadership"

    def nodes(self, round: int) -> list[dict]:
        # Buys the best of everything: every node installed this round (always current), the order
        # system given headroom above demand (no capacity ceiling), high availability. Technology
        # is high by construction.
        nodes = []
        for n in r3._nodes():
            throughput = base.UNCONSTRAINED if n.throughput is not None else None
            nodes.append(base.node_dict(
                n, installed_round=round, throughput=throughput, availability=max(n.availability, 0.99)
            ))
        base.distribute_opex(nodes, 60000 + 8000 * round)  # a heavy, growing platform run-rate
        return nodes

    def deployments(self, round: int) -> list[dict]:
        # Funds zero training: every rollout live, nobody trained, process unchanged. The
        # Organisation term collapses.
        return [
            base.deployment_dict(
                d, trained_count=0, process="unchanged", adoption=0.15, ever_trained=False
            )
            for d in r3._deployments()
        ]

    def governance(self, round: int) -> list[dict]:
        return base.governance_dicts(owners=False)  # assigns no owners

    def policy(self, round: int) -> list[dict]:
        return []  # no organisational discipline: the policy screen is left untouched

    def decision_lines(self, round: int) -> list[dict]:
        # Large capital across the technology estate every round, and NOT a dollar on training or
        # ownership. Kept within the per-round capex budget the runner validates against.
        return [
            dict(key=f"d_r{round}_platform", category="platform_service",
                 capability="order_fulfilment", capex=90000, rgt_tag="grow"),
            dict(key=f"d_r{round}_infra", category="platform_service",
                 capability="firm_infrastructure", capex=40000, rgt_tag="transform"),
            dict(key=f"d_r{round}_store_app", category="application",
                 capability="store_operations", capex=30000, rgt_tag="grow"),
        ]


ARCHETYPE = AllTechNoOrg()
