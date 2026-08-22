"""Riverside R1-R3 signal-ledger history for the `--with-signals` demo (1.5 spec section 5.5).

This is authored data, the ledger analogue of `riverside_r3._signals()`. Two things live here:

* `signal_history()` -- the three `LedgerSignal` episodes whose timestamps project, under the
  frozen SignalState rule (contract-spec section 5.4), to exactly the three hand-built
  `SignalState` rows the 1.4 pin depends on. This is the compatibility gate: the projection
  must reproduce those rows byte-for-byte or the pin drifts.

* the two-path demonstration inputs -- a `do-nothing` team state (the warehouse rollout left
  unsupported) and a `cleared` team state (an `add_training` action taken), from which the same
  `warehouse_rollout_gap` card fires on one path and not the other.

Like `riverside_r3`, this module is pure data assembled outside the engine package; the engine
itself reads a clock and touches no file (invariant I2).
"""

from __future__ import annotations

from dataclasses import replace

from app.engine.ledger import LedgerSignal
from app.engine.state import ActionRecord, DeploymentState, TeamState

import seeds.riverside_r3 as r3


def signal_history() -> tuple[LedgerSignal, ...]:
    """The R1-R3 ledger whose projection reproduces the seed's three SignalState rows.

    Field values are the frozen contract-spec section 5.4 compatibility table. All three are
    `was_actionable=True`, so all three project `actionable=True`.
    """
    return (
        # ord_cap_01: raised R2 (warning), escalated to critical, then a scale_node action
        # cleared it in R3 before any outage fired -> credited (clear before fire).
        LedgerSignal(
            key="ord_cap_01", episode_id=1, capability="order_fulfilment",
            metric="capacity_utilisation", metric_kind="threshold", value=1.6609,
            severity="critical", status="cleared",
            first_shown_round=2, cleared_round=3, fire_round=None,
            cleared_by=("scale_node",), was_actionable=True, cheapest_fix_when_raised=0,
        ),
        # wh_rollout_01: presence signal, un-acted; warehouse_rollout_gap fired in R3 -> not
        # credited.
        LedgerSignal(
            key="wh_rollout_01", episode_id=1, capability="order_fulfilment",
            metric="rollout_without_support", metric_kind="presence", value=1.0,
            severity="critical", status="fired",
            first_shown_round=3, cleared_round=None, fire_round=3,
            cleared_by=(), was_actionable=True, cheapest_fix_when_raised=3000,
        ),
        # sec_identity_01: presence signal, un-acted, still open at R3 -> not credited.
        LedgerSignal(
            key="sec_identity_01", episode_id=1, capability="firm_infrastructure",
            metric="missing_identity_access", metric_kind="presence", value=1.0,
            severity="critical", status="open",
            first_shown_round=3, cleared_round=None, fire_round=None,
            cleared_by=(), was_actionable=True, cheapest_fix_when_raised=0,
        ),
    )


def do_nothing_state() -> TeamState:
    """The base R3 team: the warehouse rollout is live and unsupported (wh_rollout_01 raises).

    Seeds the round-evolution inputs the O1 affordability test reads; committed spend is already
    deducted, so R3 remaining capital is 46000 (pack.yaml)."""
    base = r3.build_team_state()
    return replace(base, available_funds_by_round=(354000, 214000, 46000))


def cleared_state() -> TeamState:
    """The same R3 team on a path where an `add_training` action supported the rollout.

    The unsupported warehouse deployment is now trained, so `rollout_without_support` is false,
    and the committed action is on the history so the engine can attribute the clear."""
    base = do_nothing_state()
    trained = tuple(
        replace(d, trained_count=20, ever_trained=True, process="partial")
        if d.key == "dep_centraline" else d
        for d in base.deployments
    )
    action = ActionRecord(
        action_type="add_training", locked_round=3, capability="order_fulfilment",
        target_key="centraline_im7", cost=12000,
    )
    return replace(base, deployments=trained, action_history=(action,))
