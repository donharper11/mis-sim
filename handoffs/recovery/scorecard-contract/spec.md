# Recovery: scorecard units and financial status

**Authored under:** `SPEC_PROTOCOL.md` v1.3. **Date:** 2026-09-14.
**Author:** `scorecard_author`. **Tier:** Heavy. **Revision:** v1, reviewed contract.
**Authoring base:** `eb06d6d46dce62a9019611379870ad61d56d12c7`.
**Authority:** supervising integration agent. **Status:** R1–R4 accepted and independent
spec review passed on `0716eb9`; see [review.md](review.md) for the ruling and evidence.
This is a reviewed authoring deliverable, not a build dispatch. The supervisor still
assigns an exact implementation base and allowed files after rechecking prerequisites.
The decision table below retains the author's proposal wording; `review.md` records its
acceptance. No scorecard implementation or LIVE contract change is claimed by this spec.

## 0. Spec basis

Read directly on the authoring base, 2026-09-14:

- `GOVERNANCE.md`, `SPEC_PROTOCOL.md`, `QUALITY_PROTOCOL.md`, `CONTRACTS.md`,
  `BATTLECARD.md`, `design/08-implementation-north-star.md` in full.
- `design/02-traceability-matrix.md`, `design/03-scoring-frame-options.md`,
  `handoffs/1.4-scoring-engine/spec.md`, `handoffs/1.6-round-runner/spec.md` in full;
  `handoffs/1.4-scoring-engine/closeout-spec.md` §§0–5.1;
  `handoffs/1.1-casepack-schema/spec.md` §5.6;
  `handoffs/1.5-event-signal-engine/spec.md` §5.2;
  `docs/casepack-schema.md` Shared Rules and events table/preconditions introduction.
- `backend/app/engine/rollup.py` and `score.py` in full;
  `backend/app/round/runner.py` `RoundRunner.advance`, `_rolled_scorecard`,
  `_write_result`, `_already_fired`, and their persistence helpers;
  `backend/app/round/models.py` `RoundResult`; `backend/app/round/db.py` in full.
- `backend/app/casepack/models.py` `StrictModel`, `Scorecard`, `InitialState`,
  `EventOutcome`, `Event`; `loader.py` in full; `validate.py` schema-version constant,
  load-error dispatch and `check_closed_vocab_load`; `checks.py` vocabulary derivation.
- `backend/packs/riverside_grocery/events.yaml` in full; `pack.yaml` metadata and
  initial scorecard; every pack/fixture event delta was additionally parsed in the
  compatibility probe below. This does not claim every fixture was read in full.
- `backend/app/calibrate/harness.py`, `report.py`,
  `backend/tests/check_calibration_harness.py`, `test_engine_scoring.py`,
  `check_engine_purity.py`, `check_round_invariants.py`, `Makefile` in full;
  `test_round_runner.py` setup and tests through the event-once test;
  `backend/seeds/archetype_base.py` estate helpers and read-back contract;
  `findings/1.7-calibration-pass-2026-08-22.md` reproduced curves/digest;
  `handoffs/recovery/calibration-report/spec.md` in full.

**Extraction sufficiency:** covered all load-bearing surfaces for this seam. No external
service or production database claim is made. New runtime PostgreSQL evidence is a
dispatch dependency, PF6, not an assumed running service. No summary is used as source.

### Verified facts, not design rulings

| ID | Source-supported conclusion |
|---|---|
| V1 | `[V]` `rollup.py:79–90` computes Financial from strategic alignment and portfolio discipline, emits `financial_partial=True`, rounds all four base values to six decimals, and emits `inputs.perspective_scale = "0..1 computed rollup; multiply by 100 for a headline"`. The computations and emitted record, not the opening comment alone, support the scale and partial-status claims. |
| V2 | `[V]` `score.py:90–101` preserves the flag in `TeamScore.record().balanced_scorecard`; `runner.py:376–388` builds a four-number map, adds raw event integers, and omits the flag. `runner.py:349–363` persists that map under `scorecard`. |
| V3 | `[V]` `models.py:388–405` declares `EventOutcome.scorecard: dict[SnakeKey, int]`, default `{}`, and requires `Event.outcomes`. It has no dimension vocabulary or unit. Runtime probes show `True → 1`, `"-12" → -12`, `-12.0 → -12`, unknown `financail` accepted; fractional `0.1`, NaN and infinity rejected by Pydantic. |
| V4 | `[V]` `events.yaml:72–74,159–161` authors Financial `-12` and `-15`. The temporary-SQLite harness reproduces Balanced R1 Financial `-26.033068`, with a captured engine base `0.966932`. These magnitudes motivate points; they do **not** prove the originally intended unit. |
| V5 | `[V]` `runner.py:311–326` records only fired events, preserving their authored outcomes; `runner.py:178–186` reads previous event keys for fire-once behavior. `models.py:294–300` stores results as a JSON payload with `(instance_id, team_id, round)` primary key. `_write_result` refuses an existing row; it contains no update path. Existing unlock deletes a result; this packet does not invoke or change it. |
| V6 | `[V]` `calibrate/report.py:99–106` explicitly indexes four dimensions. `harness.py:54–78` hashes the numeric scorecard, capability terms/realised, and firm score. The digest reproduced here is `e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129`, also recorded in the August 22 audit. `test_round_runner.py:148–177` currently enshrines raw addition; it requires a deliberate semantic update. |
| V7 | `[V]` `models.py:63–67,113–118` defines a **different** `InitialState.scorecard`: authored integers 0–100. The scorer/runner do not read that field as their base. Source search finds its reporter in `app/casepack/seed.py`; no frontend scorecard consumer exists at this base. It is preserved. |
| V8 | `[V]` the loader converts model failures to `CasepackLoadError`; existing `check_closed_vocab_load` routes `literal_error`/`enum` to E18 using the model's expected vocabulary. Other numeric model failures can still become E00, the already-owned north-star OS-D1 limitation. `SUPPORTED_SCHEMA_VERSION` is 1. |

The living `CONTRACTS.md` has no scorecard-unit entry. Its applicable existing rule is
`instance_id`: **“every query that reads or writes game state filters on it.”** Its
`LedgerSignal` entry preserves the scoring pin through the projection seam. This packet
adds a scorecard contract; it does not infer one from an unrelated field.

## 1. Pre-flight verification register

