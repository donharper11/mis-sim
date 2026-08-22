"""Snapshot assembly -- 1.6 builds what the pure engines read (spec section 5.1a).

1.4 and 1.5 are pure functions of ``(Casepack, TeamState)`` plus a prior ``LedgerSignal``
tuple; they never touch the database. 1.6 is the only packet that bridges the persistence
tables to those in-memory snapshots. Each round it rebuilds the immutable ``TeamState`` and the
prior ``LedgerSignal`` tuple from its own tables (the single source of truth) and hands them to
the engine; the snapshots are derived views, never a second home that can drift (SPEC_PROTOCOL
section 3).

Every read here filters on ``instance_id`` (and ``team_id``/``round``) -- invariant I4. All
scoped reads go through ``_scoped``, whose ``select(...)`` line names ``instance_id`` so the I4
grep (``select(`` without ``instance_id``) never trips.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.casepack.models import Casepack
from app.engine.ledger import LedgerSignal
from app.engine.state import (
    ArchEdge, ArchNode, DecisionState, DeploymentState, GovernanceState, OrgUnitState,
    PolicyDecisionState, SignalState, StaffPool, StakeholderDecisionAlignment, TeamState,
)
from app.round import models as m
from app.round.actions import action_record


def _scoped(model, instance_id: int, team_id: int, round: int | None = None):
    """A select scoped to one instance/team (and optionally one round) -- the single place a
    ``select(`` is written, and it names ``instance_id`` so I4's grep passes (invariant I4)."""
    stmt = select(model).where(model.instance_id == instance_id, model.team_id == team_id)
    if round is not None:
        stmt = stmt.where(model.round == round)
    return stmt


def committed_spend(session: Session, instance_id: int, team_id: int, round: int) -> int:
    """Total capex committed on the round's decision sheet -- the deduction in the funds ratchet."""
    rows = session.scalars(_scoped(m.DecisionLineRow, instance_id, team_id, round)).all()
    return sum(max(0, int(r.capex)) for r in rows)


def available_funds_by_round(
    session: Session, instance_id: int, team_id: int, upto_round: int, capex_per_round: list[int]
) -> tuple[int, ...]:
    """Remaining capital per round, index r-1, committed spend already deducted (decision 9/CC-D7).

    This is the same ratchet as opex (decision 5): recomputed from the live decision sheet each
    round, never accumulated. ``capex_per_round`` is the pack's authored per-round budget."""
    out: list[int] = []
    for r in range(1, upto_round + 1):
        budget = capex_per_round[r - 1] if r - 1 < len(capex_per_round) else 0
        out.append(int(budget) - committed_spend(session, instance_id, team_id, r))
    return tuple(out)


def action_history(session: Session, instance_id: int, team_id: int, upto_round: int) -> tuple:
    """Append-only ActionRecord history for every committed line locked at or before ``upto_round``
    whose category performs an action (decision 9/CC-D10). Ordered by (round, id) for determinism."""
    rows = session.scalars(
        _scoped(m.DecisionLineRow, instance_id, team_id).where(m.DecisionLineRow.round <= upto_round)
        .order_by(m.DecisionLineRow.round, m.DecisionLineRow.id)
    ).all()
    records = [action_record(r) for r in rows]
    return tuple(rec for rec in records if rec is not None)


def debt_ratio_by_capability(
    session: Session, instance_id: int, team_id: int, upto_round: int, capabilities: list[str]
) -> dict[str, float]:
    """Per-capability debt ratio from the debt ledger (decision 9/CC-D6).

    ``ratio = deferred_debt / (deferred_debt + committed_spend)`` per capability -- the share of
    the capability's investment that is still deferred. Supplied for **every** capability (0.0
    when no debt), never ``None``: the ``debt_above`` precondition then reads a real number rather
    than raising ``MissingRoundInputError`` (unreachable in v1 -- no reference-pack event uses it)."""
    debt: dict[str, int] = {c: 0 for c in capabilities}
    for row in session.scalars(
        _scoped(m.DebtItemRow, instance_id, team_id).where(m.DebtItemRow.round <= upto_round)
    ).all():
        if row.capability in debt:
            debt[row.capability] += int(row.amount)
    spend: dict[str, int] = {c: 0 for c in capabilities}
    for row in session.scalars(
        _scoped(m.DecisionLineRow, instance_id, team_id).where(m.DecisionLineRow.round <= upto_round)
    ).all():
        if row.capability in spend:
            spend[row.capability] += max(0, int(row.capex))
    # supplied for every capability, never None: `debt_above` then reads a real number rather than
    # raising MissingRoundInputError (unreachable in v1 -- no reference-pack event uses debt_above).
    ratios: dict[str, float] = {}
    for c in capabilities:
        d, s = debt[c], spend[c]
        ratios[c] = round(d / (d + s), 6) if (d + s) > 0 else 0.0
    return ratios


def load_prior_ledger(
    session: Session, instance_id: int, team_id: int
) -> tuple[LedgerSignal, ...]:
    """Rebuild the prior ``LedgerSignal`` tuple from the persisted ``signal`` table, append-order
    preserved (spec section 5.1a). ``advance_ledger`` takes this as immutable history."""
    rows = session.scalars(
        _scoped(m.SignalRow, instance_id, team_id).order_by(m.SignalRow.first_shown_round, m.SignalRow.key, m.SignalRow.episode_id)
    ).all()
    return tuple(
        LedgerSignal(
            key=r.key, episode_id=r.episode_id, capability=r.capability, metric=r.metric,
            metric_kind=r.metric_kind, value=r.value, severity=r.severity, status=r.status,
            first_shown_round=r.first_shown_round, cleared_round=r.cleared_round,
            fire_round=r.fire_round, cleared_by=tuple(r.cleared_by or ()),
            was_actionable=bool(r.was_actionable), cheapest_fix_when_raised=r.cheapest_fix_when_raised,
        )
        for r in rows
    )


def build_team_state(
    session: Session,
    instance_id: int,
    team_id: int,
    round: int,
    pack: Casepack,
    signals: tuple[SignalState, ...] = (),
) -> TeamState:
    """Assemble the immutable ``TeamState`` the engines score, from the round's persisted estate
    plus the four round-evolution inputs (spec section 5.1a, decision 9). ``signals`` is the
    projected ledger, supplied by the resolution order at step 10 (empty at the raw step-9 pass)."""
    ts_row = session.get(m.TeamStateRow, (instance_id, team_id))
    strategy = ts_row.declared_strategy if ts_row else pack.metadata.initial_state.declared_strategy

    nodes = tuple(
        ArchNode(
            key=n.key, roles_filled=tuple(n.roles_filled or ()), availability=n.availability,
            installed_round=n.installed_round, service_life_rounds=n.service_life_rounds,
            serves=tuple(n.serves or ()), throughput=n.throughput,
            owns_entities=tuple(tuple(e) for e in (n.owns_entities or ())),
            placement=n.placement,
        )
        for n in session.scalars(_scoped(m.ArchNodeRow, instance_id, team_id, round)).all()
    )
    edges = tuple(
        ArchEdge(src=e.src, dst=e.dst, kind=e.kind)
        for e in session.scalars(_scoped(m.ArchEdgeRow, instance_id, team_id, round)).all()
    )
    deployments = tuple(
        DeploymentState(
            key=d.key, catalog_key=d.catalog_key, org_unit=d.org_unit,
            people_affected=d.people_affected, trained_count=d.trained_count, process=d.process,
            adoption=d.adoption, ever_trained=d.ever_trained, serves=tuple(d.serves or ()),
            is_primary_for=d.is_primary_for, initiated=d.initiated, abandoned=d.abandoned,
        )
        for d in session.scalars(_scoped(m.DeploymentOrgStateRow, instance_id, team_id, round)).all()
    )
    org_units = tuple(
        OrgUnitState(key=u.key, resistance=u.resistance)
        for u in session.scalars(_scoped(m.OrgUnitRow, instance_id, team_id, round)).all()
    )
    governance = tuple(
        GovernanceState(capability=g.capability, owner_assigned=g.owner_assigned, sponsor_assigned=g.sponsor_assigned)
        for g in session.scalars(_scoped(m.GovernanceStateRow, instance_id, team_id, round)).all()
    )
    staff_row = session.scalars(_scoped(m.ItStaffRow, instance_id, team_id, round)).first()
    staff = StaffPool(
        staff_fte=staff_row.staff_fte if staff_row else 0.0,
        load_fte=staff_row.load_fte if staff_row else 0.0,
    )
    decisions = tuple(
        DecisionState(
            key=dl.key, category=dl.category, capability=dl.capability, capex=dl.capex,
            rgt_tag=dl.rgt_tag, is_maintenance=dl.is_maintenance,
        )
        for dl in session.scalars(_scoped(m.DecisionLineRow, instance_id, team_id, round)).all()
    )
    policy_decisions = tuple(
        PolicyDecisionState(policy=p.policy, selected=p.selected, actively_decided=p.actively_decided)
        for p in session.scalars(_scoped(m.PolicyDecisionRow, instance_id, team_id, round)).all()
    )
    stakeholder_alignments = tuple(
        StakeholderDecisionAlignment(
            stakeholder=s.stakeholder, alignment=s.alignment, cares_about=tuple(s.cares_about or ())
        )
        for s in session.scalars(_scoped(m.StakeholderAlignmentRow, instance_id, team_id, round)).all()
    )

    capex_per_round = list(pack.metadata.budget.capex_per_round)
    cap_keys = [c.key for c in pack.capabilities]

    return TeamState(
        round=round,
        declared_strategy=strategy,
        nodes=nodes,
        edges=edges,
        deployments=deployments,
        org_units=org_units,
        governance=governance,
        staff=staff,
        signals=signals,
        decisions=decisions,
        stakeholder_alignments=stakeholder_alignments,
        policy_decisions=policy_decisions,
        action_history=action_history(session, instance_id, team_id, round),
        available_funds_by_round=available_funds_by_round(
            session, instance_id, team_id, round, capex_per_round
        ),
        debt_ratio_by_capability=debt_ratio_by_capability(
            session, instance_id, team_id, round, cap_keys
        ),
    )
