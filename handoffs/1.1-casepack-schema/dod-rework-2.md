# 1.1 — Second Rework · Definition of Done

**Builder:** Claude (build session) · **Date:** 2026-08-17
**Instruction:** `handoffs/1.1-casepack-schema/rework-2.md`
**Branch:** `build/1.1-rework-2`, cut from `b6bcf37`
**Scope delivered:** all six changes (3.1 – 3.6). Nothing deferred.

> This is the DoD for the **second** rework. The first rework's record is `rework.md` /
> `dod.md` and is untouched.

**Files changed — three, and only three:**

```
backend/app/casepack/models.py     the six schema changes
backend/app/casepack/loader.py     obligation_rules.yaml read as an optional file
docs/casepack-schema.md            all six documented for the instructor
```

`backend/app/casepack/validate.py` is **not** among them, by instruction: `E12`'s presence
exemption, `E20`'s widened predicate and the new `W08` are 1.2's next rework.

---

## 1. The load-bearing check

`./backend/bin/validate_casepack --json backend/packs/riverside_grocery | python3 -c "import json,sys,collections; print(collections.Counter(f['code'] for f in json.load(sys.stdin)))"`

**Before** (at `b6bcf37`, nothing changed):

```
Counter({'E07': 8, 'E20': 6, 'E12': 2, 'E21': 2, 'E02': 1, 'E14': 1, 'W02': 1, 'W04': 1, 'W05': 1})
```

**After** (all six changes in):

```
Counter({'E07': 8, 'E20': 6, 'E12': 2, 'E21': 2, 'E02': 1, 'E14': 1, 'W02': 1, 'W04': 1, 'W05': 1})
```

**Identical.** `E07 ×8 · E20 ×6 · E12 ×2 · E21 ×2 · E02 ×1 · E14 ×1 · W02 · W04 · W05`, as
specified. `E02 ×1` still fires, which is correct — adding `owns_entities` gives Riverside
somewhere to declare the ownership; declaring it is 1.3's.

---

## 2. Definition of Done table

| Item | Status | Evidence |
|---|---|---|
| 3.1 `metric_kind` with default + the presence-half constraint | **DONE** | §3.1 below; the split explained |
| 3.2 `obligation_rules` section, matching 1.5 §5.4 | **DONE** | §3.2, field by field |
| 3.3 four `Labels` sections; the `events` shape problem reported | **DONE** | §3.3 and §4 |
| 3.4 `PlatformService.owns_entities` | **DONE** | §3.4 — see the caveat in §4 |
| 3.5 five `EventPrecondition` fields | **DONE** | §3.5 |
| 3.6 `WatchRule.key` tightened, after re-verification | **DONE** | §3.6, verification output pasted |
| `check_fixture_matrix.py` green | **DONE** | §5, exit 0, all 24 fixtures |
| Riverside's error profile UNCHANGED | **DONE** | §1, both runs pasted |
| `backend/packs/` byte-identical | **DONE** | §6, empty diff |
| `backend/tests/fixtures/` byte-identical | **DONE** | §6, empty diff |
| `docs/casepack-schema.md` updated for all six | **DONE** | §7 |
| 1.1's I1–I8 still clean | **DONE** | §8 |
| No new field required | **DONE** | §9 |

---

## 3. The six changes

### 3.1 `WatchRule.metric_kind`

```python
class WatchRule(StrictModel):
    key: SnakeKey
    capability: SnakeKey
    metric: SnakeKey
    metric_kind: Literal["threshold", "presence"] = "threshold"
    warn_above: float | None = None
    critical_above: float | None = None
    cleared_by: list[SnakeKey]
    provenance: Provenance

    @model_validator(mode="after")
    def presence_rules_carry_no_thresholds(self) -> WatchRule:
        if self.metric_kind == "presence" and (
            self.warn_above is not None or self.critical_above is not None
        ):
            raise ValueError("metric_kind 'presence' must not carry warn_above or critical_above")
        return self
```

