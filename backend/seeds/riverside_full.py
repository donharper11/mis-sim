"""The `--full` six-round seed (spec section 5.5) -- one command, clean DB -> complete demo.

This supersedes the hand-authored `--with-signals` history: it populates the `signal` table by
running the REAL `ledger.advance_ledger` transition across six rounds (spec section 5.2 step 10),
so the persisted ledger is computed, not stubbed (GOVERNANCE section 4.9). Every RoundResult is
computed by the real engine from the seeded estate; nothing is asserted alongside the result.

It is a coherent Riverside playthrough (cost leadership): the order system runs near capacity in
R2 (ord_cap_01 warns), the team scales it in R3 (a `scale_node` action CLEARS ord_cap_01 before
any outage fires -> credited), a warehouse system goes live unsupported in R3 (wh_rollout_01
fires), central sign-on is missing until R4 (sec_identity_01 open, then cleared by an add_node).
So at R3 the ledger projects to the same SignalState pattern the 1.4 pin depends on -- ord_cap
credited, wh_rollout & sec_identity un-credited, all actionable (spec section 5.5, I10).

The estate for each round is authored seed data (the post-decision-sheet state); the runner then
runs the fixed resolution order over it and writes the immutable RoundResult. The four
round-evolution inputs (action_history, available_funds_by_round, debt_ratio_by_capability,
ArchNode.placement) are derived by the runner/snapshot from the seeded decision sheet + estate.
"""

from __future__ import annotations

from dataclasses import replace

from sqlalchemy.orm import Session

import seeds.riverside_r3 as r3
from app.casepack.models import Casepack
from app.round import models as m
from app.round.runner import RoundRunner
from app.seed.demo import load_scenario

INSTANCE_ID = 1
TEAM_ID = 1
STRATEGY = "cost_leadership"

#: order_app throughput per round -> capacity_utilisation against demand_curve
#: [6000,6600,12000,15000,18000,22000]: R2 warns (6600/8000=0.825), the R3 scale clears it.
ORDER_THROUGHPUT_BY_ROUND = {1: 8000.0, 2: 8000.0, 3: 16000.0, 4: 20000.0, 5: 24000.0, 6: 30000.0}

#: opex run-rate targets (the ratchet): opening 47000 (pack.yaml), then the pinned R3 58300 and
#: the pack review's run_rate_after 62200, rising as the estate grows. Distributed across the
#: round's live nodes so opex_runrate is RECOMPUTED as their sum, never accumulated (I7).
OPEX_TARGET_BY_ROUND = {1: 47000, 2: 53000, 3: 58300, 4: 62200, 5: 66000, 6: 70000}


# --------------------------------------------------------------------------------------
# Per-round estate assembly (authored seed data), based on the riverside_r3 estate.
# --------------------------------------------------------------------------------------
def _identity_node(round: int) -> dict:
    """Central sign-on -- present from R4 (the add_node that clears sec_identity_01)."""
    return dict(
        key="central_sign_on", roles_filled=["identity_access"], availability=0.99,
        installed_round=4, service_life_rounds=6, serves=["firm_infrastructure"],
        throughput=None, owns_entities=[["user_account", "named_user"]], placement="saas",
        opex_contribution=0,
    )


def _nodes_for_round(round: int) -> list[dict]:
    nodes: list[dict] = []
    for n in r3._nodes():
        throughput = n.throughput
        if n.key == "order_app":
            throughput = ORDER_THROUGHPUT_BY_ROUND[round]
        nodes.append(dict(
            key=n.key, roles_filled=list(n.roles_filled), availability=n.availability,
            installed_round=n.installed_round, service_life_rounds=n.service_life_rounds,
            serves=list(n.serves), throughput=throughput,
            owns_entities=[list(e) for e in n.owns_entities],
            placement=("on_prem" if n.throughput is not None else None),
            opex_contribution=0,
        ))
    if round >= 4:
        nodes.append(_identity_node(round))
    _distribute_opex(nodes, OPEX_TARGET_BY_ROUND[round])
    return nodes


