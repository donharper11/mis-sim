"""Strict, versioned P1 models.

The models in this module are intentionally independent of SQLAlchemy and of
the legacy round runner.  They are the typed seam consumed by the later
estate, organisation, consequence and service packets.
"""

from __future__ import annotations

import math
import re
import copy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator, model_validator


KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
PLACEMENTS = {"on_prem", "cloud", "saas"}
CAPABILITIES = (
    "order_fulfilment", "store_operations", "financial_reporting",
    "customer_insight", "marketing_sales", "service", "firm_infrastructure",
)
COMMAND_CATEGORIES = {
    "buy_application": "application", "replace_application": "application",
    "buy_service": "platform_service", "replace_service": "platform_service",
    "connect": "integration", "disconnect": "integration",
    "cancel_order": "lifecycle", "retire_asset": "lifecycle", "project": "lifecycle",
    "train": "training", "set_process": "process_redesign", "communicate": "communication",
    "hire": "staffing", "set_support": "staffing", "assign": "governance",
    "set_primary": "governance", "declare_strategy": "governance", "set_policy": "policy",
    "respond": "event_response", "request_capital": "capital_request",
}
COMMAND_FIELDS: dict[str, tuple[str, ...]] = {
    "buy_application": ("catalog", "placement", "config", "primary_for", "tco_categories"),
    "replace_application": ("asset", "placement", "config"),
    "buy_service": ("service", "placement", "units"),
    "replace_service": ("asset", "placement", "units"),
    "connect": ("src", "dst", "kind", "entity", "tier"),
    "disconnect": ("connection",),
    "cancel_order": ("order",), "retire_asset": ("asset",),
    "project": ("order", "choice"), "train": ("asset", "option"),
    "set_process": ("asset", "choice"), "communicate": ("org_unit", "option"),
    "hire": ("option",), "set_support": ("tier", "covered_assets"),
    "assign": ("capability", "owner", "sponsor"),
    "set_primary": ("capability", "asset"), "declare_strategy": ("strategy",),
    "set_policy": ("policy", "selected"),
    "respond": ("event", "option", "rationale_tag"),
    "request_capital": ("amount", "reason"),
}
NULLABLE_COMMAND_FIELDS = {"primary_for", "entity", "tier", "owner", "sponsor", "asset"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


def _key(value: str, limit: int = 64) -> str:
    if not isinstance(value, str) or not KEY_RE.fullmatch(value) or len(value) > limit:
        raise ValueError(f"must be lower snake_case and at most {limit} characters")
    return value


def _finite(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("must be a finite number")
    return float(value)


class SimulationError(ValueError):
    """Closed, machine-readable error at the P1 boundary."""

    CODES = {
        "not_found", "invalid_input", "invalid_reference", "conflicting_commands",
        "unaffordable", "revision_conflict", "locked", "round_state", "pack_mismatch",
        "scope_exists", "unsupported_operation", "arrival_after_game_end", "invalid_output",
    }

    def __init__(self, code: str, field: str = "", details: dict[str, Any] | None = None):
        if code not in self.CODES:
            raise ValueError(f"unknown simulation error code: {code}")
        self.code, self.field, self.details = code, field, details or {}
        super().__init__(f"{code}{(': ' + field) if field else ''}")


class CommandV1(StrictModel):
    key: StrictStr = Field(min_length=1, max_length=48)
    op: StrictStr
    # The union of the frozen operation fields.  The validator below supplies
    # the closed discriminated vocabulary while keeping a convenient public DTO.
    catalog: str | None = None
    placement: str | None = None
    config: str | None = None
    primary_for: str | None = None
    tco_categories: list[str] | None = None
    service: str | None = None
    units: StrictInt | None = None
    asset: str | None = None
    src: str | None = None
    dst: str | None = None
    kind: str | None = None
    entity: str | None = None
    tier: str | None = None
    connection: str | None = None
    order: str | None = None
    choice: str | None = None
    option: str | None = None
    org_unit: str | None = None
    covered_assets: list[str] | None = None
    capability: str | None = None
    owner: str | None = None
    sponsor: str | None = None
    strategy: str | None = None
    policy: str | None = None
    selected: str | None = None
    event: str | None = None
    rationale_tag: str | None = None
    amount: StrictInt | None = None
    reason: str | None = None

    @field_validator("key")
    @classmethod
    def valid_command_key(cls, value: str) -> str:
        return _key(value, 48)

    @model_validator(mode="after")
    def validate_operation(self) -> "CommandV1":
        if self.op not in COMMAND_CATEGORIES:
            raise ValueError("unknown command operation")
        fields = COMMAND_FIELDS[self.op]
        unexpected = self.model_fields_set - (set(fields) | {"key", "op"})
        if unexpected:
            raise ValueError(f"fields not allowed for {self.op}: {sorted(unexpected)}")
        nullable = {"primary_for", "entity", "tier", "owner", "sponsor"}
        if self.op == "set_primary":
            nullable.add("asset")
        for field in fields:
            if field not in self.model_fields_set:
                raise ValueError(f"{self.op} requires {field}")
            value = getattr(self, field)
            if value is None and field not in nullable:
                raise ValueError(f"{self.op}.{field} cannot be null")
        if self.placement is not None and self.placement not in PLACEMENTS:
            raise ValueError("invalid placement")
        if self.units is not None and self.units <= 0:
            raise ValueError("units must be positive")
        if self.amount is not None and self.amount <= 0:
            raise ValueError("amount must be positive")
        if self.reason is not None and (not self.reason.strip() or len(self.reason) > 1000):
            raise ValueError("reason must be nonempty and at most 1000 characters")
        if self.op == "connect" and self.kind not in {"network", "integration", "failover"}:
            raise ValueError("invalid connection kind")
        if self.op == "project" and self.choice not in {"continue", "pause", "kill"}:
            raise ValueError("invalid project choice")
        if self.op == "set_process" and self.choice not in {"unchanged", "partial", "redesigned"}:
            raise ValueError("invalid process choice")
        if self.op == "set_support" and self.tier is None and self.covered_assets is None:
            raise ValueError("set_support requires tier or covered_assets")
        if self.tco_categories is not None:
            if len(set(self.tco_categories)) != len(self.tco_categories):
                raise ValueError("duplicate tco category")
        for name, value in self.__dict__.items():
            if name in {"key", "op", "reason"} or value is None:
                continue
            if isinstance(value, str):
                _key(value)
            elif isinstance(value, list):
                for item in value:
                    _key(item)
        return self


class SheetPatchV1(StrictModel):
    version: Literal[1]
    replace_categories: dict[str, list[CommandV1]]

    @model_validator(mode="after")
    def validate_categories(self) -> "SheetPatchV1":
        keys: set[str] = set()
        for category, commands in self.replace_categories.items():
            if category not in set(COMMAND_CATEGORIES.values()):
                raise ValueError("unknown command category")
            for command in commands:
                if COMMAND_CATEGORIES[command.op] != category:
                    raise ValueError("command category does not match operation")
                if command.key in keys:
                    raise ValueError("duplicate command key")
                keys.add(command.key)
        return self


class CatalogRuntimeV1(StrictModel):
    purchasable_placements: list[str]
    capacity_by_capability: dict[str, float | None]
    capacity_multiplier_by_config: dict[str, float]
    opex_multiplier_by_config: dict[str, float]

    @model_validator(mode="after")
    def unique_placements(self) -> "CatalogRuntimeV1":
        if len(set(self.purchasable_placements)) != len(self.purchasable_placements):
            raise ValueError("duplicate purchasable placement")
        return self


class SupplyV1(StrictModel):
    compute: float
    storage_gb: float


class ServiceRuntimeV1(StrictModel):
    serves: list[str]
    availability: float
    service_life_rounds: StrictInt
    capacity_by_capability: dict[str, float | None]
    supply_by_placement: dict[str, SupplyV1]
    max_units: StrictInt

    @model_validator(mode="after")
    def unique_serves(self) -> "ServiceRuntimeV1":
        if len(set(self.serves)) != len(self.serves):
            raise ValueError("duplicate service capability")
        if isinstance(self.availability, bool) or not math.isfinite(self.availability) or not 0 <= self.availability <= 1:
            raise ValueError("availability must be finite and within 0..1")
        if any(value is not None and (not math.isfinite(value) or value <= 0) for value in self.capacity_by_capability.values()):
            raise ValueError("service capacity must be positive or null")
        return self


class HiringOptionV1(StrictModel):
    fte: float
    wage_per_round: StrictInt
    lead_time_rounds: StrictInt


class CommunicationOptionV1(StrictModel):
    cost: StrictInt
    resistance_reduction: float


class UnitV1(StrictModel):
    label: StrictStr
    initial_resistance: float

    @field_validator("initial_resistance")
    @classmethod
    def valid_resistance(cls, value: float) -> float:
        if isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("initial resistance must be finite and within 0..1")
        return value


class PeopleV1(StrictModel):
    training_retention: float
    resistance_retention: float
    arrival_shock: float
    strategy_shock: float
    resistance_ceiling: float
    adoption_adjustment: float
    sponsor_present: float
    sponsor_absent: float
    staff_floor: float
    starting_wage_per_fte: StrictInt
    placement_staff_multiplier: dict[str, float]
    hiring_options: dict[str, HiringOptionV1]
    communication_options: dict[str, CommunicationOptionV1]
    units: dict[str, UnitV1]


class InitialAssetV1(StrictModel):
    id: str
    source_kind: Literal["catalog", "service"]
    source_key: str
    placement: str
    config: str | None
    units: StrictInt
    installed_round: StrictInt


class InitialConnectionV1(StrictModel):
    id: str
    src: str
    dst: str
    kind: Literal["network", "integration", "failover"]
    entity: str | None
    tier: str | None


class GovernanceV1(StrictModel):
    owner: str | None
    sponsor: str | None


class InitialV1(StrictModel):
    assets: list[InitialAssetV1]
    connections: list[InitialConnectionV1]
    training_fraction: float
    adoption: float
    process_with_option: Literal["partial", "redesigned"]
    process_without_option: Literal["unchanged"]
    primary: dict[str, str | None]
    governance: dict[str, GovernanceV1]


class ConnectionTermsV1(StrictModel):
    capex_source: Literal["none", "integration_tier"]
    opex: StrictInt
    staff_load: float


class AccountingV1(StrictModel):
    opening_capital: StrictInt
    opening_operating: StrictInt
    operating_allowances: list[StrictInt]
    connection_terms: dict[str, ConnectionTermsV1]
    cancellation: Literal["sunk"]
    platform_capability: str
    decision_attribution_version: Literal[1]
    action_attribution_version: Literal[1]
    tco_estimators: dict[str, Literal["full_training", "basic_integration", "full_process", "compute_unit", "backup_unit", "capex_fraction", "max_policy", "one_round_opex"]]
    tco_capex_fraction: float
    process_partial_fraction: float

    @model_validator(mode="after")
    def exact_tco_estimators(self) -> "AccountingV1":
        expected = {
            "training": "full_training", "integration": "basic_integration",
            "process_redesign": "full_process", "capacity": "compute_unit",
            "backup": "backup_unit", "lifecycle": "capex_fraction",
            "policy": "max_policy", "maintenance": "one_round_opex",
            "data_migration": "capex_fraction",
        }
        if self.tco_estimators != expected:
            raise ValueError("tco_estimators must equal the closed P1 estimator map")
        return self


class PreferenceViewV1(StrictModel):
    metric: str
    ideal: float | str
    weight: float
    source_note: str


class PreferenceRuleV1(StrictModel):
    stakeholder: str
    cares_about: list[str]
    views: list[PreferenceViewV1]


class PreferenceDispositionV1(StrictModel):
    source_path: str
    disposition: Literal["live_v1", "context_m4", "no_preference"]
    runtime_views: list[str]
    reason: str


class PreferencesV1(StrictModel):
    rules: list[PreferenceRuleV1]
    dispositions: list[PreferenceDispositionV1]

    @model_validator(mode="after")
    def unique_sources(self) -> "PreferencesV1":
        paths = [item.source_path for item in self.dispositions]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate preference disposition")
        for rule in self.rules:
            if len(rule.cares_about) != len(set(rule.cares_about)):
                raise ValueError("duplicate caring capability")
        return self


class ResponseDispositionV1(StrictModel):
    fund_effect: Literal["prevent_current_round"]
    explanation: str


class ProvenanceEntryV1(StrictModel):
    source: Literal["AUTHORED", "HARVESTED", "PINNED"]
    note: str


class RuntimeContentV1(StrictModel):
    version: Literal[1]
    catalog: dict[str, CatalogRuntimeV1]
    services: dict[str, ServiceRuntimeV1]
    drivers: dict[str, list[float]]
    people: PeopleV1
    initial: InitialV1
    accounting: AccountingV1
    preferences: PreferencesV1
    response_disposition: dict[str, ResponseDispositionV1]
    provenance: dict[str, ProvenanceEntryV1]
    units: dict[str, StrictStr]

    @model_validator(mode="after")
    def validate_numbers(self) -> "RuntimeContentV1":
        def walk(value: Any, path: str = ""):
            if isinstance(value, bool):
                raise ValueError(f"boolean is not a numeric/content value at {path}")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"non-finite numeric value at {path}")
            if isinstance(value, dict):
                for k, v in value.items(): walk(v, f"{path}/{k}")
            elif isinstance(value, list):
                for i, v in enumerate(value): walk(v, f"{path}/{i}")
        walk(self.model_dump())
        return self


class RuntimePackV1(StrictModel):
    """Bound immutable semantic bundle (the constructor copies its inputs)."""

    casepack: Any
    runtime: RuntimeContentV1
    pack_digest: StrictStr = Field(pattern=HEX64_RE.pattern)
    canonical_bytes: bytes

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    def __getattribute__(self, name: str):
        # Do not expose mutable aliases to the bound semantic inputs.  Later
        # packets receive detached copies; the digest and bound content remain
        # unchanged if a caller mutates a returned view.
        value = super().__getattribute__(name)
        if name in {"casepack", "runtime"}:
            return copy.deepcopy(value)
        return value


class PackIdentityV1(StrictModel):
    key: str
    version: str
    digest: StrictStr = Field(pattern=HEX64_RE.pattern)


class OperatingForecastV1(StrictModel):
    round: StrictInt; opening: StrictInt; allowance: StrictInt; recurring: StrictInt; closing: StrictInt


class WarningV1(StrictModel):
    code: Literal["operating_deficit", "unpriced_repair"]
    keys: list[str]


class PreviewV1(StrictModel):
    version: Literal[1]
    round: StrictInt
    normalized_commands: list[CommandV1]
    arrivals: list[str]; retirements: list[str]; expiries: list[str]
    capital_available: StrictInt; capital_spend: StrictInt; capital_remaining: StrictInt
    operating_runrate: StrictInt
    operating_forecast: list[OperatingForecastV1]
    challenges: list[dict[str, Any]]
    repair_assessments: list[dict[str, Any]]
    prevented_events: list[str]; would_fire: list[str]
    cost_entries: list[dict[str, Any]]; warnings: list[WarningV1]


class SheetViewV1(StrictModel):
    version: Literal[1]
    round: StrictInt; revision: StrictInt; locked_revision: StrictInt | None
    commands: list[CommandV1]; preview: PreviewV1


class RunViewV1(StrictModel):
    version: Literal[1]
    pack_identity: PackIdentityV1
    current_round: StrictInt
    status: Literal["draft", "locked", "completed"]
    checkpoint_round: StrictInt
    checkpoint_digest: StrictStr = Field(pattern=HEX64_RE.pattern)
    state: CheckpointStateV1
    sheet: SheetViewV1 | None


class CostEntryV1(StrictModel):
    round: StrictInt; kind: str; source: str
    asset: str | None = None; capability: str | None = None; category: str | None = None
    capital_delta: StrictInt; operating_delta: StrictInt


class EffectCandidateV1(StrictModel):
    effect_kind: Literal["arrival", "replacement", "training", "process", "integration", "support", "retirement", "policy"]
    source_round: StrictInt; source_command: str; effect_round: StrictInt
    asset_id: str | None; target_key: str | None; capabilities: list[str]
    cost: StrictInt
    action_type: Literal["add_node", "scale_node", "move_to_cloud", "upgrade_component", "add_training", "redesign_process", "add_service_tier", "retire_component", "add_policy"]


class ResourceViewV1(StrictModel):
    by_placement: dict[str, dict[str, float]]
    by_asset: dict[str, dict[str, Any]]
    integration_load: float; policy_load: float; total_load: float; total_opex: StrictInt


class StaffPoolV1(StrictModel):
    capacity: float; load: float; available: float


class StakeholderDecisionAlignmentV1(StrictModel):
    stakeholder: str; value: float; cares_about: list[str]


class EstateDeltaV1(StrictModel):
    assets: dict[str, AssetV1]; connections: dict[str, ConnectionV1]; projects: dict[str, ProjectV1]
    hiring_orders: dict[str, dict[str, Any]]; staff_hires: list[dict[str, Any]]; rollouts: dict[str, RolloutV1]; primary: dict[str, str | None]
    charge_entries: list[CostEntryV1]; arrived_ids: list[str]; retired_ids: list[str]; expired_ids: list[str]; effect_candidates: list[EffectCandidateV1]


class OrgDeltaV1(StrictModel):
    rollouts: dict[str, RolloutV1]; unit_resistance: dict[str, float]; governance: dict[str, GovernanceStateV1]
    primary: dict[str, str | None]; policies: dict[str, PolicyStateV1]; support: SupportV1
    strategy: str; strategy_declared_round: StrictInt; staff: StaffPoolV1
    communication: dict[str, str]; charge_entries: list[CostEntryV1]; stakeholder_alignments: list[StakeholderDecisionAlignmentV1]
    effect_candidates: list[EffectCandidateV1]


class TransitionV1(StrictModel):
    state: CheckpointStateV1; result: dict[str, Any]; preview: PreviewV1


class AssetV1(StrictModel):
    id: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    source_kind: Literal["catalog", "service"]; source_key: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    placement: str; config: str | None; units: StrictInt
    installed_round: StrictInt; retired_round: StrictInt | None

    @model_validator(mode="after")
    def valid_asset_numbers(self) -> "AssetV1":
        if self.units <= 0 or self.installed_round < 0 or (self.retired_round is not None and self.retired_round < self.installed_round):
            raise ValueError("invalid asset units or rounds")
        return self


class ProjectV1(StrictModel):
    id: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    asset_id: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    source_kind: Literal["catalog", "service"]; source_key: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    placement: str; config: str | None; units: StrictInt; ordered_round: StrictInt
    paid_capex: StrictInt; remaining_lead: StrictInt
    status: Literal["pending", "paused", "arrived", "cancelled", "abandoned"]
    replacement_target: str | None; tco_categories: list[str]

    @model_validator(mode="after")
    def valid_project_numbers(self) -> "ProjectV1":
        if self.units <= 0 or self.ordered_round < 0 or self.paid_capex < 0 or self.remaining_lead < 0:
            raise ValueError("invalid project units, money or rounds")
        return self


class ConnectionV1(StrictModel):
    id: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    src: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    dst: StrictStr = Field(min_length=1, max_length=64, pattern=KEY_RE.pattern)
    kind: Literal["network", "integration", "failover"]
    entity: str | None; tier: str | None; created_round: StrictInt; retired_round: StrictInt | None

    @model_validator(mode="after")
    def valid_connection_rounds(self) -> "ConnectionV1":
        if self.created_round < 0 or (self.retired_round is not None and self.retired_round < self.created_round):
            raise ValueError("invalid connection rounds")
        return self


class RolloutV1(StrictModel):
    trained_count: StrictInt; adoption: float
    process: Literal["unchanged", "partial", "redesigned"]
    ever_trained: bool; lifecycle: Literal["active", "retired", "abandoned"]

    @model_validator(mode="after")
    def valid_rollout(self) -> "RolloutV1":
        if self.trained_count < 0 or isinstance(self.adoption, bool) or not math.isfinite(self.adoption) or not 0 <= self.adoption <= 1:
            raise ValueError("invalid rollout count or adoption")
        return self


class GovernanceStateV1(StrictModel):
    owner: str | None; sponsor: str | None


class PolicyStateV1(StrictModel):
    selected: str; actively_decided: bool


class SupportV1(StrictModel):
    tier: str | None; covered_assets: list[str]


class ActionRecordV1(StrictModel):
    action_type: str; locked_round: StrictInt; capability: str | None
    target_key: str | None; cost: StrictInt

    @model_validator(mode="after")
    def valid_action_record(self) -> "ActionRecordV1":
        if self.locked_round < 0 or self.cost < 0:
            raise ValueError("invalid action round or cost")
        return self


class ActionEnvelopeV1(StrictModel):
    id: StrictStr = Field(pattern=HEX64_RE.pattern)
    source_round: StrictInt; source_command: str; effect_round: StrictInt
    record: ActionRecordV1

    @model_validator(mode="after")
    def valid_action_rounds(self) -> "ActionEnvelopeV1":
        if self.source_round < 0 or self.effect_round < self.source_round:
            raise ValueError("invalid action envelope rounds")
        return self


class HiringOrderV1(StrictModel):
    id: str; option: str; ordered_round: StrictInt; remaining_lead: StrictInt
    status: Literal["pending", "arrived", "cancelled"]; arrival_round: StrictInt | None

    @model_validator(mode="after")
    def valid_hiring_order(self) -> "HiringOrderV1":
        if self.ordered_round < 0 or self.remaining_lead < 0 or (self.arrival_round is not None and self.arrival_round < self.ordered_round):
            raise ValueError("invalid hiring order rounds")
        return self


class StaffHireV1(StrictModel):
    order_id: str; option: str; arrival_round: StrictInt

    @field_validator("arrival_round")
    @classmethod
    def nonnegative_arrival(cls, value: int) -> int:
        if value < 0: raise ValueError("arrival round must be nonnegative")
        return value


class DebtV1(StrictModel):
    signal: str; episode_id: StrictInt; capability: str; opened_round: StrictInt
    amount: StrictInt; settled_round: StrictInt | None

    @model_validator(mode="after")
    def valid_debt(self) -> "DebtV1":
        if self.episode_id < 0 or self.opened_round < 0 or self.amount < 0 or (self.settled_round is not None and self.settled_round < self.opened_round):
            raise ValueError("invalid debt money or rounds")
        return self


class SignalV1(StrictModel):
    key: str; episode_id: StrictInt; capability: str; metric: str; metric_kind: str
    value: float; severity: Literal["warning", "critical"]
    status: Literal["open", "cleared", "fired"]
    first_shown_round: StrictInt; cleared_round: StrictInt | None; fire_round: StrictInt | None
    cleared_by: list[str]; was_actionable: bool; cheapest_fix_when_raised: StrictInt | None

    @model_validator(mode="after")
    def valid_signal(self) -> "SignalV1":
        rounds = (self.first_shown_round, self.cleared_round, self.fire_round)
        if self.episode_id < 0 or self.first_shown_round < 0 or any(value is not None and value < self.first_shown_round for value in rounds[1:]):
            raise ValueError("invalid signal rounds")
        if isinstance(self.value, bool) or not math.isfinite(self.value):
            raise ValueError("signal value must be finite")
        if self.cheapest_fix_when_raised is not None and self.cheapest_fix_when_raised < 0:
            raise ValueError("signal repair cost must be nonnegative")
        return self


class EventOutcomeV1(StrictModel):
    revenue_loss: StrictInt | None
    scorecard: dict[Literal["financial", "customer", "internal_process", "learning_growth"], StrictInt]


class EventEvidenceV1(StrictModel):
    key: StrictStr; node: str | None; blast_radius: list[StrictStr]
    base_rto_hours: float | None = None; failover_exists: bool | None = None
    failover_factor: float | None = None; staffing_modifier: float | None = None
    duration_hours: float | None = None; outcomes: EventOutcomeV1 | None = None

    @model_validator(mode="after")
    def finite_outage(self) -> "EventEvidenceV1":
        for value in (self.base_rto_hours, self.failover_factor, self.staffing_modifier, self.duration_hours):
            if value is not None and (isinstance(value, bool) or not math.isfinite(value) or value < 0):
                raise ValueError("outage evidence values must be finite and nonnegative")
        return self


class SuppressionV1(StrictModel):
    event_key: StrictStr; round: StrictInt
    reason: Literal["cap", "already_fired"]; capability: str | None


class SignalEpisodeV1(StrictModel):
    key: StrictStr; episode_id: StrictInt


class PreventionEvidenceV1(StrictModel):
    key: StrictStr; round: StrictInt; option: StrictStr; rationale_tag: StrictStr
    cost: StrictInt; effect: Literal["prevent_current_round"]
    signal_episodes: list[SignalEpisodeV1]

    @model_validator(mode="after")
    def valid_cost_and_round(self) -> "PreventionEvidenceV1":
        if self.round < 0 or self.cost < 0:
            raise ValueError("prevention round/cost out of range")
        return self


class EventHistoryV1(StrictModel):
    round: StrictInt; fired: list[EventEvidenceV1]; suppressed: list[SuppressionV1]; prevented: list[PreventionEvidenceV1]


class ResponseV1(StrictModel):
    round: StrictInt; key: str; event: str; option: str; rationale_tag: str
    cost: StrictInt; effect: Literal["prevent_current_round", "none"]

    @model_validator(mode="after")
    def valid_response(self) -> "ResponseV1":
        if self.round < 0 or self.cost < 0:
            raise ValueError("response round and cost must be nonnegative")
        for value in (self.key, self.event, self.option, self.rationale_tag):
            if not isinstance(value, str) or not 1 <= len(value) <= 64 or not KEY_RE.fullmatch(value):
                raise ValueError("response identifiers must be bounded keys")
        return self


class TcoV1(StrictModel):
    asset_id: str; ordered_round: StrictInt; selected_categories: list[str]
    forecast: StrictInt; forecast_horizon_round: StrictInt; estimates: dict[str, StrictInt]

    @model_validator(mode="after")
    def valid_tco(self) -> "TcoV1":
        if not 1 <= len(self.asset_id) <= 64 or not KEY_RE.fullmatch(self.asset_id):
            raise ValueError("TCO asset id must be a bounded key")
        if self.ordered_round < 0 or self.forecast < 0 or self.forecast_horizon_round < 0 or any(value < 0 for value in self.estimates.values()):
            raise ValueError("TCO rounds and money must be nonnegative")
        return self


class RepairWitnessV1(StrictModel):
    candidate_key: StrictStr = Field(pattern=HEX64_RE.pattern)
    commands: list[CommandV1]; capital_cost: StrictInt; effective_round: StrictInt
    affordable: bool; operating_forecast: list[OperatingForecastV1]
    baseline_metric: float | bool; candidate_metric: float | bool
    emitted_action_ids: list[StrictStr] = Field(default_factory=list)
    credit_eligible: bool; assumptions: Literal["empty_future_decisions"]

    @field_validator("emitted_action_ids")
    @classmethod
    def valid_action_ids(cls, values: list[str]) -> list[str]:
        if any(not HEX64_RE.fullmatch(value) for value in values):
            raise ValueError("emitted action id must be sha256")
        if len(values) != len(set(values)):
            raise ValueError("duplicate emitted action id")
        return values


class RepairExcludedV1(StrictModel):
    candidate_key: StrictStr = Field(pattern=HEX64_RE.pattern)
    reason: Literal[
        "not_found", "invalid_input", "invalid_reference", "conflicting_commands", "unaffordable",
        "revision_conflict", "locked", "round_state", "pack_mismatch", "scope_exists",
        "unsupported_operation", "arrival_after_game_end", "invalid_output", "held_response_ineligible",
        "command_key_collision", "baseline_not_raised", "metric_not_repaired", "no_positive_path",
        "no_in_game_effect",
    ]


class RepairAssessmentV1(StrictModel):
    round: StrictInt; signal: str
    status: Literal["verified", "unassessed"]
    reason: Literal["bounded_catalogue_no_verified_repair"] | None
    initial_state_digest: StrictStr = Field(pattern=HEX64_RE.pattern)
    merged_sheet_digest: StrictStr = Field(pattern=HEX64_RE.pattern)
    candidates: list[RepairWitnessV1]
    repaired_but_uncredited: list[RepairWitnessV1]
    excluded: list[RepairExcludedV1]

    @model_validator(mode="after")
    def valid_status(self) -> "RepairAssessmentV1":
        if self.round < 0:
            raise ValueError("assessment round out of range")
        if self.status == "verified" and self.reason is not None:
            raise ValueError("verified assessment cannot have an unassessed reason")
        if self.status == "unassessed" and self.reason is None:
            raise ValueError("unassessed assessment requires a reason")
        return self


class UnpricedSignalExposureV1(StrictModel):
    signal: str; episode_id: StrictInt; capability: str; reason: Literal["unpriced", "unassessed"]


class CheckpointStateV1(StrictModel):
    strategy: str; strategy_declared_round: StrictInt
    assets: dict[str, AssetV1]; connections: dict[str, ConnectionV1]
    projects: dict[str, ProjectV1]; hiring_orders: dict[str, HiringOrderV1]
    staff_hires: list[StaffHireV1]; support: SupportV1
    rollouts: dict[str, RolloutV1]; unit_resistance: dict[str, float]
    governance: dict[str, GovernanceStateV1]; primary: dict[str, str | None]
    policies: dict[str, PolicyStateV1]; capital_balance: StrictInt; operating_reserve: StrictInt
    cost_ledger: list[CostEntryV1]; technical_debt: list[DebtV1]
    signal_ledger: list[SignalV1]; action_history: list[ActionEnvelopeV1]
    available_funds_by_round: list[StrictInt]; event_history: list[EventHistoryV1]
    response_history: list[ResponseV1]; tco_forecasts: list[TcoV1]
    repair_assessment_history: list[RepairAssessmentV1]; unpriced_signal_exposures: list[UnpricedSignalExposureV1]

    @model_validator(mode="after")
    def validate_state(self) -> "CheckpointStateV1":
        if not KEY_RE.fullmatch(self.strategy) or not self.strategy_declared_round >= 0:
            raise ValueError("invalid strategy or declared round")
        if any(k != v.id for k, v in self.assets.items()):
            raise ValueError("asset map key must equal asset id")
        if any(not KEY_RE.fullmatch(k) or len(k) > 64 for k in self.assets) or any(v.units <= 0 or v.installed_round < 0 for v in self.assets.values()):
            raise ValueError("invalid asset identity or units")
        if any(k != v.id for k, v in self.projects.items()):
            raise ValueError("project map key must equal project id")
        if any(not KEY_RE.fullmatch(k) or len(k) > 64 for k in self.projects):
            raise ValueError("invalid project identity")
        if any(v is not None and v not in self.assets for v in self.primary.values()):
            raise ValueError("primary references unknown asset")
        if set(self.primary) - set(CAPABILITIES):
            raise ValueError("primary references unknown capability")
        if any(not 0 <= value <= 1 or not math.isfinite(value) for value in self.unit_resistance.values()):
            raise ValueError("unit resistance out of range")
        if any(k != v.id for k, v in self.connections.items()):
            raise ValueError("connection map key must equal connection id")
        if any(k != v.id for k, v in self.hiring_orders.items()):
            raise ValueError("hiring order map key must equal order id")
        if any(not KEY_RE.fullmatch(k) or len(k) > 64 for k in self.connections | self.hiring_orders | self.rollouts | self.governance | self.policies | self.unit_resistance):
            raise ValueError("invalid checkpoint map key")
        if any(k not in self.assets for k in self.rollouts):
            raise ValueError("rollout references unknown asset")
        if any(k not in CAPABILITIES for k in self.governance | self.primary):
            raise ValueError("governance/primary capability key is unknown")
        if len(self.staff_hires) != len({x.order_id for x in self.staff_hires}):
            raise ValueError("duplicate staff hire order")
        covered = self.support.covered_assets
        if len(covered) != len(set(covered)) or any(x not in self.assets for x in covered):
            raise ValueError("support covered asset join invalid")
        if len(self.action_history) != len({x.id for x in self.action_history}):
            raise ValueError("duplicate action envelope")
        if any(x.effect_round < x.source_round or x.source_round < 0 for x in self.action_history):
            raise ValueError("action round ordering invalid")
        if len(self.event_history) != len({x.round for x in self.event_history}) or [x.round for x in self.event_history] != sorted(x.round for x in self.event_history):
            raise ValueError("event history must be unique and ascending")
        if len(self.response_history) != len({(x.round, x.key) for x in self.response_history}):
            raise ValueError("duplicate response history")
        if len(self.tco_forecasts) != len({(x.asset_id, x.ordered_round) for x in self.tco_forecasts}):
            raise ValueError("duplicate TCO forecast")
        if any(x.asset_id not in self.assets for x in self.tco_forecasts):
            raise ValueError("TCO references unknown asset")
        keys = [(x.round, x.signal) for x in self.repair_assessment_history]
        if len(keys) != len(set(keys)) or keys != sorted(keys):
            raise ValueError("repair assessment history must be canonical")
        if any(x.round < 0 for x in self.event_history + self.response_history + self.repair_assessment_history):
            raise ValueError("negative checkpoint round")
        for key, project in self.projects.items():
            if project.asset_id not in self.assets and project.status not in {"cancelled", "abandoned"}:
                raise ValueError("project references unknown asset")
        if any(x < 0 for x in self.available_funds_by_round):
            raise ValueError("available funds cannot be negative")
        return self


# A few inter-packet DTOs are declared before the detailed checkpoint records so
# their public order mirrors the contract.  Resolve those forward references once
# the complete P1 type graph exists.
for _model in (RunViewV1, EstateDeltaV1, OrgDeltaV1, TransitionV1):
    _model.model_rebuild()