**The constraint is split, deliberately, and only half of it is here.**

| Half | Where enforced | Why there |
|---|---|---|
| `presence` → **both** thresholds must be null | **the model**, above | A presence rule carrying a threshold is incoherent, and no pack in the repo authors one. Rejecting it at load costs nothing and can break nothing |
| `threshold` → **at least one** threshold must be set | **the validator's `E12`**, unchanged | Riverside authors two thresholdless threshold-shaped rules today. Rejecting them at load makes the pack **unloadable**, which replaces twenty specific findings with a single `E00` and destroys 1.2's evidence |

The second row is the whole reason for the split. The model layer's failure mode is total —
one bad record and the pack does not load at all — so the model may only reject things no
pack currently contains. `E12` can say "this rule is wrong" about a pack that still loads,
and everything else in it still gets checked. Enforcing both halves at the model would have
been the same defect the compatibility rule exists to prevent.

The default is a **migration affordance, not the end state**, and the docstring says so:
1.3 must declare the kind explicitly on every rule, and a later packet may tighten this to
required once no pack relies on the default.

**Behaviour under the default, demonstrated:**

```
default metric_kind      -> threshold
thresholdless threshold  -> loads OK, metric_kind = threshold
presence, no thresholds  -> loads OK, kind = presence
presence + threshold     -> rejected: Value error, metric_kind 'presence' must not carry warn_above or critical_above
```

Riverside's `sec_identity_01` and `wh_rollout_01` inherit `threshold` with both thresholds
null, so they remain illegal and keep raising `E12 ×2`. They become legal when **1.3**
declares them `presence`, not when this field was added.

### 3.2 `obligation_rules`

```python
class ObligationRule(StrictModel):
    key: SnakeKey
    entity: SnakeKey
    condition: SnakeKey
    policy: SnakeKey
    permissive_value: str
    severity: Literal["critical"] = "critical"
    cleared_by: list[SnakeKey]
    arms: list[SnakeKey] = Field(default_factory=list)
    provenance: Provenance


class Casepack(StrictModel):
    ...
    obligation_rules: list[ObligationRule] = Field(default_factory=list)
```

**Field by field against 1.5 §5.4.** The shape was implemented, not designed.

| 1.5 §5.4 | Implemented as | Note |
|---|---|---|
| `key: customer_pii_retention` | `key: SnakeKey` | |
| `entity: customer` — "an entity the pack defines" | `entity: SnakeKey` | Cross-reference to `entities.yaml` is a validator check, not a model one |
| `condition: policy_permits` | `condition: SnakeKey` | §5.4 names one value and does not close the set, so **no enum was invented** |
| `policy: data_retention` | `policy: SnakeKey` | |
| `permissive_value: indefinite` | `permissive_value: str` | Policy values are free-form (`PolicyOption.effects` already carries `float \| int \| str`) |
| `severity: critical` — "obligations are presence-shaped (decision 10)" | `severity: Literal["critical"] = "critical"` | §5.4's comment plus decision 10 — *"presence signals raise at critical, never at warning"* — is a one-value vocabulary. Declared as a reading, see §9 |
| `cleared_by: [add_policy, retire_component]` | `cleared_by: list[SnakeKey]`, required | Mirrors `WatchRule.cleared_by`, which is required |
| `arms: [regulator_letter]` | `arms: list[SnakeKey] = []` | An obligation that arms nothing is coherent; follows the codebase pattern for optional linkage lists |
| `provenance: {...}` | `provenance: Provenance` | The elided `{...}` is the existing model every other authored record uses |

**Optional section.** The loader reads `obligation_rules.yaml` if the file is there and
substitutes an empty list if it is not. Its absence is `CG-5` and stays 1.3's to close.

```python
# loader.py
"obligation_rules": _optional(root, "obligation_rules.yaml", []),
```

Proven end to end against a **scratchpad copy** of Riverside carrying the §5.4 example
verbatim (the real pack was not touched):

