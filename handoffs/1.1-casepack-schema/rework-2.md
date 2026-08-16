# 1.1 — Second Rework Instruction

**Drafted by:** the AUTHOR · **Date:** 2026-08-17
**Branch to cut:** `build/1.1-rework-2`, from `main` @ `6b4578b`
**Scope:** schema only. No pack content, no engine, no validator.

> **This is not the rework in `rework.md`.** That one was a gate that was lifted, and it is
> closed. This is a **second, unrelated rework**, driven by decisions taken 2026-08-14/15
> and by the two 1.2 audits. `rework.md` stays as the record of the first; do not edit it.

---

## 1. Why this exists

1.2 shipped a validator, and the moment it ran against real content it found things the
schema cannot express. Separately, a user ruling on 2026-08-15 (thresholdless watch rules
are illegal, and presence-style rules get a declared kind) requires a field that does not
exist.

**Nothing downstream can proceed without this packet.** `handoffs/1.3-harvest/spec.md` §3a
is gated on items 1–4 below; `handoffs/1.5-event-signal-engine/spec.md` §10 is gated on
items 1, 2 and 5. Eleven of Riverside's twenty validator errors cannot be cleared by any
amount of authoring until items 1 and 4 land.

**Scale.** Six schema changes, all specified, **none requiring design.** This is a small
packet with a large blast radius — which is exactly why the compatibility rule in §2 is the
most important thing in this document.

---

## 2. The rule that governs every change here

> **Nothing you do may break the loading of an existing pack.**

There are **24 fixture packs** under `backend/tests/fixtures/packs/` plus
`backend/packs/riverside_grocery`, and **every one of them carries watch rules.** They are
1.2's evidence and 1.3's starting point.

If a new field is required, every one of those packs fails to load, `validate_casepack`
reports `E00` instead of the twenty errors it should, and `check_fixture_matrix.py` goes
red. **A schema change that silently destroys the validator's test suite is a worse defect
than the gaps it closes.**

Therefore: **every field added here is optional, or carries a default.** Verification is
`check_fixture_matrix.py` staying green and Riverside's error profile staying *identical* —
see §4.

**You do not fix the packs.** Making Riverside's content correct is 1.3's work, and
`backend/packs/` must be byte-identical when you finish. The fixtures are 1.2's; leave them
alone too.

---

## 3. The six changes

### 3.1 `WatchRule.metric_kind` — gates CG-1

```python
metric_kind: Literal["threshold", "presence"] = "threshold"
```

**Author ruling: optional with a default of `threshold`, not required.** Reasoning, because
you should not have to guess at it:

- Required would break all 25 packs (§2). Every existing rule is threshold-shaped, so
  `threshold` is the honest default rather than a convenience.
- The default is **migration affordance, not the end state.** 1.3 must declare the kind
  explicitly on every rule (its `I8`), and a later change may tighten this to required once
  no pack relies on the default. Note that in the docstring so the next reader knows it is
  deliberate.
- Under the default, Riverside's `sec_identity_01` and `wh_rollout_01` stay `threshold` with
  both thresholds null — so they **remain illegal and keep raising `E12`**, which is correct.
  They become legal when *1.3* declares them `presence`, not when you add the field.

**Add the constraint the ruling asked for**, as a model validator:

```
metric_kind == "threshold"  →  at least one of warn_above / critical_above must be set
metric_kind == "presence"   →  BOTH must be null
```

**Careful.** A `threshold` rule with no thresholds must **not** raise at load time — that is
`E12`'s job, and making the model reject it turns Riverside unloadable and destroys 1.2's
evidence. Enforce the `presence` half at the model (a presence rule carrying a threshold is
incoherent and no pack authors one today); leave the `threshold` half to `E12`. **Say in
your report that you split it this way and why.**

### 3.2 `obligation_rules` as a schema section — gates CG-5

**The shape is already specified. Do not design it.** See
`handoffs/1.5-event-signal-engine/spec.md` §5.4, which defines the section 1.3 will author
into:

```yaml
obligation_rules:
  - key: customer_pii_retention
    entity: customer                 # an entity the pack defines
    condition: policy_permits
    policy: data_retention
    permissive_value: indefinite
    severity: critical
    cleared_by: [add_policy, retire_component]
    arms: [regulator_letter]         # event keys this obligation can arm
    provenance: {...}
```

Optional section — a pack without it loads clean. Its absence is `CG-5` and stays 1.3's to
close.

### 3.3 `Labels` sections — `1.2-008`, `1.2-024`

`Labels` today has `capabilities · roles · sidebar · strategies · stakeholders · events ·
policies · misc`. Add optional sections for **`entities` · `catalog` · `watch_rules` ·
`questions`**, so eight validator codes stop leading with a machine key.

