"""The signal ledger: raise/escalate/clear/fire, episodes, and the SignalState projection.

The 1.5 engine takes the prior ledger (immutable) plus the current round-close snapshot and
returns a new ledger of `LedgerSignal` rows; it never mutates a prior row (contract-spec
section 5.2). The 1.4 scorer does not read this rich ledger -- it reads the 4-field
`SignalState`, which is a frozen projection of it (section 5.4), so the 1.4 pin is preserved by
construction.

`metric_kind` is read in exactly two places, and both are here: the watch-rule evaluator
(`evaluate`) and the ledger writer (`advance_ledger` records it on each row). Nothing else in
the engine branches on it (invariant I8).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from app.casepack.models import Casepack, WatchRule
from app.engine import metrics
from app.engine.state import SignalState, TeamState

Severity = Literal["warning", "critical"]
Status = Literal["open", "cleared", "fired"]

_SEVERITY_RANK: dict[str, int] = {"warning": 0, "critical": 1}


@dataclass(frozen=True)
class LedgerSignal:
    """One signal episode on the rich ledger (contract-spec section 5.1)."""

    key: str
    episode_id: int
    capability: str
    metric: str
    metric_kind: str
    value: float
    severity: Severity
    status: Status
    first_shown_round: int
    cleared_round: int | None = None
    fire_round: int | None = None
    cleared_by: tuple[str, ...] = ()
    was_actionable: bool = False
    cheapest_fix_when_raised: int | None = None

    @property
    def lead_time(self) -> int | None:
        """Rounds from first shown to cleared (contract-spec section 5.3). None if never
        cleared. A same-round raise+clear is `0`, which is maximally responsive (O5)."""
        if self.cleared_round is None:
            return None
        return self.cleared_round - self.first_shown_round


# -- the watch-rule evaluator (contract-spec section 5.1a) --------------------------------


def evaluate(rule: WatchRule, state: TeamState, pack: Casepack) -> tuple[Severity, float] | None:
    """Evaluate one watch rule at round close: return `(severity, value)` or `None` (no raise).

    Threshold rules compare an unclipped float against the two thresholds with strict `>`
    (decision 3); presence rules raise at `critical` when the boolean is True (decision 10).
    Comparisons run on the unrounded value; the stored value is rounded to 4 dp (decision 5).
    """
    raw = metrics.metric_value(rule, state, pack)
    if rule.metric_kind == "presence":
        if raw is True:
            return "critical", 1.0
        return None
    # threshold
    value = float(raw)
    if rule.critical_above is not None and value > rule.critical_above:
        return "critical", round(value, 4)
    if rule.warn_above is not None and value > rule.warn_above:
        return "warning", round(value, 4)
    return None


# -- lifecycle status (contract-spec section 5.2, the frozen decision procedure) ----------


def compute_status(cleared_round: int | None, fire_round: int | None, still_raises: bool) -> Status:
    """The total, ordered decision procedure of contract-spec section 5.2.

    A clear on-or-before fire (or a clear that prevents a fire) yields `cleared`; a clear
    strictly after fire leaves `fired` (O3). A lapse -- metric false with no clearing action --
    is a `cleared` lifecycle with `cleared_round = None` and earns no responsiveness credit.
    """
    if fire_round is not None and not (cleared_round is not None and cleared_round <= fire_round):
        return "fired"
    if cleared_round is not None or not still_raises:
        return "cleared"
    return "open"


# -- the SignalState projection (contract-spec section 5.4, CC-A-001) ---------------------


def project_signal_state(ledger: tuple[LedgerSignal, ...]) -> tuple[SignalState, ...]:
    """Project the rich ledger to the 4-field `SignalState` the 1.4 scorer reads.

    One total rule (contract-spec section 5.4): a clear is credited whenever the episode was
    cleared AND either it never fired (`fire_round is None`, the most responsive outcome of
    all -- the student acted so early the bill never arrived) OR the clear landed on-or-before
    the fire. A clear strictly after fire, or a never-cleared/lapsed signal, earns nothing.
    """
    rows: list[SignalState] = []
    for s in ledger:
        actionable = s.was_actionable
        acted_before_fire = (s.cleared_round is not None) and (
            s.fire_round is None or s.cleared_round <= s.fire_round
        )
        rows.append(SignalState(s.key, s.capability, actionable, acted_before_fire))
    return tuple(rows)


# -- action-target matching and the clearing-price lookup (contract-spec section 5.5) -----


def _serves(target_key: str | None, pack: Casepack) -> tuple[str, ...]:
    """Capabilities a catalog item with `target_key` serves; empty tuple if not a catalog item."""
    if target_key is None:
        return ()
    for item in pack.catalog:
        if item.key == target_key:
            return tuple(item.serves)
    return ()


def _candidate_costs(action_type: str, capability: str, rule: WatchRule, pack: Casepack) -> list[int]:
    """The costs of the EFFECTFUL priced options that perform `action_type` for `capability`.

    The effectfulness filter (contract-spec section 5.5.4): a zero-coverage `training.none`
    option is dropped (it trains no one), and a `redesign_process` candidate exists only where
    the item declares a non-null `process_option`.
    """
    costs: list[int] = []
    if action_type in {"scale_node", "add_node", "move_to_cloud", "upgrade_component"}:
        for item in pack.catalog:
            if capability in item.serves:
                for mode in item.deployment_modes.values():
                    costs.append(mode.capex)
    elif action_type == "add_training":
        for item in pack.catalog:
            if capability in item.serves:
                for opt in item.training_options.values():
                    if opt.coverage > 0:  # exclude the zero-effect `none` option
                        costs.append(opt.cost)
    elif action_type == "add_service_tier":
        for tier in pack.platform.support_tiers:
            costs.append(tier.cost)
        for tier in pack.platform.integration_tiers:
            costs.append(tier.cost)
    elif action_type == "add_policy":
        for policy in pack.policies:
            costs.append(policy.cost)
    elif action_type == "redesign_process":
        for item in pack.catalog:
            if capability in item.serves and item.process_option is not None:
                costs.append(item.process_option.cost)
    elif action_type == "retire_component":
        costs.append(0)  # no purchase
    elif action_type == "fund_response":
        for event in pack.events:
            arms_signal = any(
                pc.type == "signal_open" and pc.signal == rule.key for pc in event.preconditions
            )
            if arms_signal:
                for opt in event.options:
                    if opt.key == "fund":
                        costs.append(opt.cost)
    return costs


def cheapest_effectful_fix(rule: WatchRule, pack: Casepack) -> int | None:
    """The minimum cost among the effectful options that perform any `cleared_by` action for
    the rule's capability, or `None` when no effectful candidate exists (contract-spec 5.5.4).

    `None` (not `0`) is the honest reading of "no fix ever existed": the signal is then not
    actionable and is excluded from the responsiveness denominator (O1).
    """
    candidates: list[int] = []
    for action_type in rule.cleared_by:
        candidates.extend(_candidate_costs(action_type, rule.capability, rule, pack))
    if not candidates:
        return None
    return min(candidates)


def was_actionable(cheapest_fix: int | None, funds_by_round: tuple[int, ...], open_rounds: range) -> bool:
    """True iff the cheapest fix was affordable in ANY round the episode was open (O1).

    Funds are remaining capital with committed spend already deducted (contract-spec 5.5.2), so
    the comparison never double-counts a spend already made.
    """
    if cheapest_fix is None:
        return False
    for r in open_rounds:
        idx = r - 1
        if 0 <= idx < len(funds_by_round) and cheapest_fix <= funds_by_round[idx]:
            return True
    return False


def matching_clear_actions(
    rule: WatchRule, capability: str, state: TeamState, first_shown_round: int, close_round: int, pack: Casepack
) -> tuple[int | None, tuple[str, ...]]:
    """Which committed actions cleared this episode (contract-spec section 5.5.3).

    Returns `(cleared_round, cleared_by)`: `cleared_round` is the earliest matching
    `locked_round`, `cleared_by` the matching action types in `rule.cleared_by` order. When no
    effectful action matches (a lapse), returns `(None, ())`.
    """
    matched_types: set[str] = set()
    locked_rounds: list[int] = []
    for a in state.action_history:
        if a.action_type not in rule.cleared_by:
            continue
        cap_ok = a.capability == capability or (
            a.capability is None and capability in _serves(a.target_key, pack)
        )
        if not cap_ok:
            continue
        if not (first_shown_round <= a.locked_round <= close_round):
            continue
        # effectfulness proxy: a zero-cost add_training is the `none` option -> not a fix
        if a.action_type == "add_training" and a.cost == 0:
            continue
        matched_types.add(a.action_type)
        locked_rounds.append(a.locked_round)
    if not locked_rounds:
        return None, ()
    ordered = tuple(t for t in rule.cleared_by if t in matched_types)
    return min(locked_rounds), ordered


# -- the per-round ledger transition (contract-spec section 5.2) --------------------------


def _watch_rule(pack: Casepack, key: str) -> WatchRule:
    for rule in pack.watch_rules:
        if rule.key == key:
            return rule
    raise KeyError(f"watch rule {key!r} not in pack")


def advance_ledger(
    prior: tuple[LedgerSignal, ...],
    state: TeamState,
    pack: Casepack,
    fired_signals: frozenset[str] = frozenset(),
) -> tuple[LedgerSignal, ...]:
    """Advance the ledger by one round: immutable history in, a new ledger out.

    Terminal (cleared/fired) episodes and every non-latest episode are carried forward
    byte-identical; only the latest open episode per key transitions. A condition that raises
    again after a terminal episode opens a NEW episode (`episode_id + 1`) -- history is never
    overwritten (section 5.2).
    """
    close_round = state.round
    latest_index: dict[str, int] = {}
    for i, row in enumerate(prior):
        latest_index[row.key] = i  # prior is append-order, so the last wins

    out: list[LedgerSignal] = list(prior)

    for rule in pack.watch_rules:
        raised = evaluate(rule, state, pack)
        still_raises = raised is not None
        fired = rule.key in fired_signals
        idx = latest_index.get(rule.key)
        latest = out[idx] if idx is not None else None

        if latest is not None and latest.status == "open":
            severity = latest.severity
            value = latest.value
            if raised is not None:
                new_sev, new_val = raised
                # no de-escalation: severity is a floor
                if _SEVERITY_RANK[new_sev] > _SEVERITY_RANK[severity]:
                    severity = new_sev
                value = new_val
            cleared_round, cleared_by = matching_clear_actions(
                rule, rule.capability, state, latest.first_shown_round, close_round, pack
            )
            if still_raises:
                cleared_round, cleared_by = None, ()
            fire_round = latest.fire_round if latest.fire_round is not None else (close_round if fired else None)
            status = compute_status(cleared_round, fire_round, still_raises)
            actionable = latest.was_actionable or was_actionable(
                latest.cheapest_fix_when_raised, state.available_funds_by_round,
                range(latest.first_shown_round, close_round + 1),
            )
            out[idx] = replace(
                latest, severity=severity, value=value, status=status,
                cleared_round=cleared_round, fire_round=fire_round, cleared_by=cleared_by,
                was_actionable=actionable,
            )
            continue

        # no open episode: only a fresh raise opens one (a new episode on recurrence)
        if raised is None:
            continue
        severity, value = raised
        episode_id = (latest.episode_id + 1) if latest is not None else 1
        cheapest = cheapest_effectful_fix(rule, pack)
        actionable = was_actionable(
            cheapest, state.available_funds_by_round, range(close_round, close_round + 1)
        )
        fire_round = close_round if fired else None
        status = compute_status(None, fire_round, True)
        out.append(LedgerSignal(
            key=rule.key, episode_id=episode_id, capability=rule.capability,
            metric=rule.metric, metric_kind=rule.metric_kind, value=value,
            severity=severity, status=status, first_shown_round=close_round,
            fire_round=fire_round, was_actionable=actionable, cheapest_fix_when_raised=cheapest,
        ))

    return tuple(out)
