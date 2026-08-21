"""Riverside Grocers, round 3 -- the scoreable team state behind the pinned figures.

This is the architecture that PRODUCES Technology 0.750, Organisation 0.507,
Management 0.648, realised 0.249 for `order_fulfilment` (spec 5.7). Every input
here is a fact the mockups pinned (0.3 spec section 5.6, 0.4) or a coherent
consequence of one; the engine reads them and computes the terms. Nothing is
asserted alongside the result.

The order-fulfilment serving graph is modelled at the granularity the spec's worked
example implies -- a store endpoint reaches the order record across the WAN through
the firewall and the core switch -- so the four single points of failure it names
(`wan_link`, `hq_firewall`, `core_switch`, `order_app`) fall out of the topology as
articulation points, not from a hand-written list.

CALIBRATION KNOBS. A few inputs are set so the three terms land on the pinned
figures, and each is a real state value with a stated meaning:
  * ORDER_THROUGHPUT       -- order-system throughput vs demand -> capacity (Technology)
  * ORDER_STORE_INSTALLED  -- one node a round newer, tuning currency (Technology)
  * STORE_OPS_RESISTANCE   -- store-operations resistance (Organisation)
  * OPERATIONS_ALIGNMENT   -- operations' alignment to the order rollout (Management)
They were fitted against the approved mockup figures; the fit is the pin (spec 5.7).
None of them is a mockup-pinned number -- the mockups pin what the terms come to,
not the raw throughput or resistance behind them -- so fitting them is authoring the
architecture, not asserting the answer.
"""

from __future__ import annotations

from app.engine.state import (
    ArchEdge,
    ArchNode,
    DecisionState,
    DeploymentState,
    GovernanceState,
    OrgUnitState,
    PolicyDecisionState,
    SignalState,
    StaffPool,
    StakeholderDecisionAlignment,
    TeamState,
)

ROUND = 3

# -- calibration knobs (see module docstring) -----------------------------------
ORDER_STORE_INSTALLED = 1     # newer than the rest of the estate -> currency lift
ORDER_THROUGHPUT = 7225.0     # order system throughput -> capacity (Technology)
STORE_OPS_RESISTANCE = 0.4665  # organisation term throttle
OPERATIONS_ALIGNMENT = 0.3648  # operations' displeasure with the order rollout

# A throughput far above any round-3 demand: a node that imposes no capacity ceiling.
UNCONSTRAINED = 10_000_000.0


def _nodes() -> tuple[ArchNode, ...]:
    return (
        # --- order fulfilment serving graph ------------------------------------
        ArchNode(
            key="store_pc", roles_filled=("client_access",), availability=0.95,
            installed_round=1, service_life_rounds=4,
            serves=("order_fulfilment", "store_operations", "financial_reporting"),
            throughput=UNCONSTRAINED,
        ),
        ArchNode(
            key="wan_link", roles_filled=("network_path",), availability=0.98,
            installed_round=0, service_life_rounds=6,
            serves=("order_fulfilment", "store_operations"), throughput=UNCONSTRAINED,
        ),
        ArchNode(
            key="hq_firewall", roles_filled=("network_path", "security_monitoring"),
            availability=0.99, installed_round=0, service_life_rounds=6,
            serves=("order_fulfilment",), throughput=UNCONSTRAINED,
        ),
        ArchNode(
            key="core_switch", roles_filled=("network_path",), availability=0.99,
            installed_round=0, service_life_rounds=6,
            serves=("order_fulfilment",), throughput=UNCONSTRAINED,
        ),
        ArchNode(
            key="order_app", roles_filled=("order_app",), availability=0.98,
            installed_round=0, service_life_rounds=6,
            serves=("order_fulfilment", "store_operations"),
            throughput=ORDER_THROUGHPUT,  # near capacity: ~7,225 of 12,000 round-3 demand
            # The order application processes orders but is NOT their store of record --
            # the order DB cluster is (order_store). Keeping the record on the cluster is
            # what makes the serving path run through order_app to reach it, so order_app
            # is an interior single point of failure rather than the path's endpoint. The
            # app remains the (unintegrated) second holder of inventory.
            owns_entities=(("inventory", "sku_location"),),
        ),
        ArchNode(
            key="order_store", roles_filled=("transaction_store",), availability=0.99,
            installed_round=ORDER_STORE_INSTALLED, service_life_rounds=6,
            serves=("order_fulfilment", "store_operations"), throughput=UNCONSTRAINED,
            owns_entities=(("order", "order_line"),),
        ),
        ArchNode(
            key="inventory_app", roles_filled=("wms_integration", "inventory_app"),
            availability=0.99, installed_round=0, service_life_rounds=6,
            serves=("order_fulfilment",), throughput=UNCONSTRAINED,
            owns_entities=(("inventory", "sku_location"),),
        ),
        # --- store operations extra reach --------------------------------------
        ArchNode(
            key="pos_node", roles_filled=("pos_app", "transaction_store"), availability=0.96,
            installed_round=0, service_life_rounds=4,
            serves=("store_operations",), throughput=6000.0,
            owns_entities=(("sale", "individual_transaction"), ("product", "sku")),
        ),
        # --- finance -----------------------------------------------------------
        ArchNode(
            key="accounting_node", roles_filled=("accounting_app", "transaction_export"),
            availability=0.98, installed_round=0, service_life_rounds=6,
            serves=("financial_reporting",), throughput=UNCONSTRAINED,
            owns_entities=(("ledger", "account_period"), ("sale", "daily_store_total")),
        ),
    )


