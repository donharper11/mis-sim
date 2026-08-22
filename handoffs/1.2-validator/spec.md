# 1.2 — Casepack Validator · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Spec version:** v1.6 · **Amended:** 2026-08-22 — findings CU-001/CU-002/CU-003: `E18` closes the closed-vocabulary E00-collapse class; the E29 behaviours are enumerated and made variant-visible; the label-routing narrowing is guarded
**Previously amended:** v1.5, 2026-08-21 — readiness closeout added exact precondition-shape code `E29` and pack-relative W08
**Previously:** v1.4, 2026-08-21 — obligation and policy coverage; v1.3, 2026-08-18 — `W08` added; v1.2, 2026-08-14, post-audit, against `findings/1.2-2026-08-14-audit.md`
**Code list is versioned, not frozen** *(`SPEC_PROTOCOL §3`)* — `E00`–`E18` · `E20`–`E29` · `W01`–`W08` · `I3` · `I8`
**Phase:** 1 · **Depends on:** **1.1 as approved** · **Blocks:** 1.3, 6.1

> An unvalidated pack does not fail loudly — it runs and scores wrongly, and you find out
> in week 9. This is the guardrail that makes packs 2–5 authorable by someone who is not
> the schema's author.

---

## 0. Spec Basis

**Read in full:** `handoffs/1.1-casepack-schema/spec.md` (the schema being enforced) ·
`design/01-mis_lite-harvest.md` §4 (the seed-quality failures this must catch) ·
`GOVERNANCE.md` §5 (the validator gate) · `CONTRACTS.md`.

**Extraction sufficiency:** covered. 1.1's `checks.py` is the substrate; this wraps and
extends it.

---

## 1. Purpose and scope

A CLI that refuses to let a broken pack reach a section.

**In scope:** `validate_casepack <pack_dir>` · three severity levels · human-readable
output naming file and field · non-zero exit on error · a machine-readable `--json` mode
for 5.6's instructor view.

**Out of scope:** fixing anything · loading to DB (2.5) · UI (5.6) · validating *content
quality* beyond the heuristics in §5.3.

---

## 2. Project-specific statements

**Scoring factors touched:** none directly — it protects every one of them by ensuring
their authored inputs exist and resolve. **Casepack keys read:** all.
**Instance scoping:** N/A. **Business-language check:** validator output is for
instructors, not engineers — errors say *"capability 'Customer Service' needs customer
data at individual level, but no catalog item can hold it"*, not
`required_entities[1].min_level_of_detail unsatisfiable`.

---

## 3. Settled decisions

1. **Three severities.** `ERROR` blocks loading. `WARN` loads but is reported.
   `INFO` is advisory.
2. **Exit codes.** `0` clean · `1` errors present · `2` validator itself failed.
3. **Every check names its fix, at every severity.** A message that states a problem
   without a next action is incomplete. **Amended v1.2:** this binds `WARN` and `INFO` as
   well as `ERROR`. v1.1 said so here and contradicted itself in §5.4's sample, which
   showed WARN blocks with no fix line; the build followed the picture over the decision
   (`1.2-009`). The decision is what governs. A warning is the case an instructor is
   *most* likely to need help acting on, precisely because nothing forces them to act.
4. **Wraps 1.1's `checks.py`** rather than reimplementing it.
5. **`E20` stays an ERROR, and Riverside is therefore expected to fail this build.**
   Settled 2026-08-14. A capability that cannot raise a signal is invisible to
   responsiveness scoring — that is error-grade, and the check most likely to catch a real
   authoring mistake does not get weakened to fit today's content. See §9.1.
6. **The action-type vocabulary already exists.** `checks.py:12` defines `ACTION_TYPES`,
   ten values. `E05` validates against that set; it is not re-declared here. Extending the
   set is a 1.4/1.5 decision, not this packet's.
7. **A watch rule carrying neither threshold is illegal.** Ruled by the user 2026-08-14 in
   response to `1.2-001` and `1.2-013`. A rule with `warn_above: null` **and**
   `critical_above: null` can never fire, so it is not a watch rule — it is the appearance
   of one, which is worse than its absence because it satisfies a coverage count while
   watching nothing. Two consequences, both binding:

   - **`E12` is added** (§5.1) — the rule itself is the defect, reported where it is
     authored.
   - **`E20`'s predicate widens** (§5.2) from *"appears in no watch rule"* to *"has no
     watch rule carrying at least one threshold"*, so the check finally matches the
     rationale it has always been written with.

   **This is a schema constraint that `models.py` should enforce**, so an illegal rule
   cannot be constructed at all. That is a **1.1 change and out of scope here** — 1.2
   detects, it does not repair. Filed against 1.1 as the disposition of `1.2-013`.
8. **`E00` is ratified into the code list.** The builder added it for a missing or
   unparseable pack file and declared it; the auditor ruled there was no compliant route
   without it (`1.2-016` item 1). `SPEC_PROTOCOL §3` requires the code list to be frozen or
   versioned, and 5.6's UI will key on it, so it is named here rather than left as
   undeclared scope.
9. **`ARCHETYPES` moves to `checks.py`, beside `ACTION_TYPES`.** The builder derived the 14
   values correctly from `design/05 §1.4.1` and the auditor verified the sourcing. It is
   schema vocabulary, not validator-local state, and 1.4/1.5 will want it. Relocation is
   rework, not a rebuild.

### 3.1 One compliant route *(`SPEC_PROTOCOL.md §4.1`)*

