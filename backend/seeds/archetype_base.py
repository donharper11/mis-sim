"""Shared machinery for the 1.7 calibration archetypes (spec section 5.1 / decision 6).

Each archetype is a seed builder in the shape of ``seeds/riverside_full.py``: per round it
authors the post-decision *estate* (nodes/edges/deployments/governance/staff/policy/stakeholder
rows) **and** a ``decision_line`` sheet, then the harness runs ``RoundRunner.advance`` over it --
the exact path ``--full`` exercises (spec section 13). The scores are computed by the real engine
from real DB rows (seed, not stub, GOVERNANCE section 4.9); the harness reads them back from
``RoundResult.payload``.

Live decision-sheet -> estate mutation is the ruled deferral ``1.6-A-002``: ``runner.advance``
reads the seed-authored estate (steps 2/4-6), so an archetype authors the estate directly. If/when
live mutation lands, archetypes migrate to sheet-only with no change to the harness read-back.

This base holds the parts every archetype shares -- the per-instance wipe (idempotent, so a
re-run and a clean DB produce the same results), the estate assembly, and the lock/advance loop --
so each ``archetype_*.py`` states only what makes it distinct. The four estate building blocks come
from ``seeds/riverside_r3.py`` (the reference architecture behind the 1.4 pin); an archetype varies
them to express its play.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

import seeds.riverside_r3 as r3
from app.casepack.models import Casepack
from app.round import models as m
from app.round.runner import RoundRunner

#: A throughput far above any round demand: a node that imposes no capacity ceiling.
UNCONSTRAINED = 10_000_000.0


# --------------------------------------------------------------------------------------
# Row-dict helpers -- convert the r3 reference dataclasses into the runner's row payloads,
# with per-archetype overrides.
# --------------------------------------------------------------------------------------
_UNSET = object()


def node_dict(
    n,
    *,
    installed_round=_UNSET,
    throughput=_UNSET,
    availability=_UNSET,
    placement=_UNSET,
    opex_contribution: int = 0,
) -> dict:
    """One ``ArchNodeRow`` payload from an r3 ``ArchNode``, with optional overrides."""
    return dict(
        key=n.key,
        roles_filled=list(n.roles_filled),
        availability=n.availability if availability is _UNSET else availability,
        installed_round=n.installed_round if installed_round is _UNSET else installed_round,
        service_life_rounds=n.service_life_rounds,
        serves=list(n.serves),
        throughput=n.throughput if throughput is _UNSET else throughput,
        owns_entities=[list(e) for e in n.owns_entities],
        placement=(
            ("on_prem" if n.throughput is not None else None)
            if placement is _UNSET
            else placement
        ),
        opex_contribution=opex_contribution,
    )


def distribute_opex(nodes: list[dict], target: int) -> None:
    """Split an opex target across the round's live nodes so ``opex_runrate == sum(contributions)``
    (I7: recomputed from live nodes, never a running total). Deterministic: even share, remainder
    to the first node -- the same rule ``seeds/riverside_full.py`` uses."""
    if not nodes:
        return
    share = target // len(nodes)
    for nd in nodes:
        nd["opex_contribution"] = share
    nodes[0]["opex_contribution"] += target - share * len(nodes)


def edge_dicts() -> list[dict]:
    return [dict(src=e.src, dst=e.dst, kind=e.kind) for e in r3._edges()]


def org_unit_dicts() -> list[dict]:
    return [dict(key=u.key, headcount=0, resistance=u.resistance) for u in r3._org_units()]


def stakeholder_dicts() -> list[dict]:
    return [
        dict(stakeholder=s.stakeholder, alignment=s.alignment, cares_about=list(s.cares_about))
        for s in r3._stakeholder_alignments()
    ]


def attentive_policy_dicts() -> list[dict]:
    """The r3 information-policy decisions: every switch actively decided (policy_discipline 1.0)."""
    return [
        dict(policy=p.policy, selected=p.selected, actively_decided=p.actively_decided)
        for p in r3._policy_decisions()
    ]


def deployment_dict(d, **overrides) -> dict:
    base = dict(
        key=d.key,
        catalog_key=d.catalog_key,
        org_unit=d.org_unit,
        people_affected=d.people_affected,
        trained_count=d.trained_count,
        process=d.process,
        adoption=d.adoption,
        ever_trained=d.ever_trained,
        serves=list(d.serves),
        is_primary_for=d.is_primary_for,
        initiated=d.initiated,
        abandoned=d.abandoned,
    )
    base.update(overrides)
    return base


def governance_dicts(*, owners: bool) -> list[dict]:
    """Governance rows for the r3 capabilities. ``owners=False`` assigns no owner/sponsor
    (the ``do_nothing`` / ``all_tech_no_org`` no-ownership case)."""
    caps = [g.capability for g in r3._governance()]
    return [
        dict(capability=c, owner_assigned=owners, sponsor_assigned=owners)
        for c in caps
    ]


def r3_governance_dicts() -> list[dict]:
    """The exact r3 governance rows (order fulfilment owner+sponsor, store operations owner only,
    finance owner+sponsor) -- the shape the riverside_full playthrough and the 1.4 pin use."""
    return [
        dict(capability=g.capability, owner_assigned=g.owner_assigned,
             sponsor_assigned=g.sponsor_assigned)
        for g in r3._governance()
    ]


# --------------------------------------------------------------------------------------
# The base archetype: identity + the lock/advance loop. Subclasses override the per-round
# builders below to express their play.
# --------------------------------------------------------------------------------------
class Archetype:
    #: machine key (used for grouping results; no case identity)
    key: str = ""
    #: instructor-readable label (I3: no raw engine key ever reaches the report)
    label: str = ""
    #: a distinct (instance_id, team_id) per archetype so the four neither collide nor leak
    instance_id: int = 0
    team_id: int = 1
    #: the declared strategy the play is judged against
    strategy: str = "cost_leadership"

    # -- per-round estate builders (override in subclasses) --------------------------
    def nodes(self, round: int) -> list[dict]:
        raise NotImplementedError

    def edges(self, round: int) -> list[dict]:
        return edge_dicts()

    def deployments(self, round: int) -> list[dict]:
        raise NotImplementedError

    def org_units(self, round: int) -> list[dict]:
        return org_unit_dicts()

    def governance(self, round: int) -> list[dict]:
        raise NotImplementedError

    def staff(self, round: int) -> dict:
        s = r3.build_team_state().staff
        return dict(staff_fte=s.staff_fte, load_fte=s.load_fte)

    def policy(self, round: int) -> list[dict]:
        return []

    def stakeholders(self, round: int) -> list[dict]:
        return stakeholder_dicts()

    def decision_lines(self, round: int) -> list[dict]:
        return []

    def tco(self, round: int) -> list[dict]:
        committed = sum(int(l.get("capex", 0)) for l in self.decision_lines(round))
        return [dict(item="round_capex", forecast=committed, actual=committed)]

    # -- seeding + running (shared) --------------------------------------------------
    def wipe(self, session: Session) -> None:
        """Tear the instance's rows down (idempotent, spec I4). A clean DB and a re-run both
        produce the same six immutable results."""
        for model in m.ALL_TABLES:
            session.query(model).filter(
                model.instance_id == self.instance_id, model.team_id == self.team_id
            ).delete(synchronize_session=False)
        session.flush()

    def seed_round_estate(self, session: Session, pack: Casepack, round: int) -> None:
        iid, tid = self.instance_id, self.team_id
        for nd in self.nodes(round):
            session.add(m.ArchNodeRow(instance_id=iid, team_id=tid, round=round, **nd))
        for e in self.edges(round):
            session.add(m.ArchEdgeRow(instance_id=iid, team_id=tid, round=round, **e))
        for dp in self.deployments(round):
            session.add(m.DeploymentOrgStateRow(instance_id=iid, team_id=tid, round=round, **dp))
        for u in self.org_units(round):
            session.add(m.OrgUnitRow(instance_id=iid, team_id=tid, round=round, **u))
        for g in self.governance(round):
            session.add(m.GovernanceStateRow(instance_id=iid, team_id=tid, round=round, **g))
        session.add(m.ItStaffRow(instance_id=iid, team_id=tid, round=round, **self.staff(round)))
        for p in self.policy(round):
            session.add(m.PolicyDecisionRow(instance_id=iid, team_id=tid, round=round, **p))
        for sa in self.stakeholders(round):
            session.add(m.StakeholderAlignmentRow(instance_id=iid, team_id=tid, round=round, **sa))
        for dl in self.decision_lines(round):
            session.add(m.DecisionLineRow(
                instance_id=iid, team_id=tid, round=round,
                key=dl["key"], category=dl["category"], capability=dl.get("capability"),
                capex=dl.get("capex", 0), rgt_tag=dl.get("rgt_tag", "run"),
                is_maintenance=dl.get("is_maintenance", False),
                action_type=dl.get("action_type"), target_key=dl.get("target_key"),
            ))
        for tco in self.tco(round):
            session.add(m.TcoForecastRow(instance_id=iid, team_id=tid, round=round, **tco))
        session.flush()

    def run(self, session: Session, pack: Casepack) -> list[dict]:
        """Seed and run the six-round game for this archetype; return its six RoundResult
        payloads. Wipes the instance first (idempotent)."""
        self.wipe(session)
        session.add(m.TeamStateRow(
            instance_id=self.instance_id, team_id=self.team_id, current_round=1,
            declared_strategy=self.strategy,
            declared_strategy_round=pack.metadata.initial_state.declared_strategy_round,
            cash=0, opex_runrate=pack.metadata.budget.opening_opex,
        ))
        session.flush()

        runner = RoundRunner(session, pack, self.instance_id, self.team_id)
        results: list[dict] = []
        for round in range(1, pack.metadata.rounds + 1):
            self.seed_round_estate(session, pack, round)
            runner.lock(round)
            results.append(runner.advance(round))
        return results
