"""Typed casepack schema models."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SnakeKey = str
SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Placement(StrEnum):
    on_prem = "on_prem"
    cloud = "cloud"
    saas = "saas"


class RgtTag(StrEnum):
    run = "run"
    grow = "grow"
    transform = "transform"


class SourceTag(StrEnum):
    harvested = "HARVESTED"
    pinned = "PINNED"
    authored = "AUTHORED"


class Provenance(StrictModel):
    source: SourceTag
    note: str


class Company(StrictModel):
    employees: int = Field(gt=0)
    sites: int = Field(gt=0)
    revenue_musd: float = Field(gt=0)
    founded: int = Field(gt=0)
    narrative: str


class Budget(StrictModel):
    capex_per_round: list[int] = Field(min_length=1)
    opening_opex: int = Field(ge=0)


class RoundBudgetState(StrictModel):
    round: int = Field(gt=0)
    capital_remaining: int = Field(ge=0)
    capital_available: int = Field(gt=0)
    run_rate: int = Field(ge=0)


class Scorecard(StrictModel):
    financial: int = Field(ge=0, le=100)
    customer: int = Field(ge=0, le=100)
    internal_process: int = Field(ge=0, le=100)
    learning_growth: int = Field(ge=0, le=100)


class UnitResponse(StrictModel):
    unit: SnakeKey
    people: int = Field(gt=0)
    running: list[str]
    implemented: list[str]
    responding: list[str]
    contributing: str
    contribution_pct: int = Field(ge=0, le=100)


class PeopleState(StrictModel):
    staff_fte: float = Field(ge=0)
    load_fte: float = Field(ge=0)
    overcommitted_pct: int = Field(ge=0)
    platform_load: float = Field(ge=0)
    application_load: float = Field(ge=0)


class ReviewLine(StrictModel):
    area: SnakeKey
    changes: str
    capital: int = Field(ge=0)
    run_rate_effect: int


class ReviewState(StrictModel):
    lines: list[ReviewLine]
    capital_committed: int = Field(ge=0)
    capital_available: int = Field(gt=0)
    capital_remaining: int
    run_rate_after: int = Field(ge=0)
    run_rate_before: int = Field(ge=0)
    warnings: list[str]


class InitialState(StrictModel):
    round: int = Field(gt=0)
    declared_strategy: SnakeKey
    declared_strategy_round: int = Field(gt=0)
    budget: RoundBudgetState
    scorecard: Scorecard
    needs_attention: list[str]
    unit_responses: list[UnitResponse]
    value_chain_coverage: dict[SnakeKey, str]
    open_signals: int = Field(ge=0)
    inbox_waiting: int = Field(ge=0)
    people: PeopleState
    review: ReviewState
    provenance: Provenance


class PackMetadata(StrictModel):
    pack_key: SnakeKey
    pack_version: str
    schema_version: int = Field(gt=0)
    display_name: str
    vertical: SnakeKey
    rounds: int = Field(gt=0)
    company: Company
    budget: Budget
    initial_state: InitialState

    @field_validator("pack_key", "vertical")
    @classmethod
    def snake(cls, value: str) -> str:
        if not SNAKE_RE.fullmatch(value):
            raise ValueError("must be snake_case")
        return value

    @field_validator("pack_version")
    @classmethod
    def semver(cls, value: str) -> str:
        if not re.fullmatch(r"\d+\.\d+\.\d+", value):
            raise ValueError("must be semver")
        return value

    @model_validator(mode="after")
    def budget_rounds_match(self) -> PackMetadata:
        if len(self.budget.capex_per_round) != self.rounds:
            raise ValueError("budget.capex_per_round length must match rounds")
        return self


class RequiredEntity(StrictModel):
    entity: SnakeKey
    min_level_of_detail: SnakeKey


class Capability(StrictModel):
    key: SnakeKey
    chain_position: str
    required_roles: list[SnakeKey]
    required_entities: list[RequiredEntity]
    demand_curve: list[int]
    demand_unit: SnakeKey
    provenance: Provenance


class DeploymentMode(StrictModel):
    capex: int = Field(ge=0)
    opex: int = Field(ge=0)
    lead_time_rounds: int = Field(ge=0)
    bypasses_platform: bool = False


class ResourceDraw(StrictModel):
    compute: float = Field(ge=0)
    storage_gb: float = Field(ge=0)


class PerUnitDraw(ResourceDraw):
    per: int = Field(gt=0)


class Sizing(StrictModel):
    driver: SnakeKey
    base: ResourceDraw
    per_unit: PerUnitDraw


class EntityDetail(StrictModel):
    entity: SnakeKey
    level_of_detail: SnakeKey


class EntityDependency(StrictModel):
    entity: SnakeKey
    from_capability: SnakeKey | None = None
    to_capability: SnakeKey | None = None


class PeopleAffected(StrictModel):
    org_unit: SnakeKey
    count: int = Field(gt=0)


class TrainingOption(StrictModel):
    cost: int = Field(ge=0)
    coverage: float = Field(ge=0, le=1)


class ProcessOption(StrictModel):
    cost: int = Field(ge=0)
    label_key: SnakeKey


class ConfigTier(StrictModel):
    capex_multiplier: float = Field(gt=0)
    compute_multiplier: float = Field(gt=0)


class CatalogItem(StrictModel):
    key: SnakeKey
    roles_filled: list[SnakeKey]
    serves: list[SnakeKey]
    deployment_modes: dict[Placement, DeploymentMode]
    sizing: Sizing
    availability: float = Field(gt=0, le=1)
    service_life_rounds: int = Field(gt=0)
    staff_load: float = Field(ge=0)
    owns_entities: list[EntityDetail] = Field(default_factory=list)
    must_be_fed_by: list[EntityDependency] = Field(default_factory=list)
    must_feed: list[EntityDependency] = Field(default_factory=list)
    people_affected: PeopleAffected
    training_options: dict[SnakeKey, TrainingOption]
    process_option: ProcessOption | None = None
    rgt_tag: RgtTag
    true_cost_categories: list[SnakeKey]
    decoy_cost_categories: list[SnakeKey]
    config_tiers: dict[SnakeKey, ConfigTier]
    provenance: Provenance


class Strategy(StrictModel):
    key: SnakeKey
    headline_metric: SnakeKey
    capability_weights: dict[SnakeKey, float]
    expected_concentration: float = Field(ge=0, le=1)
    target_rgt_mix: dict[RgtTag, float]
    maintenance_floor_pct: float = Field(ge=0, le=1)
    punishes: SnakeKey
    reopen_cost: int = Field(ge=0)
    harvested_raw_fit: dict[SnakeKey, float] = Field(default_factory=dict)
    provenance: Provenance

    @model_validator(mode="after")
    def weights_sum(self) -> Strategy:
        total = sum(self.capability_weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError("capability_weights must sum to 1.0")
        return self


class PlatformService(StrictModel):
    key: SnakeKey
    roles_filled: list[SnakeKey]
    placement_options: dict[Placement, DeploymentMode]
    capacity_pct: int = Field(ge=0, le=100)
    staff_load: float = Field(ge=0)
    provenance: Provenance


class SupportTier(StrictModel):
    key: SnakeKey
    cost: int = Field(ge=0)
    fte_equivalent: float = Field(ge=0)
    provenance: Provenance


class IntegrationTier(StrictModel):
    key: SnakeKey
    cost: int = Field(ge=0)
    provenance: Provenance


class Platform(StrictModel):
    services: list[PlatformService]
    support_tiers: list[SupportTier]
    integration_tiers: list[IntegrationTier]
    starting_staff_fte: float = Field(ge=0)


class Entity(StrictModel):
    key: SnakeKey
    levels_of_detail: list[SnakeKey]
    sensitivity: Literal["low", "medium", "high"]
    provenance: Provenance


class WatchRule(StrictModel):
    key: str
    capability: SnakeKey
    metric: SnakeKey
    warn_above: float | None = None
    critical_above: float | None = None
    cleared_by: list[SnakeKey]
    provenance: Provenance


class EventPrecondition(StrictModel):
    type: SnakeKey
    signal: str | None = None
    severity: Literal["warning", "critical"] | None = None
    capability: SnakeKey | None = None
    ratio: float | None = None


class EventOutcome(StrictModel):
    revenue_loss: int | None = Field(default=None, ge=0)
    scorecard: dict[SnakeKey, int] = Field(default_factory=dict)


class EventOption(StrictModel):
    key: SnakeKey
    tags: list[SnakeKey]
    cost: int = Field(ge=0)


class Event(StrictModel):
    key: SnakeKey
    preconditions: list[EventPrecondition]
    strategy_affinity: list[SnakeKey]
    from_persona: SnakeKey
    body_key: SnakeKey
    outcomes: EventOutcome
    options: list[EventOption]
    provenance: Provenance


class Stakeholder(StrictModel):
    key: SnakeKey
    archetype: SnakeKey
    display_name_key: SnakeKey
    role_key: SnakeKey
    stakeholder_type: Literal["internal", "external"]
    provenance: Provenance


class PreferenceDefaults(StrictModel):
    defaults_by_archetype: dict[SnakeKey, dict[SnakeKey, Any]]
    overrides: list[dict[str, Any]] = Field(default_factory=list)
    provenance: Provenance


class PolicyOption(StrictModel):
    key: SnakeKey
    category: SnakeKey
    cost: int = Field(ge=0)
    effects: dict[SnakeKey, float | int | str]
    provenance: Provenance


class Question(StrictModel):
    key: SnakeKey
    requires_entities: list[RequiredEntity]
    provenance: Provenance


class Labels(StrictModel):
    capabilities: dict[SnakeKey, str] = Field(default_factory=dict)
    roles: dict[SnakeKey, str] = Field(default_factory=dict)
    sidebar: dict[SnakeKey, str] = Field(default_factory=dict)
    strategies: dict[SnakeKey, str] = Field(default_factory=dict)
    stakeholders: dict[SnakeKey, str] = Field(default_factory=dict)
    events: dict[SnakeKey, str] = Field(default_factory=dict)
    policies: dict[SnakeKey, str] = Field(default_factory=dict)
    misc: dict[SnakeKey, str] = Field(default_factory=dict)


class Casepack(StrictModel):
    metadata: PackMetadata
    strategies: list[Strategy]
    capabilities: list[Capability]
    catalog: list[CatalogItem]
    platform: Platform
    entities: list[Entity]
    watch_rules: list[WatchRule]
    events: list[Event]
    stakeholders: list[Stakeholder]
    preferences: dict[SnakeKey, PreferenceDefaults]
    policies: list[PolicyOption]
    questions: list[Question]
    labels: Labels

    @model_validator(mode="after")
    def demand_curves_match_rounds(self) -> Casepack:
        rounds = self.metadata.rounds
        for capability in self.capabilities:
            if len(capability.demand_curve) != rounds:
                raise ValueError(f"capabilities.{capability.key}.demand_curve length must match rounds")
        return self