Stated concretely, satisfying I1–I5 simultaneously: a single `validate.py` module exposes
`validate(casepack) -> list[Finding]`, where `Finding` carries `code`, `severity`, `file`,
`field`, `message` and `fix` — `fix` non-empty is enforced at construction, which satisfies
**I1** by making a fix-less ERROR unconstructible rather than merely discouraged. The CLI
renders that list to text (§5.4) or, under `--json`, `json.dumps` of the same list —
one producer, two renderers, so **I5** cannot drift from the human output. Exit code is
`1 if any(f.severity == ERROR) else 0`, giving **I2** and **I3** from one expression.
All displayed strings come from a message catalogue keyed by code, or from the pack's own
`labels.yaml`, never from a hardcoded case name, satisfying **I4**.

> **Corrected v1.2, three stale claims** (`1.2-017`, and the auditor's Part C read).
> The route the build actually takes is sound and satisfies I1–I5 simultaneously, but this
> paragraph described it wrongly in three places, and a compliant route that misdescribes
> the compliant implementation is not doing its job.
>
> 1. **Messages do not come from `labels.yaml`.** They live in
>    `validate_messages.yaml`, a validator-owned catalogue, because 1.1's **I2** forbids
>    displayed English in `app/casepack/*.py` and this module's entire output is displayed
>    English. `labels.yaml` is the *pack's* vocabulary and cannot carry validator copy —
>    a broken pack may not have a readable one.
> 2. **`--json` is not `json.dumps` of the same list in every mode.** Directory mode
>    reorders and drops pack attribution (`1.2-005`), so the guarantee holds in
>    single-pack mode only. That is a build defect against this paragraph, and the
>    paragraph is the thing it is measured against — it stands as written, and the build
>    is what changes.
> 3. **`Finding.__post_init__` is the mechanism that delivers I1**, not the grep in §6.
>    See I1's corrected check.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Should `WARN` block a *production* section while allowing a draft? | **Default: no — WARN never blocks.** A blocking warning is an error under another name. 5.6 surfaces warnings to the instructor; the decision to run anyway is theirs | Record |
| **O2** | Validate cross-pack uniqueness of `pack_key`? | **Default: yes, when given a directory of packs**; skip for a single pack | Record |

---

## 5. Design

### 5.1 Structural checks — ERROR

Inherited from 1.1 §6 as **emitted codes in their own right — `I3` and `I8`** — plus the
E-codes below.

> **Corrected v1.2** (`1.2-003`). §7 of v1.1 asserted that *"E01–E11 is a superset of the
> six"*. It is not. Four of 1.1's six check functions map onto E-codes — I4→`E01`, I5→`E03`,
> I6→`E05`, I7→`E04` — but **`I3`** (snake_case machine keys) and **`I8`** (YAML round-trip)
> have no E-code anywhere in E01–E12 or E20–E23. Had the builder believed §7's sentence,
> two inherited invariants would have been silently dropped from the validator. It followed
> §5.1's *"inherited from 1.1 §6"* instead and emitted them under their 1.1 identifiers,
> which was correct. They are now named here explicitly so 1.3's authors and 5.6's UI know
> the code list is `E00`–`E14` · `E20`–`E23` · `W01`–`W07` · **`I3` · `I8`**.

```
E00  a pack file is missing or cannot be parsed
     (ratified v1.2, §3 decision 8 — a broken pack, not a broken validator,
      so it is an ERROR and exit 1, never the exit 2 reserved for our own failure)
E01  a required_role no catalog item can fill
E02  a required_entity at a level_of_detail no catalog item can own
E03  strategy capability_weights do not sum to 1.0 (±0.001)
E04  demand_curve length ≠ pack.rounds
E05  cleared_by references an unknown action type
E06  event precondition references an unknown signal, capability, or entity
E07  a label key referenced anywhere is absent from labels.yaml
E08  a persona bound to an archetype outside the platform's 14
E09  must_feed / must_be_fed_by names a capability that does not exist
E10  duplicate key within any collection
E11  schema_version newer than this validator understands
E12  a watch rule carrying neither warn_above nor critical_above — it can never
     fire, so it is not a watch rule (§3 decision 7)                    NEW v1.2
E13  a reference inside initial_state that resolves to nothing — a declared
     strategy, capability, unit or catalog key that the pack does not define
                                                                        NEW v1.2
E14  an authored figure in initial_state contradicting one derived from the
     same pack, beyond a stated tolerance                               NEW v1.2
E15  a policy option value, or a non-null default, that is not a valid
     snake_case machine key (an empty string included)                  NEW v1.4
E16  a policy options list that names the same value twice               NEW v1.4
E17  a policy default that is not one of its declared options — the precise
     form of the model-load failure that used to collapse to E00        NEW v1.4
E18  any closed model vocabulary (a Literal or StrEnum field) set outside its
     range — entities.sensitivity, stakeholders.stakeholder_type,
     provenance.source, catalog.rgt_tag, watch_rules.metric_kind, and any
     field like them added later                                        NEW v1.6
```

> **`E18` closes finding `CU-001`.** `E15`–`E17` and `E29` each pre-empt ONE family of
> closed-vocabulary value before the load; every OTHER `Literal`/`StrEnum` field still made
> `models.py` refuse the whole pack and collapsed to a single opaque `E00` naming no field,
> against a file that parsed perfectly (`GOVERNANCE 4.10`). `E18` closes the **class**: it
> reads pydantic's own error report on the load-failure path, which knows the exact field,
> the bad value and the allowed set for every enum failure — present, future, or nested —
> so no closed vocabulary can collapse to `E00` again. It restates no vocabulary: `allowed`
> comes straight off the model. Two independent bad values now both surface as `E18`, and an
> `E18` no longer hides an independent `E03`/`E04`/`E15`.

> **`E15`–`E17` close finding `1.2-RA-003`.** `PolicyOption.options` is a plain `list[str]`,
> so the model never checked its shape — empty, non-snake or duplicated option keys loaded
> silently. And the one policy rule the model *does* enforce (`default` ∈ `options`) raised a
> `CasepackLoadError` that reached the instructor as a single opaque `E00`, hiding every other
> finding in the pack. `E15`/`E16` are the validator's only line on malformed vocabularies;
> `E17` runs on **raw YAML before the load** (like `E03`/`E04`), so a bad default is reported
> precisely and **co-reports** with the other raw-stage checks instead of collapsing. A
> model-load failure whose cause is a policy default no longer suppresses an independent
> `E03`/`E04`/`E10`/`E11`/`E15`/`E16`.

> **`E13` and `E14` close the hole `1.2-014` found.** `initial_state` is 14 fields deep and
> **not one check reads any of it.** The auditor demonstrated a pack that names a strategy
> that does not exist, a capability that does not exist, and holds more capital than it has
> — validating clean, exit 0.
>
> `E14`'s first instance is live on `main` today: Riverside's
> `budget.capital_remaining: 44000` against `review.capital_available 220000 −
> review.capital_committed 174000 = 46000`. That is `CG-6` — logged as *"round-3 capital
> authored in two places"* — and the two places **already disagree by 2,000.**
>
> `E13` is the cheaper and more general of the two and should be built first. Both must
> land **before 1.3 regenerates `initial_state` wholesale**, or 1.3 will author into an
> unchecked structure exactly as 1.1 did.

### 5.2 Coherence checks — ERROR

```
E20  a capability with no watch rule CARRYING AT LEAST ONE THRESHOLD — it can
     never raise a signal, so it is invisible to responsiveness scoring and
     effectively unmanaged                                      WIDENED v1.2
E21  an event whose preconditions can never all be true simultaneously
E22  a strategy whose highest-weighted capability has no catalog path to full coverage
E23  a management question requiring an entity/level no catalog item can produce
E24  an obligation reading a policy switch the pack does not define        NEW v1.4
E25  an obligation protecting an entity the pack does not define           NEW v1.4
E26  an obligation whose permissive_value is not a declared option of its
     policy — it would watch for a switch position that cannot occur       NEW v1.4
E27  an obligation cleared_by referencing an unknown action type           NEW v1.4
E28  an obligation arming an event the pack does not define                NEW v1.4
E29  an event precondition that is not one exact known shape, in any of four
     ways: (1) an unknown type; (2) a missing required field; (3) a field
     belonging to another type; (4) a field set outside its own closed
     vocabulary (placement, severity) — the `E29_vocab` variant, which runs
     on raw YAML before the load so it does not collapse to E00     NEW v1.5
```

> **`E29` has four behaviours, and they are variants of one code by design.** All four are
> the same defect — *"this precondition is not one exact known shape"* — so inventing a code
> per behaviour would break `I1`'s set equality for no gain. The one that runs before the
> load (`E29_vocab`, behaviour 4) mirrors `E17`: a `Literal` field set out of range would
> otherwise refuse the whole pack as `E00`. Because the behaviours ride under one code, they
> are held by a **second** invariant, not `I1`: `catalogue()["variants"]` is checked
> set-equal against the variants the spec names (finding `CU-002` — `I1` counts codes only,
> so a new variant used to be able to appear with no spec change and no fixture). The
> variant register is in **§6** (invariant `I1v`).

> **`E24`–`E28` close finding `1.2-RA-001`.** `obligation_rules.yaml` is loaded
> (`loader.py:27,89`) but no check read it, so a nonexistent entity, policy, permissive
> value, action or armed event reached the event and scoring engines while
> `validate_casepack` stayed green. An obligation reuses the signal machinery entirely
> (1.5 decision 7), so a dangling reference is the same class of defect `E05`/`E06`/`E09`
> already catch for watch rules and events — in the one shipped section that had no checks.
> `E26` is the coherence half `CONTRACTS.md`'s `PolicyOption.options` / `permissive_value`
> entry calls for: the permissive value must name a declared option, checked only when the
> policy resolves and declares options.

E20 is the one most likely to be hit by a real author and least likely to be noticed
without it.

> **Why it widened** (`1.2-001`). E20's purpose has always been written as *"it can never
> raise a signal."* Its predicate was *"appears in no watch rule."* Those are not the same
> test, and Riverside sits exactly in the gap: `firm_infrastructure` **has** a watch rule,
> `sec_identity_01`, whose thresholds are both `null`. E20 stayed silent on it. Riverside
> has **six** signal-mute capabilities and the check reported five.
>
> The consequence was not the miscount. It was that **`CG-1`'s closure condition became
> gameable**: *"a watch rule for every capability — validator E20 clean"* can be satisfied
> by authoring five more rules shaped like `sec_identity_01`, turning the gate green with
> seven of seven capabilities still unable to raise a signal. The gate would have certified
> the precise condition it exists to prevent, and it would have done so at 1.3 — the packet
> that authors watch rules. `E12` plus the widened `E20` close both halves.

**A schema gap this ruling exposes, for 1.5 and not for here.** `sec_identity_01`'s metric
is `missing_identity_access` — a **presence** condition, not a magnitude, so there is no
threshold to author and the rule was written thresholdless because `WatchRule` offers no
other shape. Under decision 7 it is now illegal, and it has no legal form. Riverside's
`wh_rollout_01` (metric `adoption`) is the same case.

This spec does **not** invent that shape. It records the requirement: **1.5 must settle how
a presence-style watch rule expresses its trigger**, and 1.1's `WatchRule` must then carry
it. Until then, both rules are illegal and 1.3 must not author more of them. Filed as the
disposition of `1.2-013`, which is the same root: two of Riverside's three event cards wait
on `critical` from a rule that can never reach it, leaving a deck of **one**.

### 5.3 Seed-quality heuristics — WARN

Directly from the harvest's findings (`design/01` §4), where `business_process_mapping`
showed identical `ideal_value 85.00` and identical weights across all six stakeholders —
placeholder seeding indistinguishable from authored judgement.

```
W01  ≥6 preference rows share an identical (ideal, weight) tuple
     → "looks like placeholder seeding, not authored judgement"
     N BOUND TO 6 in v1.2 — the smallest value that fires on the six-stakeholder
     business_process_mapping case in design/01 §4 that §8 step 3 requires it to
     catch. Recorded so it is known that five identical rows pass.
     GENERALISED v1.4 — the ideal is whichever of `ideal_value` (legacy
     catalog/platform/training overrides), `ideal_posture` (policies) or
     `ideal_tier` (services) a row carries, found by walking every domain by its
     semantic fields rather than by one legacy shape (finding 1.2-RA-002).
W02  a capability no strategy weights above 0.05 — content nobody will engage
W03  an event with no strategy_affinity — it will fire regardless of declaration
W04  a catalog item reachable from no capability — dead content
W05  the deck holds fewer event cards than the pack has rounds     REWRITTEN v1.2
W06  every training option has coverage 1.0 — the tier choice is not a choice
W07  no accepted-risk / no decoy in true_cost_categories — TCO forecast is trivially winnable
W08  a strategy fewer than `pack.metadata.rounds` event cards can be dealt to —
     the per-strategy draw check of 1.5 §5.2a and O4                    UPDATED v1.5
```

> **`W05` rewritten to what the schema can express** (`1.2-016` item 3). v1.1 wrote *"the
> deck contains no event for a round"*, but `Event` carries **no round field** — the spec
> described a check the schema cannot support. That is a spec/schema conflict the builder
> should have stopped on under `GOVERNANCE §7`; it shipped the deck-depth proxy instead and
> declared it, which the auditor ruled adequate and honestly labelled. The proxy is now the
> specified check.
>
> **It is weaker than the original intent, and the gap is named rather than papered over:**
> deck depth will not catch a six-card deck whose cards are all affine to one strategy,
> which is `CG-2`'s actual shape — *"strategies that draw nothing"*. Catching that needs
> either a round binding on `Event` or a per-strategy draw check. **Both are 1.5's to
> settle**, and `CG-2` stays open at 1.3 regardless of `W05` passing.

### 5.4 Output

**Rewritten in v1.2.** The v1.1 sample was wrong in three ways, and because a sample is a
picture it beat the written decisions it contradicted — the build followed it twice.
`1.2-007`, `1.2-009`, `1.2-010`.

**The locator line leads with the business name; the field path follows it.** An instructor
reads the first line first, and `firm_infrastructure.required_entities.user_account` is a
schema path they cannot parse. The path is genuinely useful to whoever opens the YAML, so it
is kept — moved, not deleted.

```
$ validate_casepack packs/riverside_grocery

  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  3 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  ERROR  E02  Customer Service               capabilities.yaml:41
         Needs customer data at individual level. No catalog item can hold it.
         Fix: add a catalog item with owns_entities CUSTOMER at individual_record,
              or lower min_level_of_detail.
         Field: customer_service.required_entities.customer

  ERROR  E20  Financial Reporting            watch_rules.yaml
         Nothing watches it, so it can never raise a signal and no team can be
         scored on responding to one.
         Fix: add a watch rule in watch_rules.yaml naming this capability, with
              warn_above or critical_above set.

  ERROR  E12  Warehouse rollout watch rule   watch_rules.yaml:8
         Has neither a warning nor a critical threshold, so it can never fire.
         Fix: set warn_above or critical_above, or remove the rule.
         Field: wh_rollout_01

  WARN   W01  Catalog preferences            preferences/catalog.yaml
         18 rows share (ideal_value 85.00, weight 0.80). Looks like placeholder
         seeding rather than authored judgement.
         Fix: author the rows that differ, or state in provenance why they agree.

  3 errors · 1 warning · exit 1
```

Three corrections to note against v1.1's sample, each of which the build inherited:

| v1.1 sample | Defect | Finding |
|---|---|---|
| `WARN  … financial_reporting has no watch rule` | Renders **E20's exact condition at WARN**, contradicting decision 5 added by the same amendment. The summary line was wrong on its own terms too — as an ERROR that run reads `2 errors · 1 warning` | `1.2-010` |
| WARN blocks carry no `Fix:` line | Contradicts decision 3, *"every check names its fix"*. The build printed `fix` for ERROR only, so every warning reached the instructor as a problem with no action — while `--json` carried the fix all along | `1.2-009` |
| `capabilities.yaml:41  customer_service` | Machine key and field path lead the line; the business name appears nowhere on it | `1.2-007` |

---

## 5.5 Seed — real fixture packs *(GOVERNANCE §4.9)*

```
seed        backend/tests/fixtures/packs/
              minimal_valid/     a small COHERENT pack that passes clean
              broken_<CODE>/     one per error code, minimally broken
command     validate_casepack backend/tests/fixtures/packs/<name>
demonstrate exit 0 on minimal_valid · exit 1 with the named error on each broken pack
            EXIT 1 on the real riverside_grocery, per §9.1        CORRECTED v1.2
```

> **Corrected v1.2.** This block still read *"exit 0 on the real riverside_grocery"* — the
> third surviving copy of the acceptance criterion v1.1 replaced in §9.1, and the v1.1
> changelog did not sweep for it. Riverside is expected to **fail**; see §9.1.

`minimal_valid` is real content, not empty scaffolding — a two-capability company that
would actually run.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | **Every code this spec names is implemented**, and every ERROR carries file, field and fix | compare the code set emitted by `catalogue()` against the codes named in §5.1, §5.2 and §5.3 | **set equality**, no extras and no absences |
| I1v | **Every message variant this build carries is named in the register below**, and vice versa | compare `catalogue()["variants"]` against the variant register in this section | **set equality**, no extras and no absences |
| I2 | Exit 1 whenever ≥1 ERROR | run against a deliberately broken pack | exit 1 |
| I3 | Exit 0 with warnings only | run against a warn-only pack | exit 0 |
| I4 | No pack-identity branching | `grep -rniE "riverside\|grocer" backend/app/casepack/validate*` | zero |
| I5 | `--json` is parseable **and carries the same findings, in the same order, as the text renderer — in every mode, directory mode included** | diff the code/file/field/message tuples from both renderers, on a single pack **and on a directory of packs** | identical sequences |

> **I1 rewritten in v1.2** (`1.2-017`). Its old check counted `Fix:` prefixes in
> `validate_messages.yaml` against the ERROR-code count read from *the same file* — adding a
> code incremented both sides, so it could never fail on the dimension its name describes.
> It passed at 18 = 18 while the spec named 15. The property it appeared to guard — a
> spec-named code that was never implemented — was exactly what it could not see. The real
> guarantee that no ERROR ships without a fix is `Finding.__post_init__`, which makes such a
> Finding unconstructible; that is a construction, not a check, and §3.1 is where it belongs.
>
> **I5 tightened in v1.2** (`1.2-005`). "Parseable" was too weak: directory mode dropped pack
> attribution and reordered relative to the text output, and still satisfied `json.tool`.
> Since 5.6's instructor view consumes directory mode, the guarantee has to hold there most
> of all.

> **`I1v` added by finding `CU-002`.** `I1` counts `catalogue()["codes"]` only, so a code's
> *behaviours* — its message variants — were invisible to it: the catch-up packet added
> `E29_vocab` (E29's fourth behaviour) with no spec change and no fixture, and `I1` stayed
> set-equal the whole time. A variant is a distinct thing the validator can say; it is now
> held set-equal against a register the spec owns, so a new one cannot appear silently.

### Variant register

A **variant** is an alternate message under an existing code, used when one code has more
than one authored behaviour. Each is set-equal against `catalogue()["variants"]` by `I1v`.

```
E10_pack_key       E10 when two packs in a directory share a pack_key
E15_default        E15 when the malformed value is the DEFAULT, not an option
E26_no_options     E26 when the referenced policy declares no options at all
E29_vocab          E29 behaviour 4: a precondition field outside its closed vocabulary
```

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.1 merged; `casepack/models.py` and `checks.py` exist | `[V]` | `ls backend/app/casepack/` | both present |
| 2 | Riverside loads and parses under 1.1 | `[V]` | `python3 -c "from app.casepack.loader import load_casepack; p=load_casepack('packs/riverside_grocery'); print(p.metadata.pack_key, len(p.capabilities), len(p.watch_rules))"` | prints `riverside_grocery 7 3`; **and the same call against a nonexistent path must raise** |
| 3 | 1.1's `checks.py` exposes **six** check functions, covering I3–I8 | `[V]` | `grep -c "^def check_" backend/app/casepack/checks.py` | exactly `6` |
| 4 | The action-type set for E05 exists as `ACTION_TYPES` | `[V]` | `grep -n "^ACTION_TYPES" backend/app/casepack/checks.py` | found at line 12, 10 values |

> **Rows 3 and 4 were corrected 2026-08-14.** As authored they were both wrong against
> merged 1.1, and each would have stopped the builder on a false FAIL.
>
> **Row 3** expected eight functions; there are six. 1.1's I1 (no pack-identity branching)
> and I2 (no displayed English in engine code) are **static grep invariants over the source
> tree**, not predicates over a parsed `Casepack` — they cannot be functions here, which is
> why the count is six and not eight. Nothing is missing; six is the expected number, not a
> shortfall.
>
> ~~E01–E11 is a superset of the six regardless, so this packet implements the remainder
> itself.~~ **Struck in v1.2** (`1.2-003`) — the superset relation does not hold. `I3` and
> `I8` have no E-code, and this sentence would have justified dropping them. See §5.1.
>
> **Row 2 was corrected in v1.2** (`1.2-004`). v1.1 corrected the two rows that returned the
> *wrong* answer and left the one row that could not return one: `loader.py` has no
> `__main__`, so `python -m app.casepack.loader <anything>` exits 0 for a valid pack, a
> nonexistent pack and no argument alike. The row reported PASS against a pack that does not
> exist. `SPEC_PROTOCOL §4` requires an invariant to ship its falsification check; a
> pre-flight row that cannot fail is that defect one level up. The replacement is the check
> the builder actually ran — it substituted a working call, pasted its output honestly, but
> did not declare the substitution, which is how the vacuous row survived the one pass that
> would have caught it.
>
> **Row 4** grepped for `action_type|ActionType` and found nothing, because the set is
> named `ACTION_TYPES`. It exists. Do **not** declare a new one.

---

## 8. Build steps

1. **Structural checks** E01–E11 wrapping 1.1's `checks.py`. *Verify:* each fires against a
   purpose-broken fixture; paste output.
2. **Coherence checks** E20–E23. *Verify:* same, one fixture per code.
3. **Heuristics** W01–W07. *Verify:* W01 fires against the real
   `business_process_mapping` shape from `design/01` §4.
4. **CLI + output formatting + `--json`.** *Verify:* I1–I5.
5. **Fixture suite** — one minimal broken pack per error code, under
   `backend/tests/fixtures/packs/`. *Verify:* every code has a fixture; a code with no
   fixture is untested and is a finding.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–4 | | |
| `E00`–`E14` implemented, each with a fixture | | |
| `E20`–`E23` implemented, each with a fixture | | |
| `I3`, `I8` emitted as codes | | |
| `W01`–`W07` implemented, `W05` in its §5.3 deck-depth form | | |
| CLI output matches §5.4 shape — business name leading, `Fix:` at **every** severity | | |
| `--json` mode, including directory mode (I5) | | |
| I1–I5 | | |
| O1, O2 recorded | | |
| `ARCHETYPES` relocated to `checks.py` beside `ACTION_TYPES` | | |
| **Seed** — fixture packs, one per error code, all exercised | | |
| **Riverside fails with exactly the known content gaps, and no others** — see §9.1 | | |
| Browser / auth / instance canaries | | **N-A** — headless CLI |
| Re-run sequence for the auditor | | see §9.2 |

### 9.2 The auditor's re-run sequence *(added v1.2, `1.2-018`)*

1.1 shipped a `verify.md` naming the CLI sequence an auditor re-runs; 1.2 shipped none, and
`SPEC_PROTOCOL`'s anatomy requires a stated disposition when the browser rung does not apply.

**The disposition is that `backend/tests/check_fixture_matrix.py` is that artifact**, and it
is a better one than a `verify.md` would have been: it is executable rather than prose, it
asserts codes *and* exit codes, and it fails if a declared code has no fixture. The auditor
re-ran it unmodified and it held.

No `verify.md` is required for this module. The DoD row is satisfied by the matrix script
running clean from a fresh checkout, plus the three §9.1 invocations.

### 9.1 What "done" means against the real Riverside pack

**Amended 2026-08-14.** The original DoD carried two rows — *"Riverside skeleton validates
(errors only where 1.3 will fill stubs)"* and *"Real Riverside pack validates clean"*.
Both were stale, and together they were unsatisfiable:

- The **skeleton** row predates 1.1. 1.1 shipped **real content** under `GOVERNANCE §4.9`,
  not a skeleton of stubs. There is no skeleton to validate.
- The **clean** row contradicts `E20`. Riverside declares **7 capabilities** and
  **3 watch rules covering 2 of them** — `order_fulfilment` and `firm_infrastructure`.
  The other five raise `E20` by construction. This is `CG-1`, logged in
  `findings/content-coverage-2026-07-27.md` and owned by **1.3, which has not run.**
  No build of 1.2 could satisfy both rows.

**The replacement gate.** A validator that reports the defects we already know are there is
a validator that works. The build is done when:

```
validate_casepack backend/packs/riverside_grocery   →   exit 1

  and every error it reports is traceable to a logged content gap:

  6 × E20   store_operations · financial_reporting · customer_insight ·
            marketing_sales · service          — no watch rule at all
            firm_infrastructure                — watched only by a rule that
                                                 carries no threshold        → CG-1
  2 × E12   wh_rollout_01 · sec_identity_01    — neither threshold set       → CG-1
  1 × E14   budget.capital_remaining 44000 vs review's derived 46000         → CG-6
```

> **§9.1 was itself wrong in v1.1, and this is the correction** (`1.2-002`). The gate above
> replaced an unsatisfiable pair — then predicted four lines of output, **three of which the
> check set provably could not produce.** `CG-2` surfaces as `W05`, a *warning*, so it never
> reaches "errors it reports" at all. `CG-5` was uncatchable because `obligation_rules.yaml`
> is not a section 1.1's schema defines, so its absence is not a missing file. `CG-6` was
> uncatchable because nothing read `initial_state`.
>
> The v1.1 gate could therefore be satisfied only by invoking its own escape clause. That is
> `SPEC_PROTOCOL §4.1`'s failure again in a quieter register, and it is the
> `GOVERNANCE §6.1` blind spot in textbook form: the author who wrote the CG list, the check
> set **and** the acceptance criterion did not notice that the first two do not intersect on
> three of four rows. It took an independent read to see it.
>
> **What changed.** `E13`/`E14` make `CG-6` catchable, so it stays in the gate. `CG-1`'s line
> is corrected from five to six and gains its `E12` half. `CG-2` and `CG-5` are **removed
> from the error gate** and restated below as what they actually are.

**`CG-2` and `CG-5` are not errors and must not be gated as such.**

- **`CG-2`** surfaces as `W05` — a warning, exit code unaffected. It is *reported*, not
  *gated*, and `W05` in its rewritten deck-depth form cannot see CG-2's real shape anyway
  (§5.3). It closes at 1.3, not here.
- **`CG-5`** is invisible to every check in §5.1–§5.3 and will stay invisible until
  `obligation_rules.yaml` is a schema section. **That is 1.1's to add**, and until it exists
  no validator can report its absence. Recorded here so the silence is known to be a gap
  rather than a pass.
- **`CG-3`** (project duration) and **`CG-4`** (policy switches) are likewise uncatchable
  today, for the same structural reason.

**Any error not traceable to a logged CG is a finding against 1.1**, and is reported rather
than fixed — 1.2 does not repair packs (§1, out of scope). Likewise, a CG that the
validator **fails to catch** is a finding against this spec: the check set is incomplete.
Both dispositions were exercised on the v1.1 build and both produced real findings, which is
the evidence that this gate shape works even when its individual lines were wrong.

**Clean-Riverside moves to 1.3's exit gate**, where the content gaps are actually closed.
This is consistent with `GOVERNANCE §5`: *"No casepack reaches a section until
`validate_casepack` passes clean"* — no section exists yet, and none can until Phase 2.

---

## 10. Changelog

**v1.6 — 2026-08-22, findings CU-001 / CU-002 / CU-003.** Adds `E18`: every closed model
vocabulary (a `Literal` or `StrEnum` field) set out of range now names its file and field
instead of collapsing the whole pack into an opaque `E00`. It closes the *class* that
`E15`–`E17` and `E29` each closed one instance of, by reading pydantic's own error report on
the load-failure path — so `sensitivity`, `stakeholder_type`, `source`, `rgt_tag`,
`metric_kind` and any future closed field are covered without restating a vocabulary. `E29`'s
four behaviours are enumerated in §5.2 and the schema guide, and a new invariant `I1v` holds
`catalogue()["variants"]` set-equal against the §6 variant register, so a code's behaviours
can no longer drift invisibly to `I1`. `test_label_routing.py` makes the B5 label-display
contract executable in both halves — business-label routing and the `misc` narrowing — each
proven to fail on revert. `broken_E18` fixture added; I1/I5 keep their guards; no invariant
moved or was dropped.

**v1.5 — 2026-08-21, 1.5 readiness closeout.** Adds `E29` for the closed eleven-type precondition vocabulary and exact per-type fields, including the frozen `placement` and `other_policy` shapes. W08 now derives its minimum from `pack.metadata.rounds`; empty affinity still counts for every strategy and still raises W03. The fixture matrix, focused shape/round tests, catalogue and schema guide change together. I1/I5 keep their numbers and guards; no invariant moved or was dropped.

**v1.4 — 2026-08-21, post-audit.** Amended against
`handoffs/rework/1.2-validator-audit-2026-08-21.md`, which returned **PASSING SUITE,
INCOMPLETE CONTRACT COVERAGE** — the 29-row matrix passed and Riverside was clean, but three
shipped domains were outside the validator's reach. All three findings are closed in this
build (spec + code + fixtures + catalogue + matrix together, `GOVERNANCE §8`).

| Change | Why |
|---|---|
| Header code list `E00`–`E14` → `E00`–`E17`, `E20`–`E23` → `E20`–`E28`; version v1.3 → v1.4 | Eight codes added; `GOVERNANCE §8` binds the bump and the enumerated list together (the omission `1.2-033` was filed for) |
| §5.1 gains `E15`–`E17` (policy value vocabulary) | `1.2-RA-003`: malformed/duplicate/non-snake option vocabularies were unchecked, and a default-outside-options error collapsed the whole pack into an opaque `E00`. `E17` runs on raw YAML so it co-reports instead of hiding independent errors |
| §5.2 gains `E24`–`E28` (obligation references) | `1.2-RA-001`: `obligation_rules.yaml` loaded but nothing validated its entity/policy/permissive-value/action/event references; a dangling reference reached the event and scoring engines while the validator stayed green |
| §5.3 `W01` generalised from `ideal_value` to any of `ideal_value`/`ideal_posture`/`ideal_tier` | `1.2-RA-002`: W01 read only the legacy `defaults_by_archetype`+`ideal_value` shape and was blind to `preferences/policies.yaml` and `preferences/services.yaml`, which nest ideals under `by_decision`. It now walks every domain by semantic fields |
| Eleven fixtures added (nine broken, one paired-valid, one by-decision warn) | §8 step 5 — a code with no fixture is untested; `broken_policy_aggregate` demonstrates E17+E03 co-reporting; `warn_W01_by_decision` demonstrates the generalised traversal |

**Post-audit corrections** (`findings/1.2-validator-rework-2026-08-21-audit.md`, PASS WITH
FINDINGS, both mechanical): `1.2-VR-001` — `E26` now also fires when an obligation's policy
declares **no** options at all (its `permissive_value` then names nothing), via the
`E26_no_options` catalogue variant; `1.2-VR-002` — a malformed **default** is reported against
the `default` field with a default-specific message (`E15_default` variant), not lumped into
`options`. Both are catalogue variants, not new codes, so the code list and `I1` are
unchanged. Two fixtures added (`broken_E26_no_options`, `broken_E15_default`) and a
field-locator assertion (`check_field_locators`) now guards that a finding names the field an
author must edit, not only the code.

**No invariant changed and no guard moved** (`R2`). `I1` reads the header code-list line and
holds it against `catalogue()`; the header and §5.1–§5.3 were updated together so I1 stays
set-equal. `I5` (text/JSON parity) is unaffected — the new findings flow through the one
producer both renderers consume. **R1:** no build cycle is open against v1.3; this lands on
the branch the rework is built on, and this DoD names what changed.

**v1.3 — 2026-08-18.** Closes `1.2-033`. The versioned code list gained `W08` during the
second rework and the version was not bumped, so the spec pointed at a code list it did not
declare — `GOVERNANCE §8` requires the bump and the changelog entry together, and the rework
instruction that authorised the edit had explicitly forbidden both (`1.2-032`).

| Change | Why |
|---|---|
| Header: `W01`–`W07` → `W01`–`W08`, version v1.2 → v1.3 | `W08`, the per-strategy draw check, shipped in the second rework |
| This entry | `GOVERNANCE §8` — a contract change is merged into the living document with a version bump and a changelog entry, never left implicit |

**No invariant changed and no guard moved** (`R2`). `I1` reads the header code-list line as
its authority, which is why the header and §5.3 must agree — and why the one-line
authorisation that produced this defect had no compliant route.


**v1.2 — 2026-08-14, post-audit.** Amended against
`findings/1.2-2026-08-14-audit.md`, which returned **substance PASS WITH FINDINGS · spec
FAIL · process PASS**, 0 blocking. Ten of the nineteen findings were against this spec; all
ten are dispositioned below.

**R1 disposition.** The build cycle is not open — the builder has reported and the auditor
has filed. No agent is mid-build against v1.1. This lands on `main`; the rework dispatch
reads v1.2 from there and its `dod.md` names the steps v1.1 invalidated.

**R2 disposition.** No invariant was renumbered. **I1 and I5 keep their numbers and both had
their checks rewritten** — I1's guard *moved* out of the invariant table entirely, to
`Finding.__post_init__` in §3.1, and what I1 now guards is a different property (spec-named
codes are all implemented). I5's guard was *widened*, not moved. Nothing else changed hands.

**R5 disposition — this amendment closes no build finding.** Spec changes prevent
recurrence; artifacts need repair. `1.2-005`, `1.2-006` and `1.2-015` are against the build
and are untouched by this document. Neither are the code changes v1.2 *requires*: `E12`,
`E13`, `E14`, the widened `E20`, the new output shape, `Fix:` at every severity, the
relocated `ARCHETYPES` and the rewritten I1/I5 checks are all unbuilt. **A rework packet
follows; v1.2 is its input, not its substitute.**

| Finding | Change | Disposition |
|---|---|---|
| `1.2-001` | §3 decision 7 · `E12` added · `E20` widened to *"no rule carrying at least one threshold"* | **Closed by ruling.** Thresholdless watch rules are illegal — user, 2026-08-14 |
| `1.2-002` | §9.1's gate rewritten: `CG-1` corrected 5→6 plus its `E12` half, `CG-6` gated via `E14`, `CG-2`/`CG-5` removed from the error gate and restated | Closed in spec |
| `1.2-003` | §5.1 names `I3` and `I8` as emitted codes; §7's superset sentence struck | Closed in spec |
| `1.2-004` | Pre-flight row 2 replaced with a check that can fail | Closed in spec |
| `1.2-007` | §5.4 leads with the business name; field path moved below the fix | Spec closed, **build rework required** |
| `1.2-009` | §3 decision 3 binds every severity; §5.4 sample shows `Fix:` on WARN | Spec closed, **build rework required** |
| `1.2-010` | §5.4 renders E20 as ERROR; summary line corrected | Closed in spec |
| `1.2-014` | `E13` and `E14` added for `initial_state` | Spec closed, **build rework required** |
| `1.2-017` | I1 rewritten to compare implemented codes against spec-named codes | Spec closed, **build rework required** |
| `1.2-018` | §9.2 — `check_fixture_matrix.py` is the re-run artifact; no `verify.md` needed | Closed in spec |
| `1.2-016` items 1, 2, 3, 5 | §3 decisions 8 and 9; §5.3 `W05` rewritten and `W01`'s N bound to 6 | Author rulings given |
| — | §5.5's *"exit 0 on the real riverside_grocery"* corrected | Fourth surviving copy of the criterion v1.1 replaced |

**Carried out of this packet, owned elsewhere:**

| Item | Owner | Why |
|---|---|---|
| `WatchRule` must reject a thresholdless rule at construction | **1.1** | A schema constraint belongs in the model; 1.2 detects, it does not repair |
| How a presence-style watch rule expresses its trigger | **1.5** | `missing_identity_access` and `adoption` have no legal form under decision 7, and this spec does not invent one |
| `obligation_rules.yaml` as a schema section | **1.1** | Until it exists, `CG-5` is structurally invisible |
| `CG-1`'s closure condition restated as *"a watch rule carrying at least one threshold for every capability"* | **1.3** | The logged wording is gameable; see `1.2-001` |
| `CG-2`'s real shape — a deck no strategy draws from | **1.5** | Needs a round binding on `Event` or a per-strategy draw check |
| `1.2-008`, `1.2-011`, `1.2-012`, `1.2-013` | **1.1 / 1.3** | Pack and schema defects the validator correctly reported |

---

**v1.1 — 2026-08-14, pre-dispatch.** Amended by the author against merged 1.1 before any
builder was dispatched; no build cycle was open, so `handoffs/README.md` **R1** does not
apply. No invariant was renumbered — **R2** requires the statement, so: I1–I5 keep their
numbers and their guards, and no guard moved.

| Change | Why |
|---|---|
| §3 decision 5 — E20 stays ERROR | Settled by the user 2026-08-14 against the alternative of downgrading it to WARN |
| §3 decision 6 — `ACTION_TYPES` already exists | Prevents the builder declaring a second, competing vocabulary |
| §3.1 — one compliant route added | `SPEC_PROTOCOL §4.1` requires it and v1.0 shipped without it |
| §7 rows 3, 4 corrected | Both were false against merged 1.1; each would have stopped the builder on a spurious pre-flight FAIL |
| §9 two rows replaced by one, plus §9.1 | The pair was jointly unsatisfiable — the exact failure `SPEC_PROTOCOL §4.1` exists to prevent |
