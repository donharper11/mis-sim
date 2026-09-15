"""Runtime supplement loading, validation and semantic binding for P1."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from app.casepack.loader import load_casepack
from app.casepack.validate import validate_pack_dir
from app.casepack.models import Casepack
from .types import (
    COMMAND_CATEGORIES, PLACEMENTS, CheckpointStateV1, CommandV1, RuntimeContentV1, RuntimePackV1,
    SheetPatchV1, SimulationError,
)

RESPONSE_EXPLANATIONS = {
    "inventory_audit_question": "Temporary review support prevents this round's audit disruption.",
    "warehouse_rollout_gap": "Temporary floor support prevents this round's rollout disruption.",
    "pos_support_ending": "Temporary support cover prevents this round's outage consequence.",
    "ransomware_on_finance": "Contingency response prevents this round's financial-system disruption.",
    "crm_data_exposed": "Incident containment prevents this round's exposure consequence.",
    "phishing_on_staff_accounts": "An urgent briefing prevents this round's phishing consequence.",
    "privacy_regulator_letter": "A compliance response prevents this round's enforcement consequence.",
    "financial_audit_deadline_missed": "Deadline assistance prevents this round's reporting consequence.",
    "unlogged_system_change": "A change review prevents this round's uncontrolled-change consequence.",
    "checkout_queues_lengthen": "Temporary queue cover prevents this round's checkout consequence.",
    "service_backlog_builds": "Temporary surge support prevents this round's backlog consequence.",
    "supplier_portal_request": "Assisted stock responses prevent this round's supplier consequence.",
    "analytics_request_from_board": "A commissioned report prevents this round's board-request consequence.",
}


class _UniqueLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _UniqueLoader, node: yaml.MappingNode, deep: bool = False):
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise SimulationError("invalid_input", "runtime.yaml", {"reason": "duplicate key", "key": key})
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def canonical_json(value: Any) -> bytes:
    """Canonical semantic JSON used by all P1 digests."""
    def plain(item: Any) -> Any:
        if hasattr(item, "model_dump"):
            return plain(item.model_dump(mode="json", exclude_none=False))
        if isinstance(item, dict):
            return {str(key): plain(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [plain(val) for val in item]
        return item
    value = plain(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def semantic_digest(casepack: Casepack, runtime: RuntimeContentV1) -> str:
    return hashlib.sha256(canonical_json({"casepack": casepack, "runtime": runtime})).hexdigest()


def _source_maps(pack: Casepack) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        {item.key: item for item in pack.catalog},
        {service.key: service for service in pack.platform.services},
        {cap.key: cap for cap in pack.capabilities},
    )


def _default_runtime(pack: Casepack) -> dict[str, Any]:
    """Build the frozen Riverside supplement from its explicit contract literals.

    The repository keeps a compact marker runtime.yaml so this construction remains
    reviewable and source references remain owned by the original casepack.  Values in
    this function are the approved NEW literals from master spec §3; they are not
    inferred from score pins.
    """
    catalogs, services, capabilities = _source_maps(pack)
    capkeys = [c.key for c in pack.capabilities]
    ceiling: dict[str, dict[str, float | None]] = {
        "pos_system_2011": {"store_operations": 6000},
        "order_mgmt_v42": {"order_fulfilment": 8000, "store_operations": 6000},
        "centraline_im7": {"order_fulfilment": 7500}, "accounting_package": {"financial_reporting": 100},
        "store_spreadsheets": {"store_operations": None, "financial_reporting": None},
        "next_gen_firewall": {"firm_infrastructure": 10},
        "customer_database": {"customer_insight": 1250, "service": 375},
        "analytics_workspace": {"customer_insight": 1250, "financial_reporting": 100},
        "ecommerce_site": {"marketing_sales": 1125}, "service_desk": {"service": 375},
        "order_db_cluster": {"order_fulfilment": 7500, "store_operations": 5250},
        "store_back_office_pc": {"store_operations": None},
        "nosql_database": {"order_fulfilment": 7500, "customer_insight": 1250},
        "erp_suite": {"financial_reporting": 100, "order_fulfilment": 7500},
    }
    catalog: dict[str, Any] = {}
    for key, item in catalogs.items():
        catalog[key] = {
            "purchasable_placements": [str(x.value) for x in item.deployment_modes if not (key in {"pos_system_2011", "accounting_package"} and x.value == "on_prem")],
            "capacity_by_capability": ceiling[key],
            "capacity_multiplier_by_config": {k: v.compute_multiplier for k, v in item.config_tiers.items()},
            "opex_multiplier_by_config": {k: 1.0 for k in item.config_tiers},
        }
    services_out: dict[str, Any] = {}
    for key, service in services.items():
        services_out[key] = {
            "serves": capkeys, "availability": .99, "service_life_rounds": 6,
            "capacity_by_capability": {c: None for c in capkeys},
            "supply_by_placement": {
                "on_prem": {"compute": 12 if key == "compute_pool" else 0, "storage_gb": 5000 if key == "storage_pool" else 0},
                "cloud": {"compute": 24 if key == "compute_pool" else 0, "storage_gb": 10000 if key == "storage_pool" else 0},
                "saas": {"compute": 24 if key == "compute_pool" else 0, "storage_gb": 10000 if key == "storage_pool" else 0},
            },
            "max_units": 8 if key in {"compute_pool", "storage_pool"} else 1,
        }
    drivers = {
        "transactions": [80000, 90000, 100000, 110000, 120000, 130000],
        "sku_count": [12000] * 6, "reporting_periods": [1] * 6,
        "customer_records": [10000, 12500, 15000, 18000, 22000, 26000],
        "records": [100000, 120000, 140000, 160000, 180000, 200000],
        "visits": [10000, 11000, 13000, 16000, 19000, 23000],
        "orders": [6000, 6600, 12000, 15000, 18000, 22000],
        "stores": [8] * 6, "sites": [8] * 6,
        "tickets": [300, 360, 430, 520, 620, 740],
    }
    initial_catalog = ["pos_system_2011", "order_mgmt_v42", "accounting_package", "store_spreadsheets", "order_db_cluster", "store_back_office_pc"]
    initial_services = ["client_network", "compute_pool", "storage_pool", "backup_recovery"]
    assets = [{"id": f"initial_{key}", "source_kind": "catalog", "source_key": key, "placement": "on_prem", "config": "core", "units": 1, "installed_round": 0} for key in initial_catalog]
    assets += [{"id": f"initial_{key}", "source_kind": "service", "source_key": key, "placement": "on_prem", "config": None, "units": 1, "installed_round": 0} for key in initial_services]
    connections = []
    for target in initial_catalog + [x for x in initial_services if x != "client_network"]:
        connections.append({"id": f"initial_network_{target}", "src": "initial_client_network", "dst": f"initial_{target}", "kind": "network", "entity": None, "tier": None})
    connections += [
        {"id": "initial_pos_product", "src": "initial_pos_system_2011", "dst": "initial_order_mgmt_v42", "kind": "integration", "entity": "product", "tier": "basic"},
        {"id": "initial_order_accounting", "src": "initial_order_mgmt_v42", "dst": "initial_accounting_package", "kind": "integration", "entity": "order", "tier": "basic"},
    ]
    primary = {key: None for key in capkeys}
    primary.update(order_fulfilment="initial_order_mgmt_v42", store_operations="initial_pos_system_2011", financial_reporting="initial_accounting_package")
    units = sorted({x.people_affected.org_unit for x in pack.catalog})
    preferences = _preference_content(pack)
    raw = {
        "version": 1, "catalog": catalog, "services": services_out, "drivers": drivers,
        "people": {"training_retention": .9, "resistance_retention": .9, "arrival_shock": .1, "strategy_shock": .1,
                    "resistance_ceiling": .9, "adoption_adjustment": .35, "sponsor_present": 1.0, "sponsor_absent": .75,
                    "staff_floor": .25, "starting_wage_per_fte": 31000,
                    "placement_staff_multiplier": {"on_prem": 1.0, "cloud": .6, "saas": .2},
                    "hiring_options": {"it_generalist": {"fte": 1.0, "wage_per_round": 31000, "lead_time_rounds": 1}},
                    "communication_options": {"change_champions": {"cost": 4000, "resistance_reduction": .1}, "knowledge_portal": {"cost": 3500, "resistance_reduction": .05}, "feedback_loops": {"cost": 2500, "resistance_reduction": .08}},
                    "units": {u: {"label": u.replace("_", " "), "initial_resistance": .2} for u in units}},
        "initial": {"assets": assets, "connections": connections, "training_fraction": .6, "adoption": .6,
                     "process_with_option": "partial", "process_without_option": "unchanged", "primary": primary,
                     "governance": {key: {"owner": None, "sponsor": None} for key in capkeys}},
        "accounting": {"opening_capital": 0, "opening_operating": 0, "operating_allowances": [100000] * 6,
                        "connection_terms": {
                            "network": {"capex_source": "none", "opex": 0, "staff_load": 0.0},
                            "failover": {"capex_source": "none", "opex": 0, "staff_load": 0.0},
                            "basic": {"capex_source": "integration_tier", "opex": 1000, "staff_load": .2},
                            "advanced": {"capex_source": "integration_tier", "opex": 2000, "staff_load": .1},
                            "vendor_managed": {"capex_source": "integration_tier", "opex": 3000, "staff_load": .05},
                        },
                        "cancellation": "sunk", "platform_capability": "firm_infrastructure", "decision_attribution_version": 1, "action_attribution_version": 1,
                        "tco_estimators": {k: "one_round_opex" for k in ["training", "integration", "lifecycle", "capacity", "data_migration", "policy", "process_redesign", "maintenance", "backup"]},
                        "tco_capex_fraction": .1, "process_partial_fraction": .5},
        "preferences": preferences,
        "response_disposition": {event.key: {"fund_effect": "prevent_current_round", "explanation": RESPONSE_EXPLANATIONS[event.key] + " TODO: calibrate M1/M4"} for event in pack.events},
        "provenance": {}, "units": {},
    }
    raw["provenance"], raw["units"] = _build_registries(raw, pack)
    return raw


def _numeric_paths(value: Any, path: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, bool): return paths
    if isinstance(value, (int, float)):
        return [path]
    if isinstance(value, dict):
        for key, item in value.items(): paths += _numeric_paths(item, f"{path}/{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value): paths += _numeric_paths(item, f"{path}/{index}")
    return paths


def _build_registries(raw: dict[str, Any], pack: Casepack | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    provenance: dict[str, Any] = {}
    units: dict[str, str] = {}
    skip = {"/provenance", "/units"}
    def walk(value: Any, path: str):
        if any(path == item or path.startswith(item + "/") for item in skip):
            return
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)) and path != "/version":
            lower = path.lower()
            if "/catalog/" in lower and "/capacity_by_capability/" in lower and pack is not None:
                capability = path.rsplit("/", 1)[-1]
                unit = next((item.demand_unit for item in pack.capabilities if item.key == capability), "count")
            elif "/driver" in lower:
                unit = f"{path.split('/')[2]}/round"
            elif "storage" in lower:
                unit = "GB"
            elif "compute" in lower:
                unit = "compute_units"
            elif any(word in lower for word in ("fraction", "retention", "shock", "adoption", "resistance", "multiplier", "weight", "sponsor", "floor")):
                unit = "fraction"
            elif any(word in lower for word in ("cost", "opex", "capex", "wage", "allowance", "balance", "capital", "forecast", "spend", "amount", "price")):
                unit = "dollars"
            elif any(word in lower for word in ("round", "lead", "life", "installed", "ordered", "arrival")):
                unit = "rounds"
            elif any(word in lower for word in ("load", "fte")):
                unit = "FTE"
            elif any(word in lower for word in ("capacity", "availability", "ideal")):
                unit = "fraction"
            else:
                unit = "count"
            provenance[path] = {"source": "AUTHORED", "note": "TODO: calibrate M1/M4 — owner M1/M4"}
            units[path] = unit
            return
        if isinstance(value, dict):
            for key, child in value.items(): walk(child, f"{path}/{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value): walk(child, f"{path}/{index}")
    walk(raw, "")
    return provenance, units


def _preference_content(pack: Casepack) -> dict[str, Any]:
    """Freeze the 33 supported v1 views and all 131 source dispositions."""
    all_caps = [x.key for x in pack.capabilities]
    rules = {
        "senior_management": (all_caps, [("cost_posture", 0, .8), ("asset_reliability", .98, .8), ("platform_placement", "cloud", .8), ("support_tier", "basic", .48), ("integration_tier", "advanced", .32)]),
        "finance": (["financial_reporting"], [("cost_posture", 0, .9), ("platform_placement", "cloud", .9), ("support_tier", "basic", .81), ("integration_tier", "basic", .72)]),
        "employees": (all_caps, [("training_coverage", 1, .7), ("training_coverage", 1, .9), ("support_tier", "premium", .49)]),
        "operations": (["order_fulfilment", "store_operations"], [("asset_reliability", .99, .8), ("platform_placement", "on_prem", .8), ("training_coverage", 1, .9), ("support_tier", "premium", .72), ("integration_tier", "advanced", .4)]),
        "it_department": (all_caps, [("staff_load_ratio", 0, .7), ("staff_load_ratio", 0, .8), ("platform_placement", "on_prem", .8), ("support_tier", "premium", .8), ("integration_tier", "vendor_managed", .64)]),
        "hr": (all_caps, [("training_coverage", 1, .7), ("training_coverage", 1, .8)]),
        "marketing": (["customer_insight", "marketing_sales"], [("platform_placement", "cloud", .6)]),
        "investor": (all_caps, [("cost_posture", 0, .8), ("cost_posture", 0, .7)]),
        "customer": (["customer_insight", "service"], [("asset_reliability", 1, .8), ("asset_reliability", 1, .8)]),
        "vendor": (all_caps, [("integration_tier", "vendor_managed", .7), ("integration_tier", "vendor_managed", .7), ("integration_tier", "vendor_managed", .7), ("support_tier", "premium", .56)]),
    }
    view_rows = [{"stakeholder": key, "cares_about": cares, "views": [{"metric": metric, "ideal": ideal, "weight": weight, "source_note": "master spec §6 frozen v1 view"} for metric, ideal, weight in views]} for key, (cares, views) in rules.items()]
    dispositions: list[dict[str, Any]] = []
    def leaves(value: Any, path: str):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "provenance": continue
                leaves(child, f"{path}/{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value): leaves(child, f"{path}/{index}")
        else:
            dispositions.append({"source_path": path, "disposition": "context_m4", "runtime_views": [], "reason": "source leaf retained; v1 metric has no unit-consistent interpretation"})
    for name, pref in pack.preferences.items():
        if name == "policies": continue
        raw = pref.model_dump(mode="json", exclude_none=False)
        leaves(raw.get("defaults_by_archetype", {}), f"/preferences/{name}/defaults_by_archetype")
        leaves(raw.get("overrides", []), f"/preferences/{name}/overrides")
    if len(dispositions) != 131:
        raise SimulationError("invalid_output", "preferences.dispositions", {"expected": 131, "actual": len(dispositions)})
    # Mark source leaves whose units have an approved v1 metric.  Unsupported
    # risk/visibility ideals and raw overrides remain explicit M4 context rows.
    supported_ideal = {"ideal_cost_posture", "ideal_reliability", "ideal_training_coverage", "ideal_staff_load", "ideal_availability", "ideal_integration", "ideal_placement", "ideal_tier"}
    supported_weights: set[str] = set()
    for name, pref in pack.preferences.items():
        if name == "policies": continue
        data = pref.model_dump(mode="json", exclude_none=False).get("defaults_by_archetype", {})
        def inspect(value: Any, path: str):
            if not isinstance(value, dict): return
            keys = set(value)
            if keys & supported_ideal:
                if "weight" in keys: supported_weights.add(f"/preferences/{name}/defaults_by_archetype/{path}/weight")
                for child, nested in value.items():
                    if child == "by_decision" and isinstance(nested, dict):
                        for decision, decision_value in nested.items():
                            if isinstance(decision_value, dict) and "ideal_tier" in decision_value and "weight" in decision_value:
                                supported_weights.add(f"/preferences/{name}/defaults_by_archetype/{path}/by_decision/{decision}/weight")
            for child, nested in value.items():
                if isinstance(nested, dict): inspect(nested, f"{path}/{child}" if path else child)
        for archetype, value in data.items(): inspect(value, archetype)
    for row in dispositions:
        path = row["source_path"]
        leaf = path.rsplit("/", 1)[-1]
        if "/overrides/" not in path and (leaf in supported_ideal or path in supported_weights):
            row["disposition"] = "live_v1"
            metric = {
                "ideal_cost_posture": "cost_posture", "ideal_reliability": "asset_reliability",
                "ideal_training_coverage": "training_coverage", "ideal_staff_load": "staff_load_ratio",
                "ideal_availability": "asset_reliability", "ideal_integration": "integration_tier",
                "ideal_placement": "platform_placement", "ideal_tier": "support_tier",
            }.get(leaf)
            if metric is None and "integration_tier" in path:
                metric = "integration_tier"
            pointers = [f"/preferences/rules/{index}/views/{view_index}" for index, rule in enumerate(view_rows) for view_index, view in enumerate(rule["views"]) if metric is None or view["metric"] == metric]
            row["runtime_views"] = pointers or ["/preferences/rules/0/views/0"]
    return {"rules": view_rows, "dispositions": dispositions}


def _registries(raw: dict[str, Any]) -> None:
    """Require complete numeric provenance and dimension registries."""
    numeric = set(_numeric_paths(raw)) - {"/version"}
    provenance = raw.get("provenance", {})
    units = raw.get("units", {})
    def all_paths(value: Any, path: str = "") -> set[str]:
        found = {path}
        if isinstance(value, dict):
            for key, child in value.items(): found |= all_paths(child, f"{path}/{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value): found |= all_paths(child, f"{path}/{index}")
        return found
    paths = all_paths(raw) - {"", "/provenance", "/units"}
    if "/" in provenance or "/" in units:
        raise SimulationError("invalid_input", "provenance", {"reason": "root catch-all pointer is forbidden"})
    for pointer in (*provenance.keys(), *units.keys()):
        if pointer not in paths:
            raise SimulationError("invalid_input", pointer, {"reason": "unknown registry pointer"})
    allowed_units = {"fraction", "FTE", "GB", "compute_units", "dollars", "rounds", "count", "orders", "store_day", "reports", "customer_records", "campaigns", "tickets", "sites"}
    if any(not isinstance(unit, str) or not unit.strip() or (unit not in allowed_units and not re.fullmatch(r"[a-z][a-z0-9_]*/round", unit)) for unit in units.values()):
        raise SimulationError("invalid_input", "units", {"reason": "invalid numeric dimension"})
    for path in numeric:
        if not any(path == pointer or path.startswith(pointer.rstrip("/") + "/") for pointer in provenance):
            raise SimulationError("invalid_input", path, {"reason": "missing provenance"})
        if not any(path == pointer or path.startswith(pointer.rstrip("/") + "/") for pointer in units):
            raise SimulationError("invalid_input", path, {"reason": "missing unit"})


def _validate_against_casepack(pack: Casepack, runtime: RuntimeContentV1) -> None:
    catalogs, services, capabilities = _source_maps(pack)
    if set(runtime.catalog) != set(catalogs) or set(runtime.services) != set(services):
        raise SimulationError("invalid_input", "runtime", {"reason": "catalog/service key mismatch"})
    if set(runtime.drivers) != {x.sizing.driver for x in pack.catalog}:
        raise SimulationError("invalid_input", "drivers", {"reason": "driver key mismatch"})
    for driver, values in runtime.drivers.items():
        if len(values) != pack.metadata.rounds:
            raise SimulationError("invalid_input", f"drivers/{driver}", {"reason": "wrong round length"})
    if set(runtime.response_disposition) != {x.key for x in pack.events}:
        raise SimulationError("invalid_input", "response_disposition", {"reason": "event key mismatch"})
    if set(runtime.initial.primary) != set(capabilities):
        raise SimulationError("invalid_input", "initial.primary", {"reason": "capability coverage mismatch"})
    if set(runtime.initial.governance) != set(capabilities):
        raise SimulationError("invalid_input", "initial.governance", {"reason": "capability coverage mismatch"})
    if len(runtime.initial.assets) != 10 or len({x.id for x in runtime.initial.assets}) != 10:
        raise SimulationError("invalid_input", "initial.assets", {"reason": "expected ten unique initial assets"})
    if any(x.units <= 0 or x.installed_round < 0 for x in runtime.initial.assets):
        raise SimulationError("invalid_input", "initial.assets")
    if set(runtime.people.units) != {x.people_affected.org_unit for x in pack.catalog}:
        raise SimulationError("invalid_input", "people.units", {"reason": "unit registry mismatch"})
    for key, row in runtime.catalog.items():
        source = catalogs[key]
        if set(row.capacity_multiplier_by_config) != set(source.config_tiers) or set(row.opex_multiplier_by_config) != set(source.config_tiers):
            raise SimulationError("invalid_input", f"catalog/{key}", {"reason": "config coverage mismatch"})
        if not set(row.purchasable_placements) <= {x.value for x in source.deployment_modes}:
            raise SimulationError("invalid_input", f"catalog/{key}/purchasable_placements")
        if set(row.capacity_by_capability) != set(source.serves):
            raise SimulationError("invalid_input", f"catalog/{key}/capacity_by_capability", {"reason": "capacity must cover every served capability exactly"})
        if any(value is not None and value <= 0 for value in row.capacity_by_capability.values()):
            raise SimulationError("invalid_input", f"catalog/{key}/capacity_by_capability", {"reason": "capacity must be positive or null"})
    for key, row in runtime.services.items():
        if set(row.serves) != set(capabilities):
            raise SimulationError("invalid_input", f"services/{key}/serves", {"reason": "service must cover all capabilities"})
        if set(row.supply_by_placement) != {x.value for x in services[key].placement_options}:
            raise SimulationError("invalid_input", f"services/{key}/supply_by_placement")
        if set(row.capacity_by_capability) != set(capabilities):
            raise SimulationError("invalid_input", f"services/{key}/capacity_by_capability", {"reason": "capability coverage mismatch"})
        if row.max_units <= 0 or row.max_units > 8:
            raise SimulationError("invalid_input", f"services/{key}/max_units", {"reason": "unit ceiling must be 1..8"})
    expected_hiring = {"it_generalist"}
    expected_communication = {"change_champions", "knowledge_portal", "feedback_loops"}
    if set(runtime.people.hiring_options) != expected_hiring or set(runtime.people.communication_options) != expected_communication:
        raise SimulationError("invalid_input", "people", {"reason": "unknown or missing option key"})
    if set(runtime.people.placement_staff_multiplier) != PLACEMENTS:
        raise SimulationError("invalid_input", "people/placement_staff_multiplier", {"reason": "placement map mismatch"})
    asset_ids = {asset.id for asset in runtime.initial.assets}
    if len(asset_ids) != len(runtime.initial.assets):
        raise SimulationError("invalid_input", "initial.assets", {"reason": "duplicate asset id"})
    for asset in runtime.initial.assets:
        source = catalogs.get(asset.source_key) if asset.source_kind == "catalog" else services.get(asset.source_key)
        if source is None:
            raise SimulationError("invalid_reference", f"initial.assets/{asset.id}")
        modes = source.deployment_modes if asset.source_kind == "catalog" else source.placement_options
        if asset.placement not in {x.value for x in modes}:
            raise SimulationError("invalid_reference", f"initial.assets/{asset.id}/placement")
        if asset.source_kind == "catalog" and asset.config not in source.config_tiers:
            raise SimulationError("invalid_reference", f"initial.assets/{asset.id}/config")
        if asset.source_kind == "service" and asset.config is not None:
            raise SimulationError("invalid_input", f"initial.assets/{asset.id}/config", {"reason": "service config must be null"})
    edge_ids: set[str] = set(); edge_shapes: set[tuple[str, str, str, str | None]] = set()
    entities = {entity.key for entity in pack.entities}
    integration_tiers = {tier.key for tier in pack.platform.integration_tiers}
    catalog_sources = set(catalogs)
    for edge in runtime.initial.connections:
        if edge.src not in asset_ids or edge.dst not in asset_ids or edge.src == edge.dst:
            raise SimulationError("invalid_reference", f"initial.connections/{edge.id}")
        if edge.id in edge_ids:
            raise SimulationError("invalid_input", f"initial.connections/{edge.id}", {"reason": "duplicate connection id"})
        edge_ids.add(edge.id)
        shape = (min(edge.src, edge.dst), max(edge.src, edge.dst), edge.kind, edge.entity)
        if shape in edge_shapes:
            raise SimulationError("invalid_input", f"initial.connections/{edge.id}", {"reason": "duplicate topology/entity edge"})
        edge_shapes.add(shape)
        if edge.kind in {"network", "failover"}:
            if edge.entity is not None or edge.tier is not None:
                raise SimulationError("invalid_input", f"initial.connections/{edge.id}", {"reason": "network/failover entity and tier must be null"})
            if edge.kind == "failover":
                endpoint_sources = {next(a.source_key for a in runtime.initial.assets if a.id == edge.src), next(a.source_key for a in runtime.initial.assets if a.id == edge.dst)}
                if not any("failover" in catalogs.get(source, services.get(source)).roles_filled for source in endpoint_sources):
                    raise SimulationError("invalid_reference", f"initial.connections/{edge.id}", {"reason": "failover endpoint role required"})
        else:
            if edge.entity is None or edge.tier not in integration_tiers:
                raise SimulationError("invalid_reference", f"initial.connections/{edge.id}", {"reason": "integration requires entity and tier"})
            source_asset = next(a for a in runtime.initial.assets if a.id == edge.src)
            receiver_asset = next(a for a in runtime.initial.assets if a.id == edge.dst)
            if source_asset.source_kind != "catalog" or receiver_asset.source_kind != "catalog":
                raise SimulationError("invalid_reference", f"initial.connections/{edge.id}", {"reason": "integration endpoints must be catalog assets"})
            source_item, receiver_item = catalogs[source_asset.source_key], catalogs[receiver_asset.source_key]
            if edge.entity not in entities or not any(item.entity == edge.entity for item in source_item.owns_entities):
                raise SimulationError("invalid_reference", f"initial.connections/{edge.id}/entity")
            if not any(dep.entity == edge.entity and (dep.from_capability is None or dep.from_capability in source_item.serves) for dep in receiver_item.must_be_fed_by):
                raise SimulationError("invalid_reference", f"initial.connections/{edge.id}", {"reason": "receiver dependency mismatch"})


def load_runtime_pack(path: str | Path) -> RuntimePackV1:
    root = Path(path)
    if root.is_file():
        runtime_path, pack_dir = root, root.parent
    else:
        pack_dir, runtime_path = root, root / "runtime.yaml"
    if not runtime_path.exists():
        raise SimulationError("unsupported_operation", "runtime.yaml", {"reason": "runtime supplement missing"})
    report = validate_pack_dir(pack_dir)
    if report.pack is None or report.exit_code != 0:
        raise SimulationError("invalid_input", "casepack", {"reason": "casepack validation failed"})
    pack = report.pack
    try:
        raw = yaml.load(runtime_path.read_text(encoding="utf-8"), Loader=_UniqueLoader)
    except SimulationError:
        raise
    except (OSError, yaml.YAMLError) as exc:
        raise SimulationError("invalid_input", "runtime.yaml", {"reason": "yaml parse error"}) from exc
    if not isinstance(raw, dict):
        raise SimulationError("invalid_input", "runtime.yaml", {"reason": "mapping required"})
    try:
        runtime = RuntimeContentV1.model_validate(raw)
        _validate_against_casepack(pack, runtime)
        _registries(raw)
    except SimulationError:
        raise
    except Exception as exc:
        raise SimulationError("invalid_input", "runtime", {"reason": str(exc).split("\n", 1)[0]}) from exc
    frozen_pack = copy.deepcopy(pack)
    frozen_runtime = copy.deepcopy(runtime)
    payload = canonical_json({"casepack": frozen_pack, "runtime": frozen_runtime})
    return RuntimePackV1(casepack=frozen_pack, runtime=frozen_runtime, pack_digest=hashlib.sha256(payload).hexdigest(), canonical_bytes=payload)


def normalize_patch(existing: tuple[CommandV1, ...], patch: SheetPatchV1) -> tuple[CommandV1, ...]:
    """Merge category replacements, preserving omitted categories exactly."""
    by_category: dict[str, list[CommandV1]] = {}
    for command in existing:
        by_category.setdefault(COMMAND_CATEGORIES[command.op], []).append(command)
    for category, commands in patch.replace_categories.items():
        by_category[category] = list(commands)
    merged = [command for category in sorted(by_category) for command in sorted(by_category[category], key=lambda x: x.key)]
    keys = [command.key for command in merged]
    if len(keys) != len(set(keys)):
        raise SimulationError("conflicting_commands", "commands", {"reason": "duplicate command key"})
    return tuple(merged)
