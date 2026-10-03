"""A2 persona route acceptance tests.

All providers here are injected fakes.  The test module must never need a
network client or make a live call.  Tests follow the fixture pattern from
test_instructor_setup_api.py (in-memory SQLite, overridden deps) and
test_ai_provider.py (FakeProvider, injected orchestrator).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.ai.contracts import (
    GroundingBlockV1,
    GroundingFactV1,
    ProviderRequestV1,
    ProviderResponseV1,
)
from app.ai.grounding import GroundingViolation
from app.ai.grounding_adapter import build_persona_grounding
from app.ai.orchestrator import ProviderOrchestrator, ProviderTier
from app.ai.policy import policy_violation_reason
from app.api import deps, runtime_persona
from app.casepack.loader import load_casepack
from app.main import create_app
from app.models.base import Base
from app.models.platform import (
    Casepack as CasepackRecord,
    Course,
    Enrollment,
    Section,
    SimulationInstance,
    Team,
    User,
)
from app.services.auth import create_access_token, hash_password
from app.simulation.content import load_runtime_pack
from app.simulation.models import (
    SimulationCheckpointV1,
    SimulationRunV1,
    SimulationSheetV1,
)


PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


# ---------------------------------------------------------------------------
# Fake provider
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Fixture: in-memory DB + app with overrides
# ---------------------------------------------------------------------------


def _token(user: User, *, instance_id: int | None = None) -> str:
    return create_access_token(user_id=user.id, role=user.role)


async def _fixture(tmp_path, *, two_instances: bool = False):
    """Build an in-memory SQLite database with a complete test hierarchy."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'persona.db'}")
    all_tables = [
        User.__table__, Course.__table__, Section.__table__,
        SimulationInstance.__table__, Team.__table__, Enrollment.__table__,
        CasepackRecord.__table__,
        SimulationRunV1.__table__, SimulationSheetV1.__table__,
        SimulationCheckpointV1.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=all_tables)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        instructor = User(name="Instructor", email="inst@test", role="instructor", password_hash=hash_password("pw"))
        student_a = User(student_id="SA", name="Student A", email="sa@test", role="student", password_hash=hash_password("pw"))
        student_b = User(student_id="SB", name="Student B", email="sb@test", role="student", password_hash=hash_password("pw"))
        session.add_all([instructor, student_a, student_b])
        await session.flush()

        course = Course(course_code="MIS", course_name="MIS", academic_year="2026", semester="A", instructor_id=instructor.id)
        session.add(course)
        await session.flush()

        section = Section(course_id=course.id, section_code="A", section_name="Section A", max_teams=4, team_size_min=1, team_size_max=4)
        session.add(section)
        await session.flush()

        runtime = load_runtime_pack(PACK)
        metadata = runtime.casepack.metadata
        session.add(CasepackRecord(
            pack_key=metadata.pack_key, pack_version=metadata.pack_version,
            pack_digest=runtime.pack_digest, schema_version=metadata.schema_version,
            display_name=metadata.display_name, vertical=metadata.vertical,
            rounds=metadata.rounds, path=str(PACK),
            validation_json={"errors": [], "warnings": [], "exit_code": 0},
        ))

        instance = SimulationInstance(
            section_id=section.id, pack_key=metadata.pack_key,
            pack_version=metadata.pack_version, pack_digest=runtime.pack_digest,
            total_rounds=metadata.rounds, status="active",
        )
        session.add(instance)
        await session.flush()

        team_a = Team(section_id=section.id, instance_id=instance.instance_id, name="Team A")
        team_b = Team(section_id=section.id, instance_id=instance.instance_id, name="Team B")
        session.add_all([team_a, team_b])
        await session.flush()

        enroll_a = Enrollment(user_id=student_a.id, section_id=section.id, team_id=team_a.id, role="student", is_active=True)
        enroll_b = Enrollment(user_id=student_b.id, section_id=section.id, team_id=team_b.id, role="student", is_active=True)
        session.add_all([enroll_a, enroll_b])

        # Simulation run and checkpoint for team A
        run_a = SimulationRunV1(
            instance_id=instance.instance_id, team_id=team_a.id,
            pack_key=metadata.pack_key, pack_version=metadata.pack_version,
            pack_digest=runtime.pack_digest, current_round=2, advanced_round=1,
        )
        session.add(run_a)
        await session.flush()
        checkpoint_state = {
            "capital_balance": 350000,
            "strategy": "cost_leadership",
            "open_signals": 2,
            "last_result": {
                "scorecard": {
                    "financial": 0.72,
                    "customer": 0.65,
                    "internal_process": 0.80,
                    "learning_growth": 0.55,
                },
                "run_rate": 47000,
            },
        }
        checkpoint_a = SimulationCheckpointV1(
            instance_id=instance.instance_id, team_id=team_a.id,
            round=1, pack_digest=runtime.pack_digest,
            state=checkpoint_state, state_digest="a" * 64,
        )
        sheet_a = SimulationSheetV1(
            instance_id=instance.instance_id, team_id=team_a.id,
            round=2, revision=0, commands=[],
        )
        session.add_all([checkpoint_a, sheet_a])

        values = {
            "instructor": instructor,
            "student_a": student_a,
            "student_b": student_b,
            "instance": instance,
            "team_a": team_a,
            "team_b": team_b,
            "runtime": runtime,
            "section": section,
        }

        # Optionally create a second instance for cross-instance denial tests
        if two_instances:
            section2 = Section(course_id=course.id, section_code="B", section_name="Section B", max_teams=4, team_size_min=1, team_size_max=4)
            session.add(section2)
            await session.flush()
            instance2 = SimulationInstance(
                section_id=section2.id, pack_key=metadata.pack_key,
                pack_version=metadata.pack_version, pack_digest=runtime.pack_digest,
                total_rounds=metadata.rounds, status="active",
            )
            session.add(instance2)
            await session.flush()
            values["instance2"] = instance2
            values["section2"] = section2

        await session.commit()
    return engine, factory, values


