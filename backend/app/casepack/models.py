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
    #: The round's remaining capital is NOT a field here, deliberately -- CG-6, finding
    #: `1.3-001`. It was one fact with two schema-REQUIRED homes, this one and the round
    #: budget's, and both were derived from the very same expression that this model already
    #: holds both sides of: `capital_available - capital_committed`. `SPEC_PROTOCOL`
    #: section 3 says prefer elimination over reconciliation, and 1.3 could not eliminate it
    #: because doing so is a schema change 1.3's scope excluded. Removed here, so the round
    #: budget above holds the single authored figure, the validator's `E14` still enforces it
    #: against this derivation with zero tolerance, and a review block can no longer disagree
    #: with itself.
    lines: list[ReviewLine]
    capital_committed: int = Field(ge=0)
    capital_available: int = Field(gt=0)
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
    #: Entities this shared service is the system of record for, at a stated level
    #: of detail. Same shape `CatalogItem.owns_entities` uses: a platform service
    #: can fill a role *and* own the entity that role's capability requires.
    owns_entities: list[EntityDetail] = Field(default_factory=list)
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
    """A rule that raises a signal.

    `metric_kind` declares how the rule is evaluated (1.5 spec section 5.1a):

    * `threshold` -- the metric is a float, compared against `warn_above` /
      `critical_above`.
    * `presence` -- the metric is a boolean; it raises at `critical` and carries
      no thresholds at all (1.5 decision 10).

    The default of `threshold` is a **migration affordance, not the end state**.
    Every rule authored before this field existed is threshold-shaped, so
    `threshold` is the honest default rather than a convenience -- but 1.3 must
    declare the kind explicitly on every rule (its I8), and a later change may
    tighten this to required once no pack relies on the default. Do not read the
    default as permission to leave it unauthored.

    Only the *presence* half of the constraint is enforced here. A `threshold`
    rule carrying no threshold is illegal, but it is 1.2's `E12` that says so:
    rejecting it at load time would make packs that exist today unloadable and
    would replace twenty specific validator findings with one load failure.
    """

    key: SnakeKey
    capability: SnakeKey
    metric: SnakeKey
    metric_kind: Literal["threshold", "presence"] = "threshold"
    warn_above: float | None = None
    critical_above: float | None = None
    cleared_by: list[SnakeKey]
    provenance: Provenance

    @model_validator(mode="after")
    def presence_rules_carry_no_thresholds(self) -> WatchRule:
        if self.metric_kind == "presence" and (
            self.warn_above is not None or self.critical_above is not None
        ):
            raise ValueError("metric_kind 'presence' must not carry warn_above or critical_above")
        return self


class EventPrecondition(StrictModel):
    """One clause of an event's firing condition.

    The field set is the union of what the eleven precondition types of 1.5 spec
    section 5.2 need. Every field is optional because each type reads only its
    own; which fields a given `type` requires is a validator question, not a
    schema one.
    """

    type: SnakeKey
    signal: str | None = None
    severity: Literal["warning", "critical"] | None = None
    capability: SnakeKey | None = None
    ratio: float | None = None
    node: SnakeKey | None = None
    entity: SnakeKey | None = None
    policy: SnakeKey | None = None
    placement: Literal["on_prem", "cloud", "saas"] | None = None
    other_policy: SnakeKey | None = None
    round: int | None = Field(default=None, gt=0)
    count: int | None = Field(default=None, ge=0)


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


