"""Versioned DTOs at the governed AI boundary.

These models intentionally do not contain provider credentials, ORM objects, or
simulation commands.  A grounding block is a compact, immutable projection of
the current scoped state and is the only numeric source a provider response may
quote.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator, model_validator


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_PROVIDER_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_PATH_RE = re.compile(r"^/[A-Za-z0-9_./:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AIContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


def _bounded_key(value: str, field: str = "key") -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise ValueError(f"{field} must be a lower snake_case key of at most 64 characters")
    return value


def _provider_key(value: str, field: str = "provider") -> str:
    if not isinstance(value, str) or not _PROVIDER_KEY_RE.fullmatch(value):
        raise ValueError(f"{field} must be a bounded provider key")
    return value


def _finite_number(value: float | int | None, field: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    return value


class GroundingFactV1(AIContractModel):
    key: StrictStr = Field(min_length=1, max_length=64)
    display_value: StrictStr = Field(min_length=1, max_length=512)
    numeric_value: float | int | None = None
    unit: StrictStr | None = Field(default=None, min_length=1, max_length=64)
    source_path: StrictStr = Field(min_length=1, max_length=128)
    round: StrictInt = Field(ge=0)

    @field_validator("key")
    @classmethod
    def valid_key(cls, value: str) -> str:
        return _bounded_key(value)

    @field_validator("unit")
    @classmethod
    def valid_unit(cls, value: str | None) -> str | None:
        return None if value is None else _bounded_key(value, "unit")

    @field_validator("source_path")
    @classmethod
    def valid_source_path(cls, value: str) -> str:
        if not _PATH_RE.fullmatch(value):
            raise ValueError("source_path must be a bounded absolute path")
        return value

    @field_validator("numeric_value")
    @classmethod
    def valid_numeric_value(cls, value: float | int | None) -> float | int | None:
        return _finite_number(value, "numeric_value")


class GroundingBlockV1(AIContractModel):
    version: Literal[1]
    instance_id: StrictInt = Field(gt=0)
    team_id: StrictInt = Field(gt=0)
    round: StrictInt = Field(ge=0)
    state_digest: StrictStr = Field(min_length=64, max_length=64)
    facts: tuple[GroundingFactV1, ...] = Field(max_length=128)
    numbers_must_be_in_facts: Literal[True] = True

    @field_validator("state_digest")
    @classmethod
    def valid_digest(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("state_digest must be a lowercase SHA-256 digest")
        return value

    @field_validator("facts", mode="before")
    @classmethod
    def freeze_facts(cls, value):
        # The wire contract is a list, while the in-process DTO is immutable.
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_fact_rounds(self) -> "GroundingBlockV1":
        if any(fact.round != self.round for fact in self.facts):
            raise ValueError("all grounding facts must belong to the block round")
        keys = [fact.key for fact in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("grounding fact keys must be unique")
        return self

    @classmethod
    def from_digest(
        cls,
        *,
        instance_id: int,
        team_id: int,
        round: int,
        state: bytes | str,
        facts: tuple[GroundingFactV1, ...] | list[GroundingFactV1],
    ) -> "GroundingBlockV1":
        """Build a block from a deterministic state representation.

        Callers should hash a canonical scoped state snapshot before constructing
        this DTO.  This helper accepts bytes or text only and never serializes an
        ORM row or unrestricted state implicitly.
        """
        payload = state.encode("utf-8") if isinstance(state, str) else state
        if not isinstance(payload, bytes):
            raise TypeError("state must be bytes or str")
        return cls(
            version=1,
            instance_id=instance_id,
            team_id=team_id,
            round=round,
            state_digest=hashlib.sha256(payload).hexdigest(),
            facts=tuple(facts),
        )


class ProviderRequestV1(AIContractModel):
    purpose: Literal["persona", "coach", "debrief", "rationale"]
    system_prompt: StrictStr = Field(min_length=1, max_length=32_000)
    user_prompt: StrictStr = Field(min_length=1, max_length=32_000)
    grounding: GroundingBlockV1 | None = None
    timeout_ms: StrictInt = Field(gt=0, le=120_000)
    max_output_tokens: StrictInt = Field(gt=0, le=16_384)

    @model_validator(mode="after")
    def validate_prompts(self) -> "ProviderRequestV1":
        if not self.system_prompt.strip() or not self.user_prompt.strip():
            raise ValueError("prompts must be nonempty")
        return self


class ProviderResponseV1(AIContractModel):
    status: Literal["generated", "disabled", "unavailable"]
    text: StrictStr | None = Field(default=None, max_length=12_000)
    provider: StrictStr = Field(min_length=1, max_length=128)
    model: StrictStr | None = Field(default=None, min_length=1, max_length=128)
    latency_ms: float | int | None = Field(default=None, ge=0)
    cost_usd: float | int | None = Field(default=None, ge=0)
    reason: StrictStr | None = Field(default=None, min_length=1, max_length=64)
    tier: Literal["primary", "fallback", "local", "none"]
    grounding_digest: StrictStr | None = Field(default=None, min_length=64, max_length=64)

    @field_validator("provider", "model")
    @classmethod
    def valid_provider_keys(cls, value: str | None, info) -> str | None:
        return None if value is None else _provider_key(value, info.field_name)

    @field_validator("reason")
    @classmethod
    def valid_reason(cls, value: str | None) -> str | None:
        return None if value is None else _bounded_key(value, "reason")

    @field_validator("latency_ms", "cost_usd")
    @classmethod
    def valid_observation(cls, value: float | int | None, info) -> float | int | None:
        return _finite_number(value, info.field_name)

    @field_validator("grounding_digest")
    @classmethod
    def valid_grounding_digest(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256_RE.fullmatch(value):
            raise ValueError("grounding_digest must be a lowercase SHA-256 digest")
        return value

    @model_validator(mode="after")
    def validate_status_shape(self) -> "ProviderResponseV1":
        if self.status == "generated" and not self.text:
            raise ValueError("generated response requires text")
        if self.status == "generated" and self.tier == "none":
            raise ValueError("generated response requires a provider tier")
        if self.status != "generated" and self.tier != "none":
            raise ValueError("disabled and unavailable responses use tier=none")
        if self.status == "disabled" and self.reason != "all_providers_disabled":
            raise ValueError("disabled response requires the governed reason")
        return self