Run before implementation against the exact dispatch base. Paste every result into the
NEW `handoffs/recovery/scorecard-contract/dod.md`. Commands below start at repository root
unless they explicitly change directory. An unexpected FAIL is a STOP to the authority;
the expected red acceptance probe on the old implementation is not an unexpected FAIL.

| ID | Claim / dependency | Executable check and expected outcome | Falsification |
|---|---|---|---|
| PF1 | V1–V3, V5: actual producer and persistence boundary | Run source probe A below; inspect the cited complete functions. All assertions pass on the authoring base. | A mutates each asserted source excerpt in memory; each assertion fails. |
| PF2 | V4, V6: reproduce old result and capture before evidence | Run B below with a fresh `/tmp` output path. Expect the historical digest and four R1 values printed below. Save its JSON through audit. | B alters Financial and then the digest input in independent copies; both assertions fail. |
| PF3 | V3, V8: the proposed shape preserves shipped event content | Run C below. Expect 251 rows compatible at this base; known invalid key/bool/string/float/NaN/infinity rejected by the proposed type adapter. Read existing E18 dispatch. | C deliberately feeds each rejected shape, checks a real `ValidationError`, and verifies its type. |
| PF4 | V6–V7: out-of-scope dependencies and first-wave changes | Run the consumer search below. Inspect every consumer. Existing core scorer, pack-seed display, calibration report and digest can consume the unchanged four-number map; the one raw-addition test is in scope. New consumers/strict payload readers are a STOP. Run A's frontend absence assertion. | A plants a frontend consumer and observes failure. Candidate tests inject extra metadata and verify the actual integrated report still reads the four numeric fields. |
| PF5 | Protected arithmetic and fixtures | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py tests/test_round_pin.py -q`. Preserve pack/seed/engine and pin-file bytes using the diff check in §6. | The candidate suite must reject one planted capability-term change and one planted pack/seed edit; never edit the historical expectations. |
| PF6 | `[A]` first-wave runtime/report work has passed its own audit and supplies a disposable PostgreSQL command | Supervisor names the audited runtime/report SHAs, exact disposable verification command, and reachable interpreter in dispatch; builder runs that command and records backend/dependency versions and migration/read-back evidence. No command is invented here because this authoring base predates those deliverables. This row blocks build dispatch, not this specification. | An unavailable interpreter/database or incomplete runtime command is a failed row, never a skip. No application DB default may be used. |

No search returning zero merely because a directory does not exist counts as dependency
evidence. The source probe and PF4 are intentionally sensitive to a changed implementation;
the approved report-only first-wave changes can add consumers that explicitly index the
same four dimensions, which the supervisor must confirm at dispatch.

PF4 consumer search (repository root):
`rg -n 'scorecard|balanced_scorecard|financial_partial' backend/app frontend/src backend/tests --glob '*.py' --glob '*.jsx'`.

### Probe A — source and consumer assertions, with planted defects

```bash
python3 - <<'PY'
from pathlib import Path
root = Path.cwd()
paths = {
    'rollup': 'backend/app/engine/rollup.py',
    'record': 'backend/app/engine/score.py',
    'runner': 'backend/app/round/runner.py',
    'model': 'backend/app/casepack/models.py',
    'storage': 'backend/app/round/models.py',
}
src = {k: (root / p).read_text() for k, p in paths.items()}
needles = {
    'rollup': 'financial_partial=True,',
    'record': '"financial_partial": self.balanced_scorecard.financial_partial,',
    'runner': 'sc[dim] = sc[dim] + delta',
    'model': 'scorecard: dict[SnakeKey, int] = Field(default_factory=dict)',
    'storage': 'payload: Mapped[dict] = mapped_column(JSON, nullable=False)',
}
for k, needle in needles.items():
    def check(text):
        assert needle in text, k
    check(src[k])
    try:
        check(src[k].replace(needle, '# planted missing contract'))
    except AssertionError:
        pass
    else:
        raise AssertionError('undetected source plant: ' + k)
front = root / 'frontend/src'
assert front.is_dir()
content = '\n'.join(p.read_text() for p in front.rglob('*')
                    if p.is_file() and p.suffix in {'.js', '.jsx', '.ts', '.tsx'})
def no_front_consumer(text):
    assert not any(k in text for k in ('scorecard', 'financial_partial'))
no_front_consumer(content)
try:
    no_front_consumer(content + '\nconst x = payload.scorecard;')
except AssertionError:
    pass
else:
    raise AssertionError('undetected consumer plant')
print('PF1/PF4 source assertions PASS; 6 source/consumer plants detected')
PY
```

### Probe B — actual old results and retained before artifact

```bash
cd backend
PYTHONPATH=. python3 - /tmp/scorecard-contract-before.json <<'PY'
import copy, json, sys, tempfile
from pathlib import Path
from unittest.mock import patch
from app.casepack.loader import load_casepack
from app.calibrate.harness import run_calibration, score_digest
from app.round.runner import RoundRunner
old = RoundRunner._rolled_scorecard
captured = []
def spy(self, score, events):
    b = score.balanced_scorecard
    captured.append((self.instance_id, {d: getattr(b, d) for d in
        ('financial', 'customer', 'internal_process', 'learning_growth')}, b.financial_partial))
    return old(self, score, events)
with tempfile.TemporaryDirectory() as td, patch.object(RoundRunner, '_rolled_scorecard', spy):
    archetypes, results = run_calibration(load_casepack('packs/riverside_grocery'),
                                         db_url=f'sqlite:///{td}/before.db')
expected = {'financial': -26.033068, 'customer': 0.6083,
            'internal_process': -17.506477, 'learning_growth': -6.560728}
def check_r1(r):
    assert r['balanced'][0]['scorecard'] == expected
check_r1(results)
def check_digest(r):
    assert score_digest(r) == 'e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129'
check_digest(results)
for check in (check_r1, check_digest):
    planted = copy.deepcopy(results)
    planted['balanced'][0]['scorecard']['financial'] = 0.966932
    try:
        check(planted)
    except AssertionError:
        pass
    else:
        raise AssertionError('baseline check did not detect plant')
balanced_id = next(a.instance_id for a in archetypes if a.key == 'balanced')
base = next(row for row in captured if row[0] == balanced_id)
assert base[1] == {'financial': 0.966932, 'customer': 0.6083,
                   'internal_process': 0.493523, 'learning_growth': 0.439272}
