"""A4 provider and grounding contract tests.

All providers here are injected fakes.  The test module must never need a
network client or make a live call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai import (
    GroundingBlockV1,
    GroundingFactV1,
    ProviderOrchestrator,
    ProviderRequestV1,
    ProviderTier,
    validate_grounded_text,
)
from app.ai.grounding import GroundingViolation


def _request(*, grounding: GroundingBlockV1 | None = None, max_output_tokens: int = 100) -> ProviderRequestV1:
    return ProviderRequestV1(
        purpose="persona",
        system_prompt="Explain authored stakeholder context.",
        user_prompt="What is the current context?",
        grounding=grounding,
        timeout_ms=9000,
        max_output_tokens=max_output_tokens,
    )


def _grounding() -> GroundingBlockV1:
    return GroundingBlockV1(
        version=1,
        instance_id=3,
        team_id=7,
        round=2,
        state_digest="a" * 64,
        facts=[
            GroundingFactV1(
                key="round",
                display_value="Round 2",
                numeric_value=2,
                source_path="/state/round",
                round=2,
            ),
            GroundingFactV1(
                key="capital_balance",
                display_value="$1,250",
                numeric_value=1250,
                unit="usd",
                source_path="/state/capital_balance",
                round=2,
            ),
        ],
    )


@dataclass
class FakeProvider:
    result: object
    calls: list[ProviderRequestV1] = field(default_factory=list)

    def generate(self, request: ProviderRequestV1):
        self.calls.append(request)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


def _tiers(*enabled: str) -> tuple[ProviderTier, ...]:
    return (
        ProviderTier(name="primary", provider="dashscope", model="qwen_max", enabled="primary" in enabled, timeout_ms=101),
        ProviderTier(name="fallback", provider="together", model="qwen_72b", enabled="fallback" in enabled, timeout_ms=202),
        ProviderTier(name="local", provider="vllm", model="qwen_14b_awq", enabled="local" in enabled, timeout_ms=303),
    )


def test_all_disabled_makes_no_provider_call_and_returns_authored_fallback():
    fake = FakeProvider({"text": "must never be called"})
    result = ProviderOrchestrator(providers={"dashscope": fake}, tiers=_tiers()).generate(
        _request(), safe_fallback="The stakeholder is unavailable."
    )
    assert result.status == "disabled"
    assert result.text == "The stakeholder is unavailable."
    assert result.provider == "disabled"
    assert result.tier == "none"
    assert result.reason == "all_providers_disabled"
    assert fake.calls == []


def test_timeout_or_exception_falls_through_in_fixed_order_and_bounds_timeout():
    primary = FakeProvider(TimeoutError())
    together = FakeProvider(TimeoutError())
    local = FakeProvider({"text": "The stakeholder can explain the current context.", "cost_usd": 0.01})
    result = ProviderOrchestrator(
        providers={"dashscope": primary, "together": together, "vllm": local},
        tiers=_tiers("primary", "fallback", "local"),
    ).generate(_request())
    assert result.status == "generated"
    assert result.provider == "vllm"
    assert result.tier == "local"
    assert [len(primary.calls), len(together.calls), len(local.calls)] == [1, 1, 1]
    assert [primary.calls[0].timeout_ms, together.calls[0].timeout_ms, local.calls[0].timeout_ms] == [101, 202, 303]
    assert result.latency_ms is not None and result.latency_ms >= 0
    assert result.cost_usd == 0.01


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ({"text": ""}, "all_providers_unavailable"),
        ({"text": "You should buy the cloud service."}, "all_providers_unavailable"),
        ({"text": "This value is 999."}, "all_providers_unavailable"),
        ({"text": "one two three four five six seven eight nine ten"}, "all_providers_unavailable"),
    ],
)
def test_malformed_policy_ungrounded_and_budget_outputs_use_safe_fallback(raw, reason):
    fake = FakeProvider(raw)
    result = ProviderOrchestrator(
        providers={"dashscope": fake},
        tiers=_tiers("primary"),
    ).generate(_request(grounding=_grounding(), max_output_tokens=5), safe_fallback="Authored safe fallback.")
    assert result.status == "unavailable"
    assert result.text == "Authored safe fallback."
    assert result.reason == reason
    assert "exception" not in result.text.lower()


def test_primary_policy_rejection_moves_to_together():
    primary = FakeProvider({"text": "I recommend buying cloud."})
    fallback = FakeProvider({"text": "The stakeholder describes the tradeoff."})
    result = ProviderOrchestrator(
        providers={"dashscope": primary, "together": fallback},
        tiers=_tiers("primary", "fallback"),
    ).generate(_request())
    assert result.status == "generated"
    assert result.provider == "together"
    assert result.tier == "fallback"


def test_grounding_accepts_only_injected_numeric_figures():
    grounding = _grounding()
    assert validate_grounded_text("This is round 2 and the balance is $1,250.", grounding)
    with pytest.raises(GroundingViolation):
        validate_grounded_text("This is round 3 and the balance is $1,250.", grounding)
    with pytest.raises(GroundingViolation):
        validate_grounded_text("The balance is $1,250.", None)


def test_grounding_block_is_digest_bound_and_immutable():
    grounding = GroundingBlockV1.from_digest(
        instance_id=1, team_id=2, round=1, state=b"scoped-state", facts=[]
    )
    assert len(grounding.state_digest) == 64
    assert isinstance(grounding.facts, tuple)
    with pytest.raises(ValidationError):
        grounding.round = 2
    with pytest.raises(ValidationError):
        GroundingBlockV1(
            version=1, instance_id=1, team_id=2, round=1,
            state_digest="b" * 64,
            facts=[GroundingFactV1(key="r", display_value="Round 2", source_path="/round", round=2)],
        )


def test_disabled_or_unavailable_response_carries_current_grounding_digest():
    grounding = _grounding()
    result = ProviderOrchestrator(tiers=_tiers()).generate(_request(grounding=grounding))
    assert result.grounding_digest == grounding.state_digest


def test_settings_constructor_preserves_fixed_order_and_disabled_defaults():
    settings = SimpleNamespace(
        AI_PRIMARY_PROVIDER="dashscope", AI_PRIMARY_MODEL="qwen_max", AI_PRIMARY_ENABLED=False,
        AI_PRIMARY_URL=None, AI_PRIMARY_TIMEOUT_MS=111,
        AI_FALLBACK_PROVIDER="together", AI_FALLBACK_MODEL="qwen_72b", AI_FALLBACK_ENABLED=True,
        AI_FALLBACK_URL="https://example.invalid", AI_FALLBACK_TIMEOUT_MS=222,
        AI_LOCAL_PROVIDER="vllm", AI_LOCAL_MODEL="qwen_14b_awq", AI_LOCAL_ENABLED=False,
        AI_LOCAL_URL=None, AI_LOCAL_TIMEOUT_MS=333,
    )
    fake = FakeProvider({"text": "The stakeholder describes the tradeoff."})
    orchestrator = ProviderOrchestrator.from_settings(settings, providers={"together": fake})
    assert [tier.name for tier in orchestrator.tiers] == ["primary", "fallback", "local"]
    result = orchestrator.generate(_request())
    assert result.status == "generated" and result.tier == "fallback"
    assert fake.calls[0].timeout_ms == 222


def test_dto_rejects_bad_digest_and_non_neutral_non_generated_metadata():
    with pytest.raises(ValidationError):
        GroundingBlockV1(version=1, instance_id=1, team_id=1, round=0, state_digest="bad", facts=[])
    with pytest.raises(ValidationError):
        # A disabled response may not masquerade as a provider result.
        from app.ai.contracts import ProviderResponseV1
        ProviderResponseV1(
            status="disabled", text="fallback", provider="disabled",
            model=None, latency_ms=None, cost_usd=None,
            reason="all_providers_disabled", tier="primary",
        )