```
loaded with obligation_rules.yaml present: 1 rule(s)
{'key': 'customer_pii_retention', 'entity': 'customer', 'condition': 'policy_permits',
 'policy': 'data_retention', 'permissive_value': 'indefinite', 'severity': 'critical',
 'cleared_by': ['add_policy', 'retire_component'], 'arms': ['regulator_letter'], ...}

validator on that probe pack:
Counter({'E07': 8, 'E20': 6, 'E12': 2, 'E21': 2, 'E02': 1, 'E14': 1, 'W02': 1, 'W04': 1, 'W05': 1})
```

A pack that *has* the section validates to the same profile as one that does not — the
section is additive, and the validator does not yet read it. That is expected: obligations
have no validator codes until 1.2 and no engine until 1.5.

### 3.3 `Labels` sections

```python
class Labels(StrictModel):
    capabilities: dict[SnakeKey, str] = Field(default_factory=dict)
    roles: dict[SnakeKey, str] = Field(default_factory=dict)
    sidebar: dict[SnakeKey, str] = Field(default_factory=dict)
    strategies: dict[SnakeKey, str] = Field(default_factory=dict)
    stakeholders: dict[SnakeKey, str] = Field(default_factory=dict)
    events: dict[SnakeKey, str] = Field(default_factory=dict)
    policies: dict[SnakeKey, str] = Field(default_factory=dict)
    entities: dict[SnakeKey, str] = Field(default_factory=dict)      # new
    catalog: dict[SnakeKey, str] = Field(default_factory=dict)       # new
    watch_rules: dict[SnakeKey, str] = Field(default_factory=dict)   # new
    questions: dict[SnakeKey, str] = Field(default_factory=dict)     # new
    misc: dict[SnakeKey, str] = Field(default_factory=dict)
```

All four default to empty, so no pack is required to author them.

Confirmed not to disturb `E07`: `_label_references()` in `validate.py` builds its
expectation list from **hardcoded** sections, not from `Labels`' field list, so four empty
sections add zero references. `E07 ×8` before and after.

The `labels.events` shape problem is reported in §4 and **not fixed**.

### 3.4 `PlatformService.owns_entities`

```python
class PlatformService(StrictModel):
    key: SnakeKey
    roles_filled: list[SnakeKey]
    placement_options: dict[Placement, DeploymentMode]
    capacity_pct: int = Field(ge=0, le=100)
    staff_load: float = Field(ge=0)
    owns_entities: list[EntityDetail] = Field(default_factory=list)   # new
    provenance: Provenance
```

Same shape `CatalogItem` uses — `list[EntityDetail]`, i.e. `{entity, level_of_detail}`.

`E02 ×1` still fires, as specified. **But see §4** — it will still fire after 1.3 authors
the ownership too, and that is a validator gap 1.2 must close.

### 3.5 `EventPrecondition` fields

```python
class EventPrecondition(StrictModel):
    type: SnakeKey
    signal: str | None = None
    severity: Literal["warning", "critical"] | None = None
    capability: SnakeKey | None = None
    ratio: float | None = None
    node: SnakeKey | None = None                          # node_is_spof
    entity: SnakeKey | None = None                        # entity_unowned
    policy: SnakeKey | None = None                        # policy_contradiction
    round: int | None = Field(default=None, gt=0)         # round_equals — an int
    count: int | None = Field(default=None, ge=0)         # placement_count
```

All five optional. `round` is an integer and rejects a float, so the *"press it into
`ratio`"* failure mode 1.5 §5.2 warns about cannot be reproduced by accident:

```
precondition -> {'type': 'node_is_spof', 'node': 'wan_link'}
precondition -> {'type': 'entity_unowned', 'entity': 'user_account'}
precondition -> {'type': 'policy_contradiction', 'policy': 'data_retention'}
precondition -> {'type': 'round_equals', 'round': 4}
precondition -> {'type': 'placement_count', 'count': 3}
round=1.5    -> rejected: Input should be a valid integer, got a number with a fractional part
```

`policy_contradiction` needs **two** policy keys and has one field — reported in §4, not
designed here.

