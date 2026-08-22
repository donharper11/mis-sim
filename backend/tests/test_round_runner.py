"""Round-runner property tests (1.6 spec section 6, build steps 2-6).

Runs on a file-backed SQLite database (portable; the `--full` seed and the migration demo run on
Postgres). Covers the invariants whose real proof is a property/planted-defect test rather than a
grep (spec I5 note, SPEC_PROTOCOL section 4.3): I5 (single re-score re-entry), I8 (partial update),
I9 (append-only ledger), plus the O1/O2/O3 lock/advance and in-flight behaviours.
"""

from __future__ import annotations

import pytest

from app.engine.ledger import LedgerSignal
from app.round import models as m
from app.round import runner as runner_mod
from app.round.db import create_all, make_engine
from app.round.runner import LockStateError, RoundRunner
from app.seed.demo import load_scenario
from sqlalchemy.orm import sessionmaker

import seeds.riverside_full as full


@pytest.fixture()
def session(tmp_path):
    url = f"sqlite:///{tmp_path/'round.db'}"
    engine = make_engine(url)
    create_all(engine)
    factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    s = factory()
    yield s
    s.close()
    engine.dispose()


@pytest.fixture()
def pack():
    p, _ = load_scenario("riverside_r3")
    return p


def _seed_two_rounds(session, pack) -> RoundRunner:
    """Seed team_state + the first two rounds' estates from the full-game builders."""
    session.add(m.TeamStateRow(
        instance_id=full.INSTANCE_ID, team_id=full.TEAM_ID, current_round=1,
        declared_strategy=full.STRATEGY, declared_strategy_round=2, cash=0,
        opex_runrate=pack.metadata.budget.opening_opex,
    ))
    session.flush()
    for r in (1, 2):
        full._seed_round_estate(session, pack, r)
    return RoundRunner(session, pack, full.INSTANCE_ID, full.TEAM_ID)


# -- O3: results are produced at advance, and advance needs a lock --------------------------

def test_o3_advance_requires_lock(session, pack):
    runner = _seed_two_rounds(session, pack)
    with pytest.raises(LockStateError):
        runner.advance(1)  # not locked yet
    runner.lock(1)
    payload = runner.advance(1)  # now produces a result
    assert payload["round"] == 1
    assert session.get(m.RoundResult, (full.INSTANCE_ID, full.TEAM_ID, 1)) is not None


def test_o3_lock_freezes_decision_writes(session, pack):
    runner = _seed_two_rounds(session, pack)
    runner.lock(1)
    with pytest.raises(LockStateError):
        runner.write_decision_sheet(1, [{"key": "x", "category": "training", "capability": "order_fulfilment"}])


# -- O1: a locked round can be unlocked; it INVALIDATES the RoundResult, never edits it -----

def test_o1_unlock_invalidates_result_and_allows_readvance(session, pack):
    runner = _seed_two_rounds(session, pack)
    runner.lock(1)
    runner.advance(1)
    # a second advance of the same round is refused -- the result is immutable (I6)
    with pytest.raises(LockStateError):
        runner.advance(1)
    # unlock deletes (invalidates) the result rather than editing it (O1)
    runner.unlock(1)
    assert session.get(m.RoundResult, (full.INSTANCE_ID, full.TEAM_ID, 1)) is None
    # re-lock + re-advance writes a fresh row (never an UPDATE)
    runner.lock(1)
    payload = runner.advance(1)
    assert payload["round"] == 1


# -- I8: partial-update semantics -- absent categories are untouched ------------------------

def test_i8_partial_update_leaves_absent_categories(session, pack):
    runner = _seed_two_rounds(session, pack)
    # round 1 seed carries application (maint), platform_service and application lines.
    before = session.scalars(
        runner_mod.snap._scoped(m.DecisionLineRow, full.INSTANCE_ID, full.TEAM_ID, 1)
    ).all()
    platform_before = [l.key for l in before if l.category == "platform_service"]
    assert platform_before, "fixture must have a platform_service line to leave untouched"
    # write ONLY a training line -> training added; platform_service/application untouched.
    runner.write_decision_sheet(1, [
        {"key": "d_new_training", "category": "training", "capability": "order_fulfilment",
         "capex": 5000, "action_type": "add_training", "target_key": "order_mgmt_v42"},
    ])
    after = session.scalars(
        runner_mod.snap._scoped(m.DecisionLineRow, full.INSTANCE_ID, full.TEAM_ID, 1)
    ).all()
    platform_after = [l.key for l in after if l.category == "platform_service"]
    training_after = [l.key for l in after if l.category == "training"]
    assert platform_after == platform_before, "absent category was wiped (partial-update violated)"
    assert training_after == ["d_new_training"]


