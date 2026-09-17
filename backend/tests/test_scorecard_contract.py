"""Scorecard contract v1: points, bounded fractions and immutable persisted evidence.

Historical estates are retained fixtures, not decision-driven game-play evidence.
The unaffected-payload hash was captured before implementation at c7283dc.
"""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import shutil
from types import SimpleNamespace
from typing import get_args
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import Session
import yaml

from app.calibrate import report
from app.calibrate.harness import run_calibration, score_digest
from app.casepack.loader import CasepackLoadError, load_casepack
from app.casepack.models import Event, EventOutcome, EventPrecondition, ScorecardPerspective
from app.casepack.validate import validate_pack_dir
from app.engine.rollup import BalancedScorecard
from app.round import models as m
from app.round import runner as runner_mod
from app.round.db import create_all, make_engine
from app.round.runner import LockStateError, RoundRunner
import seeds.riverside_full as full


PACK_DIR = Path(__file__).resolve().parents[1] / "packs/riverside_grocery"
DIMS = get_args(ScorecardPerspective)
HISTORICAL_DIGEST = "e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129"
UNAFFECTED_DIGEST = "17b0d426e18224a8be03346b3798a0915903ec2a41f42b5989ae8f652849eb26"


def _score(base=0.8, partial=True):
    return SimpleNamespace(balanced_scorecard=BalancedScorecard(base, base, base, base, partial))


def _events(points, dim="financial"):
    return [{"key": f"event_{i}", "outcomes": {"scorecard": {dim: value}}}
            for i, value in enumerate(points)]


def _roll(score, events):
    return RoundRunner.__new__(RoundRunner)._rolled_scorecard(score, events)


def _assert_evidence(payload, engine_base, partial):
    sc, meta = payload["scorecard"], payload["scorecard_meta"]
    assert set(sc) == {"financial", "customer", "internal_process", "learning_growth"}
    points = {d: sum(ev["outcomes"].get("scorecard", {}).get(d, 0)
                     for ev in payload["events"]) for d in DIMS}
    assert meta == {
        "version": 1, "score_unit": "fraction", "event_delta_unit": "scorecard_points",
        "financial_partial": partial, "base": engine_base, "event_delta_points": points,
    }
    assert type(meta["version"]) is int
    assert type(meta["financial_partial"]) is bool
    assert all(type(p) is int for p in meta["event_delta_points"].values())
    for dim in DIMS:
        assert type(sc[dim]) in (int, float) and math.isfinite(sc[dim])
        assert 0 <= sc[dim] <= 1
        assert sc[dim] == round(min(1.0, max(0.0, engine_base[dim] + points[dim] / 100)), 6)
        if sc[dim] == 0:
            assert type(sc[dim]) is float and math.copysign(1, sc[dim]) == 1
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize("dim", DIMS)
@pytest.mark.parametrize("base,points,expected", [
    (0.8, [-12], 0.68), (0.966932, [-12, -15], 0.696932),
    (0.493523, [-8, -4, -6], 0.313523), (0.439272, [-7], 0.369272),
    (0.6083, [], 0.6083), (0.1, [-12, -8], 0.0), (0.95, [10], 1.0),
    (0.95, [10, -10], 0.95), (0.95, [-10, 10], 0.95),
    (0.876543, [-1], 0.866543), (0.1, [-150], 0.0),
    (0.0, [], 0.0), (1.0, [], 1.0), (-0.0, [], 0.0), (0.1234567, [], 0.123457),
])
def test_n1_n2_literal_point_arithmetic(dim, base, points, expected):
    events = _events(points, dim)
    score = _score(base)
    before = deepcopy((score, events))
    sc, meta = _roll(score, events)
    assert sc == {d: expected if d == dim else round(base, 6) for d in DIMS}
    _assert_evidence({"scorecard": sc, "scorecard_meta": meta, "events": events},
                     dict.fromkeys(DIMS, base), True)
    assert (score, events) == before


@pytest.mark.parametrize("outcomes", [{}, {"scorecard": {}}, {"revenue_loss": 100000}])
def test_n2_empty_points_and_money_do_not_change_scores(outcomes):
    events = [{"key": "money_only", "outcomes": outcomes}]
    sc, meta = _roll(_score(), events)
    assert sc == dict.fromkeys(DIMS, 0.8)
    assert meta["event_delta_points"] == dict.fromkeys(DIMS, 0)
    assert EventOutcome().scorecard == {}