def _edges() -> tuple[ArchEdge, ...]:
    return (
        ArchEdge("store_pc", "wan_link", "network"),
        ArchEdge("wan_link", "hq_firewall", "network"),
        ArchEdge("hq_firewall", "core_switch", "network"),
        ArchEdge("core_switch", "order_app", "network"),
        # order is integrated between the app and its store of record: no penalty.
        ArchEdge("order_app", "order_store", "integration"),
        # inventory is NOT integrated between the order app and the warehouse system:
        # the two disagree about inventory numbers (entities.yaml auditor challenge).
        ArchEdge("order_app", "inventory_app", "network"),
        # store operations reach
        ArchEdge("core_switch", "pos_node", "network"),
        # finance reach
        ArchEdge("core_switch", "accounting_node", "network"),
    )


def _deployments() -> tuple[DeploymentState, ...]:
    return (
        # The order rollout: the primary rollout of order_fulfilment. 49 of 140
        # store-operations staff trained (0.35), process partly redesigned, adoption
        # 0.61 -- exactly the spec 5.6 worked example.
        DeploymentState(
            key="dep_order_mgmt", catalog_key="order_mgmt_v42", org_unit="store_operations",
            people_affected=140, trained_count=49, process="partial", adoption=0.61,
            ever_trained=True, serves=("order_fulfilment", "store_operations"),
            is_primary_for="order_fulfilment",
        ),
        # The warehouse system: live with no training. It serves order_fulfilment but
        # is NOT its primary rollout; its neglect shows up in follow-through and in the
        # wh_rollout_01 signal, not by dragging the order term.
        DeploymentState(
            key="dep_centraline", catalog_key="centraline_im7", org_unit="warehouse",
            people_affected=34, trained_count=0, process="unchanged", adoption=0.22,
            ever_trained=False, serves=("order_fulfilment",),
        ),
        DeploymentState(
            key="dep_pos", catalog_key="pos_system_2011", org_unit="store_operations",
            people_affected=62, trained_count=62, process="redesigned", adoption=0.97,
            ever_trained=True, serves=("store_operations",), is_primary_for="store_operations",
        ),
        DeploymentState(
            key="dep_accounting", catalog_key="accounting_package", org_unit="finance",
            people_affected=8, trained_count=8, process="redesigned", adoption=0.94,
            ever_trained=True, serves=("financial_reporting",),
            is_primary_for="financial_reporting",
        ),
        DeploymentState(
            key="dep_spreadsheets", catalog_key="store_spreadsheets", org_unit="store_operations",
            people_affected=140, trained_count=70, process="unchanged", adoption=0.48,
            ever_trained=True, serves=("store_operations", "financial_reporting"),
        ),
    )


def _org_units() -> tuple[OrgUnitState, ...]:
    return (
        OrgUnitState("store_operations", resistance=STORE_OPS_RESISTANCE),
        OrgUnitState("warehouse", resistance=0.62),
        OrgUnitState("finance", resistance=0.18),
    )