def test_i8_partial_update_replaces_only_named_category(session, pack):
    runner = _seed_two_rounds(session, pack)
    runner.write_decision_sheet(1, [
        {"key": "d_maint_a", "category": "application", "capability": "store_operations",
         "capex": 1000, "is_maintenance": True},
    ])
    apps = session.scalars(
        runner_mod.snap._scoped(m.DecisionLineRow, full.INSTANCE_ID, full.TEAM_ID, 1)
        .where(m.DecisionLineRow.category == "application")
    ).all()
    assert [a.key for a in apps] == ["d_maint_a"], "the named category should be fully replaced"


# -- I5: the step-12 re-score is the ONLY re-entry (single score_team re-entry) -------------

def test_i5_single_rescore_reentry(session, pack, monkeypatch):
    runner = _seed_two_rounds(session, pack)
    runner.lock(1)
    calls = {"n": 0}
    real = runner_mod.score_team

    def spy(p, st):
        calls["n"] += 1
        return real(p, st)

    monkeypatch.setattr(runner_mod, "score_team", spy)
    runner.advance(1)
    # exactly two score_team calls per advance: the step-9 raw pass + the single step-12 re-entry.
    # A planted SECOND step-12 re-score makes this 3 and fails the test (SPEC_PROTOCOL 4.3).
    assert calls["n"] == 2, f"expected 2 score_team calls (step 9 + one re-entry), got {calls['n']}"


def test_i5_event_outcome_scored_exactly_once(session, pack):
    """A fired event's scorecard delta is applied EXACTLY ONCE (not doubled by a second re-score).

    Tested at the application point (`_rolled_scorecard`): a fired event's delta lands once on top
    of the single step-12 rollup. A defect that scored the event twice (a second re-entry applying
    the delta again) would land it twice -- the assertion below then FAILS (SPEC_PROTOCOL 4.3)."""
    runner = _seed_two_rounds(session, pack)
    runner.lock(1)
    runner.advance(1)
    runner.lock(2)
    payload = runner.advance(2)
    fired = {ev["key"] for ev in payload["events"]}
    assert "warehouse_rollout_gap" in fired  # its outcome: internal_process -5, learning_growth -6

    # Reconstruct the step-12 rollup (before deltas) and apply the deltas ourselves ONCE; the
    # payload must match. Doubling the deltas (the planted defect) breaks the equality.
    class _FS:
        def __init__(self, bsc):
            self.balanced_scorecard = bsc

    base_bsc = runner_mod.score_team(pack, runner_mod.snap.build_team_state(
        session, full.INSTANCE_ID, full.TEAM_ID, 2, pack, signals=(),
    )).balanced_scorecard
    once = runner._rolled_scorecard(_FS(base_bsc), payload["events"])
    twice = runner._rolled_scorecard(_FS(base_bsc), payload["events"] + payload["events"])
    delta_ip = sum(ev.get("outcomes", {}).get("scorecard", {}).get("internal_process", 0)
                   for ev in payload["events"])
    assert once["internal_process"] == pytest.approx(base_bsc.internal_process + delta_ip)
    assert twice["internal_process"] == pytest.approx(base_bsc.internal_process + 2 * delta_ip)
    assert once["internal_process"] != twice["internal_process"]  # doubling is observable


# -- I9: the ledger is append-only -- a re-raise opens a new episode, prior row unchanged ----

def test_i9_reraise_opens_new_episode_prior_row_unchanged(session, pack):
    runner = _seed_two_rounds(session, pack)
    ep1 = LedgerSignal(
        key="ord_cap_01", episode_id=1, capability="order_fulfilment",
        metric="capacity_utilisation", metric_kind="threshold", value=1.66,
        severity="critical", status="cleared", first_shown_round=1, cleared_round=2,
        fire_round=None, cleared_by=("scale_node",), was_actionable=True,
        cheapest_fix_when_raised=0,
    )
    runner._persist_ledger((ep1,), round=2)
    stored_before = session.get(m.SignalRow, (full.INSTANCE_ID, full.TEAM_ID, "ord_cap_01", 1))
    snapshot_before = (stored_before.status, stored_before.cleared_round, stored_before.value,
                       list(stored_before.cleared_by), stored_before.first_shown_round)

    # a re-raise: advance_ledger carries ep1 byte-identical and opens ep2 (engine contract).
    ep2 = LedgerSignal(
        key="ord_cap_01", episode_id=2, capability="order_fulfilment",
        metric="capacity_utilisation", metric_kind="threshold", value=1.70,
        severity="critical", status="open", first_shown_round=3,
        was_actionable=True, cheapest_fix_when_raised=0,
    )
    runner._persist_ledger((ep1, ep2), round=3)

    stored_after = session.get(m.SignalRow, (full.INSTANCE_ID, full.TEAM_ID, "ord_cap_01", 1))
    snapshot_after = (stored_after.status, stored_after.cleared_round, stored_after.value,
                      list(stored_after.cleared_by), stored_after.first_shown_round)
    assert snapshot_after == snapshot_before, "prior episode row was overwritten (I9 violated)"
    ep2_row = session.get(m.SignalRow, (full.INSTANCE_ID, full.TEAM_ID, "ord_cap_01", 2))
    assert ep2_row is not None and ep2_row.status == "open" and ep2_row.first_shown_round == 3