def test_n3_closed_vocabulary_and_finite_extreme_points():
    assert DIMS == ("financial", "customer", "internal_process", "learning_growth")
    for points, expected in [([10**310], 1.0), ([-10**310], 0.0),
                             ([10**310, 10**310, -10**310], 1.0)]:
        sc, _ = _roll(_score(), _events(points))
        assert sc["financial"] == expected
    with pytest.raises(ValueError, match="financial"):
        _roll(_score(), _events([10**310, 10**310]))


INVALID_POINTS = [True, False, "-12", -12.0, 0.1, None, float("nan"),
                  float("inf"), float("-inf"), 10**311]


@pytest.mark.parametrize("value", INVALID_POINTS)
def test_n3_invalid_delta_rejected_by_model_and_runtime(value):
    with pytest.raises(ValidationError, match="financial"):
        EventOutcome(scorecard={"financial": value})
    with pytest.raises(ValueError, match="event_0.*|financial"):
        _roll(_score(), _events([value]))


@pytest.mark.parametrize("delta", [None, [], 12, "", {"financail": -12}])
def test_n3_invalid_delta_map(delta):
    with pytest.raises(ValidationError):
        EventOutcome(scorecard=delta)
    with pytest.raises(ValueError, match="bad_event"):
        _roll(_score(), [{"key": "bad_event", "outcomes": {"scorecard": delta}}])


@pytest.mark.parametrize("value", [None, True, "0.8", [], float("nan"), float("inf"),
                                  float("-inf"), -0.01, 1.01, 10**400, "missing"])
@pytest.mark.parametrize("dim", DIMS)
def test_n3_invalid_base_rejected(dim, value):
    bsc = dict.fromkeys(DIMS, 0.8) | {"financial_partial": True}
    if value == "missing":
        del bsc[dim]
    else:
        bsc[dim] = value
    with pytest.raises(ValueError, match=dim):
        _roll(SimpleNamespace(balanced_scorecard=SimpleNamespace(**bsc)), [])


@pytest.mark.parametrize("partial", [None, 0, 1, "true", [], "missing"])
def test_n3_missing_or_non_boolean_status(partial):
    bsc = dict.fromkeys(DIMS, 0.8)
    if partial != "missing":
        bsc["financial_partial"] = partial
    with pytest.raises(ValueError, match="financial_partial"):
        _roll(SimpleNamespace(balanced_scorecard=SimpleNamespace(**bsc)), [])


@pytest.mark.parametrize("records", [None, (), {}, 3, [None], [[]], [{}],
    [{"key": "", "outcomes": {}}], [{"key": 7, "outcomes": {}}],
    [{"key": True, "outcomes": {}}], [{"key": "x"}],
    [{"key": "x", "outcomes": None}], [{"key": "x", "outcomes": []}],
    [{"key": "x", "outcomes": 1}], [{"key": "x", "outcomes": ""}],
])
def test_n3_invalid_record_shapes(records):
    with pytest.raises(ValueError):
        _roll(_score(), records)


def test_n3_absent_event_records_refused():
    with pytest.raises(ValueError, match="event_records"):
        RoundRunner.__new__(RoundRunner)._rolled_scorecard(_score())


def test_n4_duplicate_events_refused_and_inputs_unchanged():
    score, events = _score(), _events([-12])
    before = deepcopy((score, events))
    with pytest.raises(ValueError, match="event_0.*duplicate"):
        _roll(score, events + events)
    assert (score, events) == before
    sc, meta = _roll(score, events)
    assert sc["financial"] == 0.68
    assert events == [{"key": "event_0", "outcomes": {"scorecard": {"financial": -12}}}]
    sc["financial"] = 0
    meta["base"]["financial"] = 0
    assert (score, events) == before


@pytest.mark.parametrize("delta,code", [({"financail": -12}, "E18"),
    *[({"financial": value}, "E00") for value in INVALID_POINTS],
    (None, "E00"), ([], "E00"), (12, "E00"),
])
def test_n3_loader_and_diagnostics(tmp_path, delta, code):
    pack_dir = tmp_path / "pack"
    shutil.copytree(PACK_DIR, pack_dir)
    path = pack_dir / "events.yaml"
    rows = yaml.safe_load(path.read_text())
    rows[0]["outcomes"]["scorecard"] = delta
    path.write_text(yaml.safe_dump(rows))
    with pytest.raises(CasepackLoadError):
        load_casepack(pack_dir)
    findings = validate_pack_dir(pack_dir).errors
    assert {f.code for f in findings} == {code}
    assert all(f.file == "events.yaml" for f in findings)