def _governance() -> tuple[GovernanceState, ...]:
    return (
        # Two assignments (pack review): order fulfilment has an owner and a sponsor.
        GovernanceState("order_fulfilment", owner_assigned=True, sponsor_assigned=True),
        GovernanceState("store_operations", owner_assigned=True, sponsor_assigned=False),
        GovernanceState("financial_reporting", owner_assigned=True, sponsor_assigned=True),
    )


def _signals() -> tuple[SignalState, ...]:
    # Three open, actionable signals (pack open_signals: 3); two received no action.
    return (
        SignalState("ord_cap_01", "order_fulfilment", actionable=True, acted_before_fire=True),
        SignalState("wh_rollout_01", "order_fulfilment", actionable=True, acted_before_fire=False),
        SignalState("sec_identity_01", "firm_infrastructure", actionable=True, acted_before_fire=False),
    )


def _decisions() -> tuple[DecisionState, ...]:
    # A cost leader concentrating on the order chain and store operations, with a
    # maintenance line and NO customer-insight spend (the pack's standing review
    # warning). Spend feeds strategic alignment, concentration, R/G/T mix and the
    # maintenance floor.
    return (
        DecisionState("d_order_capacity", "platform_service", "order_fulfilment", 98000, "grow"),
        DecisionState("d_order_training", "training", "order_fulfilment", 34000, "grow"),
        DecisionState("d_store_ops", "application", "store_operations", 60000, "run", is_maintenance=True),
        DecisionState("d_finance", "application", "financial_reporting", 18000, "run", is_maintenance=True),
        DecisionState("d_infra", "platform_service", "firm_infrastructure", 12000, "grow"),
        DecisionState("d_marketing", "application", "marketing_sales", 20000, "transform"),
    )


def _policy_decisions() -> tuple[PolicyDecisionState, ...]:
    # An ATTENTIVE team (1.4 closeout decision 10): it opened the information-policy
    # screen and made an explicit call on all six switches, so policy_discipline is
    # 1.0 -- not an ignored screen. Each `selected` is the switch's existing authored
    # `default` (the permissive index-0 end); this preserves pack content and invents
    # no new team choice. Retaining the default IS a managed decision, so
    # `actively_decided=True`. Because every switch sits at the permissive end,
    # policy_alignment is whatever the frozen asymmetric formula computes against the
    # stakeholders who wanted stricter -- it is not tuned.
    return (
        PolicyDecisionState("data_collection", "everything_by_default", actively_decided=True),
        PolicyDecisionState("data_retention", "indefinite", actively_decided=True),
        PolicyDecisionState("data_access", "open_to_all_staff", actively_decided=True),
        PolicyDecisionState("access_logging", "unlogged", actively_decided=True),
        PolicyDecisionState("data_egress", "unrestricted", actively_decided=True),
        PolicyDecisionState("staff_monitoring", "untracked", actively_decided=True),
    )


def _stakeholder_alignments() -> tuple[StakeholderDecisionAlignment, ...]:
    # These are ROLLOUT-alignment scalars only (how well the capabilities a
    # stakeholder cares about are actually delivered). They deliberately EXCLUDE the
    # information-policy-switch dimension of spec 5.5, which the 1.4 closeout now
    # scores separately and firm-wide (management.policy_switch_alignment /
    # policy_discipline over the `policy_decisions` above). This scalar is unchanged.
    return (
        # Operations cares about the order chain and store operations. Their alignment
        # is low: the order system is near capacity and only a third of staff are
        # trained on it (ideal_reliability 0.99, ideal_training high -- both missed).
        StakeholderDecisionAlignment(
            "operations", alignment=OPERATIONS_ALIGNMENT,
            cares_about=("order_fulfilment", "store_operations"),
        ),
        StakeholderDecisionAlignment(
            "finance", alignment=0.78, cares_about=("financial_reporting",),
        ),
        StakeholderDecisionAlignment(
            "customer", alignment=0.35, cares_about=("customer_insight", "service"),
        ),
    )


def build_team_state() -> TeamState:
    return TeamState(
        round=ROUND,
        declared_strategy="cost_leadership",
        nodes=_nodes(),
        edges=_edges(),
        deployments=_deployments(),
        org_units=_org_units(),
        governance=_governance(),
        staff=StaffPool(staff_fte=2.0, load_fte=3.4),  # pack people block: 2.0 / 3.4
        signals=_signals(),
        decisions=_decisions(),
        stakeholder_alignments=_stakeholder_alignments(),
        policy_decisions=_policy_decisions(),
    )
