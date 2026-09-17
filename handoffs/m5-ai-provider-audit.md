# M5 AI provider audit

Date: 2026-09-18  
Baseline audited: `d786bd6779fb2751e6336e75c123c3ae7ad72664`  
Correction re-audited: `c6e4c24dc99e99a860ab203a4d710b6086a5a0a`  
Contract: `handoffs/m5-ai-teaching-support-contract.md`

## Verdict

**A4 PASS after correction commit `c6e4c24`; overall M5 remains FAIL.** The correction closes the previously reported A4 grounding, advisor-policy, and timeout findings. The A2 persona contract/route, scoped grounding adapter, casepack roster/mapping, authorization checks, 20-response grounding audit, and 15-prompt advisor audit remain absent and are residual blockers for the broader M5 gate.

## Correction re-audit: `c6e4c24`

The exact previously failing probes now pass:

- Signed and reformatted values (`-5`, `+5`, and `5.0`) are rejected when the injected display value is exactly `5`.
- A numeric `numeric_value=100` with non-numeric `display_value="one hundred"` does not authorize output `100`.
- All six advisor probes (`What should we buy?`, `I suggest cloud.`, `I would go cloud.`, `The best architecture is cloud.`, `Which architecture wins?`, and `Recommendation: migrate.`) are rejected by the policy guard and degrade through the orchestrator to the authored safe fallback.
- A primary adapter sleeping 80 ms behind a 1 ms timeout falls through to Together in about 1.4 ms; the primary request carries `timeout_ms=1`.

The correction also adds focused regression coverage: `tests/test_ai_provider.py` now passes 22 tests. The A4 status for disabled-by-default behavior, fixed provider order, fallback, malformed-output handling, output bounds, safe metadata, grounding digest propagation, no-network injection, policy refusal, and timeout fallback is **PASS** based on the focused tests and probes below.

## Findings after correction

### Resolved A4 findings

1. **Resolved: signed/reformatted numeric grounding.** `c6e4c24` preserves sign and exact numeric token representation, so `-5`, `+5`, and `5.0` do not match a display value of `5`.

2. **Resolved: numeric metadata cannot authorize a different display value.** `_allowed_numbers()` now derives authorization only from parsed `display_value`; `numeric_value` remains semantic adapter metadata.

3. **Resolved for the six audited probes: advisor policy.** The expanded deterministic patterns reject the six direct recommendation forms and the orchestrator safely returns `status="unavailable"` with the authored fallback. The required full 15-prompt audit and purpose-specific A2 behavior remain residual gaps below.

### Residual blocking A2/content/route findings

4. **Required A2 integration is missing.** The commits add no persona DTO/content shape, state-to-grounding adapter, read-only persona router, response DTO, authorization path, stale/mismatched digest handling, or `main.py` registration. No student/team/instance scope can be enforced by this code, and no test proves AI calls leave sheet/checkpoint/result/revision/lock state unchanged.

5. **Riverside persona roster/mapping is missing.** `Casepack.stakeholders` remains the existing 14 archetype rows and has no `voice`, `stance`, `safe_fallback`, or `allowed_topics`. Event `from_persona` values are `centraline_vendor`, `dana_ruiz`, `lena_hart`, `maya_oduya`, `priya_shah`, `rob_alderman`, `sam_okoro`, and `tom_beckett`; none is a current stakeholder key. The existing casepack validator reports zero findings for these dangling references, so the required named validation is absent.

6. **No 20-response grounding audit or full 15-prompt coach audit exists.** The correction adds eight direct policy probes (including the six requested here), but there is no sampled persona response set, current-state cross-check, or complete adversarial prompt matrix.

### A4 observations

7. **Resolved: timeout enforcement.** `_invoke_with_timeout()` runs an injected synchronous adapter behind a daemon-thread deadline and advances to the next tier after timeout. The adapter’s worker may continue in the background, so cancellation/resource behavior remains an implementation limitation for future live adapters.

8. **PASS: provider chain and disabled default.** Tier order is exactly primary DashScope, fallback Together, local vLLM; missing adapters, exceptions, malformed text, policy rejection, grounding rejection, timeout, and budget rejection degrade to later tiers or an authored fallback. The default tiers are all disabled and the disabled path makes no provider call. Latency/cost observations are bounded to finite non-negative values, and exception details are not returned in product text.

9. **No network client or live provider dependency was added.** The AI package contains no `httpx`, `requests`, `urllib`, `aiohttp`, socket, or provider client import. Provider adapters are injected. This part passes the no-network test requirement.

10. **Simulation state safety is structural only.** The commits change only `backend/app/ai/*` and provider tests for this slice; they import no simulation service/model and do not write simulation state. This is consistent with read-only behavior, but the locked-round byte-for-byte and independent advance acceptance test is not present.

## Baseline commands and results (`d786bd6`, historical)

From `/home/ubuntu/projects/mis-sim/backend`:

```text
SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=. python3 -m pytest -q tests/test_ai_provider.py
12 passed in 0.05s

SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=. python3 -m pytest -q tests/test_simulation_rationale.py tests/test_simulation_consequences.py
18 passed in 62.13s

SECRET_KEY=mis-sim-test-only-secret PYTHONPATH=. python3 -m pytest -q tests/test_instance_isolation.py
1 passed in 1.08s
```

From the repository root, the baseline direct Python probe exercised the grounding and policy bypasses above. It printed:

```text
negative sign ACCEPT -5
numeric hidden display ACCEPT 100
policy 'What should we buy?' None
policy 'I suggest cloud.' None
policy 'The best architecture is cloud.' None
policy 'Which architecture wins?' None
policy 'Recommendation: migrate.' None
policy 'I would go cloud.' None
```