**Also report, do not fix:** `labels.events` maps an event key to a **persona quote**, not to
a name, which is why `E21` and `W03` print machine keys. Whether that becomes
`events.name` + `events.quote` is a **content-shape question for 1.3** and possibly a
`CONTRACTS.md` entry. Name the problem in your report and stop there.

### 3.4 `PlatformService.owns_entities` — `1.2-011`

```python
owns_entities: list[EntityOwnership] = Field(default_factory=list)
```

Same shape `CatalogItem` uses. `firm_infrastructure` requires `user_account` at `named_user`;
`central_sign_on` fills the *role* but nothing can own the *entity*, so the requirement is
unsatisfiable as authored. **Adding the field does not clear `E02`** — Riverside must then
declare the ownership, which is 1.3's. Expect `E02 ×1` to still fire when you finish. That
is correct.

### 3.5 `EventPrecondition` fields — gates 1.5, not 1.3

`handoffs/1.5-event-signal-engine/spec.md` §5.2 has the table: **six of eleven precondition
types have no fields to carry their parameters.** Add, all optional:

```python
node: SnakeKey | None = None          # node_is_spof
entity: SnakeKey | None = None        # entity_unowned
policy: SnakeKey | None = None        # policy_contradiction (a second policy field
                                      #   may be needed — read 1.5 §5.2 and report)
round: int | None = None              # round_equals — an int, never `ratio`
count: int | None = None              # placement_count
```

**This item gates 1.5, not 1.3.** If you run short or hit a problem, deliver 3.1–3.4 and
report 3.5 undone — that still unblocks 1.3, which is the urgent path.

### 3.6 `WatchRule.key` → `SnakeKey` — cosmetic

Every sibling key is `SnakeKey`; this one is bare `str`. Verified 2026-08-17: all six
distinct rule keys across all 25 packs are already valid snake_case, so tightening it breaks
nothing. **Re-verify before you change it** — if any key fails, stop and report rather than
renaming pack content.

---

## 4. Definition of Done

| Item | Evidence required |
|---|---|
| 3.1 `metric_kind` with default + the presence-half constraint | model excerpt; the split explained |
| 3.2 `obligation_rules` section, matching 1.5 §5.4 | model excerpt, field by field against that spec |
| 3.3 four `Labels` sections; the `events` shape problem reported | model excerpt + the report |
| 3.4 `PlatformService.owns_entities` | model excerpt |
| 3.5 five `EventPrecondition` fields (or reported undone) | model excerpt |
| 3.6 `WatchRule.key` tightened, after re-verification | the verification output |
| **`check_fixture_matrix.py` green** | pasted, exit 0, all 24 fixtures |
| **Riverside's error profile UNCHANGED** | see below — this is the load-bearing check |
| `backend/packs/` byte-identical | `git diff 6b4578b..HEAD -- backend/packs/` → empty |
| `backend/tests/fixtures/` byte-identical | same, → empty |
| `docs/casepack-schema.md` updated for all six | the instructor authors from this document |
| 1.1's I1–I8 still clean | re-run them |

**The load-bearing check.** Before and after your change:

```
./backend/bin/validate_casepack --json backend/packs/riverside_grocery \
  | python3 -c "import json,sys,collections; print(collections.Counter(f['code'] for f in json.load(sys.stdin)))"
```

Expected **identical** before and after:
`E07 ×8 · E20 ×6 · E12 ×2 · E21 ×2 · E02 ×1 · E14 ×1 · W02 · W04 · W05`

**Paste both runs.** If the profile changes, you have either broken loading or accidentally
fixed content, and both are defects in this packet. A schema addition that changes what the
validator says about unchanged content has changed the meaning of the content.

---

## 5. What you must NOT do

- **Do not touch `backend/packs/` or `backend/tests/fixtures/`.** Content is 1.3's, fixtures
  are 1.2's. Both diffs must be empty.
- **Do not make any new field required.** §2.
- **Do not update the validator.** `E12`'s presence exemption, `E20`'s widened predicate and
  the new `W08` are 1.2's next rework, correctly sequenced *after* this one. Touching
  `validate.py` here couples two packets and makes both harder to audit.
- **Do not design `obligation_rules`.** 1.5 §5.4 specified it. Implement that.
- **Do not rename or re-key anything in a pack**, including under 3.6.

---

## 6. When you are done

Fill `handoffs/1.1-casepack-schema/dod-rework-2.md` — a new file; do not overwrite the
original `dod.md`. Push `build/1.1-rework-2` and verify the push landed by comparing
`git ls-remote` against your local HEAD. **Do not merge.** A fresh auditor takes it from
there.

Stop and report on anything this document does not settle. The one item most likely to need
a ruling is 3.3's `labels.events` shape — it is named as report-only for exactly that reason.
