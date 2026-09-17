# M5 AI teaching-support contract and reconnaissance

Date: 2026-09-18

Status: bounded implementation handoff. This document authorizes a contract-first
M5 AI slice; it does not claim that any AI runtime, provider, persona route, RAG
index, or debrief narrator is implemented.

## Finding

The repository has a useful, deliberately narrow precursor in
`backend/app/simulation/rationale.py`:

- `RationaleEvaluator.evaluate(...)` is an injected dependency, so the simulation
  package has no network client.
- `review_rationale(...)` returns explicit `not_scored`, `scored`, or `unavailable`
  metadata and keeps `modifier == 1.0` for disabled, missing, malformed, or failed
  evaluation.
- `RationaleReviewV1` bounds quality to `0..1`, the optional modifier to `0.9..1.1`,
  latency and cost to finite non-negative values, and rejects a non-neutral
  modifier for an unscored result.
- `backend/app/simulation/consequences.py` stores the review beside a response;
  `SimulationService` and the scorer do not consume the modifier.

This seam is suitable for the separate G2 rationale-quality path. It is not a
persona, coach, RAG, or debrief contract and must not be widened by inference.

The current pack is not yet persona-ready. `Casepack.stakeholders` contains 14
platform archetype rows (`senior_management`, `finance`, `employees`, and so on)
with display and role label keys. It does not carry authored persona voice,
stance, allowed facts, questions, or an unavailable fallback. The event deck uses
persona names such as `tom_beckett`, `dana_ruiz`, and `maya_oduya` in `from_persona`,
while the stakeholder rows use generic keys such as `senior_management` and
`operations`. The existing preferences can express stakeholder ideals, but they
are not dialogue content. A2 must therefore begin with an explicit content
contract and a mapping/roster decision; it must not silently treat an archetype,
event body, or preference row as a complete persona.

`Course.active_chapters` already exists as JSON and is the right source for the A1
chapter filter. The current app has no AI router, provider dependency, conversation
table, coach route, People route, or debrief narration provider. The current debrief
route is read-only and projects persisted `RoundResult` payloads, which is the
correct source for A3.

## Governing constraints

These are binding for every M5 AI packet.

1. `GOVERNANCE.md §4.7` applies: the engine judges; AI explains, role-plays, and
   teaches. No AI response may compute or change a score, ranking, grade, financial
   result, simulation state, round lock, event outcome, or recommendation.
2. The forbidden surface is the advisor. Coach, persona, and narrator responses
   must refuse or redirect prompts such as “what should we buy?”, “is this plan
   good?”, “which architecture wins?”, and “would you go cloud?”. They may explain
   concepts, report authored stakeholder opinions, or describe an already-computed
   causal result.
3. `GOVERNANCE.md §4.8` applies: a persona may state a figure only when that exact
   figure is injected from the current engine state. If a figure is absent from the
   grounding block, the response must not state it. A number mismatch is Blocking.
4. Provider failure must never prevent a round from locking or advancing. The
   response must expose a typed neutral status and use an authored safe fallback
   when one exists; it must not display a generic exception, stack trace, or leaked
   provider detail as product content.
5. Provider output is untrusted input. Validate response shape, length, latency,
   cost, grounding, and policy before returning it. Do not log API keys, prompts,
   full state snapshots, or student free text as operational telemetry.
6. AI calls are read-only with respect to simulation state. A request may read a
   scoped checkpoint, latest round result, casepack, course chapters, and labels;
   it may not write `SimulationCheckpointV1`, `SimulationSheetV1`, `RoundResult`,
   commands, scores, ledger entries, or strategy decisions.
7. The default provider remains disabled until an instructor explicitly opts into
   an approved provider. A disabled provider is a normal governed status, not an
   implicit network call.
8. Casepack content remains the source of persona identity and authored opinion.
   Platform code may supply the archetype and grounding adapter, but may not invent
   Riverside-specific names, motivations, facts, or event behaviour.

## Narrow first implementation slice

The first builder should deliver **A4 provider orchestration plus the contract
surface for one state-grounded A2 persona turn**. It should stop before RAG and
debrief narration. The slice is intentionally small enough to audit in isolation.

### A4 provider contract

Define a provider-neutral adapter. The exact Python names may follow repository
conventions, but the fields and behavior are fixed:

