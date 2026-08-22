"""Runtime team state consumed by the pure scorer.

This is the second input to the engine, alongside the parsed `Casepack`. It is a
plain-data snapshot of one team at one round: the architecture graph they have
built, what they funded, who they assigned, and the signal ledger. The engine
takes it in and returns results out; it never mutates it, reads a clock, or
touches a database (invariant I2).

The evolution of this state between rounds -- training decay, the adoption
simulation, the change-volume resistance shock -- is round orchestration and
belongs to module 1.6. 1.4 scores a given snapshot. Where a field here is the
*output* of a 1.6 simulation (adoption, resistance), the traceability matrix
(design/02 section B) already lists it as persisted in a runtime table
(`round_result.adoption`, `org_unit.resistance`); 1.4 reads it, it does not
invent the formula that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


EdgeKind = Literal["network", "integration", "failover"]
ProcessState = Literal["redesigned", "partial", "unchanged"]


@dataclass(frozen=True)
class ArchNode:
    """One placed thing in the team's architecture graph.

    `throughput` is the node's capacity in the demand unit of the capabilities it
    serves; `None` means the node imposes no capacity ceiling (a client endpoint,
    a firewall). `serves` lists the capability keys this node participates in.
    """

    key: str
    roles_filled: tuple[str, ...]
    availability: float
    installed_round: int
    service_life_rounds: int
    serves: tuple[str, ...] = ()
    throughput: float | None = None
    owns_entities: tuple[tuple[str, str], ...] = ()  # (entity_key, level_of_detail)
    #: Runtime placement of the deployed item behind this node, one of on_prem/cloud/saas
    #: (never the derived `hybrid`, CONTRACTS.md placement). The `placement_count`
    #: precondition reads it; it is a 1.6 round-evolution field the pure 1.5 engine only
    #: reads. `None` means the round runner has not populated it (unused by the reference pack).
    placement: str | None = None

    @property
    def is_client_access(self) -> bool:
        return "client_access" in self.roles_filled


@dataclass(frozen=True)
class ArchEdge:
    src: str
    dst: str
    kind: EdgeKind = "network"


@dataclass(frozen=True)
class DeploymentState:
    """A catalog item placed into an org unit, with its rollout state.

    `is_primary_for` names the capability this deployment is the primary rollout
    of (the application whose adoption defines the capability's Organisation
    term). A deployment can serve several capabilities but is primary for at most
    one.
    """

    key: str
    catalog_key: str
    org_unit: str
    people_affected: int
    trained_count: int
    process: ProcessState
    adoption: float
    ever_trained: bool
    serves: tuple[str, ...] = ()
    is_primary_for: str | None = None
    initiated: bool = True
    abandoned: bool = False


@dataclass(frozen=True)
class OrgUnitState:
    key: str
    resistance: float  # persisted; design/02 org_unit.resistance


@dataclass(frozen=True)
class GovernanceState:
    capability: str
    owner_assigned: bool
    sponsor_assigned: bool


@dataclass(frozen=True)
class StaffPool:
    """The IT capacity pool (G1). `load_fte` is the operational load of everything
    the firm runs; `staff_fte` is the capacity available to carry it."""

    staff_fte: float
    load_fte: float


@dataclass(frozen=True)
class SignalState:
    key: str
    capability: str
    actionable: bool
    acted_before_fire: bool


@dataclass(frozen=True)
class ActionRecord:
    """One committed team action, as the immutable snapshot the 1.5 engine reads to decide
    which action cleared which signal (1.5 contract-spec section 5.5.1).

    Append-only history produced by 1.6 round evolution; the pure 1.5 engine never writes it.
    `action_type` is one of the closed ten-key `checks.ACTION_TYPES` set; `locked_round` is the
    round the team committed the action (the responsiveness clock); `capability` is the
    capability it targets (`None` = firm-wide, e.g. `add_policy`); `target_key` is the exact
    catalog item / platform tier / policy / node acted on; `cost` is the capex actually
    committed for it.
    """

    action_type: str
    locked_round: int
    capability: str | None = None
    target_key: str | None = None
    cost: int = 0


@dataclass(frozen=True)
class DecisionState:
    """One line of committed spend, keyed to a capability and an R/G/T tag.

    Feeds strategic alignment, portfolio concentration, the R/G/T mix and the
    maintenance floor (design/02 section C, all firm-wide).
    """

    key: str
    category: str
    capability: str | None
    capex: int
    rgt_tag: str  # run | grow | transform
    is_maintenance: bool = False


@dataclass(frozen=True)
class StakeholderDecisionAlignment:
    """Pre-resolved alignment of the team's decisions to one stakeholder's
    preferences, in [0, 1], and the capabilities that stakeholder cares about.

    Resolving a stakeholder's archetype-default-plus-override preference block
    against the decision state is the preference-model half of the two engines
    (design/01 section 5). 1.4 consumes the alignment scalar and the caring set;
    it does not re-run the preference resolution, which is authored content plus
    1.3's harvest, not scoring.
    """

    stakeholder: str
    alignment: float
    cares_about: tuple[str, ...]


@dataclass(frozen=True)
class PolicyDecisionState:
    """One information-policy switch as the team currently holds it (1.4 closeout).

    `policy` is a `PolicyOption.key`; `selected` is one of that policy's declared
    `options` (a machine key, never prose). `actively_decided` records whether the
    team committed a choice this round -- including deliberately RETAINING the
    authored default, which is a managed decision and distinct from never opening
    the screen.

    This is scorer input only. The runtime table that PRODUCES it round to round is
    1.6/2.x's, and that table carries `instance_id`; the pure scorer receives an
    immutable snapshot and performs no I/O (invariant I2). Interface FROZEN by the
    1.4 closeout packet; producer/consumer contract in `CONTRACTS.md`.
    """

    policy: str
    selected: str
    actively_decided: bool


@dataclass(frozen=True)
class TeamState:
    round: int
    declared_strategy: str
    nodes: tuple[ArchNode, ...]
    edges: tuple[ArchEdge, ...]
    deployments: tuple[DeploymentState, ...]
    org_units: tuple[OrgUnitState, ...]
    governance: tuple[GovernanceState, ...]
    staff: StaffPool
    signals: tuple[SignalState, ...]
    decisions: tuple[DecisionState, ...]
    stakeholder_alignments: tuple[StakeholderDecisionAlignment, ...] = ()
    #: The team's current information-policy switch selections. Empty means no
    #: switch was touched: every pack policy resolves to its authored `default`
    #: with `actively_decided=False` (1.4 closeout decision 6), which keeps the
    #: null path deterministic and backward-compatible with existing callers while
    #: still charging the information-policy discipline factor.
    policy_decisions: tuple[PolicyDecisionState, ...] = ()
    #: Immutable action history (1.6 output, 1.5 contract-spec section 5.5.1). The empty-tuple
    #: default preserves every existing constructor and the 1.4 pin; the 1.5 signal engine
    #: reads it to match a committed action to the signal it clears.
    action_history: tuple[ActionRecord, ...] = ()
    #: Remaining capital available for NEW commitments per round, index r-1 for round r, AFTER
    #: that round's already-committed spend is subtracted (1.6 output, contract-spec 5.5.2).
    #: The affordability test (`was_actionable`, O1) reads it; committed spend is already
    #: deducted, so it never double-counts. Empty default preserves existing constructors.
    available_funds_by_round: tuple[int, ...] = ()
    #: Per-capability debt ratio (1.6 output, contract-spec S5). `None` means the round runner
    #: did not supply it; the `debt_above` precondition then raises `MissingRoundInputError`
    #: rather than silently reading FALSE. Unreachable in v1 (no reference-pack event uses it).
    debt_ratio_by_capability: dict[str, float] | None = None

    # -- convenience indexes, all pure ------------------------------------------
    def node(self, key: str) -> ArchNode | None:
        for n in self.nodes:
            if n.key == key:
                return n
        return None

    def nodes_serving(self, capability: str) -> tuple[ArchNode, ...]:
        return tuple(n for n in self.nodes if capability in n.serves)

    def deployments_serving(self, capability: str) -> tuple[DeploymentState, ...]:
        return tuple(d for d in self.deployments if capability in d.serves)

    def primary_deployment(self, capability: str) -> DeploymentState | None:
        for d in self.deployments:
            if d.is_primary_for == capability:
                return d
        return None

    def org_unit(self, key: str) -> OrgUnitState | None:
        for u in self.org_units:
            if u.key == key:
                return u
        return None

    def governance_for(self, capability: str) -> GovernanceState | None:
        for g in self.governance:
            if g.capability == capability:
                return g
        return None