assert base[2] is True
out = Path(sys.argv[1])
assert not out.exists(), 'choose a fresh before-artifact path; never overwrite history'
out.write_text(json.dumps(results, sort_keys=True, allow_nan=False))
print('PF2 PASS; 2 baseline plants detected', score_digest(results))
print('Balanced R1 base/partial:', base)
print('Balanced R1 old scorecard:', results['balanced'][0]['scorecard'])
print('Before artifact:', out)
PY
```

### Probe C — proposed input compatibility, not an implemented model claim

```bash
cd backend
PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from typing import Literal
import math, yaml
from pydantic import TypeAdapter, StrictInt, ValidationError
t = TypeAdapter(dict[Literal['financial', 'customer', 'internal_process', 'learning_growth'], StrictInt])
paths = list(Path('packs').glob('*/events.yaml')) + list(Path('tests/fixtures/packs').glob('*/events.yaml'))
assert paths
count = 0
for path in paths:
    for event in yaml.safe_load(path.read_text()) or []:
        values = t.validate_python((event.get('outcomes') or {}).get('scorecard', {}))
        assert all(math.isfinite(v / 100) for v in values.values()), path
        count += 1
assert count == 251, count
for bad, kind in [({'financail': -12}, 'literal_error'),
                  *[({'financial': v}, 'int_type') for v in
                    (True, '-12', -12.0, 0.1, float('nan'), float('inf'), None)]]:
    try:
        t.validate_python(bad)
    except ValidationError as exc:
        assert exc.errors()[0]['type'] == kind
    else:
        raise AssertionError(('invalid value accepted', bad))
