"""Archetype: OVERSPENDER -- funds everything generously, ignores strategy alignment
(spec section 5.1).

What it must demonstrate: **punished by cost efficiency and portfolio discipline, not by outcomes.**
So its estate, training and signal responses match the balanced play (the ``riverside_full``
playthrough) -- Technology, Organisation and responsiveness are held at the balanced level, the
outcomes are fine. What differs is the *spend pattern*: capital sprayed across every capability,
weighted toward the differentiation capabilities the declared cost-leadership strategy does NOT
prize, transform-heavy, with a thin maintenance floor. That drags strategic alignment and portfolio
discipline (concentration, the R/G/T mix, the maintenance floor) -- and only those -- so realised
value lands below the balanced play. The punishment is in the Management discipline factors, not in
Tech or Org.

Holding the estate and responses at the balanced level isolates exactly the variable the spec says
this archetype tests. Everything is authored seed data; the engine computes the terms. Nothing is
asserted.
"""

from __future__ import annotations

import seeds.archetype_base as base
import seeds.riverside_full as full


class Overspender(base.Archetype):
    key = "overspender"
    label = "Overspender"
    instance_id = 14
    team_id = 1
    strategy = full.STRATEGY  # declares cost_leadership -- the spend below does not match it

    # Estate, training, governance, policy held at the balanced level (the riverside_full shape),
    # so the only thing that differs from balanced is the spend pattern below.
    def nodes(self, round: int) -> list[dict]:
        return full._nodes_for_round(round)

    def deployments(self, round: int) -> list[dict]:
        return full._deployments_for_round(round)

    def governance(self, round: int) -> list[dict]:
        return base.r3_governance_dicts()

    def policy(self, round: int) -> list[dict]:
        return base.attentive_policy_dicts()

    def decision_lines(self, round: int) -> list[dict]:
        # (a) Signal responses mirroring the balanced play, so responsiveness is held at the
        #     balanced level (kept modest in capex -- the estate above supplies the capacity;
        #     these lines supply the ActionRecord that clears the signal).
        responses: dict[int, list[dict]] = {
            3: [
                dict(key=f"d_r{round}_scale", category="platform_service",
                     capability="order_fulfilment", capex=20000, rgt_tag="grow",
                     action_type="scale_node", target_key="order_app"),
                dict(key=f"d_r{round}_train_order", category="training",
                     capability="order_fulfilment", capex=20000, rgt_tag="grow",
                     action_type="add_training", target_key="order_mgmt_v42"),
                dict(key=f"d_r{round}_response", category="event_response",
                     capability="order_fulfilment", capex=12000, rgt_tag="run",
                     action_type="fund_response", target_key="warehouse_rollout_gap"),
            ],
            4: [
                dict(key=f"d_r{round}_train_wh", category="training",
                     capability="order_fulfilment", capex=20000, rgt_tag="grow",
                     action_type="add_training", target_key="centraline_im7"),
                dict(key=f"d_r{round}_identity", category="platform_service",
                     capability="firm_infrastructure", capex=20000, rgt_tag="transform",
                     action_type="add_node", target_key="central_sign_on"),
            ],
            5: [dict(key=f"d_r{round}_scale", category="platform_service",
                     capability="order_fulfilment", capex=20000, rgt_tag="grow",
                     action_type="scale_node", target_key="order_app")],
            6: [dict(key=f"d_r{round}_scale", category="platform_service",
                     capability="order_fulfilment", capex=20000, rgt_tag="grow",
                     action_type="scale_node", target_key="order_app")],
        }

        # (b) The misaligned overlay every round: large capital on the differentiation capabilities
        #     (customer insight / marketing / service) that cost leadership does not prize, transform-
        #     heavy, with only a thin maintenance line. This is what the discipline factors punish.
        overlay = [
            dict(key=f"d_r{round}_customer", category="application",
                 capability="customer_insight", capex=48000, rgt_tag="transform"),
            dict(key=f"d_r{round}_marketing", category="application",
                 capability="marketing_sales", capex=44000, rgt_tag="transform"),
            dict(key=f"d_r{round}_service", category="application",
                 capability="service", capex=40000, rgt_tag="grow"),
            dict(key=f"d_r{round}_store_maint", category="application",
                 capability="store_operations", capex=10000, rgt_tag="run", is_maintenance=True),
        ]
        return responses.get(round, []) + overlay


ARCHETYPE = Overspender()
