"""Runtime persistence tables for the round runner (1.6 spec section 5.1).

Every table here carries ``instance_id`` **non-null from creation** (GOVERNANCE section 4.5,
1.6 decision 1) and ``team_id``; the snapshot builder and every runner query filter on both
(invariant I4). No ``simulation_instance`` table exists yet -- 2.1 creates it and adds the FK
(pre-flight row 4); here ``instance_id`` is an unconstrained non-null integer scoping key, as
is ``team_id`` (2.x add the course/section/instance/team entities).

These are the *persistence* tables. The pure engine snapshots 1.6 assembles from them
(``TeamState``/``ArchNode``/``LedgerSignal``) carry no ``instance_id`` -- the engine performs
no I/O (1.4 I2, 1.5 I2), so none of this module is importable from ``app.engine``.

Types are deliberately portable (Integer/String/Float/Boolean/JSON, no ARRAY, no server
defaults): the invariant guards and the instance-isolation canary run on in-memory SQLite,
while ``--full`` and the migration demo run on Postgres. One shared ``Base.metadata`` so the
Alembic autogenerate/target metadata sees them.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# --------------------------------------------------------------------------------------
# The team's current pointer + lock/advance state (one row per instance/team).
# --------------------------------------------------------------------------------------
class TeamStateRow(Base):
    __tablename__ = "team_state"

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False)
    declared_strategy: Mapped[str] = mapped_column(String, nullable=False)
    declared_strategy_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cash: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: Opex run-rate for the current round. A RATCHET recomputed from live deployments each
    #: round (decision 5, I7) -- never a stored running total; this column caches the last
    #: recompute for the current-round display, the authoritative per-round figure lives on
    #: the immutable RoundResult.
    opex_runrate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: lock/advance state machine (O1/O3). `locked_round` is the highest round whose sheet is
    #: frozen; `advanced_round` the highest round whose results are written. Advance produces
    #: results (O3); unlock invalidates the RoundResult rather than editing it (O1).
    locked_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    advanced_round: Mapped[int | None] = mapped_column(Integer, nullable=True)


# --------------------------------------------------------------------------------------
# The architecture estate -- a full per-round snapshot (one estate per (instance,team,round)).
# --------------------------------------------------------------------------------------
class ArchNodeRow(Base):
    __tablename__ = "arch_node"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    roles_filled: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    availability: Mapped[float] = mapped_column(Float, nullable=False)
    installed_round: Mapped[int] = mapped_column(Integer, nullable=False)
    service_life_rounds: Mapped[int] = mapped_column(Integer, nullable=False)
    serves: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    throughput: Mapped[float | None] = mapped_column(Float, nullable=True)
    owns_entities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    #: Runtime placement, one of on_prem/cloud/saas -- NEVER the derived `hybrid`
    #: (CONTRACTS.md placement, decision 9/CC-D8). Read by the `placement_count` precondition.
    placement: Mapped[str | None] = mapped_column(String, nullable=True)
    #: This node's contribution to the opex run-rate; opex_runrate is the SUM over the round's
    #: live nodes (recomputed, never accumulated -- decision 5, I7).
    opex_contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ArchEdgeRow(Base):
    __tablename__ = "arch_edge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    src: Mapped[str] = mapped_column(String, nullable=False)
    dst: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False, default="network")


class DeploymentOrgStateRow(Base):
    __tablename__ = "deployment_org_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    catalog_key: Mapped[str] = mapped_column(String, nullable=False)
    org_unit: Mapped[str] = mapped_column(String, nullable=False)
    people_affected: Mapped[int] = mapped_column(Integer, nullable=False)
    trained_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    process: Mapped[str] = mapped_column(String, nullable=False, default="unchanged")
    adoption: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ever_trained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    serves: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_primary_for: Mapped[str | None] = mapped_column(String, nullable=True)
    initiated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    abandoned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PlatformServiceRow(Base):
    __tablename__ = "platform_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    placement: Mapped[str | None] = mapped_column(String, nullable=True)
    capacity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    utilisation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class OrgUnitRow(Base):
    __tablename__ = "org_unit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resistance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ItStaffRow(Base):
    __tablename__ = "it_staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_fte: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    load_fte: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class GovernanceStateRow(Base):
    __tablename__ = "governance_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    capability: Mapped[str] = mapped_column(String, nullable=False)
    owner_assigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sponsor_assigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PolicyDecisionRow(Base):
    __tablename__ = "policy_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    policy: Mapped[str] = mapped_column(String, nullable=False)
    selected: Mapped[str] = mapped_column(String, nullable=False)
    actively_decided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class StakeholderAlignmentRow(Base):
    __tablename__ = "stakeholder_alignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    stakeholder: Mapped[str] = mapped_column(String, nullable=False)
    alignment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cares_about: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


# --------------------------------------------------------------------------------------
# Lead-time purchases (O2): ordered, not yet arrived; materialise at arrival_round.
# --------------------------------------------------------------------------------------
class InFlightRow(Base):
    __tablename__ = "in_flight"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    catalog_key: Mapped[str] = mapped_column(String, nullable=False)
    ordered_round: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_round: Mapped[int] = mapped_column(Integer, nullable=False)
    capex: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: the ArchNode payload to materialise into the estate at arrival_round (kept as JSON so
    #: an in-flight order carries exactly the node it will become -- O2).
    node_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    materialised: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# --------------------------------------------------------------------------------------
# Decision sheet -- one row per committed decision line; the source each ActionRecord is
# derived from (decision 9/CC-D10). Partial-update semantics (decision 7, I8).
# --------------------------------------------------------------------------------------
class DecisionLineRow(Base):
    __tablename__ = "decision_line"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False)
    #: one of the CONTRACTS.md decision_line.category enum (12 values).
    category: Mapped[str] = mapped_column(String, nullable=False)
    capability: Mapped[str | None] = mapped_column(String, nullable=True)
    capex: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rgt_tag: Mapped[str] = mapped_column(String, nullable=False, default="run")
    is_maintenance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: the specific engine action_type this line commits (one of checks.ACTION_TYPES), when the
    #: line performs a signal-clearing action. Disambiguates categories that map to a family
    #: (e.g. `application` -> add_node vs scale_node). NULL => derive from the category map, or
    #: no ActionRecord if the category performs no action (staffing/governance/communication/
    #: capital_request). See app/round/actions.py.
    action_type: Mapped[str | None] = mapped_column(String, nullable=True)
    #: the exact catalog item / platform tier / policy / node the action targets.
    target_key: Mapped[str | None] = mapped_column(String, nullable=True)


# --------------------------------------------------------------------------------------
# The persisted 1.5 LedgerSignal ledger (decision 10). PK is episode identity; append-only,
# immutable (I9) -- a re-raise opens episode_id+1, a prior episode row is never overwritten.
# --------------------------------------------------------------------------------------
class SignalRow(Base):
    __tablename__ = "signal"

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String, primary_key=True)
    episode_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    capability: Mapped[str] = mapped_column(String, nullable=False)
    metric: Mapped[str] = mapped_column(String, nullable=False)
    metric_kind: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    first_shown_round: Mapped[int] = mapped_column(Integer, nullable=False)
    cleared_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fire_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cleared_by: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    was_actionable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cheapest_fix_when_raised: Mapped[int | None] = mapped_column(Integer, nullable=True)


# --------------------------------------------------------------------------------------
# Debt ledger (decision 6) -- deferrals with accrual; source of debt_ratio_by_capability
# (decision 9/CC-D6).
# --------------------------------------------------------------------------------------
class DebtItemRow(Base):
    __tablename__ = "debt_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    capability: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: the deferred decision line / signal key this debt accrued from (audit trail).
    source_key: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str] = mapped_column(String, nullable=False, default="deferral")


# --------------------------------------------------------------------------------------
# TCO forecast vs actual reconciliation (design/02 D).
# --------------------------------------------------------------------------------------
class TcoForecastRow(Base):
    __tablename__ = "tco_forecast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    item: Mapped[str] = mapped_column(String, nullable=False)
    forecast: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# --------------------------------------------------------------------------------------
# Immutable RoundResult (decision 2) -- one row per (instance, team, round). Never UPDATEd
# (I6); the whole result payload is stored as JSON so a debrief needs no recomputation
# (spec section 5.3).
# --------------------------------------------------------------------------------------
class RoundResult(Base):
    __tablename__ = "round_result"

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)


#: Every runtime table, for the isolation canary and the migration.
ALL_TABLES = (
    TeamStateRow, ArchNodeRow, ArchEdgeRow, DeploymentOrgStateRow, PlatformServiceRow,
    OrgUnitRow, ItStaffRow, GovernanceStateRow, PolicyDecisionRow, StakeholderAlignmentRow,
    InFlightRow, DecisionLineRow, SignalRow, DebtItemRow, TcoForecastRow, RoundResult,
)
