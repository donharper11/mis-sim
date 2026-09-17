"""Disabled-by-default, injected three-tier provider orchestration."""

from __future__ import annotations

import math
import queue
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

from .contracts import ProviderRequestV1, ProviderResponseV1, _provider_key
from .grounding import GroundingViolation, validate_grounded_text
from .policy import PolicyViolation, validate_teaching_output


class ProviderAdapter(Protocol):
    """The only provider seam; application code injects an approved adapter."""

    def generate(self, request: ProviderRequestV1) -> Mapping[str, Any] | ProviderResponseV1: ...


class ProviderTier(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: Literal["primary", "fallback", "local"]
    provider: StrictStr = Field(min_length=1, max_length=128)
    model: StrictStr | None = Field(default=None, min_length=1, max_length=128)
    enabled: bool = False
    timeout_ms: StrictInt = Field(gt=0, le=120_000)
    endpoint: StrictStr | None = Field(default=None, min_length=1, max_length=512)

    @field_validator("provider", "model")
    @classmethod
    def bounded_name(cls, value: str | None) -> str | None:
        return None if value is None else _provider_key(value, "provider/model")


@dataclass(frozen=True)
class _AttemptFailure(Exception):
    reason: str


_Provider = ProviderAdapter | Callable[[ProviderRequestV1], Mapping[str, Any] | ProviderResponseV1]
_MAX_TEXT_CHARS = 12_000


class ProviderOrchestrator:
    """Try injected tiers in fixed order and return a safe typed product result."""

    ORDER = ("primary", "fallback", "local")

    def __init__(
        self,
        *,
        providers: Mapping[str, _Provider] | None = None,
        tiers: tuple[ProviderTier, ...] | list[ProviderTier] | None = None,
    ) -> None:
        self._providers = dict(providers or {})
        self._tiers = tuple(tiers or self.default_tiers())
        self._validate_tier_order()

    @staticmethod
    def default_tiers() -> tuple[ProviderTier, ...]:
        """Return the governed defaults: all disabled and therefore no I/O."""
        return (
            ProviderTier(name="primary", provider="dashscope", model="qwen_max", timeout_ms=2_000),
            ProviderTier(name="fallback", provider="together", model="qwen_72b", timeout_ms=3_000),
            ProviderTier(name="local", provider="vllm", model="qwen_14b_awq", timeout_ms=5_000),
        )

    @classmethod
    def from_settings(cls, settings: Any, *, providers: Mapping[str, _Provider] | None = None) -> "ProviderOrchestrator":
        """Build the fixed chain from non-secret application settings.

        The injected ``providers`` mapping is still required for any actual
        generation.  This constructor therefore cannot create a network client
        accidentally when settings enable a tier.
        """
        tiers = (
            ProviderTier(
                name="primary", provider=settings.AI_PRIMARY_PROVIDER,
                model=settings.AI_PRIMARY_MODEL, enabled=settings.AI_PRIMARY_ENABLED,
                endpoint=settings.AI_PRIMARY_URL, timeout_ms=settings.AI_PRIMARY_TIMEOUT_MS,
            ),
            ProviderTier(
                name="fallback", provider=settings.AI_FALLBACK_PROVIDER,
                model=settings.AI_FALLBACK_MODEL, enabled=settings.AI_FALLBACK_ENABLED,
                endpoint=settings.AI_FALLBACK_URL, timeout_ms=settings.AI_FALLBACK_TIMEOUT_MS,
            ),
            ProviderTier(
                name="local", provider=settings.AI_LOCAL_PROVIDER,
                model=settings.AI_LOCAL_MODEL, enabled=settings.AI_LOCAL_ENABLED,
                endpoint=settings.AI_LOCAL_URL, timeout_ms=settings.AI_LOCAL_TIMEOUT_MS,
            ),
        )
        return cls(providers=providers, tiers=tiers)

    def _validate_tier_order(self) -> None:
        names = tuple(tier.name for tier in self._tiers)
        if names != self.ORDER:
            raise ValueError("provider tiers must be ordered primary, fallback, local")

    @property
    def tiers(self) -> tuple[ProviderTier, ...]:
        return self._tiers

    def generate(self, request: ProviderRequestV1, *, safe_fallback: str = "This stakeholder is unavailable right now.") -> ProviderResponseV1:
        """Generate read-only teaching content, degrading safely on every failure."""
        if not isinstance(safe_fallback, str) or not safe_fallback.strip() or len(safe_fallback) > _MAX_TEXT_CHARS:
            raise ValueError("safe_fallback must be nonempty and bounded")
        enabled_tiers = [tier for tier in self._tiers if tier.enabled]
        digest = request.grounding.state_digest if request.grounding is not None else None
        if not enabled_tiers:
            return ProviderResponseV1(
                status="disabled", text=safe_fallback, provider="disabled",
                model=None, latency_ms=None, cost_usd=None,
                reason="all_providers_disabled", tier="none", grounding_digest=digest,
            )

        failures: list[_AttemptFailure] = []
        for tier in enabled_tiers:
            provider = self._providers.get(tier.provider)
            if provider is None:
                failures.append(_AttemptFailure("provider_unavailable"))
                continue
            tier_request = request.model_copy(update={"timeout_ms": tier.timeout_ms})
            started = time.perf_counter()
            try:
                raw = self._invoke_with_timeout(provider, tier_request, tier.timeout_ms)
                payload = self._payload(raw)
                text = payload.get("text")
                if not isinstance(text, str) or not text.strip():
                    raise _AttemptFailure("malformed_response")
                if len(text) > min(_MAX_TEXT_CHARS, tier_request.max_output_tokens * 4):
                    # A cheap deterministic upper bound prevents unbounded output
                    # without pretending to measure provider tokenizer internals.
                    raise _AttemptFailure("output_budget_exceeded")
                validate_teaching_output(text)
                validate_grounded_text(text, tier_request.grounding)
                latency = payload.get("latency_ms")
                cost = payload.get("cost_usd")
                latency = self._observation(latency, "latency_ms")
                cost = self._observation(cost, "cost_usd")
                if latency is None:
                    latency = (time.perf_counter() - started) * 1000
                return ProviderResponseV1(
                    status="generated", text=text, provider=tier.provider,
                    model=tier.model or self._optional_key(payload.get("model"), "model"),
                    latency_ms=latency, cost_usd=cost,
                    reason=None, tier=tier.name, grounding_digest=digest,
                )
            except _AttemptFailure as failure:
                failures.append(failure)
            except (PolicyViolation, GroundingViolation) as exc:
                failures.append(_AttemptFailure(self._safe_reason(str(exc))))
            except (ValueError, TypeError, KeyError):
                failures.append(_AttemptFailure("malformed_response"))
            except Exception:
                # Never expose provider exception details or let an outage block
                # a round.  The next tier receives the same bounded request.
                failures.append(_AttemptFailure("provider_exception"))

        return ProviderResponseV1(
            status="unavailable", text=safe_fallback, provider="fallback",
            model=None, latency_ms=None, cost_usd=None,
            reason="all_providers_unavailable", tier="none", grounding_digest=digest,
        )

    @staticmethod
    def _invoke(provider: _Provider, request: ProviderRequestV1) -> Any:
        generate = getattr(provider, "generate", None)
        return generate(request) if callable(generate) else provider(request)

    @staticmethod
    def _invoke_with_timeout(provider: _Provider, request: ProviderRequestV1, timeout_ms: int) -> Any:
        """Run an injected synchronous adapter behind a hard caller deadline.

        Provider implementations are deliberately injected and may be blocking.
        A daemon thread keeps the orchestration path from waiting after a tier
        deadline; the next tier can therefore run immediately.  No provider
        client or network primitive is created here.
        """
        result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

        def call() -> None:
            try:
                result_queue.put((True, ProviderOrchestrator._invoke(provider, request)))
            except BaseException as exc:  # captured and converted to safe status below
                result_queue.put((False, exc))

        worker = threading.Thread(target=call, name="mis-sim-ai-provider", daemon=True)
        worker.start()
        worker.join(timeout_ms / 1000)
        if worker.is_alive():
            raise _AttemptFailure("provider_timeout")
        try:
            succeeded, value = result_queue.get_nowait()
        except queue.Empty as exc:  # defensive: a completed thread must publish a result
            raise _AttemptFailure("provider_exception") from exc
        if succeeded:
            return value
        if isinstance(value, Exception):
            raise value
        raise _AttemptFailure("provider_exception")

    @staticmethod
    def _payload(raw: Any) -> dict[str, Any]:
        if isinstance(raw, ProviderResponseV1):
            if raw.status != "generated":
                raise _AttemptFailure("provider_unavailable")
            return raw.model_dump()
        if not isinstance(raw, Mapping):
            raise _AttemptFailure("malformed_response")
        return dict(raw)

    @staticmethod
    def _observation(value: Any, field: str) -> float | int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"invalid {field}")
        return value

    @staticmethod
    def _optional_key(value: Any, field: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip() or len(value) > 128 or any(char.isspace() for char in value):
            raise ValueError(f"invalid {field}")
        return value

    @staticmethod
    def _safe_reason(reason: str) -> str:
        known = {
            "empty_output", "decision_recommendation", "plan_evaluation",
            "purchase_instruction", "architecture_recommendation", "ranking_or_score",
            "numeric_claim_without_grounding", "ungrounded_numeric_claim",
            "provider_timeout",
        }
        return reason if reason in known else "policy_rejected"