print('PF3 PASS: 251 existing event rows compatible; 8 invalid input plants rejected')
PY
```

Author evidence: A, B and C were executed in this isolated worktree. The observed base
values and historical digest are reproduced above. A detected six source/consumer plants;
B detected two corrupted-result plants; C rejected eight invalid inputs. PF5 completed
with **14 passed**. The acceptance probe in §5 was run and failed with
`AssertionError: expected scorecard + metadata`: the base helper returns four raw-added
numbers, not the proposed tuple.
These source/data plants establish check sensitivity; the builder additionally plants
defects in the **actual candidate implementation**, as required in §5. They are not a claim
that the future implementation has already passed audit.

## 2. Scope and decisions

**Already settled by source or assignment:** preserve the multiplicative Tech/Org/Mgmt
model, per-capability results, `firm_score`, scoring pins, event selection/timing, pack
numbers, all immutable historical results and the historical digest. Correct only the
event-to-scorecard units seam and persisted evidence/status.

**Proposed new rulings — authority must accept or return them together:**

| Ruling | Proposed decision | Criteria and reporting obligation |
|---|---|---|
| R1 | An event delta is an integer number of **scorecard points on a 100-point headline**. A persisted runtime perspective is a fraction on **0–1**. Divide point totals by 100 once. | Align existing engine units and authored magnitudes without changing content. Authority records acceptance; if original intent differs, return to author, do not change pack numbers. |
| R2 | Sum all this round's fired-event point deltas per perspective, then add to that perspective's engine base, clamp once to `[0,1]`, and round to six decimal places. Preserve unclipped inputs in evidence. | Bound displayed outcomes while keeping every penalty/credit explainable. Saturation is visible, and event order cannot change the score. This is a design ruling, not a claim the old spec already required bounds. |
| R3 | Add `scorecard_meta` version 1 beside the existing four-number `scorecard`. Carry the engine's partial-financial status plus base and point totals. Leave unversioned historical payloads untouched. | Distinguish corrected semantics without breaking consumers that explicitly index existing dimensions. No silent retroactive reinterpretation. |
| R4 | Tighten event dimensions to a closed vocabulary and authored values to strict integers; reject invalid/nonfinite runtime data rather than skip/coerce/clamp it. Keep casepack schema_version 1 and unchanged valid pack bytes; document the deliberately narrower accepted input set. | All 251 existing event rows are compatible. This is an explicit compatibility ruling, not “no schema change.” Accept existing E00 numeric-diagnostic residue with owner OS-D1/M2; new unknown-key failures use existing E18. If that residue is unacceptable, return to author for a separately bounded validator scope amendment before dispatch. |

No unresolved implementation choice may be silently delegated. Once R1–R4 and PF6 are
recorded, the rules below are FROZEN for this implementation. A newly discovered consumer,
different baseline, required migration or stricter diagnostics demand returns to authority.
No product balance verdict is requested or implied.

### Project-specific statements and exclusions

- **Scoring touched:** `design/02` §E Balanced Scorecard only. It reads the existing
  §A–D rollup and event outcomes; it introduces no Tech/Org/Mgmt subfactor or money model.
- **Keys:** `events[].key`, `events[].outcomes.scorecard`; `outcomes.revenue_loss` is
  preserved evidence, never converted into scorecard points or used as another penalty.
  `InitialState.scorecard` remains authored 0–100 context, not the runtime base.
- **Scoping:** no new tables, columns, queries, migrations or scope filters. Existing
  result keys and instance/team predicates remain intact; run the existing isolation
  canary plus the new persistence tests. No claim of completed second-vertical coverage.
- **No UI or student copy:** business effect is “a 12-point penalty lowers 80 to 68.”
  Evidence keys remain internal. No browser, auth, screenshot or responsive-layout
  acceptance applies; this is a headless numerical contract. Report formatting remains
  owned by the first-wave report packet.
- **Excluded:** full Financial scoring or revenue/cash mutation, decision-to-estate
  evolution, training/adoption, calibration tuning, per-strategy balance, event response
  mutations, atomic advance/rollback/retry/unlock redesign, scheduler/auth/UI/API routes,
  infra startup by this author, production/shared DB writes and historical backfills.
  PF4 and the before/after comparison prove these exclusions, rather than merely asserting them.

## 3. Frozen proposed behavior

### 3.1 Units, aggregation and precision

The four keys are exactly `financial`, `customer`, `internal_process`, `learning_growth`.
For each key `d`, with step-12 engine base `b[d]` and **current fired events only**:

```text
p[d] = integer sum of events[i].outcomes.scorecard.get(d, 0)
u[d] = b[d] + p[d] / 100
scorecard[d] = round(min(1.0, max(0.0, u[d])), 6)
```

Use the existing six-decimal engine base as supplied; do not recompute an unrounded base.
Sum integers before division; do not round per event, reweight by strategy/capability,
multiply penalties by the base, compound percentages, or clip between events. Validate
the base, each delta conversion and the aggregate conversion for finite representation
**before** bounds; NaN/infinity/overflow are errors, not endpoint scores. There is no new
pedagogical magnitude limit on finite integer points. A finite `-150` is valid and can
saturate the score; an integer too large for finite division by 100 raises `ValueError`.
Represent zero as `0.0`, including a result that rounds to negative zero.

| Business case | Base | Fired point deltas | Raw fraction | Persisted score |
|---|---:|---|---:|---:|
| 80-point result, 12-point penalty | 0.8 | -12 | 0.68 | 0.68 |
| Two Financial incidents, Balanced R1 | 0.966932 | -12, -15 | 0.696932 | 0.696932 |
| All Internal Process incidents, Balanced R1 | 0.493523 | -8, -4, -6 | 0.313523 | 0.313523 |
| Staff-account incident, Balanced R1 | 0.439272 | -7 | 0.369272 | 0.369272 |
| No Customer incident, Balanced R1 | 0.6083 | none | 0.6083 | 0.6083 |
| Severe combined losses | 0.1 | -12, -8 | -0.1 | 0.0 |
| Credit beyond maximum | 0.95 | +10 | 1.05 | 1.0 |
| Credit/penalty in either order | 0.95 | +10, -10 | 0.95 | 0.95 |
| Precision boundary | 0.876543 | -1 | 0.866543 | 0.866543 |

The last mixed-sign example falsifies sequential clipping, which would incorrectly yield
0.9 in one order. Clipping does not erase the authored loss from `events` or its total in
metadata; a negligent team can reach zero while its unbounded penalty remains inspectable.

### 3.2 Payload and compatibility

Preserve `payload.scorecard` as exactly the four numeric fields. Add this **NEW** root
field and **NEW** nested identifiers, shown using the verified Balanced R1 example:

```json
"scorecard_meta": {
  "version": 1,
  "score_unit": "fraction",
  "event_delta_unit": "scorecard_points",
  "financial_partial": true,
  "base": {
    "financial": 0.966932, "customer": 0.6083,
    "internal_process": 0.493523, "learning_growth": 0.439272
  },
  "event_delta_points": {
    "financial": -27, "customer": 0,
    "internal_process": -18, "learning_growth": -7
  }
}
```

`version` is the **scorecard contract version**, not casepack schema, pack version,
database migration or whole-result API version. Version 1 fixes both unit strings above.
`base` has all four finite 0–1 numbers copied from the base; `event_delta_points` has all
four integer totals, including zero. `financial_partial` is an actual boolean copied from
`final_score.balanced_scorecard.financial_partial`, including `False` if a future separately
authorized producer emits it. Do not infer it from financial-ledger presence or default a
missing value to `False`. In today's real scorer it remains `True` in every round.

The authoritative result remains `scorecard`; metadata is its immutable audit evidence,
not an independently editable second score. Its reconciliation rule is the §3.1 equation,
verified before persistence and after JSON read-back. Unit strings and version are
constants; base/flag are copied; totals are derived from `events` exactly once. No extra
copies of raw/unbounded/final scores or per-event normalized deltas are needed.

`events[].outcomes.scorecard` continues to carry authored point integers, not normalized
fractions. `financials`, `tco_variance`, capability decompositions and `firm_score` retain
their current shapes and values. `TeamScore.record().balanced_scorecard` is unchanged.

**Unversioned historical payload:** absence of `scorecard_meta` means historical/unknown
scorecard semantics and unknown persisted partial-status, not version 1, not complete
Financial scoring. Read/return its bytes as stored; never auto-rescale it, attach invented
metadata, or infer its version from whether its numbers happen to fall in 0–1. New writes
use version 1. No compatibility writer, legacy recomputation mode, migration or backfill
is introduced. A future reader that interprets metadata must dispatch on `version`; an
unknown version is unsupported, never guessed. No such new reader is part of this packet.

The full calibration score digest **will change**, because it includes corrected BSC
numbers. Record the new digest beside the historical digest with the formula/version
explanation; preserve the old audit file and pins. Demonstrate exact equality of all
other payload fields over all 24 results. Never overwrite a digest expectation to make a
green gate, omit scorecard from `score_digest`, or retune inputs to recover the old hash.

### 3.3 Input validity and null paths

**NEW** type alias `ScorecardPerspective` belongs in `app/casepack/models.py`:
`Literal["financial", "customer", "internal_process", "learning_growth"]`.
Change `EventOutcome.scorecard` to `dict[ScorecardPerspective, StrictInt]`, retaining its
default empty map. A field validator additionally rejects integer values whose division
by 100 is nonfinite or raises overflow. Any reusable dimension list derives from this
alias with `typing.get_args`; do not introduce another independently maintained vocabulary.

| Input | Required behavior and boundary |
|---|---|
| Event `outcomes` omitted / null | Existing `Event` required-object model failure; do not loosen it. |
| `outcomes: {}` or omitted `scorecard` | Valid; map defaults to `{}`, contributes zero. |
| `scorecard: {}` / no fired events | Valid; all totals zero; base returned to six decimals, metadata and partial flag still present. |
| Explicit null/non-map `scorecard` | Reject at model/loader; reject at runtime if validation was bypassed. Never interpret explicit null as no effect. |
| Missing perspective in a delta map | Zero for that perspective. |
| Unknown perspective | Model `literal_error`; loader refuses; existing validator reports E18. Runtime also refuses. No skip or alias. |
| Bool, string, float (even `-12.0`), fraction, null, NaN, infinity as authored delta | Model `ValidationError`, wrapped as `CasepackLoadError` by loader. Strict integer contract; no coercion. Existing numeric E00 fallback is the R4 accepted residue. |
| Huge integer or aggregate causing nonfinite normalized value / overflow | Model catches individual values; rollup catches aggregate. Runtime raises `ValueError` identifying the perspective. No saturation of invalid arithmetic. |
| Missing/non-numeric/bool/nonfinite/outside-0–1 engine base | Rollup raises `ValueError` identifying the perspective before returning output. An invalid base is not repaired by clipping. |
| Missing/non-bool engine partial flag | Rollup raises `ValueError`; no fabricated flag. |
| `event_records` absent/null/non-list, a non-map record, missing/empty/non-string `key`, or duplicate event key | Rollup raises `ValueError`. Duplicate events indicate invalid input; do not silently deduplicate or double-apply. |
| Missing/null/non-map `outcomes` in a runtime event record | Reject; real runner records always carry `outcomes`. Empty object is valid. |

**Validation placement:** normal authoring validation happens in `EventOutcome`, hence
`load_casepack` and the existing validator entry point. Add a NEW runner method
`_validate_scorecard_outcomes()` that revalidates every pack event's outcome using the
same model at the start of `advance`, after the lock check and before `_validate_sheet`,
arrivals or any other write. **Reconstruct a raw mapping before model validation:**
after rejecting a value that is neither an `EventOutcome` nor a mapping with `ValueError`,
use `EventOutcome.model_validate(dict(event.outcomes))`. Never pass the existing model
instance directly to `model_validate`: same-model validation can return it unchanged,
retaining invalid values introduced by mutable-map edits, `model_copy(update=...)` or
`model_construct(...)`. The raw-mapping reconstruction forces field validation in all
three cases, including a bad event that would not fire. Do not mutate/rewrite the pack
while validating. This requirement closes review finding **SC-SR-001**; the author
reproduced all three bool-corruption bypasses with the proposed strict field type and
observed raw-mapping validation reject each with `int_type`.
The rollup revalidates record shape/deltas and validates base/flag/aggregate before
`_persist_ledger` and `_write_result` can execute. Runtime failures are `ValueError`
(Pydantic's `ValidationError` qualifies); error detail identifies the event/dimension
where known. No new public error code or UI error string is introduced.

The preflight validation of malformed pack outcomes makes **no database changes**.
An invalid derived base or aggregate discovered later prevents result/ledger publication
and round-pointer advance, but this packet does **not** promise rollback of earlier
arrivals/debt writes. The caller's existing transaction owns rollback. Tests can roll back
their disposable session; redesigning that transaction boundary belongs to M1.

## 4. One compliant route and exact build scope

**Compliant route:** keep the pure scorer byte-identical; close the event-delta vocabulary
and integer type in `EventOutcome`; reconstruct each outcome as a raw mapping and call
`EventOutcome.model_validate(dict(event.outcomes))` before round mutations (never validate
the existing model instance directly);
change the runner's private `_rolled_scorecard(final_score, event_records)` to return
`(scorecard, scorecard_meta)` from one aggregate calculation; unpack it at step 14 and
persist both fields in the existing JSON row. Validate before returning the pair. Preserve
the raw event evidence, all other payload fields, event selection and existing query keys.
This simultaneously satisfies units, bounds, status, evidence, immutability and purity.

The private helper's return shape is explicitly **VERSIONED by this change** from a map
to the two-map tuple. PF4 confirms its only production caller is `advance`; its existing
test is named below. It is not an externally frozen API. Avoid a second helper call that
could recompute totals differently or apply effects twice.

**Builder may change only:**

| File | Allowed change |
|---|---|
| `backend/app/casepack/models.py` | NEW `ScorecardPerspective`, `StrictInt` import, only `EventOutcome.scorecard` annotation and its finite-point validator. No `InitialState.Scorecard` or other model changes. |
| `backend/app/round/runner.py` | NEW `_validate_scorecard_outcomes` and its early call; `_rolled_scorecard` validation/aggregate/tuple result; step-14 unpacking and NEW `scorecard_meta` payload key. No other state-machine, scoring-call, query or write-order changes. |
| `backend/tests/test_round_runner.py` | Update **only** `test_i5_event_outcome_scored_exactly_once` for point units and the new private return shape. Duplicate input now raises; assert the persisted once-applied result against independent point totals and keep the event-fired assertion. Do not delete/weaken the other tests. |
| `backend/tests/test_scorecard_contract.py` — **NEW** | Focused numerical, validation, persistence, compatibility and regression tests in §5, reachable through existing pytest/`make check`. |
| `handoffs/recovery/scorecard-contract/dod.md` — **NEW** | Preflight, accepted rulings, before/after numbers, commands, mutation failures, candidate SHA and limitations. |

No builder edit to engine files, packs, seeds, pin fixtures, historical findings/reports,
calibration harness/report, dependencies, migrations, infrastructure or shared documents.
No push, deployment, main merge, `git add -A`, new track or subagent. The supervisor owns
the shared living deltas in §7 and incorporates them into the reviewed integration change;
they are required for landing, not optional follow-up letters. If a supervisor wants the
builder to apply those exact deltas, issue an explicit allowed-file amendment first.

## 5. Acceptance checks and build phases

1. **Before coding:** run/report PF1–PF6, save B's actual results, run the acceptance
   probe below against the base and record the expected failure. Record R1–R4 approvals
   and independent spec-review identity. A runtime/report rebase is inspected, not assumed.
2. **Schema boundary:** implement only the approved event-delta type/finite validation;
   add loader and runtime-bypass tests. Verify invalid/empty/default cases and E18 routing
   using a temporary copy of an existing valid fixture; do not edit a historical fixture.
3. **Runner boundary:** implement aggregation/metadata and early validation. Add the
   numerical tests below and update the single old raw-addition test. Verify the partial
   flag by stored JSON read-back, not only helper output.
4. **Integration proof:** run the 24-result before/after comparison, existing pins and
   canaries, real report on corrected results, `make check`, and the audited disposable
   PostgreSQL command supplied under PF6. Re-run failures after each candidate correction.
5. **Falsification and review:** plant each listed regression in a disposable copy or by
   a targeted monkeypatch of the actual implementation, observe a nonzero named test,
   restore it, run the clean required checks, commit only allowed files and return for
   independent audit. This author is not the build auditor.

| Test group (**NEW** tests unless noted) | Direct acceptance | Required candidate mutation / falsification |
|---|---|---|
| N1: units and normal aggregation | Every row of §3.1, every perspective, independent expected values; `0.8 + (-12 points) = 0.68`; mixed signs in either order give 0.95. | Restore raw addition; divide by 10 or 100 twice; clamp each event. Each relevant assertion fails. |
| N2: bounds and absence | Finite output within `[0,1]`; lower/upper saturation; no events/empty map preserve base; missing dimension contributes zero; endpoint and six-decimal precision cases. | Remove lower/upper clamp or apply a penalty to an absent dimension; targeted test fails. |
| N3: invalid inputs | Parameterize every §3.3 invalid class, including huge single integer and overflowing aggregate; all fail rather than produce a result. Test early validation on an unfired bad event with bool corruption introduced separately by mutable-map edits, `model_copy(update=...)` and `model_construct(...)`. | Pass an existing model directly to `model_validate`, accept a bool, ignore an unknown dimension, return a base despite NaN, or remove early validation; corresponding negative test fails. |
| N4: exactly once / immutable inputs | Duplicate event keys rejected; raw event values and input base untouched; no changes to fired/suppressed event selection; existing re-score-count test still passes. | Duplicate event application or mutate one input value; assertion fails. The old raw-addition test is replaced by the literal 12-point example plus a real persisted event case, not expectations computed by calling the helper again. |
| N5: evidence, status and JSON | Returned and persisted `scorecard` agree; exact four-number shape; metadata version/unit strings, base and totals agree with real step-12 capture/events; real flag remains True over 24 rounds; a synthetic False is copied, missing/non-bool refused. `json.dumps(payload, allow_nan=False)` succeeds for every valid payload. | Omit flag/metadata, force False/True, alter one base/total/unit/version or discard metadata at persistence; named read-back test fails. |
| N6: backward compatibility and scope | Read an inserted unversioned old payload unchanged before/after a new result in another round/instance; no added metadata on the old row. Existing immutable-result refusal/isolation/pin tests pass. Compare all 24 payloads excluding only `scorecard` and NEW `scorecard_meta` to B's before artifact: exact equality, including capability terms, firm score, events and financials. | Change a historical payload, capability term, firm score, event evidence or query scope; relevant test/comparison fails. No unlocking is used to obtain this proof. |
| N7: actual business reproduction | Balanced R1 emits Financial `0.696932`, Customer `0.6083`, Internal Process `0.313523`, Learning & Growth `0.369272`, firm score `0.35825`, and partial Financial status True. Every other round's four scores are finite/bounded and traceable. | Restore original raw-addition helper or omit the metadata write; real seeded integration test fails on the original defect. |
| N8: no hidden baseline rewrite | Git scope/protected-file check (§6); new full digest recorded, old digest/audit retained; `score_digest` still includes scorecard. Report prints corrected stored values using its existing scale. | Edit a protected file/expected historical digest, remove BSC from digest, or introduce a strict four-root-key reader; guard/test fails. |

Tests should be behavioral and use literal business expectations where available. Do not
assert that one call to the implementation equals another call to the same implementation.
For the 24-result comparison, using B's retained independently captured old artifact is
intentional; do not regenerate the “before” artifact with the candidate code.

### Executable small acceptance/falsification probe

Run from `backend` after implementation. It is deliberately independent of any new test
function names, and should fail on the original code. It also checks its own sensitivity
by corrupting compliant returned data after the actual helper call.

```bash
PYTHONPATH=. python3 - <<'PY'
from copy import deepcopy
from types import SimpleNamespace
from app.engine.rollup import BalancedScorecard
from app.round.runner import RoundRunner
runner = RoundRunner.__new__(RoundRunner)
def run(base, points, partial=True):
    bsc = BalancedScorecard(base, base, base, base, financial_partial=partial)
    evs = [{'key': f'event_{i}', 'outcomes': {'scorecard': {'financial': p}}}
           for i, p in enumerate(points)]
    before = deepcopy(evs)
    pair = runner._rolled_scorecard(SimpleNamespace(balanced_scorecard=bsc), evs)
    assert isinstance(pair, tuple) and len(pair) == 2, 'expected scorecard + metadata'
    assert evs == before and bsc.financial == base
    return pair