### 3.6 `WatchRule.key` → `SnakeKey`

**Re-verified before changing anything.** All 25 packs, all watch rules:

```
packs scanned: 25  with watch_rules.yaml: 25
distinct keys: 6
  'book_cap_01'            x25  snake_case=True
  'book_noshow_01'         x1   snake_case=True
  'ord_cap_01'             x1   snake_case=True
  'rec_adopt_01'           x24  snake_case=True
  'sec_identity_01'        x1   snake_case=True
  'wh_rollout_01'          x1   snake_case=True
FAILURES: none
```

Six distinct keys, exactly as `rework-2.md` states, all snake_case. Nothing was renamed.

**Declared: this change is annotation-only at runtime.** `SnakeKey` in `models.py` is
`SnakeKey = str` — a documentation alias, not a constrained type. Changing `key: str` to
`key: SnakeKey` therefore makes `WatchRule.key` *say* what its siblings say without
enforcing anything new. Enforcement of snake case already exists and already covered watch
rule keys: `checks.check_snake_case_keys` walks every `key` in the dumped model and the
validator reports it as `I3`. Details in §4.

---

## 4. Reported, not fixed

### R1 — `labels.events` maps to a persona quote, not to a name

Every other section of `labels.yaml` maps a machine key to a short display **name**:
`capabilities.order_fulfilment → "Order Fulfilment"`. `events` does not. It maps an event's
`body_key` to the **body of the message the persona sends** — a whole sentence of in-world
prose:

```yaml
events:
  event_tablets_arrived: "My crew found out about the new system when the tablets arrived."
  event_inventory_numbers: "The auditors asked how we know our inventory numbers are right. I did not have an answer."
  event_pos_support_ending: "Support for your point-of-sale version ends in one round."
```

So there is **nowhere in the schema to author an event's name.** `E21` and `W03` both
format their subject as `"Event {event}"` and interpolate `event.key` directly, because
there is nothing else to interpolate. An instructor is told `Event warehouse_rollout_gap
can never happen` — a machine key, in a message whose whole purpose is to be readable.

Adding a `labels.events` name map alongside the quote does not work as the schema stands:
the two live in one dict keyed differently — the quote is keyed by `body_key`, a name would
be keyed by the event `key` — so they would collide in the same namespace and `E07`'s
`misc` catch-all would quietly accept either for the other.

The candidate resolution is `events.name` + `events.quote` as two sub-maps, which is a
**content-shape question for 1.3** and probably a `CONTRACTS.md` entry, since events cross
the validator, the inbox screen and the debrief narrator. It is named here and stopped at,
per instruction.

### R2 — `owns_entities` on a platform service is inert until 1.2 reads it

`PlatformService.owns_entities` now exists (3.4), but `E02` will still fire after 1.3
authors the ownership, because the validator does not look at platform services when it
works out what owns what:

```python
# validate.py:437-443, Lens.__init__
self.owned: dict[str, int] = {}
for item in pack.catalog:                    # <- catalog only
    for held in item.owns_entities:
        ...
        self.owned[held.entity] = max(self.owned.get(held.entity, -1), rank)
```

`Lens.owned` feeds `Lens.satisfiable()`, which is what `E02` (and `E23`) consult. A pack
declaring `central_sign_on.owns_entities: [{entity: user_account, level_of_detail:
named_user}]` will therefore still raise `E02` for `firm_infrastructure`.

**This is a fifth item for 1.2's next rework**, alongside the four already listed in 1.5
§10: `Lens.owned` must union `pack.platform.services` with `pack.catalog`. Left undone, 1.3
authors the correct content, the error does not clear, and 1.3 gets blamed for a validator
gap. Not fixed here — the instruction forbids touching `validate.py`, and correctly so.

### R3 — `policy_contradiction` needs two policy keys and has one field

1.5 §5.2's table reads `policy_contradiction | two **policy** keys | ❌ no policy field`,
while §10 item 3 lists the addition as `policy` (singular). `rework-2.md` §3.5 anticipates
this — *"a second policy field may be needed — read 1.5 §5.2 and report"*.