@pytest.mark.parametrize("outcomes", [None, "missing"])
def test_n3_event_outcomes_remain_required(outcomes):
    event = load_casepack(PACK_DIR).events[0].model_dump()
    if outcomes == "missing":
        del event["outcomes"]
    else:
        event["outcomes"] = outcomes
    with pytest.raises(ValidationError, match="outcomes"):
        Event.model_validate(event)


@pytest.fixture
def runtime(tmp_path):
    pack = load_casepack(PACK_DIR)
    engine = make_engine(f"sqlite:///{tmp_path / 'runtime.db'}")
    create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        session.add(m.TeamStateRow(
            instance_id=1, team_id=1, current_round=1, declared_strategy=full.STRATEGY,
            declared_strategy_round=2, cash=0, opex_runrate=pack.metadata.budget.opening_opex,
        ))
        full._seed_round_estate(session, pack, 1)
        runner = RoundRunner(session, pack, 1, 1)
        runner.lock(1)
        session.commit()
        yield runner, session, engine
    engine.dispose()


def _scoped_rows(session):
    return {model.__tablename__: [tuple(row) for row in session.execute(
        select(model.__table__).where(model.instance_id == 1, model.team_id == 1)
    )] for model in m.ALL_TABLES}


@pytest.mark.parametrize("corruption", ["map_edit", "model_copy", "model_construct",
                                        "mapping", "null_outcome", "nonmap_outcome"])
def test_n3_unfired_invalid_outcomes_fail_before_writes(runtime, corruption, monkeypatch):
    runner, session, _ = runtime
    bad = runner.pack.events[0].model_copy(deep=True, update={
        "key": "unfired_bad_event",
        "preconditions": [EventPrecondition(type="round_equals", round=6)],
    })
    if corruption == "map_edit":
        bad.outcomes.scorecard["financial"] = True
    elif corruption == "model_copy":
        bad.outcomes = bad.outcomes.model_copy(update={"scorecard": {"financial": True}})
    elif corruption == "model_construct":
        bad.outcomes = EventOutcome.model_construct(scorecard={"financial": True})
    elif corruption == "mapping":
        bad.outcomes = {"scorecard": {"financial": True}}
    elif corruption == "null_outcome":
        bad.outcomes = None
    else:
        bad.outcomes = []
    runner.pack.events.append(bad)
    runner._events[bad.key] = bad
    before = deepcopy(_scoped_rows(session))
    original_outcomes = deepcopy(bad.outcomes)
    sheet_calls = []
    original = runner._validate_sheet

    def validate_sheet(round):
        sheet_calls.append(round)
        return original(round)

    monkeypatch.setattr(runner, "_validate_sheet", validate_sheet)
    with pytest.raises(ValueError, match="unfired_bad_event"):
        runner.advance(1)
    assert sheet_calls == []
    assert _scoped_rows(session) == before
    assert bad.outcomes == original_outcomes


def test_n3_valid_mutated_outcome_is_checked_without_rewriting_pack(runtime):
    runner, _, _ = runtime
    for event in runner.pack.events:
        event.outcomes = event.outcomes.model_copy(update={"scorecard": {"financial": -150}})
    before = deepcopy(runner.pack)
    runner._validate_scorecard_outcomes()
    assert runner.pack == before


@pytest.mark.parametrize("failure", ["base", "aggregate"])
def test_n3_late_invalid_output_prevents_publication(runtime, monkeypatch, failure):
    runner, session, _ = runtime
    before = deepcopy(_scoped_rows(session))
    original = runner_mod.score_team
    calls = []

    def invalid_final(pack, state):
        score = original(pack, state)
        calls.append(score)
        if len(calls) == 2 and failure == "base":
            score.balanced_scorecard.financial = float("nan")
        return score

    monkeypatch.setattr(runner_mod, "score_team", invalid_final)
    if failure == "aggregate":
        # Both individual points validate; their current-round sum cannot be represented.
        fired_keys = ["ransomware_on_finance", "phishing_on_staff_accounts"]
        for key in fired_keys:
            runner._events[key].outcomes = EventOutcome(scorecard={"financial": 10**310})
        monkeypatch.setattr(runner_mod.events_mod, "resolve_events", lambda *a, **k: (tuple(fired_keys), ()))
    with pytest.raises(ValueError, match="financial"):
        runner.advance(1)
    assert len(calls) == 2
    after = _scoped_rows(session)
    for table in ("round_result", "signal", "team_state"):
        assert after[table] == before[table]
    # Earlier debt/arrivals writes are owned by the caller's existing transaction.
    session.rollback()
    assert _scoped_rows(session) == before