def check(pair, expected, base, total, partial):
    sc, meta = pair
    assert set(sc) == {'financial', 'customer', 'internal_process', 'learning_growth'}
    assert sc == {'financial': expected, 'customer': base,
                  'internal_process': base, 'learning_growth': base}, sc
    assert meta['version'] == 1 and type(meta['version']) is int
    assert meta['score_unit'] == 'fraction'
    assert meta['event_delta_unit'] == 'scorecard_points'
    assert meta['financial_partial'] is partial
    assert meta['base'] == dict.fromkeys(sc, base)
    assert meta['event_delta_points'] == dict.fromkeys(sc, 0) | {'financial': total}
for base, points, expected in [(0.8, [-12], 0.68), (0.1, [-12, -8], 0.0),
                              (0.95, [10], 1.0), (0.95, [10, -10], 0.95),
                              (0.95, [-10, 10], 0.95), (0.8, [], 0.8)]:
    check(run(base, points), expected, base, sum(points), True)
check(run(0.8, [-12], False), 0.68, 0.8, -12, False)
good = run(0.8, [-12])
for field in ('value', 'flag', 'version', 'total', 'base'):
    bad = deepcopy(good)
    if field == 'value': bad[0]['financial'] = -11.2
    if field == 'flag': bad[1]['financial_partial'] = False
    if field == 'version': bad[1]['version'] = 2
    if field == 'total': bad[1]['event_delta_points']['financial'] = -24
    if field == 'base': bad[1]['base']['financial'] = 0.9
    try:
        check(bad, 0.68, 0.8, -12, True)
    except AssertionError:
        pass
    else:
        raise AssertionError('undetected evidence plant: ' + field)