One `policy` field is what was specified, and one is what was added. A precondition of type
`policy_contradiction` cannot currently name the second policy it contradicts.

Three shapes are possible and **none was chosen here**: a second scalar (`policy_b`), making
`policy` a list, or leaving it scalar and having the engine read the contradiction from
`policies.yaml` categories rather than from the card. This needs a ruling from 1.5's author
before a field is added, because the choice changes what an event card means.

### R4 — `SnakeKey` is an alias, so 3.6 changed no behaviour

```python
# models.py:12
SnakeKey = str
SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
```

`SnakeKey` is a plain alias for `str`. `SNAKE_RE` is applied by a `field_validator` on
exactly two fields — `PackMetadata.pack_key` and `PackMetadata.vertical` — and nowhere else.
Every other `key: SnakeKey` in the schema is documentation.

3.6 was worth doing: the annotation now says what the field means, and `docs/casepack-
schema.md` already claimed watch rule keys were `snake string`, so code and document now
agree. But an auditor should not read it as new enforcement. Snake case on watch rule keys
was already enforced, one layer out, by `checks.check_snake_case_keys` → `I3`.

Whether `SnakeKey` should become a real `Annotated[str, StringConstraints(pattern=...)]` is
a schema question with a blast radius across every pack, and it is not in this packet.

### R5 — 1.3's pre-flight row 1a will FAIL spuriously as written

`handoffs/1.3-harvest/spec.md` §7 row 1a checks the gate this packet lifts. Its second grep
is written for a two-space indent; Python class bodies use four:

```
$ grep -nE "^  (entities|catalog|watch_rules|questions):" backend/app/casepack/models.py
NO MATCH

$ grep -nE "^    (entities|catalog|watch_rules|questions):" backend/app/casepack/models.py
460:    entities: dict[SnakeKey, str] = Field(default_factory=dict)
461:    catalog: dict[SnakeKey, str] = Field(default_factory=dict)
462:    watch_rules: dict[SnakeKey, str] = Field(default_factory=dict)
463:    questions: dict[SnakeKey, str] = Field(default_factory=dict)
```

All four sections are present. The row will report them absent, and its own instruction is
**"any absent → STOP and report which"** — so 1.3's builder stops on a gate that is in fact
lifted. This is the same near-miss class 1.5 §7 records as having *"cost 1.2 a spurious
pre-flight FAIL"*.

Not fixed here: 1.3's spec belongs to its author, and `GOVERNANCE §7` says surface the
disagreement rather than reconcile it. The row needs `^    ` (four spaces), or better,
`grep -nE "^ +(entities|catalog|watch_rules|questions):"`. **Row 1a's first grep** —
`metric_kind|obligation_rules|owns_entities` — passes as written.

Verified against the other downstream pre-flights, which do pass as written:

```
1.5 row 5  grep -n "metric_kind" models.py                     -> line 329  PASS
1.5 row 6  grep -n "obligation_rules|class ObligationRule"     -> 387, 478  PASS
1.5 row 7  grep -nE "node:|entity:|policy:|round:"             -> 358-361   PASS
```

---

## 5. `check_fixture_matrix.py` — green, exit 0, all 24 fixtures