def _distribute_opex(nodes: list[dict], target: int) -> None:
    """Split the round's opex target across its live nodes so opex_runrate == sum(contributions)
    (I7: recomputed from live nodes, never a running total). Deterministic: even share, remainder
    to the first node."""
    if not nodes:
        return
    share = target // len(nodes)
    for nd in nodes:
        nd["opex_contribution"] = share
    nodes[0]["opex_contribution"] += target - share * len(nodes)


def _deployments_for_round(round: int) -> list[dict]:
    deployments: list[dict] = []
    for d in r3._deployments():
        if d.key == "dep_centraline":
            # The warehouse system: absent in R1, live-unsupported from R2 (so wh_rollout_01's two
            # order_fulfilment events consume the O2 slots and SUPPRESS pos_support_ending -- which
            # otherwise fires ord_cap_01 the moment it warns, denying the clear-before-fire window),
            # trained from R4 (add_training clears it).
            if round < 2:
                continue
            if round >= 4:
                d = replace(d, trained_count=28, ever_trained=True, process="partial", adoption=0.55)
        deployments.append(dict(
            key=d.key, catalog_key=d.catalog_key, org_unit=d.org_unit,
            people_affected=d.people_affected, trained_count=d.trained_count, process=d.process,
            adoption=d.adoption, ever_trained=d.ever_trained, serves=list(d.serves),
            is_primary_for=d.is_primary_for, initiated=d.initiated, abandoned=d.abandoned,
        ))
    return deployments


def _decision_lines_for_round(round: int) -> list[dict]:
    """The scripted decision sheet per round (spec build step 7). `action_type` is set on the
    lines that perform a signal-clearing engine action (the ActionRecord source, decision 9)."""
    # Every round carries a maintenance-tagged line (portfolio discipline's maintenance floor,
    # management.py) and spends across a few capabilities (strategic-alignment cosine), so the
    # Management term is earned rather than zeroed -- mirroring the pinned round's decision shape.
    def maint() -> list[dict]:
        return [
            dict(key=f"d_r{round}_store_maint", category="application", capability="store_operations",
                 capex=40000, rgt_tag="run", is_maintenance=True),
            dict(key=f"d_r{round}_finance_maint", category="application", capability="financial_reporting",
                 capex=18000, rgt_tag="run", is_maintenance=True),
        ]

    sheets: dict[int, list[dict]] = {
        1: maint() + [
            dict(key="d_r1_order_platform", category="platform_service", capability="order_fulfilment",
                 capex=40000, rgt_tag="grow"),
            dict(key="d_r1_marketing", category="application", capability="marketing_sales",
                 capex=20000, rgt_tag="transform"),
        ],
        2: maint() + [
            dict(key="d_r2_order_platform", category="platform_service", capability="order_fulfilment",
                 capex=40000, rgt_tag="grow"),
            dict(key="d_r2_marketing", category="application", capability="marketing_sales",
                 capex=20000, rgt_tag="transform"),
        ],
        3: maint() + [
            dict(key="d_r3_order_scale", category="platform_service", capability="order_fulfilment",
                 capex=98000, rgt_tag="grow", action_type="scale_node", target_key="order_app"),
            dict(key="d_r3_order_training", category="training", capability="order_fulfilment",
                 capex=34000, rgt_tag="grow", action_type="add_training", target_key="order_mgmt_v42"),
            dict(key="d_r3_challenge", category="event_response", capability="order_fulfilment",
                 capex=12000, rgt_tag="run", action_type="fund_response", target_key="warehouse_rollout_gap"),
        ],
        4: maint() + [
            dict(key="d_r4_wh_training", category="training", capability="order_fulfilment",
                 capex=34000, rgt_tag="grow", action_type="add_training", target_key="centraline_im7"),
            dict(key="d_r4_identity", category="platform_service", capability="firm_infrastructure",
                 capex=40000, rgt_tag="transform", action_type="add_node", target_key="central_sign_on"),
        ],
        5: maint() + [
            dict(key="d_r5_order_scale", category="platform_service", capability="order_fulfilment",
                 capex=60000, rgt_tag="grow", action_type="scale_node", target_key="order_app"),
        ],
        6: maint() + [
            dict(key="d_r6_order_scale", category="platform_service", capability="order_fulfilment",
                 capex=60000, rgt_tag="grow", action_type="scale_node", target_key="order_app"),
        ],
    }
    return sheets[round]


