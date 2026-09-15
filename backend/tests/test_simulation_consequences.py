"""P4 pure consequences contract pins and negative boundaries."""

from copy import deepcopy
from pathlib import Path

import pytest

from app.round.runner import RoundRunner, rolled_scorecard
from app.simulation.content import load_runtime_pack
from app.simulation.consequences import prepare_effects, quote_transition, resolve_transition
from app.simulation.estate import initialize_state
from app.simulation.repairs import assess_repairs
from app.simulation.types import CommandV1, SimulationError


PACK = Path(__file__).parents[1] / "packs" / "riverside_grocery"


@pytest.fixture()
def pack():
    return load_runtime_pack(PACK)


@pytest.fixture()
def state(pack):
    return initialize_state(pack, "cost_leadership")


def test_empty_round_quotes_authored_allowance_and_initial_liabilities(pack, state):
    preview = quote_transition(pack, state, [], 1)
    assert preview.capital_available == pack.casepack.metadata.budget.capex_per_round[0]
    assert preview.capital_spend == 0
    assert preview.operating_runrate == 78_200
    assert preview.operating_forecast[0].recurring == 78_200


def test_quote_and_resolve_are_detached_and_reconcile_balances(pack, state):
    before = deepcopy(state.model_dump(mode="python"))
    command = CommandV1(key="buy_compute", op="buy_service", service="compute_pool", placement="cloud", units=1)
    preview = quote_transition(pack, state, [command], 1)
    assert state.model_dump(mode="python") == before
    assert preview.capital_spend > 0
    resolved = resolve_transition(pack, state, [command], 1)
    assert resolved.state.capital_balance == preview.capital_remaining
    assert resolved.state.cost_ledger
    assert resolved.state.projects


def test_invalid_command_is_atomic(pack, state):
    before = deepcopy(state.model_dump(mode="python"))
    with pytest.raises((SimulationError, ValueError)):
        quote_transition(pack, state, [CommandV1(key="bad", op="buy_service", service="missing_service", placement="cloud", units=1)], 1)
    assert state.model_dump(mode="python") == before


def test_actions_are_effect_only_and_use_legacy_commitment_identity(pack, state):
    command = CommandV1(key="buy_compute", op="buy_service", service="compute_pool", placement="cloud", units=1)
    prepared = prepare_effects(pack, state, [command], 1)
    assert all(action.record.locked_round == 1 for action in prepared.actions)
    assert all(action.record.action_type == "add_node" for action in prepared.actions) or not prepared.actions


def test_repairs_cover_every_watch_without_mutating_inputs(pack, state):
    before = deepcopy(state.model_dump(mode="python"))
    prepared = prepare_effects(pack, state, [], 1)
    assessments = assess_repairs(pack, state, [], 1, prepared)
    assert [item.signal for item in assessments] == sorted(rule.key for rule in pack.casepack.watch_rules)
    assert state.model_dump(mode="python") == before


def test_response_cost_is_capital_and_event_specific(pack, state):
    event = pack.casepack.events[0]
    option = next(item for item in event.options if item.key == "fund")
    command = CommandV1(key="fund_event", op="respond", event=event.key, option="fund", rationale_tag=option.tags[0])
    preview = quote_transition(pack, state, [command], 1)
    assert preview.capital_spend == option.cost
    assert event.key in preview.prevented_events


def test_scorer_adapter_is_the_same_legacy_helper(pack, state):
    resolved = resolve_transition(pack, state, [], 1)
    assert rolled_scorecard(pack, type("Score", (), {"balanced_scorecard": type("B", (), {"financial": .5, "customer": .5, "internal_process": .5, "learning_growth": .5, "financial_partial": False})()})(), [])
    assert hasattr(RoundRunner, "_rolled_scorecard")


def test_unaffordable_capital_refuses_without_state_mutation(pack, state):
    commands = [CommandV1(key=f"threat_{index}", op="buy_service", service="threat_detection", placement="on_prem", units=1) for index in range(11)]
    before = deepcopy(state.model_dump(mode="python"))
    with pytest.raises(SimulationError, match="unaffordable"):
        resolve_transition(pack, state, commands, 1)
    assert state.model_dump(mode="python") == before


def test_empty_round_can_carry_forward_an_existing_operating_deficit(pack, state):
    first = resolve_transition(pack, state, [], 1)
    assert first.state.operating_reserve < 0
    second = resolve_transition(pack, first.state, [], 2)
    assert second.state.operating_reserve < first.state.operating_reserve


def test_pending_hire_liability_is_refused_before_commit(pack, state):
    commands = [CommandV1(key=f"hire_{index}", op="hire", option="it_generalist") for index in range(100)]
    with pytest.raises(SimulationError, match="unaffordable"):
        resolve_transition(pack, state, commands, 1)