```
fixture          want  got  codes raised
minimal_valid       0    0  -   PASS
broken_E00          1    1  E00   PASS
broken_E01          1    1  E01,E22   PASS
broken_E02          1    1  E02,E22   PASS
broken_E03          1    1  E03   PASS
broken_E04          1    1  E04   PASS
broken_E05          1    1  E05   PASS
broken_E06          1    1  E06   PASS
broken_E07          1    1  E07   PASS
broken_E08          1    1  E08   PASS
broken_E09          1    1  E09   PASS
broken_E10          1    1  E10   PASS
broken_E11          1    1  E11   PASS
broken_E12          1    1  E12   PASS
broken_E13          1    1  E13   PASS
broken_E14          1    1  E14   PASS
broken_E20          1    1  E20   PASS
broken_E20_mute     1    1  E12,E20,E21   PASS
broken_E21          1    1  E21   PASS
broken_E22          1    1  E01,E22   PASS
broken_E23          1    1  E23   PASS
broken_I3           1    1  I3   PASS
warn_W01            0    0  W01   PASS
warn_heuristics     0    0  W02,W03,W04,W05,W06,W07   PASS

I1  implemented codes : 28 [...]
I1  spec-named codes  : 28 [...]
I1  set equality      : PASS

I5  minimal_valid                      text=  0 json=  0 identical=yes
I5  warn_heuristics                    text=  6 json=  6 identical=yes
I5  riverside_grocery                  text= 23 json= 23 identical=yes
I5  packs/  (directory mode)           text= 35 json= 35 identical=yes
I5  directory-mode pack attribution    every record names its pack

all 24 fixtures behave as named; 27 of 28 codes exercised, ['I8'] recorded as unfixturable
I1 set-equal against the spec; I5 identical in single-pack and directory mode
EXIT=0
```

Byte-identical to the same run at `b6bcf37` before any change.

**Also verified directly:** all 25 packs were loaded through `load_casepack`. 22 load; the
three that do not are `broken_E00`, `broken_E03` and `broken_E04`, which are the fixtures
built to fail loading, and they failed identically before this change.

---

## 6. The empty diffs

```
$ git diff b6bcf37..HEAD -- backend/packs/
(no output)

$ git diff b6bcf37..HEAD -- backend/tests/fixtures/
(no output)

$ git status --short
 M backend/app/casepack/loader.py
 M backend/app/casepack/models.py
 M docs/casepack-schema.md
```

No pack content, no fixture, no validator.

---

## 7. `docs/casepack-schema.md`

Updated for all six:

| Change | What the document now carries |
|---|---|
| 3.1 | `metric_kind` row in the `watch_rules.yaml` table, a **"Two kinds of rule"** section explaining threshold vs presence in business terms, a standing note that the default is a migration affordance and the kind should be declared, and **two worked examples — one of each kind** |
| 3.2 | A new `obligation_rules.yaml — optional` section: what an obligation is for, the full field table, why severity is `critical` only, and the §5.4 worked example. Listed under a new **"Optional files"** heading in Layout |
| 3.3 | Four new rows in the `labels.yaml` table, an instruction to author a label for every key an instructor will see named, the worked example extended, and a call-out that `events` is a quote map and not a name map |
| 3.4 | `owns_entities` named in the `platform.yaml` services row, a paragraph on why filling a role is not the same as owning an entity, and a worked `central_sign_on` example |
| 3.5 | A new **"Preconditions"** section under `events.yaml` — a table of all ten fields against the precondition types that read them, the warning not to press parameters into `ratio`, and a worked multi-precondition example |
| 3.6 | No change needed: the table already said `key | snake string`. The model now agrees with the document rather than the other way round |

---

## 8. 1.1's I1–I8, re-run

Commands are `handoffs/1.1-casepack-schema/verify.md`, unchanged.

```
=== I1 (no pack-identity branching) ===
zero hits
=== I2 (no displayed English) ===
zero hits
=== I3-I8 ===
I3: PASS []
I4: PASS []
I5: PASS []
I6: PASS []
I7: PASS []
I8: PASS []
=== TODO scan ===
zero hits
=== seed ===
7 capabilities, 10 catalog items, 4 strategies
cost_leadership weights sum 1.000
differentiation weights sum 1.000
customer_supplier_intimacy weights sum 1.000
focus_strategy weights sum 1.000
pinned figures: round 3; capital 44000 of 220000; run_rate 58300; scorecard 61/48/39/27;
signals 3; inbox 3; staff 2.0; load 3.4; over 170; review_capital 174000 of 220000;
remaining 46000; run_rate_after 62200; run_rate_before 58300
warehouse people 34 contribution 25
store_operations people 140 contribution 44
finance people 8 contribution 81
compileall_ok
```