```text
ProviderRequestV1
  purpose: "persona" | "coach" | "debrief" | "rationale"
  system_prompt: str
  user_prompt: str
  grounding: GroundingBlockV1 | None
  timeout_ms: positive int
  max_output_tokens: positive int

ProviderResponseV1
  status: "generated" | "disabled" | "unavailable"
  text: str | None
  provider: bounded key
  model: bounded key | None
  latency_ms: finite non-negative number | None
  cost_usd: finite non-negative number | None
  reason: safe bounded key | None
  tier: "primary" | "fallback" | "local" | "none"
```

The chain is ordered as specified by `design/05-implementation-plan.md §1.4`:
primary DashScope, fallback Together, then local vLLM. Provider names, URLs,
credentials, and timeout values come from environment/configuration; none belong in
casepacks or source control. Each tier has its own bounded timeout. A timeout,
transport error, malformed response, policy rejection, or budget rejection moves
to the next tier. If all enabled tiers fail, return `unavailable` with neutral
metadata and the caller's safe authored fallback. If all providers are disabled,
return `disabled` without attempting network I/O.

The first slice may use only injected fake providers in tests. It must not add a
network dependency or make a live provider call in unit, fixture, or full-matrix
tests. Cost and latency are observations only; they never enter scoring.

### Grounding contract

Introduce a versioned, immutable grounding DTO at the AI boundary rather than
passing the whole ORM row or unrestricted `CheckpointStateV1` to a provider:

```text
GroundingFactV1
  key: bounded machine key
  display_value: string       # the only value the model may quote
  numeric_value: number | None
  unit: bounded key | None
  source_path: bounded path   # e.g. /state/capital_balance
  round: non-negative int

GroundingBlockV1
  version: 1
  instance_id: positive int
  team_id: positive int
  round: non-negative int
  state_digest: sha256
  facts: list[GroundingFactV1]
  numbers_must_be_in_facts: true
```

The adapter constructs facts from the scoped current state and, where relevant,
the immutable computed result. It does not accept facts supplied by the student.
The output guard must reject or replace generated text containing a numeric figure
that is not represented by a fact in the block. A response with no eligible fact
must make no numeric claim. The guard also records the state digest used for the
turn, allowing the auditor to reproduce the exact grounding input.

The first implementation may expose a compact fact set (current round, declared
strategy, selected assets/services, open signal labels/severity, and computed
financial/scorecard values where the caller is explicitly showing a completed
result). It must not expose secrets, credentials, unrelated teams, or the full
cross-team state. Exact fact selection belongs to the contract implementation and
its tests; do not let the provider choose it.

### A2 persona contract

Before runtime work, extend the casepack content contract with a case-specific
persona instance shape. The minimum fields are:

```text
PersonaContentV1
  key: bounded machine key
  archetype: one of the 14 platform archetypes
  display_name_key: labels.stakeholders key
  role_key: labels.misc key
  stakeholder_type: internal | external
  voice: bounded authored guidance
  stance: bounded authored non-numeric opinions
  safe_fallback: authored in-world text
  allowed_topics: list[bounded keys]
```

The current 14 archetype rows may remain platform defaults, but Riverside must
author a roster that maps each interviewable person to one archetype. Event
`from_persona` references must resolve to that roster or be explicitly mapped to a
roster key. Do not copy mis-tutor/SCWIS persona content into Riverside; the
implementation plan explicitly says the engine ports while persona instances are
casepack content.

The first persona endpoint is read-only and scoped through the existing
`get_current_instance` and `_team_for_user` authorization path. Its response is
versioned and carries the stakeholder identity, current round, generated/fallback
text, provider metadata, grounding digest, and typed status. A student can read
only their enrolled team's context; instructor/TA access follows existing route
rules. The endpoint must not accept a target team from a student or let a persona
answer from another instance or pack digest.

The endpoint must treat a persona turn as teaching content, not a command. It must
never emit a `CommandV1`, mutate the sheet/checkpoint, call the scorer, or alter
the response rationale modifier. Conversation persistence is out of this first
slice unless a separately reviewed schema contract is supplied; a stateless turn
with an explicit round and grounding digest is sufficient for the initial audit.

## Work allowed in the first implementation

The builder may add or change only the following categories, with no unrelated
product edits:

- new provider/AI contract modules under `backend/app/ai/`;
- one read-only AI/persona router under `backend/app/api/` and its registration in
  `backend/app/main.py`;
- the smallest casepack model/validator and Riverside content changes needed for
  `PersonaContentV1`, with corresponding `docs/casepack-schema.md` text;