def _tco_forecasts_for_round(round: int) -> list[dict]:
    """A small TCO forecast-vs-actual set so the RoundResult's tco_variance is populated
    (spec section 5.3). Forecast is the sheet's declared capex; actual is what the estate cost."""
    committed = sum(l["capex"] for l in _decision_lines_for_round(round))
    return [dict(item="round_capex", forecast=committed, actual=committed)]


# --------------------------------------------------------------------------------------
# Seeding + running the full game.
# --------------------------------------------------------------------------------------
def _wipe_instance(session: Session) -> None:
    for model in m.ALL_TABLES:
        session.query(model).filter(
            model.instance_id == INSTANCE_ID, model.team_id == TEAM_ID
        ).delete(synchronize_session=False)
    session.flush()


def _seed_round_estate(session: Session, pack: Casepack, round: int) -> None:
    for nd in _nodes_for_round(round):
        session.add(m.ArchNodeRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round, **nd))
    for e in r3._edges():
        session.add(m.ArchEdgeRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
                                  src=e.src, dst=e.dst, kind=e.kind))
    for dp in _deployments_for_round(round):
        session.add(m.DeploymentOrgStateRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round, **dp))
    for u in r3._org_units():
        session.add(m.OrgUnitRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
                                 key=u.key, headcount=0, resistance=u.resistance))
    for g in r3._governance():
        session.add(m.GovernanceStateRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
                                         capability=g.capability, owner_assigned=g.owner_assigned,
                                         sponsor_assigned=g.sponsor_assigned))
    staff = r3.build_team_state().staff
    session.add(m.ItStaffRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
                             staff_fte=staff.staff_fte, load_fte=staff.load_fte))
    for p in r3._policy_decisions():
        session.add(m.PolicyDecisionRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
                                        policy=p.policy, selected=p.selected,
                                        actively_decided=p.actively_decided))
    for sa in r3._stakeholder_alignments():
        session.add(m.StakeholderAlignmentRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
                                              stakeholder=sa.stakeholder, alignment=sa.alignment,
                                              cares_about=list(sa.cares_about)))
    for dl in _decision_lines_for_round(round):
        session.add(m.DecisionLineRow(
            instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round,
            key=dl["key"], category=dl["category"], capability=dl.get("capability"),
            capex=dl.get("capex", 0), rgt_tag=dl.get("rgt_tag", "run"),
            is_maintenance=dl.get("is_maintenance", False),
            action_type=dl.get("action_type"), target_key=dl.get("target_key"),
        ))
    for tco in _tco_forecasts_for_round(round):
        session.add(m.TcoForecastRow(instance_id=INSTANCE_ID, team_id=TEAM_ID, round=round, **tco))
    session.flush()


def run_full_game(session: Session, pack: Casepack | None = None) -> list[dict]:
    """Seed and run the six-round game; returns the six RoundResult payloads. Idempotent for the
    instance: it wipes instance 1 / team 1 first, so a clean DB and a re-run both produce the
    same six immutable results."""
    if pack is None:
        pack, _ = load_scenario("riverside_r3")

    _wipe_instance(session)
    session.add(m.TeamStateRow(
        instance_id=INSTANCE_ID, team_id=TEAM_ID, current_round=1, declared_strategy=STRATEGY,
        declared_strategy_round=pack.metadata.initial_state.declared_strategy_round,
        cash=0, opex_runrate=pack.metadata.budget.opening_opex,
    ))
    session.flush()

    runner = RoundRunner(session, pack, INSTANCE_ID, TEAM_ID)
    results: list[dict] = []
    for round in range(1, pack.metadata.rounds + 1):
        _seed_round_estate(session, pack, round)
        runner.lock(round)
        results.append(runner.advance(round))
    session.commit()
    return results