@pytest.mark.parametrize("partial", [False, True])
def test_n5_persisted_status_copies_actual_engine_boolean(runtime, monkeypatch, partial):
    runner, session, engine = runtime
    original = runner_mod.score_team
    captured = []

    def score_with_status(pack, state):
        result = original(pack, state)
        result.balanced_scorecard.financial_partial = partial
        captured.append({d: getattr(result.balanced_scorecard, d) for d in DIMS})
        return result

    monkeypatch.setattr(runner_mod, "score_team", score_with_status)
    returned = runner.advance(1)
    session.commit()
    with Session(engine) as reader:
        stored = reader.get(m.RoundResult, (1, 1, 1)).payload
        assert stored["scorecard"] == returned["scorecard"]
        assert stored["scorecard_meta"] == returned["scorecard_meta"]
        assert stored == json.loads(json.dumps(returned, allow_nan=False))
        _assert_evidence(stored, captured[-1], partial)


@pytest.mark.parametrize("instance_id,team_id", [(901, 1), (1, 901)])
def test_n6_unversioned_history_remains_byte_identical(runtime, instance_id, team_id):
    runner, session, engine = runtime
    historical = {
        "instance_id": instance_id, "team_id": team_id, "round": 1,
        "scorecard": {"financial": -26.033068, "customer": 0.6083,
                      "internal_process": -17.506477, "learning_growth": -6.560728},
        "events": [], "firm_score": 0.35825,
    }
    session.add(m.RoundResult(instance_id=instance_id, team_id=team_id, round=1, payload=historical))
    session.commit()
    query = text("SELECT CAST(payload AS TEXT) FROM round_result "
                 "WHERE instance_id=:iid AND team_id=:tid AND round=1")
    parameters = {"iid": instance_id, "tid": team_id}
    with Session(engine) as reader:
        before = reader.scalar(query, parameters)
        assert reader.get(m.RoundResult, (instance_id, team_id, 1)).payload == historical
    runner.advance(1)
    session.commit()
    with Session(engine) as reader:
        assert reader.scalar(query, parameters) == before
        old = reader.get(m.RoundResult, (instance_id, team_id, 1)).payload
        assert old == historical and "scorecard_meta" not in old
        assert reader.get(m.RoundResult, (1, 1, 1)).payload["scorecard_meta"]["version"] == 1
    with pytest.raises(LockStateError, match="immutable"):
        runner._write_result(1, historical)


@pytest.fixture(scope="module")
def calibration(tmp_path_factory):
    pack = load_casepack(PACK_DIR)
    url = f"sqlite:///{tmp_path_factory.mktemp('scorecard-calibration') / 'rounds.db'}"
    original = RoundRunner._rolled_scorecard
    captured = {}

    def capture(self, final_score, event_records):
        bsc = final_score.balanced_scorecard
        captured[self.instance_id, self.team_id, final_score.round] = (
            {d: getattr(bsc, d) for d in DIMS}, bsc.financial_partial,
            deepcopy(final_score.record()),
        )
        return original(self, final_score, event_records)

    with patch.object(RoundRunner, "_rolled_scorecard", capture):
        archetypes, returned = run_calibration(pack, db_url=url)
    engine = make_engine(url)
    try:
        with Session(engine) as reader:
            persisted = {a.key: [row.payload for row in reader.scalars(
                select(m.RoundResult).where(m.RoundResult.instance_id == a.instance_id,
                    m.RoundResult.team_id == a.team_id).order_by(m.RoundResult.round)
            )] for a in archetypes}
            declarations = {a.key: reader.get(m.TeamStateRow, (a.instance_id, a.team_id)).declared_strategy
                            for a in archetypes}
        # Existing capability evidence contains tuples; JSON storage encodes them as lists.
        assert persisted == json.loads(json.dumps(returned, allow_nan=False))
        assert all(declarations[a.key] == a.strategy for a in archetypes)
        yield pack, archetypes, persisted, captured
    finally:
        engine.dispose()