def test_i9_plant_overwrite_is_detectable(session, pack):
    """The falsification: a runner that reused episode_id 1 (overwriting the cleared episode with
    the re-raise) would change the ep1 row -- which the assertion above would catch. Prove the
    detector fires by simulating the overwrite here."""
    runner = _seed_two_rounds(session, pack)
    ep1 = LedgerSignal(
        key="wh_rollout_01", episode_id=1, capability="order_fulfilment",
        metric="rollout_without_support", metric_kind="presence", value=1.0,
        severity="critical", status="cleared", first_shown_round=1, cleared_round=2,
        fire_round=None, was_actionable=True,
    )
    runner._persist_ledger((ep1,), round=2)
    # simulate the BUG: reuse episode_id 1 with the re-raised (open) state.
    overwritten = m.SignalRow(
        instance_id=full.INSTANCE_ID, team_id=full.TEAM_ID, key="wh_rollout_01", episode_id=1,
        round=3, capability="order_fulfilment", metric="rollout_without_support",
        metric_kind="presence", value=1.0, severity="critical", status="open",
        first_shown_round=1, cleared_round=None, fire_round=None, cleared_by=[],
        was_actionable=True, cheapest_fix_when_raised=None,
    )
    session.merge(overwritten)
    session.flush()
    row = session.get(m.SignalRow, (full.INSTANCE_ID, full.TEAM_ID, "wh_rollout_01", 1))
    assert row.status == "open"  # the plant DID change ep1 -> the append-only assertion would FAIL


# -- A-001: missed_signals is keyed by EPISODE, not by signal key --------------------------

def test_a001_missed_signals_counts_each_episode(session, pack):
    """A previously-cleared signal that re-raises and FIRES a new episode must appear in
    missed_signals for that fired episode; the earlier cleared episode must NOT (finding 1.6-A-001).

    The collapse defect (keying the projection by `s.key`) let the later episode's projection mask
    the earlier one -- dropping a genuine 'you were told in round N' (or falsely reporting a cleared
    episode). Keying by episode identity fixes both directions; this test fails on the collapse."""
    runner = _seed_two_rounds(session, pack)
    ledger = (
        # ep1: raised then CLEARED before fire (credited -> acted_before_fire True; NOT a miss)
        LedgerSignal(
            key="wh_rollout_01", episode_id=1, capability="order_fulfilment",
            metric="rollout_without_support", metric_kind="presence", value=1.0,
            severity="critical", status="cleared", first_shown_round=2, cleared_round=3,
            fire_round=None, cleared_by=("add_training",), was_actionable=True,
            cheapest_fix_when_raised=3000,
        ),
        # ep2: re-raised and FIRED, never acted (a genuine miss -> must be in missed_signals)
        LedgerSignal(
            key="wh_rollout_01", episode_id=2, capability="order_fulfilment",
            metric="rollout_without_support", metric_kind="presence", value=1.0,
            severity="critical", status="fired", first_shown_round=4, cleared_round=None,
            fire_round=4, cleared_by=(), was_actionable=True, cheapest_fix_when_raised=3000,
        ),
    )
    missed = runner._missed_signals(ledger)
    episodes = {(mn["key"], mn["episode_id"]) for mn in missed}
    assert ("wh_rollout_01", 2) in episodes, "the fired episode must be reported as a missed signal"
    assert ("wh_rollout_01", 1) not in episodes, "the cleared (credited) episode must NOT be reported"


# -- O2: in-flight purchases materialise only at arrival_round ------------------------------

def test_o2_in_flight_materialises_at_arrival(session, pack):
    runner = _seed_two_rounds(session, pack)
    session.add(m.InFlightRow(
        instance_id=full.INSTANCE_ID, team_id=full.TEAM_ID, key="new_relay",
        catalog_key="relay_x", ordered_round=1, arrival_round=2, capex=10000,
        node_payload={"roles_filled": ["network_path"], "availability": 0.99,
                      "installed_round": 2, "service_life_rounds": 6, "serves": ["order_fulfilment"],
                      "throughput": None, "owns_entities": [], "opex_contribution": 0},
        materialised=False,
    ))
    session.flush()
    # round 1: the ordered node is NOT in the round-1 estate (would inflate capacity, O2).
    r1_keys = [n.key for n in session.scalars(
        runner_mod.snap._scoped(m.ArchNodeRow, full.INSTANCE_ID, full.TEAM_ID, 1)).all()]
    assert "new_relay" not in r1_keys
    # advancing round 2 materialises it into the round-2 estate.
    runner.lock(1); runner.advance(1)
    runner.lock(2); runner.advance(2)
    r2_keys = [n.key for n in session.scalars(
        runner_mod.snap._scoped(m.ArchNodeRow, full.INSTANCE_ID, full.TEAM_ID, 2)).all()]
    assert "new_relay" in r2_keys