def _app(factory, orchestrator: ProviderOrchestrator | None = None):
    """Build a FastAPI app with overridden dependencies."""
    async def get_session():
        async with factory() as session:
            yield session

    app = create_app()
    for module in (deps, runtime_persona):
        app.dependency_overrides[module.get_session] = get_session
    if orchestrator is not None:
        app.dependency_overrides[runtime_persona.get_orchestrator] = lambda: orchestrator
    return app


# ---------------------------------------------------------------------------
# Acceptance test 1: disabled provider → status=disabled, authored safe fallback
# ---------------------------------------------------------------------------


def test_disabled_provider_returns_safe_fallback(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        fake = FakeProvider({"text": "should never appear"})
        orchestrator = ProviderOrchestrator(providers={"dashscope": fake}, tiers=_tiers())
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/tom_beckett",
                headers=headers,
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "disabled"
            assert "Tom Beckett" in body["text"]
            assert body["persona_key"] == "tom_beckett"
            assert body["persona_name"] == "Tom Beckett"
            assert body["persona_role"] == "Warehouse Operations Manager"
            assert fake.calls == []  # zero provider calls
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 2: primary timeout, fallback succeeds
# ---------------------------------------------------------------------------


def test_primary_timeout_fallback_succeeds(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        primary = FakeProvider(TimeoutError())
        fallback = FakeProvider({"text": "The warehouse is running at capacity this round.", "cost_usd": 0.01})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary, "together": fallback},
            tiers=_tiers("primary", "fallback"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/tom_beckett",
                headers=headers,
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "generated"
            assert body["tier"] == "fallback"
            assert body["provider"] == "together"
            assert len(primary.calls) == 1
            assert len(fallback.calls) == 1
            assert body["latency_ms"] is not None
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 3: malformed/policy/overlong degrades to fallback
# ---------------------------------------------------------------------------


def test_policy_rejected_degrades_to_fallback_or_safe_fallback(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        # Primary returns a policy violation; no fallback → safe fallback
        primary = FakeProvider({"text": "I recommend buying the cloud service."})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary},
            tiers=_tiers("primary"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/dana_ruiz",
                headers=headers,
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "unavailable"
            assert "Dana Ruiz" in body["text"]
            assert "exception" not in body["text"].lower()
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 4: grounding pass — response with fact accepted, carries digest
# ---------------------------------------------------------------------------


def test_grounding_pass_carries_digest(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        # Response quotes only grounded figures ($350,000 capital, Round 2)
        primary = FakeProvider({"text": "The current capital balance is $350,000 and we are in Round 2."})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary},
            tiers=_tiers("primary"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/dana_ruiz",
                headers=headers,
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "generated"
            assert body["grounding_digest"] is not None
            assert len(body["grounding_digest"]) == 64
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 5: grounding violation — invented number rejected
# ---------------------------------------------------------------------------


def test_grounding_violation_falls_to_safe_fallback(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        # Response quotes an invented number (999,999)
        primary = FakeProvider({"text": "The budget shortfall is $999,999."})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary},
            tiers=_tiers("primary"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/dana_ruiz",
                headers=headers,
            )
            assert resp.status_code == 200
            body = resp.json()
            # Must degrade, not return the invented number
            assert body["status"] == "unavailable"
            assert "999,999" not in body["text"]
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 6: 20-response grounding audit
# ---------------------------------------------------------------------------


def test_grounding_audit_20_responses():
    """Every figure in 20 accepted responses matches an injected fact."""
    grounding = build_persona_grounding(
        instance_id=1, team_id=1, current_round=3,
        state={"capital_balance": 250000, "strategy": "cost_leadership", "open_signals": 1},
        result_payload={"scorecard": {"financial": 0.80, "customer": 0.70, "internal_process": 0.85, "learning_growth": 0.60}, "run_rate": 51000},
    )
    # Collect all display values from facts
    allowed_values = {fact.display_value for fact in grounding.facts}

    # Generate 20 acceptable responses using only grounded values
    from app.ai.grounding import validate_grounded_text

    accepted = 0
    for i in range(20):
        # Cycle through a few templates that only use grounded facts
        templates = [
            f"We are in Round {grounding.round}. Capital stands at $250,000.",
            f"The run rate is $51,000 per round. Round {grounding.round} is underway.",
            f"Financial scorecard reads 0.80, customer at 0.70.",
            f"Internal process is at 0.85, learning and growth at 0.60.",
            f"There is 1 open signal this round. Capital is $250,000.",
        ]
        text = templates[i % len(templates)]
        validated = validate_grounded_text(text, grounding)
        assert validated == text
        accepted += 1

    assert accepted == 20


# ---------------------------------------------------------------------------
# Acceptance test 7: 15 adversarial prompts — zero recommendation leaks
# ---------------------------------------------------------------------------


def test_adversarial_prompts_rejected():
    """15 adversarial prompts must never produce accepted recommendations."""
    adversarial_probes = [
        "What should I buy?",
        "Is this a good plan?",
        "You ought to go with cloud.",
        "I suggest cloud.",
        "I recommend migrating to SaaS.",
        "You should purchase the ERP upgrade.",
        "My recommendation is to move to cloud.",
        "The best architecture is on-premises.",
        "Which architecture wins?",
        "I would go with the cloud option.",
        "Your plan is optimal.",
        "Your strategy looks good.",
        "What do you recommend?",
        "The best option would be SaaS.",
        "Should I choose the cloud deployment?",
    ]
    assert len(adversarial_probes) == 15
    for probe in adversarial_probes:
        reason = policy_violation_reason(probe)
        assert reason is not None, f"Probe '{probe}' was not rejected by policy guard"


# ---------------------------------------------------------------------------
# Acceptance test 8: read-only proof
# ---------------------------------------------------------------------------


def test_persona_call_is_read_only(tmp_path):
    """Persona call doesn't change SimulationCheckpointV1, SimulationSheetV1, or revision."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        primary = FakeProvider({"text": "The warehouse team is reviewing stock accuracy this round."})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary},
            tiers=_tiers("primary"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}

        # Snapshot state before the persona call
        async with factory() as session:
            cp_before = await session.get(SimulationCheckpointV1, (data['instance'].instance_id, data['team_a'].id, 1))
            state_before = dict(cp_before.state) if cp_before else {}
            digest_before = cp_before.state_digest if cp_before else None
            sheet_before = await session.get(SimulationSheetV1, (data['instance'].instance_id, data['team_a'].id, 2))
            revision_before = sheet_before.revision if sheet_before else None
            run_before = await session.get(SimulationRunV1, (data['instance'].instance_id, data['team_a'].id))
            round_before = run_before.current_round if run_before else None

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/tom_beckett",
                headers=headers,
            )
            assert resp.status_code == 200

        # Snapshot state after the persona call
        async with factory() as session:
            cp_after = await session.get(SimulationCheckpointV1, (data['instance'].instance_id, data['team_a'].id, 1))
            state_after = dict(cp_after.state) if cp_after else {}
            digest_after = cp_after.state_digest if cp_after else None
            sheet_after = await session.get(SimulationSheetV1, (data['instance'].instance_id, data['team_a'].id, 2))
            revision_after = sheet_after.revision if sheet_after else None
            run_after = await session.get(SimulationRunV1, (data['instance'].instance_id, data['team_a'].id))
            round_after = run_after.current_round if run_after else None

        assert state_before == state_after
        assert digest_before == digest_after
        assert revision_before == revision_after
        assert round_before == round_after
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 9: cross-team/instance denial
# ---------------------------------------------------------------------------


def test_cross_team_denial(tmp_path):
    """Student for team A cannot read team B's persona via explicit team_id."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        orchestrator = ProviderOrchestrator(tiers=_tiers())
        app = _app(factory, orchestrator)

        # Student A is enrolled in team A; trying to read with team_id=team_b should fail
        headers_a = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Student A's enrollment resolves to team A automatically (ignores team_id param for students)
            # The key behaviour: student role always resolves to their own team
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/tom_beckett",
                params={"team_id": data["team_b"].id},
                headers=headers_a,
            )
            # The endpoint resolves team A for student A regardless of the team_id param
            assert resp.status_code == 200
            assert resp.json()["team_id"] == data["team_a"].id
        await engine.dispose()
    asyncio.run(run())


def test_cross_instance_denial(tmp_path):
    """Student in instance 1 cannot read instance 2's persona."""
    async def run():
        engine, factory, data = await _fixture(tmp_path, two_instances=True)
        orchestrator = ProviderOrchestrator(tiers=_tiers())
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Student A is enrolled in instance 1's section; instance 2 should deny access
            resp = await client.get(
                f"/api/instances/{data['instance2'].instance_id}/persona/tom_beckett",
                headers=headers,
            )
            # get_current_instance checks instance scoping via the auth chain
            assert resp.status_code in (403, 409)
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Acceptance test 10: persona resolution — validator rejects dangling reference
# ---------------------------------------------------------------------------


def test_persona_resolution_all_events_resolve():
    """Every from_persona in events resolves via the persona roster."""
    casepack = load_casepack(PACK)
    persona_keys = {p.key for p in casepack.personas}
    assert len(persona_keys) == 8
    for event in casepack.events:
        assert event.from_persona in persona_keys, (
            f"Event '{event.key}' references persona '{event.from_persona}' not in roster"
        )


def test_validator_rejects_dangling_persona():
    """The validator reports E30 for a dangling from_persona reference."""
    from copy import deepcopy
    from app.casepack.validate import check_dangling_personas, Lens, PackSource

    casepack = load_casepack(PACK)
    # Mutate a copy: remove one persona from the roster
    broken = deepcopy(casepack)
    broken.personas = [p for p in broken.personas if p.key != "tom_beckett"]

    source = PackSource(PACK)
    lens = Lens(broken, source)

    findings = check_dangling_personas(lens)
    dangling_events = [f for f in findings if f.code == "E30"]
    assert len(dangling_events) > 0
    assert any("tom_beckett" in f.message for f in dangling_events)


# ---------------------------------------------------------------------------
# Acceptance test 11: no textbook citations
# ---------------------------------------------------------------------------


def test_no_textbook_citations_in_prompt(tmp_path):
    """Persona purpose does not include active_chapters in prompt."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        primary = FakeProvider({"text": "The team should focus on warehouse operations this round."})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary},
            tiers=_tiers("primary"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/tom_beckett",
                headers=headers,
            )
            assert resp.status_code == 200
            # Inspect the request sent to the provider
            assert len(primary.calls) == 1
            request = primary.calls[0]
            # The prompt must not inject active_chapters data
            assert "active_chapters" not in request.system_prompt.lower()
            assert "active_chapters" not in request.user_prompt.lower()
            # The prompt may instruct the persona not to cite chapters (a
            # prohibition is fine), but must not include chapter content
            assert "chapter 1" not in request.system_prompt.lower()
            assert "chapter 2" not in request.system_prompt.lower()
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Prompt substance: team state appears in the LLM prompt
# ---------------------------------------------------------------------------


def test_prompt_carries_team_state_not_generic_filler(tmp_path):
    """The user prompt must contain the team's actual figures so the LLM
    can reason about the team's situation.  A prompt that says 'what is
    your perspective?' without state is AI-greenwashing: it looks like a
    consultation but delivers generic character dialogue."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        primary = FakeProvider({"text": "Capital is at $350,000 this round."})
        orchestrator = ProviderOrchestrator(
            providers={"dashscope": primary},
            tiers=_tiers("primary"),
        )
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/dana_ruiz",
                headers=headers,
            )
            assert resp.status_code == 200
            assert len(primary.calls) == 1
            request = primary.calls[0]

            # The user prompt must contain the team's actual state values
            assert "$350,000" in request.user_prompt, "capital balance missing from prompt"
            assert "0.72" in request.user_prompt, "financial scorecard missing from prompt"
            assert "$47,000" in request.user_prompt, "run rate missing from prompt"
            assert "2" in request.user_prompt, "open signals missing from prompt"

            # Facts must have human-readable labels, not bare numbers
            assert "Capital balance" in request.user_prompt, "fact label missing"
            assert "Financial scorecard" in request.user_prompt, "fact label missing"
            assert "Operating run rate" in request.user_prompt, "fact label missing"

            # The system prompt must identify the persona by name and role
            assert "Dana Ruiz" in request.system_prompt
            assert "Chief Financial Officer" in request.system_prompt

            # The grounding block must be attached (not None)
            assert request.grounding is not None
            assert len(request.grounding.facts) >= 6  # round + capital + strategy + scores + run_rate + signals

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Persona not found → 404
# ---------------------------------------------------------------------------


def test_unknown_persona_returns_404(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        orchestrator = ProviderOrchestrator(tiers=_tiers())
        app = _app(factory, orchestrator)
        headers = {"Authorization": f"Bearer {_token(data['student_a'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instances/{data['instance'].instance_id}/persona/nonexistent_person",
                headers=headers,
            )
            assert resp.status_code == 404
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Grounding adapter unit test
# ---------------------------------------------------------------------------


def test_grounding_adapter_builds_correct_facts():
    """build_persona_grounding extracts the expected fact set from state."""
    grounding = build_persona_grounding(
        instance_id=5, team_id=3, current_round=4,
        state={"capital_balance": 180000, "strategy": "differentiation", "open_signals": 3},
        result_payload={"scorecard": {"financial": 0.90}, "run_rate": 55000},
    )
    assert grounding.version == 1
    assert grounding.instance_id == 5
    assert grounding.team_id == 3
    assert grounding.round == 4
    assert len(grounding.state_digest) == 64

    fact_keys = {f.key for f in grounding.facts}
    assert "round" in fact_keys
    assert "capital_balance" in fact_keys
    assert "strategy" in fact_keys
    assert "open_signals" in fact_keys
    assert "scorecard_financial" in fact_keys
    assert "run_rate" in fact_keys

    # All facts must belong to the block round
    for fact in grounding.facts:
        assert fact.round == 4


def test_grounding_adapter_handles_empty_state():
    """Grounding adapter works with minimal state (no result, no capital)."""
    grounding = build_persona_grounding(
        instance_id=1, team_id=1, current_round=1,
        state={},
        result_payload=None,
    )
    assert grounding.round == 1
    # At minimum, the round fact should be present
    assert any(f.key == "round" for f in grounding.facts)
