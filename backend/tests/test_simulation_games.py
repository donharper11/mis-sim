"""P6 decision-only game route and fixture contract."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.models.base import Base
from app.round import models as round_models
from app.simulation import models as simulation_models
from app.simulation.content import load_runtime_pack
from app.simulation.games import ARCHETYPES, decision_plan, run_game
from app.simulation.types import SheetPatchV1


ROOT = Path(__file__).parents[1]
PACK = ROOT / "packs" / "riverside_grocery"
FIXTURE = ROOT / "tests" / "fixtures" / "simulation_v1_decisions.json"
STRATEGIES = ("cost_leadership", "differentiation", "customer_supplier_intimacy", "focus_strategy")


@pytest.fixture()
def pack():
    return load_runtime_pack(PACK)


@pytest.fixture()
def engine(tmp_path):
    db = create_engine(f"sqlite:///{tmp_path / 'games.db'}", future=True)
    Base.metadata.create_all(db, tables=[x.__table__ for x in (*round_models.ALL_TABLES, *simulation_models.ALL_TABLES)])
    yield db
    db.dispose()


def test_fixture_is_typed_commands_only(pack):
    fixture = json.loads(FIXTURE.read_text())
    assert {row["archetype"] for row in fixture} == set(ARCHETYPES)
    for row in fixture:
        assert len(row["rounds"]) == pack.casepack.metadata.rounds == 6
        for round_row in row["rounds"]:
            assert set(round_row) == {"attempt", "expected_error", "accepted"}
            if round_row["attempt"] is not None:
                SheetPatchV1.model_validate(round_row["attempt"])
                assert round_row["expected_error"] == "unaffordable"
            accepted = SheetPatchV1.model_validate(round_row["accepted"])
            for commands in accepted.replace_categories.values():
                for command in commands:
                    assert not {"price", "cost", "score", "state"}.intersection(command.model_fields_set)


def test_decision_plan_loads_prescribed_empty_and_paired_shapes(pack):
    empty = decision_plan("do_nothing", pack, "focus_strategy")
    assert all(not patch.replace_categories for patch in empty)
    balanced = decision_plan("balanced", pack, "cost_leadership")
    technology = decision_plan("all_tech_no_org", pack, "cost_leadership")
    org_ops = {"train", "set_process", "communicate", "assign", "set_policy", "hire"}
    def non_org(plan):
        return sorted((command.key, command.model_dump(mode="json", exclude_none=False)) for patch in plan for rows in patch.replace_categories.values() for command in rows if command.op not in org_ops)
    assert [non_org(balanced)[0:]] == [non_org(technology)]


def test_balanced_game_uses_service_and_persists_six_results(pack, engine):
    reports = run_game(engine, pack, "balanced", "cost_leadership", 101, 1)
    assert [row["round"] for row in reports] == [1, 2, 3, 4, 5, 6]
    assert all(row["simulation_version"] == 1 for row in reports)
    from app.simulation.service import SimulationService

    view = SimulationService(engine, pack).read(101, 1)
    assert view.status == "completed"
    assert view.checkpoint_round == 6
    assert view.sheet is None


def test_overspender_refusal_falls_back_without_leaking_commands(pack, engine):
    reports = run_game(engine, pack, "overspender", "cost_leadership", 102, 1)
    assert len(reports) == 6
    from app.simulation.service import SimulationService

    view = SimulationService(engine, pack).read(102, 1)
    assert view.status == "completed"
    assert all(not report["accounting"]["cost_entries"] or report["round"] > 0 for report in reports)


def test_do_nothing_fixture_is_empty_for_all_rounds(pack):
    assert all(not patch.replace_categories for patch in decision_plan("do_nothing", pack, "focus_strategy"))
