"""Event resolution: capability attribution, firing with the O2 cap, suppression, arms, and
the blast-radius / outage-duration path (contract-spec sections 7 and 8).

Everything here is derived and deterministic: capability attribution is an ORDERED tuple (never
a set), O2 slot accounting iterates the authored deck order, and the failed-node binding is
total (a node or `None` for every event). The watch-rule metric kind is not read here
(invariant I8); no pack identity is branched on (invariant I1).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.casepack.models import Casepack, Event
from app.engine import catalog, graph
from app.engine.preconditions import evaluate_precondition
from app.engine.state import TeamState

#: Outage-duration constants (contract-spec section 8.3), all NEW and TODO: calibrate (1.7).
NO_FAILOVER_MULTIPLIER = 3.0
UNDERSTAFFED_MULTIPLIER = 4.0
DEFAULT_BASE_RTO_HOURS = 8.0

#: Per-capability event cap (O2, 1.5 spec section 4).
MAX_EVENTS_PER_CAPABILITY = 2


# -- event -> capability attribution (contract-spec section 7.1, ordered & total) ---------


def _watch_rule_capability(pack: Casepack, signal_key: str) -> str | None:
    for rule in pack.watch_rules:
        if rule.key == signal_key:
            return rule.capability
    return None


def capability_sequence(event: Event, pack: Casepack) -> tuple[str, ...]:
    """The event's capability sequence: the capabilities of its `signal_open` preconditions in
    authored order, de-duplicated preserving first occurrence (contract-spec section 7.1).

    An ordered tuple, never a set: set iteration is not deterministic across runs (I4)."""
    seq: list[str] = []
    for pc in event.preconditions:
        if pc.type == "signal_open":
            cap = _watch_rule_capability(pack, pc.signal)
            if cap is not None and cap not in seq:
                seq.append(cap)
    return tuple(seq)


def primary_capability(event: Event, pack: Casepack) -> str | None:
    """The first capability in the sequence, or `None` for an empty sequence (O2-exempt)."""
    seq = capability_sequence(event, pack)
    return seq[0] if seq else None


# -- arms (contract-spec section 7.4) -----------------------------------------------------


def _obligation_active(ob, state: TeamState, pack: Casepack) -> bool:
    """A presence-shaped obligation is active (open) iff the team holds its policy at the
    permissive value (nothing has cleared it). Deferred until 1.6 supplies policy state; falls
    back to the authored default via the same resolver the scorer uses."""
    from app.engine.management import _resolve_policy_decisions

    resolved = _resolve_policy_decisions(pack, state)
    selected = resolved.get(ob.policy, (None, False))[0]
    return selected == ob.permissive_value


def arms_gate_satisfied(event: Event, state: TeamState, pack: Casepack) -> bool:
    """Whether an armed event's arming gate is satisfied (contract-spec section 7.4).

    An event named in any obligation's `arms` fires only when at least one such obligation is
    active (multiple obligations combine by OR). An event named in no `arms` list is not gated."""
    arming = [ob for ob in pack.obligation_rules if event.key in ob.arms]
    if not arming:
        return True  # not an armed event; arms imposes no gate
    return any(_obligation_active(ob, state, pack) for ob in arming)


# -- firing with the O2 cap and suppression (contract-spec section 7) ---------------------


@dataclass(frozen=True)
class SuppressionRecord:
    event_key: str
    round: int
    reason: str  # "cap" | "already_fired"
    capability: str | None


def _satisfiable(event: Event, state: TeamState, pack: Casepack, ledger: tuple) -> bool:
    if not all(evaluate_precondition(pc, state, pack, ledger) for pc in event.preconditions):
        return False
    if event.strategy_affinity and state.declared_strategy not in event.strategy_affinity:
        return False
    return arms_gate_satisfied(event, state, pack)


def resolve_events(
    state: TeamState,
    pack: Casepack,
    ledger: tuple = (),
    already_fired: frozenset[str] = frozenset(),
) -> tuple[tuple[str, ...], tuple[SuppressionRecord, ...]]:
    """Fire the deck in authored order under the O2 cap (contract-spec section 7).

    Returns `(fired_event_keys, suppression_records)`. An event fires iff its preconditions,
    affinity and arms gate hold, it has not already fired (fire-once, section 7.2), and every
    capability in its sequence is below the per-capability cap; firing increments the count for
    each capability in its sequence. Empty-sequence events are O2-exempt.
    """
    per_cap: dict[str, int] = {}
    fired: list[str] = []
    suppressed: list[SuppressionRecord] = []

    for event in pack.events:  # authored deck order
        if not _satisfiable(event, state, pack, ledger):
            continue
        primary = primary_capability(event, pack)
        if event.key in already_fired:
            suppressed.append(SuppressionRecord(event.key, state.round, "already_fired", primary))
            continue
        seq = capability_sequence(event, pack)
        blocked = any(per_cap.get(cap, 0) >= MAX_EVENTS_PER_CAPABILITY for cap in seq)
        if blocked:
            suppressed.append(SuppressionRecord(event.key, state.round, "cap", primary))
            continue
        fired.append(event.key)
        for cap in seq:
            per_cap[cap] = per_cap.get(cap, 0) + 1

    return tuple(fired), tuple(suppressed)


# -- blast radius, failover, duration (contract-spec section 8) ---------------------------


def _primary_map(pack: Casepack, capabilities: list[str]) -> dict[str, tuple[str, str, list[str]]]:
    return {cap: catalog.primary_entity(pack, cap) for cap in capabilities}


def bottleneck_node(state: TeamState, path: list[str]) -> str | None:
    """The first node in serving-path order whose throughput equals the path minimum,
    skipping nodes with no throughput ceiling (contract-spec section 8.1). The stable path
    order makes the "first at the minimum" tie-break deterministic."""
    minimum = graph.bottleneck_capacity(state, path)
    if minimum is None:
        return None
    for key in path:
        node = state.node(key)
        if node is not None and node.throughput is not None and node.throughput == minimum:
            return key
    return None


def failed_node(event: Event, state: TeamState, pack: Casepack) -> str | None:
    """Which node an event removes -- total, returns a node or `None` (contract-spec 8.1).

    1. An explicit `node_is_spof` precondition binds its node (first in authored order).
    2. Otherwise the bottleneck of the event's PRIMARY capability's serving path.
    3. Otherwise (empty sequence, no SPOF) no node is bound.
    """
    spof_pcs = [pc for pc in event.preconditions if pc.type == "node_is_spof"]
    if spof_pcs:
        return spof_pcs[0].node
    seq = capability_sequence(event, pack)
    if seq:
        entity, level, order = catalog.primary_entity(pack, seq[0])
        path = graph.serving_path(state, seq[0], entity, level, order)
        if path is None:
            return None
        return bottleneck_node(state, path)
    return None


def failover_exists(state: TeamState, failed: str, capability: str, pack: Casepack) -> bool:
    """True iff, after removing `failed`, the capability still serves via a path that traverses
    a `failover`-kind edge (contract-spec section 8.2) -- redundancy is what saved it, not
    merely the bare existence of some surviving path."""
    entity, level, order = catalog.primary_entity(pack, capability)
    sources = [n.key for n in state.nodes_serving(capability) if n.is_client_access and n.key != failed]
    targets = {k for k in graph.owner_nodes(state, capability, entity, level, order) if k != failed}
    if not sources or not targets:
        return False
    failover_edges = [
        e for e in state.edges
        if e.kind == "failover" and e.src != failed and e.dst != failed
    ]
    if not failover_edges:
        return False
    # A surviving path that uses a failover edge: remove each failover edge in turn; if doing so
    # disconnects the capability, that edge was load-bearing for the survival -> redundancy saved it.
    adj = graph._adjacency(state, exclude=failed)
    if graph._bfs_path(adj, sources, targets) is None:
        return False  # no surviving path at all
    for fe in failover_edges:
        pruned = {k: set(v) for k, v in adj.items()}
        if fe.src in pruned and fe.dst in pruned:
            pruned[fe.src].discard(fe.dst)
            pruned[fe.dst].discard(fe.src)
        if graph._bfs_path(pruned, sources, targets) is None:
            return True  # this failover edge is what keeps the capability alive
    return False


def outage_duration(state: TeamState, failed: str, capability: str, pack: Casepack) -> dict:
    """The outage-duration evidence dict (contract-spec section 8.3).

    `duration_hours = round(base_rto_hours(node) * failover_factor * staffing_modifier, 1)`.
    """
    base_rto = DEFAULT_BASE_RTO_HOURS
    for item in pack.catalog:
        if item.key == failed and item.base_rto_hours is not None:
            base_rto = item.base_rto_hours
            break

    has_failover = failover_exists(state, failed, capability, pack)
    failover_factor = 1.0 if has_failover else NO_FAILOVER_MULTIPLIER

    if state.staff.staff_fte == 0:
        staffing_modifier = UNDERSTAFFED_MULTIPLIER
    else:
        staffing_modifier = 1.0 + max(0.0, state.staff.load_fte / state.staff.staff_fte - 1.0)

    radius = graph.blast_radius(state, failed, [capability], _primary_map(pack, [capability]))
    duration_hours = round(base_rto * failover_factor * staffing_modifier, 1)
    return {
        "node": failed,
        "base_rto_hours": base_rto,
        "failover_exists": has_failover,
        "failover_factor": failover_factor,
        "staffing_modifier": round(staffing_modifier, 4),
        "duration_hours": duration_hours,
        "blast_radius": radius,
    }