print('unit/bounds/status smoke PASS; 5 evidence plants detected')
PY
```

## 6. Definition of done and headless playthrough

Fill the table in the builder's NEW DoD, with command output and actual candidate SHA.
No row can be replaced with “all tests pass” when it requests before/after evidence.

| Item | Status | Evidence required |
|---|---|---|
| R1–R4, PF1–PF6 and independent spec review | pending | Ruling record/reviewer; per-row outputs; supplied runtime command |
| N1–N4: units, bounds, nulls, invalids and exactly-once | pending | Named pytest cases, small probe output and real candidate mutation failures |
| N5: persisted metadata/status | pending | JSON read-back in a new session, strict JSON and flag evidence |
| N6–N8: history, unchanged core, seeded business outcomes | pending | B's before artifact, 24-result exact unaffected-field comparison; Balanced R1 table; old/new digest explanation |
| Valid packs and diagnostics | pending | Riverside zero errors/warnings; existing fixture matrix green; temporary invalid pack E18/load-failure evidence with accepted E00 residue explicitly recorded |
| Required regression gate | pending | `make check`; existing scoring/round pins and instance canary; integrated report compatibility |
| Disposable PostgreSQL | pending | PF6 supplied command; migration and six-round result/read-back with metadata |
| Exact file boundary | pending | Allowlist diff check below plus clean worktree after commit |
| Living deltas and register reconciliation | pending, supervisor | §7 applied to living docs at integration; recovery finding linked to reproduced closing tests; OS-D1/full-financial ownership retained |
| Heavy independent build audit | pending | Fresh auditor reruns checks and headless script on candidate; author ≠ auditor |
| Browser/auth/UI/visual rungs | N-A | No browser workflow or surface is introduced; no screenshot claims |

Run this scope check using the **exact dispatch base**, not a moving branch name:

```bash
python3 - BASE_SHA_FROM_DISPATCH <<'PY'
import subprocess, sys
allowed = {
 'backend/app/casepack/models.py', 'backend/app/round/runner.py',
 'backend/tests/test_round_runner.py', 'backend/tests/test_scorecard_contract.py',
 'handoffs/recovery/scorecard-contract/dod.md',
}
changed = set(subprocess.check_output(['git', 'diff', '--name-only', sys.argv[1]], text=True).splitlines())
untracked = set(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True).splitlines())
def check(files):
    assert not files - allowed, files - allowed
