"""Pure money and recurring-liability helpers for the simulation packet.

All amounts are integer dollars.  This module deliberately has no persistence
or engine imports: callers pass the already validated estate and organisation
outputs and receive detached accounting evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from .types import CostEntryV1, RuntimePackV1, SimulationError


COST_KINDS = {
    "capital_grant", "capital_request", "operating_allowance", "acquisition", "integration",
    "training", "process", "communication", "policy", "strategy", "response",
    "asset_opex", "integration_opex", "wages", "support", "event_loss",
}


def money(value: int | float | Decimal) -> int:
    """Round a source amount using the authored financial rule."""
    try:
        return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except Exception as exc:  # pragma: no cover - defensive boundary
        raise SimulationError("invalid_input", "money") from exc


def entry(
    round: int,
    kind: str,
    source: str,
    *,
    capital: int = 0,
    operating: int = 0,
    asset: str | None = None,
    capability: str | None = None,
    category: str | None = None,
) -> CostEntryV1:
    if kind not in COST_KINDS:
        raise SimulationError("invalid_input", "cost.kind", {"kind": kind})
    return CostEntryV1(
        round=round, kind=kind, source=source, asset=asset,
        capability=capability, category=category,
        capital_delta=int(capital), operating_delta=int(operating),
    )


def totals(entries: Iterable[CostEntryV1]) -> tuple[int, int]:
    capital = operating = 0
    for item in entries:
        capital += int(item.capital_delta)
        operating += int(item.operating_delta)
    return capital, operating


def grant_and_allowance(pack: RuntimePackV1, round: int) -> tuple[CostEntryV1, CostEntryV1]:
    casepack, runtime = pack.casepack, pack.runtime
    if type(round) is not int or round < 1 or round > casepack.metadata.rounds:
        raise SimulationError("round_state", "round")
    grants = list(casepack.metadata.budget.capex_per_round)
    allowances = list(runtime.accounting.operating_allowances)
    if round > len(grants) or round > len(allowances):
        raise SimulationError("round_state", "round")
    return (
        entry(round, "capital_grant", "budget", capital=int(grants[round - 1])),
        entry(round, "operating_allowance", "budget", operating=int(allowances[round - 1])),
    )


def recurring_entries(pack: RuntimePackV1, state: Any, round: int) -> list[CostEntryV1]:
    """Quote live source, integration, wage and support liabilities once."""
    from .resources import resource_projection

    assets = state.assets if hasattr(state, "assets") else state["assets"]
    connections = state.connections if hasattr(state, "connections") else state["connections"]
    policies = state.policies if hasattr(state, "policies") else state["policies"]
    view = resource_projection(pack, assets, connections, policies, round)
    out: list[CostEntryV1] = []
    for asset_id, row in sorted(view.by_asset.items()):
        amount = int(row.get("opex", 0))
        if amount:
            out.append(entry(round, "asset_opex", asset_id, operating=-amount, asset=asset_id, category="maintenance"))
    for connection_id, connection in sorted(connections.items()):
        raw = connection.model_dump(mode="python") if hasattr(connection, "model_dump") else connection
        if raw.get("kind") != "integration":
            continue
        retired = raw.get("retired_round")
        created = raw.get("created_round", 0)
        if created > round or (retired is not None and retired <= round):
            continue
        terms = runtime_terms(pack, raw.get("tier"))
        if terms[0]:
            out.append(entry(round, "integration_opex", connection_id, operating=-terms[0], category="integration"))
    support = state.support if hasattr(state, "support") else state.get("support", {})
    support = support.model_dump(mode="python") if hasattr(support, "model_dump") else support
    tier = support.get("tier")
    if tier is not None:
        row = next((x for x in pack.casepack.platform.support_tiers if x.key == tier), None)
        if row is None:
            raise SimulationError("invalid_reference", "support.tier", {"tier": tier})
        out.append(entry(round, "support", tier, operating=-int(row.cost), category="support"))
    # The authored starting IT pool is a live recurring liability from round 1;
    # it is not represented as a hiring order.
    starting_wages = money(pack.casepack.platform.starting_staff_fte * pack.runtime.people.starting_wage_per_fte)
    if starting_wages:
        out.append(entry(round, "wages", "initial_staff", operating=-starting_wages, category="wages"))
    hires = state.staff_hires if hasattr(state, "staff_hires") else state.get("staff_hires", [])
    for hire in hires:
        raw = hire.model_dump(mode="python") if hasattr(hire, "model_dump") else hire
        if raw.get("arrival_round", 10**9) <= round:
            option = pack.runtime.people.hiring_options.get(raw.get("option"))
            if option is None:
                raise SimulationError("invalid_reference", "hiring.option")
            out.append(entry(round, "wages", raw["order_id"], operating=-int(option.wage_per_round), category="wages"))
    # Pending hires become recurring wage liabilities when their authored
    # arrival round is reached. Include them in the forward forecast so an
    # oversized batch is refused before it can be committed.
    hiring_orders = state.hiring_orders if hasattr(state, "hiring_orders") else state.get("hiring_orders", {})
    for order in hiring_orders.values():
        raw = order.model_dump(mode="python") if hasattr(order, "model_dump") else order
        if raw.get("status") != "pending" or raw.get("arrival_round", 10**9) > round:
            continue
        option = pack.runtime.people.hiring_options.get(raw.get("option"))
        if option is None:
            raise SimulationError("invalid_reference", "hiring.option")
        out.append(entry(round, "wages", raw["id"], operating=-int(option.wage_per_round), category="wages"))
    return out


def runtime_terms(pack: RuntimePackV1, tier: str | None) -> tuple[int, float]:
    if tier is None:
        return 0, 0.0
    row = pack.runtime.accounting.connection_terms.get(tier)
    if row is None:
        raise SimulationError("invalid_reference", "connection.tier", {"tier": tier})
    return int(row.opex), float(row.staff_load)


def forecast_operating(pack: RuntimePackV1, prior_reserve: int, state: Any, start_round: int) -> list[dict[str, int]]:
    """Produce a detached known-liability schedule through the authored horizon."""
    result: list[dict[str, int]] = []
    reserve = int(prior_reserve)
    for round in range(start_round, pack.casepack.metadata.rounds + 1):
        allowance = int(pack.runtime.accounting.operating_allowances[round - 1])
        recurring = -sum(x.operating_delta for x in recurring_entries(pack, state, round))
        opening = reserve
        reserve = opening + allowance - recurring
        result.append({"round": round, "opening": opening, "allowance": allowance, "recurring": recurring, "closing": reserve})
    return result
