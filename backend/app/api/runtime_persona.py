"""Read-only persona endpoint scoped through instance/team auth.

This endpoint constructs a provider request from the persona roster, calls
the three-tier orchestrator, and returns the result with grounding metadata.
It never writes ORM rows, mutates checkpoints, or changes scores.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import ProviderRequestV1, ProviderResponseV1
from app.ai.grounding_adapter import build_persona_grounding
from app.ai.orchestrator import ProviderOrchestrator, ProviderTier
from app.api.deps import get_current_instance, get_current_user, get_session
from app.casepack.registry import RegistryError, aresolve_runtime_pack
from app.models.platform import Enrollment, SimulationInstance, Team, User
from app.simulation.models import SimulationCheckpointV1, SimulationRunV1

router = APIRouter(tags=["persona"])


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------


class PersonaTurnOut(BaseModel):
    instance_id: int
    team_id: int
    persona_key: str
    persona_name: str
    persona_role: str
    round: int
    text: str
    status: str  # generated | disabled | unavailable
    provider: str
    tier: str
    latency_ms: float | None = None
    grounding_digest: str | None = None


# ---------------------------------------------------------------------------
# Dependency: orchestrator injection
# ---------------------------------------------------------------------------


def get_orchestrator() -> ProviderOrchestrator:
    """Return a ProviderOrchestrator with all tiers disabled by default.

    Production wiring overrides this dependency with a configured instance.
    Tests inject fakes via ``app.dependency_overrides``.
    """
    return ProviderOrchestrator(
        tiers=(
            ProviderTier(name="primary", provider="none", model="none", enabled=False, timeout_ms=1000),
            ProviderTier(name="fallback", provider="none", model="none", enabled=False, timeout_ms=1000),
            ProviderTier(name="local", provider="none", model="none", enabled=False, timeout_ms=1000),
        ),
    )


# ---------------------------------------------------------------------------
# Helpers (reuse patterns from runtime_platform.py)
# ---------------------------------------------------------------------------


async def _team_for_user(
    session: AsyncSession,
    instance: SimulationInstance,
    user: User,
    team_id: int | None,
) -> Team | None:
    """Resolve the team for the current user, scoped to the instance."""
    if user.role == "student":
        selected = await session.scalar(
            select(Enrollment.team_id).where(
                Enrollment.user_id == user.id,
                Enrollment.section_id == instance.section_id,
                Enrollment.role == "student",
                Enrollment.is_active.is_(True),
            )
        )
        if selected is None:
            return None
        team_id = selected
    if team_id is None:
        candidates = list(
            (
                await session.scalars(
                    select(Team)
                    .where(Team.instance_id == instance.instance_id)
                    .order_by(Team.id)
                )
            ).all()
        )
        if len(candidates) != 1:
            return None
        return candidates[0]
    return await session.scalar(
        select(Team).where(
            Team.instance_id == instance.instance_id,
            Team.id == team_id,
        )
    )


async def _runtime_pack(session: AsyncSession, instance: SimulationInstance):
    """Load the runtime pack for this instance."""
    try:
        return await aresolve_runtime_pack(session, instance.pack_key, instance.pack_version)
    except RegistryError:
        return None


def _label(pack: Any, key: str, section: str = "misc") -> str:
    """Resolve a display label from the pack's labels."""
    if pack is not None:
        labels = pack.casepack.labels
        value = getattr(labels, section, {}).get(key)
        if value:
            return value
        for family in ("stakeholders", "misc", "capabilities", "roles"):
            value = getattr(labels, family, {}).get(key)
            if value:
                return value
    return key.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/instances/{instance_id}/persona/{persona_key}", response_model=PersonaTurnOut)