The baseline timeout probe used a fake provider sleeping 30 ms with a 1 ms primary timeout and printed `generated dashscope 30.091...` latency. The no-network scan was:

```text
rg -n "httpx|requests|urllib|aiohttp|socket|open\\(" backend/app/ai backend/app/config.py || true
```

It returned no matches. The Riverside mapping probe loaded the pack and printed eight dangling `from_persona` keys; `validate_pack_dir()` reported `total findings/errors=0 0`.

The full `make check` gate was not run in this focused subaudit; the missing AI integration and the blocking guard findings already make the M5 AI gate fail.

## Correction commands and results (`c6e4c24`)

Correction-specific probes, run from the repository root with `PYTHONPATH=backend`, were:

```text
PYTHONPATH=backend python3 - <<'PY'
from app.ai.contracts import GroundingBlockV1, GroundingFactV1
from app.ai.grounding import validate_grounded_text, GroundingViolation
fact = GroundingFactV1(key='exposure', display_value='5', numeric_value=5, source_path='/state/exposure', round=2)
grounding = GroundingBlockV1(version=1, instance_id=3, team_id=7, round=2, state_digest='a' * 64, facts=[fact])
for text in ('Exposure is 5.', 'Exposure is -5.', 'Exposure is +5.', 'Exposure is 5.0.'):
    try:
        validate_grounded_text(text, grounding)
        outcome = 'ACCEPT'
    except GroundingViolation as exc:
        outcome = f'REJECT {exc}'
    print('signed/display probe', repr(text), outcome)
words = GroundingFactV1(key='amount', display_value='one hundred', numeric_value=100, source_path='/state/amount', round=2)
words_grounding = grounding.model_copy(update={'facts': (words,)})
try:
    validate_grounded_text('The amount is 100.', words_grounding)
    outcome = 'ACCEPT'
except GroundingViolation as exc:
    outcome = f'REJECT {exc}'
print('display-only probe', outcome)
PY
signed/display probe 'Exposure is 5.' ACCEPT
signed/display probe 'Exposure is -5.' REJECT ungrounded_numeric_claim
signed/display probe 'Exposure is +5.' REJECT ungrounded_numeric_claim
signed/display probe 'Exposure is 5.0.' REJECT ungrounded_numeric_claim
display-only probe REJECT ungrounded_numeric_claim

PYTHONPATH=backend python3 - <<'PY'
from app.ai import ProviderOrchestrator, ProviderRequestV1, ProviderTier
class Fake:
    def __init__(self, text): self.text = text
    def generate(self, request): return {'text': self.text}
probes = ['What should we buy?', 'I suggest cloud.', 'I would go cloud.', 'The best architecture is cloud.', 'Which architecture wins?', 'Recommendation: migrate.']
request = lambda: ProviderRequestV1(purpose='coach', system_prompt='Explain concepts.', user_prompt='Adversarial prompt', timeout_ms=100, max_output_tokens=100)
for probe in probes:
    orchestrator = ProviderOrchestrator(providers={'dashscope': Fake(probe)}, tiers=(ProviderTier(name='primary', provider='dashscope', enabled=True, timeout_ms=100), ProviderTier(name='fallback', provider='together', enabled=False, timeout_ms=100), ProviderTier(name='local', provider='vllm', enabled=False, timeout_ms=100)))
    response = orchestrator.generate(request(), safe_fallback='Authored safe fallback.')
    print(repr(probe), '->', response.status, response.reason, repr(response.text))
PY
'What should we buy?' -> unavailable all_providers_unavailable 'Authored safe fallback.'
'I suggest cloud.' -> unavailable all_providers_unavailable 'Authored safe fallback.'
'I would go cloud.' -> unavailable all_providers_unavailable 'Authored safe fallback.'
'The best architecture is cloud.' -> unavailable all_providers_unavailable 'Authored safe fallback.'
'Which architecture wins?' -> unavailable all_providers_unavailable 'Authored safe fallback.'
'Recommendation: migrate.' -> unavailable all_providers_unavailable 'Authored safe fallback.'

PYTHONPATH=backend python3 - <<'PY'
import time
from dataclasses import dataclass
from app.ai import ProviderOrchestrator, ProviderRequestV1, ProviderTier
@dataclass
class Slow:
    delay: float
    calls: list
    def generate(self, request):
        self.calls.append(request); time.sleep(self.delay); return {'text': 'slow tier response'}
@dataclass
class Fast:
    calls: list
    def generate(self, request):
        self.calls.append(request); return {'text': 'The fallback explains the authored context.'}
slow, fast = Slow(.08, []), Fast([])
request = ProviderRequestV1(purpose='persona', system_prompt='Explain context.', user_prompt='Current context?', timeout_ms=100, max_output_tokens=100)
started = time.perf_counter()
response = ProviderOrchestrator(providers={'dashscope': slow, 'together': fast}, tiers=(ProviderTier(name='primary', provider='dashscope', model='qwen_max', enabled=True, timeout_ms=1), ProviderTier(name='fallback', provider='together', model='qwen_72b', enabled=True, timeout_ms=100), ProviderTier(name='local', provider='vllm', enabled=False, timeout_ms=100))).generate(request)
elapsed = time.perf_counter() - started
print('timeout probe', response.status, response.provider, response.tier, 'elapsed_s=', round(elapsed, 4), 'primary_timeout=', slow.calls[0].timeout_ms, 'fallback_calls=', len(fast.calls))
PY
timeout probe generated together fallback elapsed_s=0.0014 primary_timeout=1 fallback_calls=1
```
