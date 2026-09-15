"""Pure P2 physical resource and recurring-cost projection."""

from __future__ import annotations

import math
from typing import Any

from app.casepack.models import Casepack
from .types import CheckpointStateV1, ResourceViewV1, RuntimePackV1, SimulationError


def _parts(pack: RuntimePackV1) -> tuple[Casepack, Any]:
    return pack.casepack, pack.runtime


def _round6(value: float) -> float:
    if isinstance(value, bool) or not math.isfinite(value) or value < 0: raise SimulationError("invalid_output", "resources")
    return round(value, 6)


def resource_projection(pack: RuntimePackV1, assets: dict[str, Any], connections: dict[str, Any], policies: dict[str, Any], round: int) -> ResourceViewV1:
    casepack, runtime = _parts(pack)
    if not isinstance(round, int) or isinstance(round, bool) or round < 1 or round > casepack.metadata.rounds:
        raise SimulationError("round_state", "round")
    catalogs = {x.key: x for x in casepack.catalog}; services = {x.key: x for x in casepack.platform.services}; caps = [x.key for x in casepack.capabilities]
    by_placement = {placement: {"compute_supply": 0.0, "storage_supply_gb": 0.0, "compute_draw": 0.0, "storage_draw_gb": 0.0, "factor": 1.0} for placement in ("on_prem", "cloud", "saas")}
    by_asset: dict[str, dict[str, Any]] = {}
    live = {key: (value.model_dump() if hasattr(value, "model_dump") else value) for key, value in assets.items() if (value.retired_round if hasattr(value, "retired_round") else value.get("retired_round")) is None and (value.installed_round if hasattr(value, "installed_round") else value.get("installed_round", 0)) <= round}
    for key, asset in live.items():
        source = catalogs.get(asset["source_key"]) or services.get(asset["source_key"])
        if source is None: raise SimulationError("invalid_reference", f"assets/{key}")
        placement = asset["placement"]; units = asset["units"]
        mode = source.deployment_modes[next(x for x in source.deployment_modes if x.value == placement)] if asset["source_kind"] == "catalog" else source.placement_options[next(x for x in source.placement_options if x.value == placement)]
        compute = storage = 0.0
        capacity: dict[str, float | None] = {}
        if asset["source_kind"] == "catalog":
            item = source; cfg = item.config_tiers[asset["config"]]; driver = runtime.drivers[item.sizing.driver][round - 1]
            compute = item.sizing.base.compute + item.sizing.per_unit.compute * driver / item.sizing.per_unit.per
            storage = item.sizing.base.storage_gb + item.sizing.per_unit.storage_gb * driver / item.sizing.per_unit.per
            compute *= cfg.compute_multiplier
            if mode.bypasses_platform: compute = storage = 0.0
            row = runtime.catalog[item.key]
            capacity = {cap: None if value is None else value * row.capacity_multiplier_by_config[asset["config"]] for cap, value in row.capacity_by_capability.items()}
        else:
            service = source; supply = runtime.services[service.key]
            supply_row = supply.supply_by_placement[placement]
            by_placement[placement]["compute_supply"] += supply_row.compute * units
            by_placement[placement]["storage_supply_gb"] += supply_row.storage_gb * units
        by_placement[placement]["compute_draw"] += compute * units
        by_placement[placement]["storage_draw_gb"] += storage * units
        by_asset[key] = {"capacity_by_capability": capacity, "compute_draw": _round6(compute * units), "storage_draw_gb": _round6(storage * units), "staff_load": _round6(source.staff_load * runtime.people.placement_staff_multiplier[placement]), "opex": int(mode.opex * units * (runtime.catalog[source.key].opex_multiplier_by_config[asset["config"]] if asset["source_kind"] == "catalog" else 1.0))}
    for placement, row in by_placement.items():
        cdraw, sdraw = row["compute_draw"], row["storage_draw_gb"]
        cf = row["compute_supply"] / cdraw if cdraw > 0 else 1.0
        sf = row["storage_supply_gb"] / sdraw if sdraw > 0 else 1.0
        row["factor"] = _round6(min(1.0, cf, sf))
    for key, asset in live.items():
        if asset["source_kind"] != "catalog": continue
        placement = asset["placement"]; factor = 1.0 if catalogs[asset["source_key"]].deployment_modes[next(x for x in catalogs[asset["source_key"]].deployment_modes if x.value == placement)].bypasses_platform else by_placement[placement]["factor"]
        by_asset[key]["capacity_by_capability"] = {cap: None if value is None else _round6(value * factor) for cap, value in by_asset[key]["capacity_by_capability"].items()}
    integration_load = 0.0; integration_opex = 0
    tiers = {x.key: x for x in casepack.platform.integration_tiers}
    for edge_value in connections.values():
        edge = edge_value.model_dump() if hasattr(edge_value, "model_dump") else edge_value
        if edge.get("retired_round") is not None or edge.get("kind") != "integration": continue
        term = runtime.accounting.connection_terms[edge["tier"]]
        integration_load += term.staff_load; integration_opex += term.opex
    total_load = sum(float(row["staff_load"]) for row in by_asset.values()) + integration_load
    total_opex = sum(int(row["opex"]) for row in by_asset.values()) + integration_opex
    return ResourceViewV1(by_placement=by_placement, by_asset=by_asset, integration_load=_round6(integration_load), policy_load=0.0, total_load=_round6(total_load), total_opex=total_opex)