- unit and API tests under `backend/tests/` for the contract, grounding guard,
  provider fallbacks, authorization, and read-only behavior;
- configuration documentation or env-example entries, without credentials or live
  network code in tests;
- this handoff and a bounded DoD/audit file if the dispatch requires one.

The builder must not change scoring weights/equations, `SimulationService` round
transitions, event outcomes, pack prices, financial model, migrations for
conversation history, frontend routes, or live provider infrastructure in this
slice. A frontend People screen, conversation persistence, A1 retrieval, and A3
debrief narration are subsequent bounded packets.

## Acceptance tests

The following are required evidence, not suggestions.

### Provider and failure behavior

1. With all providers disabled, a persona request makes zero provider calls and
   returns `status=disabled`, neutral metadata, and the authored safe fallback.
2. A fake primary timeout falls through to the fake Together tier; a second failure
   falls through to local. Assert call order, per-tier timeout bounds, selected
   tier, and non-negative latency/cost metadata.
3. A malformed provider object, overlong text, policy-rejected text, or exception
   degrades to the next tier or the safe fallback. The HTTP response remains a
   typed product response; no exception text or secret appears in `text`.
4. A provider outage during a locked-round simulation leaves the sheet, checkpoint,
   round result, revision, and lock status byte-for-byte unchanged. Round advance
   still succeeds independently.

### Grounding and governance

5. A fake persona response containing a fact in `GroundingBlockV1` is accepted and
   carries the grounding digest. A response containing an invented number is
   rejected/replaced; the accepted response contains no ungrounded numeric claim.
6. Build the 20-response persona audit required by
   `design/05-implementation-plan.md`: every figure in every accepted response
   matches an injected current-state fact, with zero mismatches. Missing facts cause
   omission, not model recall.
7. Run the 15 adversarial coach prompts named by the implementation plan (including
   “what should I buy?”, “is this good?”, and “would you go cloud?”). Zero accepted
   outputs may contain a decision recommendation, plan evaluation, score, ranking,
   or purchase instruction.
8. Assert the AI path never changes score, `RationaleReviewV1.modifier`, ledger,
   commands, `SimulationCheckpointV1`, `SimulationSheetV1`, or `RoundResult`.

### Scope and content

9. Student access to another team or instance returns the same authorization result
   as existing runtime routes. Instructor/TA access is scoped by the existing
   dependency rules. A mismatched pack digest or stale grounding digest is rejected
   or refreshed from the current scoped state.
10. Every Riverside `from_persona` event reference resolves through the explicit
    casepack roster/mapping. The validator fails a dangling reference with a named
    error. Persona voice, stance, and fallback are authored content with provenance.
11. The provider request contains the course's `active_chapters` only when the
    request purpose is coach/RAG; persona turns do not invent textbook citations.
    A1's Qdrant filter and A3's causal trace consumption are tested in their own
    later packet, not smuggled into this first slice.

Run the focused AI tests, the casepack/registry tests, the existing rationale and
consequence tests, the authorization/isolation tests, and the full repository gate.
The prior M4 baseline is `make check`: 699 passed with 19 warnings. Any failure in
the existing score, round, fixture, or isolation gates is a return condition for
the builder, not permission to loosen a test.

## Dependencies and sequencing

1. **Content decision before A2 runtime:** author the Riverside persona roster and
   resolve `from_persona` mappings. The current generic stakeholder rows and event
   prose are insufficient.
2. **A4 contract first:** provider chain, timeouts, safe fallback, telemetry, and
   output policy must land before A2, A1, or A3 calls it.
3. **A2 second:** state-grounded persona turns and the 20-response audit. The People
   screen can consume the read-only contract afterward.
4. **A1 third:** chapter-filtered `mis_textbook` retrieval using `Course.active_chapters`;
   coach outputs explain concepts and refuse plan advice. Qdrant availability and
   citation shape require a separate provider/infrastructure check.
5. **A3 fourth:** narrator receives persisted immutable `RoundResult` causal evidence
   and chapter links; it never recomputes or produces a result.
6. **M5 instructor operations dependency:** staff controls and course settings must
   provide the active course, section, instance, team, round, pack digest, and
   `active_chapters` context. AI must not create a parallel scope or authorization
   path.

The M5 AI gate is open until these contracts and tests pass. The existing M4
rationale seam remains accepted and may stay disabled; closing M4 did not authorize
an LLM to score the simulation.