class ObligationRule(StrictModel):
    """A privacy obligation, in the shape 1.5 spec section 5.4 specifies.

    Obligations reuse the signal machinery entirely (1.5 decision 7): a sensitive
    entity held under a permissive policy raises on the *presence* path, is
    cleared by an action in `cleared_by`, and while ignored arms the events named
    in `arms`. There is no parallel system and no second scoring path.
    """

    key: SnakeKey
    #: An entity the pack defines.
    entity: SnakeKey
    #: The condition vocabulary is open -- 1.5 section 5.4 names `policy_permits`
    #: and does not close the set, so no enum is invented here.
    condition: SnakeKey
    #: The policy switch the condition reads, and the value of it that is permissive.
    policy: SnakeKey
    permissive_value: str
    #: Obligations are presence-shaped by construction, and a presence condition
    #: raises at `critical`, never at `warning` (1.5 decision 10). There is no
    #: magnitude to be mildly concerned about, so the vocabulary is one value.
    severity: Literal["critical"] = "critical"
    cleared_by: list[SnakeKey]
    #: Event keys this obligation can arm while it stays open.
    arms: list[SnakeKey] = Field(default_factory=list)
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
    #: The states this switch can be in -- the policy's value vocabulary, e.g.
    #: `[indefinite, standard_period, minimal]` for `data_retention`. Without it
    #: an obligation's `permissive_value` is a string pointing at nothing
    #: (`1.3-012`, and the box in 1.5 spec 5.4).
    #:
    #: ORDER IS MEANINGFUL and ORDINAL. Index 0 is the least constrained / most
    #: permissive state; each higher index is progressively more restrictive, and
    #: the ordinal distance between two indexes is a real quantity that is
    #: consumed downstream. The 1.4 scorer consumes that distance between a team's
    #: choice and a stakeholder's ideal (`management.policy_switch_alignment`, live
    #: as of the 2026-08-21 closeout; the runtime snapshot it reads is
    #: `TeamState.policy_decisions`) -- so that overshooting an ideal costs less
    #: than ignoring it, where an unordered list could only ever match exactly. Ruled in
    #: design/07 section 3.5b (2026-08-18); canonical entry `PolicyOption.options`
    #: in CONTRACTS.md. On `staff_monitoring` "more constrained" means the firm
    #: watches its own people more, so its permissive index-0 end is the
    #: low-surveillance end (`untracked`) -- design/07 section 3.5a. That is the
    #: same ordering applied to a switch that constrains people, not an exception.
    #:
    #: Optional, and empty by default. A policy that declares no options is the
    #: legacy shape and loads exactly as it did before this field existed.
    options: list[SnakeKey] = Field(default_factory=list)
    #: The state a team holds by NOT deciding. This is what makes the ethics layer
    #: cost something to ignore rather than something to opt into.
    #:
    #: Usually the same value an obligation names as its `permissive_value`, but
    #: the two are distinct concepts and stay separate fields: `default` is where
    #: a team starts, `permissive_value` is what obliges. A pack may legitimately
    #: start a team somewhere already compliant.
    default: SnakeKey | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def default_is_a_declared_option(self) -> PolicyOption:
        """If a policy enumerates its states, its default must be one of them.

        The one constraint enforced here, and deliberately the only one. `options`
        is not required to be non-empty, and `default` is not required when
        `options` is empty -- all 30 packs in the repository carry `policies.yaml`
        with neither field, and every one of them must keep loading unchanged.
        """
        if self.options and self.default is not None and self.default not in self.options:
            raise ValueError(
                f"policies.{self.key}.default '{self.default}' must be one of options {self.options}"
            )
        return self


class Question(StrictModel):
    key: SnakeKey
    requires_entities: list[RequiredEntity]
    provenance: Provenance


class Labels(StrictModel):
    """Every displayed string, keyed by the machine key it stands in for.

    A section exists for each family of key that reaches a screen or a validator
    message. Without one, the message leads with the machine key -- findings
    `1.2-008` and `1.2-024`, where eight codes printed `wh_rollout_01` at an
    instructor.
    """

    capabilities: dict[SnakeKey, str] = Field(default_factory=dict)
    roles: dict[SnakeKey, str] = Field(default_factory=dict)
    sidebar: dict[SnakeKey, str] = Field(default_factory=dict)
    strategies: dict[SnakeKey, str] = Field(default_factory=dict)
    stakeholders: dict[SnakeKey, str] = Field(default_factory=dict)
    events: dict[SnakeKey, str] = Field(default_factory=dict)
    policies: dict[SnakeKey, str] = Field(default_factory=dict)
    entities: dict[SnakeKey, str] = Field(default_factory=dict)
    catalog: dict[SnakeKey, str] = Field(default_factory=dict)
    watch_rules: dict[SnakeKey, str] = Field(default_factory=dict)
    questions: dict[SnakeKey, str] = Field(default_factory=dict)
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
    #: Optional section. A pack without `obligation_rules.yaml` loads clean; its
    #: absence is `CG-5` and stays 1.3's to close.
    obligation_rules: list[ObligationRule] = Field(default_factory=list)
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
