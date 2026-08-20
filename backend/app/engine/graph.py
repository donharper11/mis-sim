"""Architecture-graph analysis: serving path, bottleneck capacity, path
availability, single points of failure, blast radius.

Pure graph theory over `TeamState`. No third-party graph library: articulation
points are computed directly with Tarjan's algorithm (pre-flight register row 5 --
networkx is absent from requirements and this keeps the engine dependency-free and
pure, invariant I2).

The interface speaks graph, never prose. The screen turns "articulation point"
into "if the Kelso Road link fails, all 8 stores stop selling" (GOVERNANCE section
2.1); this module only finds the point.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from app.engine.state import ArchNode, TeamState


def _adjacency(state: TeamState, exclude: str | None = None) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {n.key: set() for n in state.nodes if n.key != exclude}
    for e in state.edges:
        if e.src == exclude or e.dst == exclude:
            continue
        if e.src in adj and e.dst in adj:
            adj[e.src].add(e.dst)
            adj[e.dst].add(e.src)  # undirected: connectivity is symmetric
    return adj


def _bfs_path(
    adj: dict[str, set[str]], sources: Iterable[str], targets: set[str]
) -> list[str] | None:
    """Shortest node path from any source to any target, or None if disconnected."""
    prev: dict[str, str | None] = {}
    q: deque[str] = deque()
    for s in sources:
        if s in adj and s not in prev:
            prev[s] = None
            q.append(s)
    if not q:
        return None
    while q:
        cur = q.popleft()
        if cur in targets:
            path = [cur]
            while prev[path[-1]] is not None:
                path.append(prev[path[-1]])  # type: ignore[arg-type]
            path.reverse()
            return path
        for nxt in adj[cur]:
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    return None


def _level_ok(owned_level: str, required_level: str, order: list[str]) -> bool:
    """Ordinal comparison (CONTRACTS.md entity.level_of_detail): a required level
    is satisfied by that level *or finer*. `order` is coarse -> fine."""
    if owned_level not in order or required_level not in order:
        return owned_level == required_level
    return order.index(owned_level) >= order.index(required_level)


def owner_nodes(
    state: TeamState,
    capability: str,
    entity: str,
    required_level: str,
    level_order: list[str],
) -> list[str]:
    """Serving nodes that are the system of record for `entity` at >= required level."""
    out: list[str] = []
    for n in state.nodes_serving(capability):
        for owned_entity, owned_level in n.owns_entities:
            if owned_entity == entity and _level_ok(owned_level, required_level, level_order):
                out.append(n.key)
                break
    return out


def serving_path(
    state: TeamState,
    capability: str,
    primary_entity: str,
    required_level: str,
    level_order: list[str],
) -> list[str] | None:
    """Graph walk from any client_access serving node to a node owning the
    capability's primary entity at the required level (spec section 5.1)."""
    sources = [n.key for n in state.nodes_serving(capability) if n.is_client_access]
    targets = set(owner_nodes(state, capability, primary_entity, required_level, level_order))
    if not sources or not targets:
        return None
    return _bfs_path(_adjacency(state), sources, targets)


def path_reliability(state: TeamState, path: list[str]) -> float:
    """Product of node availabilities along the path (settled decision, spec 5.1).

    SPOF downtime is NOT added on top -- it is already in this product (decision 5)."""
    r = 1.0
    for key in path:
        node = state.node(key)
        if node is not None:
            r *= node.availability
    return r


def bottleneck_capacity(state: TeamState, path: list[str]) -> float | None:
    """min() of throughput along the serving path -- the bottleneck, not the sum
    (settled decision 4, invariant I8). Nodes with no throughput ceiling are
    skipped. Returns None if no node on the path declares a throughput."""
    caps = [
        state.node(k).throughput  # type: ignore[union-attr]
        for k in path
        if state.node(k) is not None and state.node(k).throughput is not None  # type: ignore[union-attr]
    ]
    if not caps:
        return None
    return min(caps)  # type: ignore[type-var]


def articulation_points(state: TeamState, subset: set[str] | None = None) -> set[str]:
    """Tarjan articulation points of the (optionally restricted) undirected graph.

    `subset` limits the graph to those node keys and the edges between them --
    used to ask "which nodes hold the serving path together" without the rest of
    the estate confusing the answer.
    """
    adj = _adjacency(state)
    if subset is not None:
        adj = {k: {v for v in vs if v in subset} for k, vs in adj.items() if k in subset}

    visited: set[str] = set()
    disc: dict[str, int] = {}
    low: dict[str, int] = {}
    ap: set[str] = set()
    timer = [0]

    def dfs(u: str, parent: str | None) -> None:
        visited.add(u)
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        children = 0
        for v in adj[u]:
            if v not in visited:
                children += 1
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if parent is not None and low[v] >= disc[u]:
                    ap.add(u)
            elif v != parent:
                low[u] = min(low[u], disc[v])
        if parent is None and children > 1:
            ap.add(u)

    for node in adj:
        if node not in visited:
            dfs(node, None)
    return ap


def spofs_on_path(state: TeamState, path: list[str]) -> list[str]:
    """Single points of failure on a serving path: nodes whose removal leaves no
    surviving path (spec 5.1). Computed as the articulation points of the whole
    graph that lie on the path, excluding the two path endpoints (the client node
    and the record node are where the path is *defined* to start and end, not
    intermediate dependencies). Order follows the path so a debrief can walk it."""
    if len(path) <= 2:
        return []
    interior = set(path[1:-1])
    aps = articulation_points(state)
    return [k for k in path[1:-1] if k in aps and k in interior]


def blast_radius(state: TeamState, node_key: str, capabilities: list[str], primary: dict[str, tuple[str, str, list[str]]]) -> list[str]:
    """Capabilities that lose their serving path when `node_key` is removed.

    `primary` maps capability -> (primary_entity, required_level, level_order).
    """
    hit: list[str] = []
    for cap in capabilities:
        entity, level, order = primary[cap]
        sources = [n.key for n in state.nodes_serving(cap) if n.is_client_access and n.key != node_key]
        targets = set(
            k for k in owner_nodes(state, cap, entity, level, order) if k != node_key
        )
        if not sources or not targets:
            # The removed node WAS the client endpoint or the record -- the
            # capability cannot serve without it.
            full = serving_path(state, cap, entity, level, order)
            if full is not None and node_key in full:
                hit.append(cap)
            continue
        adj = _adjacency(state, exclude=node_key)
        if _bfs_path(adj, sources, targets) is None:
            hit.append(cap)
    return hit


def coverage_fraction(required_roles: list[str], serving: tuple[ArchNode, ...]) -> tuple[float, list[str]]:
    """Filled / required roles, and the list of unfilled roles."""
    filled_roles: set[str] = set()
    for n in serving:
        filled_roles.update(n.roles_filled)
    missing = [r for r in required_roles if r not in filled_roles]
    if not required_roles:
        return 1.0, []
    return (len(required_roles) - len(missing)) / len(required_roles), missing
