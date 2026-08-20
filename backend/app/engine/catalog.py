"""Read-only lookups over the parsed casepack for the Technology term.

Deliberately scoped: this module answers questions about authored content --
required roles, entity level orders, demand at a round, integration expectations.
Nothing here touches the earned term of the score, and by construction the catalog
cannot raise it: a grep of this file for that term returns nothing (invariant I4).
Tech is bought and Org is funded; the earned term is earned, never authored.
"""

from __future__ import annotations

from app.casepack.models import Capability, Casepack, Entity


def capability(pack: Casepack, key: str) -> Capability:
    for c in pack.capabilities:
        if c.key == key:
            return c
    raise KeyError(f"capability {key!r} not in pack")


def entity(pack: Casepack, key: str) -> Entity:
    for e in pack.entities:
        if e.key == key:
            return e
    raise KeyError(f"entity {key!r} not in pack")


def level_order(pack: Casepack, entity_key: str) -> list[str]:
    """Coarse -> fine ordering for an entity's levels of detail."""
    return list(entity(pack, entity_key).levels_of_detail)


def primary_entity(pack: Casepack, capability_key: str) -> tuple[str, str, list[str]]:
    """The capability's first required entity, its required level, and its level
    order. The primary entity is the record the serving path must reach."""
    cap = capability(pack, capability_key)
    if not cap.required_entities:
        raise ValueError(f"capability {capability_key!r} declares no required entities")
    req = cap.required_entities[0]
    return req.entity, req.min_level_of_detail, level_order(pack, req.entity)


def demand_at(pack: Casepack, capability_key: str, round_no: int) -> int:
    """Demand for a capability in a given 1-based round."""
    cap = capability(pack, capability_key)
    idx = round_no - 1
    if idx < 0 or idx >= len(cap.demand_curve):
        raise IndexError(f"round {round_no} outside demand curve for {capability_key!r}")
    return cap.demand_curve[idx]


def required_roles(pack: Casepack, capability_key: str) -> list[str]:
    return list(capability(pack, capability_key).required_roles)


def required_entities(pack: Casepack, capability_key: str) -> list[tuple[str, str, list[str]]]:
    cap = capability(pack, capability_key)
    return [
        (r.entity, r.min_level_of_detail, level_order(pack, r.entity))
        for r in cap.required_entities
    ]