check(changed | untracked)
try:
    check(changed | {'backend/packs/riverside_grocery/events.yaml'})
except AssertionError:
    pass
else:
    raise AssertionError('scope check missed protected-file plant')
print('scope PASS; protected-file plant detected')
PY
```

The spec and its independent review should already exist at dispatch base; the builder
does not edit either to manufacture a passing scope check. Supervisor integration has a
separate allowlist for the exact shared document deltas below.

**Headless playthrough** (seeded historical estates; does not claim decision-driven play):

1. Start the four supplied teams on the disposable database via the existing harness.
   **EXPECT:** 24 newly computed round results, four perspectives each, no changed
   strategy declarations. This is computation from the retained seeds.
2. Inspect Balanced's first-round incidents and its Financial result. **EXPECT:** a
   96.6932-point base, losses of 12 and 15 points, result 69.6932 points (`0.696932`
   stored), flagged partial. The money amounts remain separate outcome evidence.
3. Inspect its other three perspectives. **EXPECT:** the §3.1 values, with unchanged
   capability terms and firm realised value `0.35825`.
4. Follow the negligent cases (Do Nothing and All Tech, No Org) through six rounds.
   **EXPECT:** the existing low realised-value/Org lesson remains intact; perspective
   losses use the same units/bounds and retain the raw event evidence. No requirement
   that every perspective ranks the negligent team last is introduced.
5. Open a pre-correction result, then run a new round/result in another scope. **EXPECT:**
   the older payload is byte-for-byte unchanged and still unversioned; the new payload
   declares version 1 and partial status. No historical result is unlocked or recomputed.
6. Introduce an invalid event scorecard value in a disposable in-memory pack, then try
   to advance. **EXPECT:** validation rejects it before mutation; zero new result,
   ledger or pointer changes. For a later injected invalid base, **EXPECT:** no result
   or ledger publication/pointer advance, with caller rollback used for earlier writes.

## 7. Exact living-document deltas — supervisor applies with implementation

These are proposed replacement/addition texts, contingent on R1–R4. They do not change
shared documents in this author's commit. Apply them to the living documents in the
reviewed integration change; retain historical entries and dated findings. Use date of
integration in changelog entries; do not rewrite August evidence as if it used version 1.

### `CONTRACTS.md`

Prepend to the last-updated history: `2026-09-14 — scorecard contract revision 1: explicit
event points, normalized bounded runtime perspectives, persisted partial-financial status
and versioned evidence; previous dated entries retained.` Add the following new entry,
and a changelog line `Scorecard contract v1 added by recovery/scorecard-contract; valid
pack bytes and historical result payloads unchanged.`

> **`EventOutcome.scorecard` / `RoundResult.payload.scorecard` — LIVE, scorecard contract v1**
>
> Event deltas use signed integer **scorecard points on a 100-point headline**, on the
> closed keys `financial`, `customer`, `internal_process`, `learning_growth`. One point
> equals `0.01` in a runtime perspective. Omitted delta map defaults to `{}`; missing
> dimensions contribute zero. Explicit null, unknown keys, bools, strings and floats
> (including integral floats) are rejected. Values and aggregate division by 100 must
> be finitely representable; overflow is invalid, not a clipped endpoint. `revenue_loss`
> remains a separate money field, never an automatic scorecard adjustment.
>
> The runtime `scorecard` contains exactly four finite 0–1 numbers. Per dimension:
> `round(clamp(engine_base + sum(current_fired_event_points)/100, 0, 1), 6)`. Aggregate
> before conversion and clamp once; no strategy reweighting or compounding. Base values
> must already be finite and in 0–1; do not repair invalid bases. Duplicate event records
> are invalid. No event mutates the pure scorer's Tech/Org/Mgmt or firm score through
> this reporting adjustment.
>
> **NEW `payload.scorecard_meta`:** `{version: 1, score_unit: "fraction",
> event_delta_unit: "scorecard_points", financial_partial: bool, base: four-number map,
> event_delta_points: four-integer map}`. Version/unit values are fixed for v1. `base`
> and `financial_partial` copy the engine output; totals derive from current fired-event
> evidence and include zeros. The final map is authoritative; metadata reconciles by
> the equation above and is immutable alongside it. Current Financial scoring remains
> the strategic-alignment/portfolio-discipline proxy, marked partial even when cost
> ledgers are present. Full Financial scoring remains separately owned by M4.
>
> Producers: `casepack.models.EventOutcome` validates authoring;
> `engine.rollup.BalancedScorecard` produces base/status;
> `round.runner` validates, converts once and persists the final map/evidence. Consumers:
> the JSON `RoundResult` row and calibration report/digest; future readers must check
> metadata version before interpreting its semantics. Runtime pack outcomes are checked
> before round writes; derived output is checked before result/ledger publication.
> Unknown model vocabulary uses E18; numeric load-error diagnostic refinement remains
> OS-D1/M2. No new validation code or label vocabulary is introduced.
>
> Compatibility: missing metadata means an unversioned historical result, with unknown
> persisted units/status. Never rescale, infer complete Financial scoring, or backfill
> metadata on read. New results use v1. This version is independent of casepack
> schema_version 1, whose valid integer event maps remain compatible while permissive
> coercions/unknown keys are now rejected. `InitialState.scorecard` is separate authored
> 0–100 context and is unchanged; `TeamScore.record().balanced_scorecard` is unchanged.
> Full calibration digest changes are expected and recorded beside, never over, old
> evidence. See `handoffs/recovery/scorecard-contract/spec.md` for null/error cases.

### `docs/casepack-schema.md` and `handoffs/1.1-casepack-schema/spec.md`

In the schema reference events table replace the outcomes Notes cell with:
`Optional nonnegative revenue_loss; scorecard is a strict-integer point-delta map (see below).`
After that table and before Preconditions insert this exact paragraph. Insert the same
paragraph after the §5.6 event YAML example in the 1.1 living spec:

> **Scorecard contract v1 (recovery):** event `outcomes.scorecard` uses signed integer
> points on a 100-point scorecard, on `financial`, `customer`, `internal_process`, and
> `learning_growth` only. For example `-12` subtracts twelve points, or `0.12` from a
> normalized runtime score. An omitted map defaults to `{}`; omitted dimensions have
> zero effect. Explicit null, unknown keys, booleans, strings and floats are invalid.
> Point conversion must be finite. `Event.outcomes` remains required. New runtime
> results sum fired-event points, divide by 100, add to the existing 0–1 base and clamp
> once to 0–1, rounded to six decimals; they retain the authored integers in the event
> trace. `revenue_loss` is separate money evidence. No authored values or pack
> schema_version are changed by this contract. Unknown dimensions are reported as E18;
> numeric diagnostic improvements remain owned by OS-D1/M2.

Add a dated `scorecard contract revision 1` changelog entry to both documents, noting the
strict-input compatibility tightening and link to the living CONTRACTS entry. Existing
worked event values remain untouched. The NEW alias is a technical field vocabulary;
existing Financial/Customer/Internal Process/Learning & Growth report labels already
cover it. No new label family is needed.

### `handoffs/1.4-scoring-engine/spec.md` §5.4 and `design/03-scoring-frame-options.md`

After the BSC perspective listing/table add:

> **Implemented scorecard boundary — contract v1:** the pure engine emits normalized
> 0–1 base perspectives. Financial is currently the strategic-alignment and
> portfolio-discipline proxy with `financial_partial=True`; the Financial measures
> listed above describe the intended fuller model, not a claim those ledgers already
> feed this score. The round runner alone applies fired-event point adjustments under
> `CONTRACTS.md` and persists bounded scores plus base/delta/status evidence. Engine
> Tech/Org/Mgmt, capability realised value, firm score and historical pins are unchanged.

Add a dated changelog entry `Scorecard contract v1 clarifies units and the existing
partial Financial boundary; no pure-scoring formula change.`

### `handoffs/1.6-round-runner/spec.md`

Add a v1.2 recovery changelog/header revision; preserve historical v1.1 evidence.
In §5.2 replace the step-14 line with:
`14  aggregate fired-event scorecard points; normalize, bound, retain evidence/status; write immutable RoundResult`.
Replace the **whole** pseudocode loop beginning `for each fired event with a bound node:`
through `apply the event's outcomes to state (I6 forbids authoring the radius/duration)`
with this exact block; leave the following ledger-advance statement outside the loop:

