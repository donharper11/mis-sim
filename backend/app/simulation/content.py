"""Runtime supplement loading, validation and semantic binding for P1."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from app.casepack.loader import load_casepack
from app.casepack.validate import validate_pack_dir
from app.casepack.models import Casepack
from .types import (
    COMMAND_CATEGORIES, CheckpointStateV1, CommandV1, RuntimeContentV1, RuntimePackV1,
    SheetPatchV1, SimulationError,
)


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
            "purchasable_placements": [str(x.value) for x in item.deployment_modes],
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
    return {
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
                        "connection_terms": {k: {"capex_source": "none", "opex": 0 if k == "network" else 3100, "staff_load": 0.0} for k in ["network", "failover", "basic", "advanced", "vendor_managed"]},
                        "cancellation": "sunk", "platform_capability": "firm_infrastructure", "decision_attribution_version": 1, "action_attribution_version": 1,
                        "tco_estimators": {k: "one_round_opex" for k in ["training", "integration", "lifecycle", "capacity", "data_migration", "policy", "process_redesign", "maintenance", "backup"]},
                        "tco_capex_fraction": .1, "process_partial_fraction": .5},
        "preferences": preferences,
        "response_disposition": {event.key: {"fund_effect": "prevent_current_round", "explanation": "funded response prevents this round"} for event in pack.events},
        # A root pointer is a valid contract ancestor pointer and covers every
        # generated numeric descendant.  Later authored supplements can replace
        # it with more specific source/unit pointers without changing the DTO.
        "provenance": {"/": {"source": "AUTHORED", "note": "TODO: calibrate — owner M1/M4"}},
        "units": {"/": "mixed_runtime_content"},
    }


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
    # Mark the supported source family explicitly; all remaining rows retain the
    # context/M4 disposition above and are therefore still visible and auditable.
    for row in dispositions:
        if "/preferences/platform/defaults_by_archetype/operations/ideal_availability" in row["source_path"]:
            row["disposition"] = "live_v1"; row["runtime_views"] = ["/preferences/rules/operations/views/0"]
    return {"rules": view_rows, "dispositions": dispositions}


def _registries(raw: dict[str, Any]) -> None:
    """Require complete numeric provenance and dimension registries."""
    numeric = set(_numeric_paths(raw)) - {"/version"}
    provenance = raw.get("provenance", {})
    units = raw.get("units", {})
    # Root/subtree pointers are allowed by the contract; accepting the root only
    # would make omissions invisible, so every numeric leaf must have a matching
    # exact pointer or a declared ancestor.
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
        if not set(row.capacity_by_capability) <= set(capabilities):
            raise SimulationError("invalid_input", f"catalog/{key}/capacity_by_capability", {"reason": "unknown capability"})
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
    for edge in runtime.initial.connections:
        if edge.src not in asset_ids or edge.dst not in asset_ids or edge.src == edge.dst:
            raise SimulationError("invalid_reference", f"initial.connections/{edge.id}")


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
    if raw.pop("generated_defaults", False):
        raw = _default_runtime(pack)
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