async def get_persona_turn(
    persona_key: str,
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    orchestrator: ProviderOrchestrator = Depends(get_orchestrator),
    team_id: int | None = Query(default=None),
) -> PersonaTurnOut:
    """Return a persona response grounded in the team's current state.

    This endpoint is read-only: it never writes ORM rows, mutates
    checkpoints, changes scores, or issues simulation commands.
    """
    # 1. Resolve the team for the current user
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Could not resolve team for user")

    # 2. Load the runtime pack
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")

    # 3. Validate persona_key resolves in pack.casepack.personas
    persona = next(
        (p for p in pack.casepack.personas if p.key == persona_key),
        None,
    )
    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_key}' not found in pack roster")

    # 4. Load team checkpoint state
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    current_round = run.current_round if run is not None else 1
    checkpoint: SimulationCheckpointV1 | None = None
    state: Mapping[str, Any] = {}
    result_payload: Mapping[str, Any] | None = None
    if run is not None:
        checkpoint = await session.get(
            SimulationCheckpointV1,
            (instance.instance_id, team.id, run.advanced_round),
        )
        if checkpoint is not None and isinstance(checkpoint.state, Mapping):
            state = checkpoint.state
            result_payload = state.get("last_result")

    # 5. Build grounding block
    strategy_labels = getattr(pack.casepack.labels, "strategies", None) or {}
    grounding = build_persona_grounding(
        instance_id=instance.instance_id,
        team_id=team.id,
        current_round=current_round,
        state=state,
        result_payload=result_payload,
        strategy_labels=strategy_labels,
    )

    # 6. Resolve display labels
    persona_name = _label(pack, persona.display_name_key, section="stakeholders")
    persona_role = _label(pack, persona.role_key, section="misc")

    # 7. Construct system and user prompts (no textbook citations)
    #
    # The system prompt establishes identity, voice and constraints.
    # The user prompt carries the team's actual state so the LLM has
    # concrete material to reason about — without this the persona
    # would produce generic character dialogue and the AI integration
    # would be cosmetic rather than substantive.
    system_prompt = (
        f"You are {persona_name}, {persona_role} at {pack.casepack.metadata.display_name}.\n\n"
        f"Voice: {persona.voice}\n\n"
        f"Stance: {persona.stance}\n\n"
        f"Rules:\n"
        f"- Respond in character as {persona_name}.\n"
        f"- Do not recommend what the team should do or evaluate their plan.\n"
        f"- Do not cite textbook chapters or course materials.\n"
        f"- You may only quote the numeric figures listed under "
        f"'Current situation' below. Do not invent, estimate, or "
        f"extrapolate any other numbers."
    )

    # Build the state section from grounding facts so every number
    # the LLM sees is authorised by the grounding guard.  Each fact
    # needs a human-readable label — bare numbers are meaningless
    # to both the LLM and to anyone auditing the prompt.
    _FACT_LABELS = {
        "round": "Current round",
        "capital_balance": "Capital balance",
        "strategy": "Declared strategy",
        "scorecard_financial": "Financial scorecard",
        "scorecard_customer": "Customer scorecard",
        "scorecard_internal_process": "Internal process scorecard",
        "scorecard_learning_growth": "Learning & growth scorecard",
        "run_rate": "Operating run rate",
        "open_signals": "Open signals",
    }
    fact_lines = "\n".join(
        f"- {_FACT_LABELS.get(fact.key, fact.key.replace('_', ' ').title())}: "
        f"{fact.display_value}"
        for fact in grounding.facts
    )

    # Resolve open signals to a meaningful statement
    open_signals = state.get("open_signals")
    signal_line = ""
    if isinstance(open_signals, int) and open_signals > 0:
        signal_line = (
            f"\nThere {'is' if open_signals == 1 else 'are'} "
            f"{open_signals} unresolved signal{'s' if open_signals != 1 else ''} "
            f"requiring attention this round."
        )

    user_prompt = (
        f"The team's current situation in Round {current_round}:\n"
        f"{fact_lines}"
        f"{signal_line}\n\n"
        f"Given this situation, what is on your mind as {persona_name}? "
        f"What concerns or observations would you raise from your "
        f"role as {persona_role}?"
    )

    # 8. Call the orchestrator
    request = ProviderRequestV1(
        purpose="persona",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        grounding=grounding,
        timeout_ms=9000,
        max_output_tokens=2048,
    )

    result: ProviderResponseV1 = orchestrator.generate(
        request, safe_fallback=persona.safe_fallback
    )

    return PersonaTurnOut(
        instance_id=instance.instance_id,
        team_id=team.id,
        persona_key=persona_key,
        persona_name=persona_name,
        persona_role=persona_role,
        round=current_round,
        text=result.text or persona.safe_fallback,
        status=result.status,
        provider=result.provider,
        tier=result.tier,
        latency_ms=result.latency_ms,
        grounding_digest=result.grounding_digest,
    )