```text
    event_records = []
    for each ev_key in fired:                                  # EVERY fired event
        event = pack event identified by ev_key
        cap = events.primary_capability(event, pack)
        node = events.failed_node(event, state, pack)
        if node is not None and cap is not None:
            evidence = dict(events.outage_duration(state, node, cap, pack))
        else:
            evidence = {"node": None, "blast_radius": []}       # no duration field
        evidence["key"] = ev_key
        evidence["outcomes"] = dict(event.outcomes)              # ALWAYS record outcomes
        event_records.append(evidence)                          # point deltas applied at step 14
```

This closes review finding **SC-SR-002**. Bound-node status controls outage evidence
only; it never gates scorecard penalties. The existing `runner.py:314–326` already uses
this scope. In the verified Balanced R1 evidence, `ransomware_on_finance` and
`phishing_on_staff_accounts` have `node=None`; their deltas still contribute to the
literal N7 expected values. This is a living-spec correction, not an event-selection or
runner-loop implementation change.
Replace the paragraph beginning `Step 12 runs **exactly once**. An event changes state`
through `Invariant I5.` with:

> Step 12 runs **exactly once** after event/signal resolution and supplies the
> authoritative capability score. Step 14 applies only the report's scorecard point
> adjustments under scorecard contract v1; no scorecard delta is fed back into
> Tech/Org/Mgmt. General event-to-estate/cash mutation remains M1 work. Invariant I5.

In §5.3 add NEW `scorecard_meta` beside `scorecard` in the illustrative payload, using the
shape in §3.2 of this recovery spec with symbolic base/totals; add:

> **Scorecard contract v1:** `scorecard` stays a four-number map; `scorecard_meta`
> stores version, units, partial-financial status, base and aggregated event points as
> defined in `CONTRACTS.md`. Step 14 computes them together and preserves raw event
> integers. The current Financial proxy remains partial. Validate event outcomes
> before any round writes and derived score/evidence before publication. Old payloads
> without metadata remain immutable and unversioned; this change performs no backfill
> or unlock. `_rolled_scorecard` now returns `(scorecard, scorecard_meta)` internally.

Changelog text: `v1.2 — recovery scorecard contract v1: explicit integer point conversion,
single final bounds, strict validation, metadata/status persistence; no changes to pure
scores, event timing, estate mutation, transaction/retry policy or old results.`

### `handoffs/1.5-event-signal-engine/spec.md` §5.2 and `design/02-traceability-matrix.md` §E

After the event-resolution pseudocode add:

> Fired-event scorecard deltas retain authored integer point units. The round runner
> converts/aggregates them exactly once at step 14 under scorecard contract v1 in
> `CONTRACTS.md`; event selection, suppression, fire-once timing and raw outcome
> evidence are unchanged. The point adjustment does not re-enter the pure MOT score.

Add a dated v1 scorecard-contract clarification changelog entry to the 1.5 spec.
Replace only the BSC row's Reads from/Status cells in design/02 with:
`1.4 normalized base plus 1.6 fired-event point adjustments; scorecard contract v1 and
persisted base/delta/partial-status evidence` /
`✅ unit/persistence contract; Financial remains a partial discipline proxy, full model M4`.
This does not mark Financial implementation or decision-driven game evolution complete.

The supervisor records the recovery finding's transition to integrated only after fresh
audit and its own reproduction of N7. Retain the north-star M4 full-financial and M2
OS-D1 owners. Historical August findings/digests and immutable result fixtures are not
living documents to rewrite.