def _unaffected(results):
    return {key: [{k: v for k, v in p.items() if k not in {"scorecard", "scorecard_meta"}}
                  for p in payloads] for key, payloads in results.items()}


def test_n5_n7_seeded_24_results_metadata_and_business_values(calibration):
    pack, archetypes, results, captured = calibration
    assert sum(map(len, results.values())) == 24
    for a in archetypes:
        assert len(results[a.key]) == 6
        seen = set()
        for payload in results[a.key]:
            base, partial, pure = captured[a.instance_id, a.team_id, payload["round"]]
            assert partial is True
            _assert_evidence(payload, base, partial)
            assert payload["capabilities"] == json.loads(json.dumps(pure["capabilities"]))
            assert payload["firm_score"] == pure["firm_score"]
            for event in payload["events"]:
                assert event["key"] not in seen
                seen.add(event["key"])
                source = next(e for e in pack.events if e.key == event["key"])
                assert event["outcomes"] == source.outcomes.model_dump()
    balanced = results["balanced"][0]
    assert balanced["scorecard"] == {"financial": 0.696932, "customer": 0.6083,
        "internal_process": 0.338769, "learning_growth": 0.369272}
    assert balanced["firm_score"] == 0.41832
    assert balanced["scorecard_meta"]["base"] == {"financial": 0.966932, "customer": 0.6083,
        "internal_process": 0.518769, "learning_growth": 0.439272}
    assert balanced["scorecard_meta"]["event_delta_points"] == {"financial": -27, "customer": 0,
        "internal_process": -18, "learning_growth": -7}
    by_event = {e["key"]: e for e in balanced["events"]}
    for key in ("ransomware_on_finance", "phishing_on_staff_accounts"):
        assert by_event[key]["node"] is None
        assert by_event["ransomware_on_finance"]["outcomes"]["revenue_loss"] == 100000
    assert [p["firm_score"] for p in results["do_nothing"]] == [0.0] * 6
    assert any(c["terms"]["org"] > 0 for p in results["do_nothing"] for c in p["capabilities"])
    assert [p["firm_score"] for p in results["all_tech_no_org"]] == [0.0] * 6
    assert any(c["terms"]["org"] > 0 for p in results["all_tech_no_org"] for c in p["capabilities"])


def test_n6_all_24_unaffected_payload_fields_match_precorrection(calibration):
    results = calibration[2]
    serialized = json.dumps(_unaffected(results), sort_keys=True, allow_nan=False)
    assert hashlib.sha256(serialized.encode()).hexdigest() == UNAFFECTED_DIGEST


def test_n8_real_report_reads_persisted_fractions_with_metadata(calibration):
    pack, archetypes, results, _ = calibration
    before = deepcopy(results)
    rendered = report.render(pack, PACK_DIR, archetypes, results)
    for dim, label in [("financial", "Financial"), ("customer", "Customer"),
                       ("internal_process", "Internal Process"), ("learning_growth", "Learning & Growth")]:
        heading = f"BALANCED SCORECARD -- {label} by round"
        assert heading in rendered
        table = rendered.split(heading, 1)[1].split("\n\n", 1)[0]
        assert table.splitlines()[1].split() == ["R1", "R2", "R3", "R4", "R5", "R6"]
        for a in archetypes:
            row = next(line.strip() for line in table.splitlines() if line.strip().startswith(a.label))
            assert row.removeprefix(a.label).split() == [f"{p['scorecard'][dim]:.3f}" for p in results[a.key]]
    assert "All reported perspective values are finite and within 0–1." in rendered
    assert " | raw value " not in rendered
    assert results == before


def test_n8_digest_includes_every_scorecard_value(calibration):
    results = calibration[2]
    original = score_digest(results)
    assert original != HISTORICAL_DIGEST
    for key, payloads in results.items():
        for index in range(len(payloads)):
            for dim in DIMS:
                changed = deepcopy(results)
                changed[key][index]["scorecard"][dim] += 0.001
                assert score_digest(changed) != original, (key, index, dim)