`I8` (round-trip) is the one that would have caught a new field being dropped on dump and
reload. It passes.

---

## 9. No new field is required

| Field | Model | Optionality |
|---|---|---|
| `WatchRule.metric_kind` | `WatchRule` | default `"threshold"` |
| `PlatformService.owns_entities` | `PlatformService` | `default_factory=list` |
| `EventPrecondition.node` / `.entity` / `.policy` / `.round` / `.count` | `EventPrecondition` | all `= None` |
| `Labels.entities` / `.catalog` / `.watch_rules` / `.questions` | `Labels` | all `default_factory=dict` |
| `Casepack.obligation_rules` | `Casepack` | `default_factory=list`; the file is optional in the loader |

`ObligationRule`'s own fields are required where §5.4 shows them, which breaks nothing: no
pack has the section, and one authored from the documented example validates.

---

## 10. Substitutions declared

| # | Instruction said | What was done | Why |
|---|---|---|---|
| S1 | `rework-2.md` §1: cut from `main @ 6b4578b` | Cut from `main @ b6bcf37` | The dispatch says `b6bcf37`, and it is current `main`. `6b4578b` is its parent — the commit **before** `rework-2.md` itself was added, so branching there would have cut from a tree not containing the instruction. Both baselines produce the specified error profile |
| S2 | `owns_entities: list[EntityOwnership]` | `owns_entities: list[EntityDetail]` | There is no `EntityOwnership` class. `EntityDetail` (`{entity, level_of_detail}`) is the class `CatalogItem.owns_entities` uses, and the instruction says *"same shape `CatalogItem` uses"*. Shape as specified; existing name reused rather than a synonym introduced |
| S3 | §5.4 shows `severity: critical` | `severity: Literal["critical"] = "critical"` | 1.5 decision 10 states presence signals raise at critical and never at warning, and §5.4 annotates the field *"obligations are presence-shaped (decision 10)"*. A one-value vocabulary is the transcription of the two together. Widening it to `warning \| critical` would have permitted a value decision 10 forbids. Flagged in case 1.5's author intended the wider enum |
| S4 | §5.4 shows `arms:` and `cleared_by:` populated | `arms` defaults to `[]`; `cleared_by` required | `cleared_by` mirrors `WatchRule.cleared_by`, which is required; `arms` is an optional linkage and follows the `owns_entities` / `overrides` pattern already in the file |
| S5 | Nothing said about the loader | `loader.py` changed | `obligation_rules` cannot be an optional *section* without the loader treating the file as optional; `_required()` would have made a missing file a load error and broken all 25 packs. This is 3.2 as specified, not scope added |
| S6 | The `obligation_rules` probe | Ran against a **scratchpad copy** of Riverside, not the pack | `backend/packs/` must be byte-identical. Proving the optional file actually loads required a pack that has one |

No other substitution. `validate.py` was read but not modified.

---

## 11. What this hands on

**To 1.2's next rework** — the four items already in 1.5 §10, plus a **fifth found here**:

5. `Lens.owned` must union `pack.platform.services` with `pack.catalog` (§4 R2). Without it
   `PlatformService.owns_entities` is inert and `E02` cannot clear.

**To 1.3** — the gate of `1.3-harvest/spec.md` §3a is lifted. All four additions it names are
present: `metric_kind`, `obligation_rules`, the four `Labels` sections, and
`PlatformService.owns_entities`. **Its pre-flight row 1a will nevertheless FAIL as written —
see `R5`; the row's grep, not the schema, is what is wrong.** `R1` (the `labels.events`
shape) is a content-shape question waiting on 1.3 or a ruling. `R2` warns that clearing
`E02` needs 1.2's validator change as well as 1.3's authoring.

**To 1.5** — pre-flight rows 5, 6 and 7 should now pass. `R3` (`policy_contradiction`'s
second policy key) needs a ruling from 1.5's author before the field is added.
