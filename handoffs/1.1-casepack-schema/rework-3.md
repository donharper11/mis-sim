# 1.1 — Third Rework Instruction

**Drafted by:** the AUTHOR · **Date:** 2026-08-18
**Branch to cut:** `build/1.1-rework-3`, from **the commit that adds this document** —
`cba47c8`, not the `03e401c` this line originally named. *(corrected 2026-08-18)*
**Scope:** two fields on one model. **Nothing else.**

> `rework.md` (July, closed) and `rework-2.md` (2026-08-17, merged) are different packets.
> Do not edit either. This document is yours.

---

## 1. Why this exists

`1.3-012`, filed by the 1.3 harvest's own hand-check and confirmed by its audit.

`obligation_rules.yaml` — six rules, authored, merged, correct against the shape 1.5 §5.4
specifies — reads `policy` + `permissive_value`:

```yaml
- key: customer_pii_retention
  entity: customer
  policy: data_retention
  permissive_value: indefinite       # <- points at nothing
```

**`PolicyOption` has no value field at all.** Verified on merged `main`:

```python
class PolicyOption(StrictModel):
    key: SnakeKey
    category: SnakeKey
    cost: int = Field(ge=0)
    effects: dict[SnakeKey, float | int | str]
    provenance: Provenance
```

A policy switch has no notion of the states it can be in, so `indefinite` is a string with
no referent. **No keying of policies fixes this** — the audit confirmed the missing thing is
the vocabulary itself, not the naming. The whole Chapter 4 ethics layer is authored,
merged, and inert.

**What breaks without it, concretely:**

- the engine **cannot tell whether a team has moved off the permissive default** — which is
  the entire mechanism by which an ignored obligation arms an event (1.5 §5.4);
- the validator cannot check that `permissive_value` names a real state;
- the Security screen (4.3) cannot render a switch's positions, because nothing enumerates
  them.

---

## 2. The two fields

```python
class PolicyOption(StrictModel):
    key: SnakeKey
    category: SnakeKey
    cost: int = Field(ge=0)
    effects: dict[SnakeKey, float | int | str]
    options: list[SnakeKey] = Field(default_factory=list)   # NEW — the states this switch can be in
    default: SnakeKey | None = None                          # NEW — the state a team holds by NOT deciding
    provenance: Provenance
```

**`options`** is the enumerated vocabulary — for `data_retention`, something like
`[minimal, standard, indefinite]`. Ordering is authoring convention, not semantics; do not
infer strictness from position.

**`default`** is the position a team occupies before it decides anything. It is what makes
the ethics layer **cost something to ignore** rather than being something to opt into. It is
usually the same value an obligation names as permissive — **but the two are distinct
concepts and must stay separate fields.** `default` is where you start; `permissive_value`
is what obliges. A pack may legitimately start a team somewhere already compliant.

### The one constraint, enforced at the model

```
options non-empty  →  default MUST be a member of options
```

Safe to enforce, because **no pack in the repository declares `options` today**, so no
existing pack can violate it. Verify that before you rely on it.

**Do not enforce anything else at the model.** In particular, do **not** require `options` to
be non-empty, and do **not** require `default` when `options` is empty — see §3.

---

## 3. The rule that governs this packet

> **Nothing you do may break the loading of an existing pack.**

**All 29 fixture packs carry `policies.yaml`**, and so does `riverside_grocery`. Making
either field required breaks all thirty: they stop loading, `validate_casepack` reports
`E00` instead of its real result, and `check_fixture_matrix.py` goes red.

This is the same lesson `rework-2.md` §2 recorded for `metric_kind`, and it held there.
**Both fields are optional with defaults that preserve today's behaviour.** A policy with no
`options` is the legacy shape and must load exactly as it does now.

Prohibitions, same as last time and for the same reasons:

- **Do not touch `backend/packs/`.** Declaring Riverside's `options` is **content**, and it
  is 1.3's. `git diff` must be empty.
- **Do not touch `backend/tests/fixtures/`.** Those are 1.2's.
- **Do not touch `validate.py`.** A check that `permissive_value` names a member of
  `options` is 1.2's next packet, correctly sequenced after this one.
- **Do not add a third field**, however tempting. If you believe one is needed, **stop and
  report** — `SPEC_PROTOCOL §3` prefers eliminating a second home to adding one.

---

## 4. Definition of Done

| Item | Evidence required |
|---|---|
| `options` and `default` on `PolicyOption`, both optional | model excerpt |
| The membership constraint, enforced at the model | all four cases constructed: no options; options with a valid default; options with a default **not** in them (**rejected**); options with no default (**accepted**) |
| No pack declares `options` today | the command and its output, run **before** you rely on it |
| **Riverside unchanged: `0 errors · 0 warnings · exit 0`** | before/after, pasted |
| `check_fixture_matrix.py` green, all 29 | pasted, exit 0 |
| `backend/packs/` byte-identical | `git diff 03e401c..HEAD -- backend/packs/` → empty |
| `backend/tests/` and `validate.py` byte-identical | same → empty |
| `docs/casepack-schema.md` updated | both fields, with a worked example and the distinction between `default` and an obligation's `permissive_value`. **An instructor authors packs from this document; a field absent from it is invisible.** |
| 1.1's I1–I8 re-run | pasted |
| **The shape proof** | a scratch pack (NOT under `backend/packs/`) whose policy declares `options` and `default`, and whose obligation's `permissive_value` names one of them: **it must load and validate clean.** That is the thing this packet exists to make possible, and it is the most important line in your report |

---

## 5. What this packet does NOT finish

State this in your report so nobody reads a merged schema as a working ethics layer.

```
1.1 rework-3   the fields exist                    THIS PACKET
1.3 follow-up  Riverside's six policies declare their options and defaults
1.2 follow-up  the validator checks permissive_value against options
```

**The engine can be built as soon as step 2 lands** — 1.5 consumes `options`/`default`
directly, and the validator check is defence in depth rather than a dependency. But until
step 2, `obligation_rules.yaml` stays exactly as inert as it is today, and the merge of
this packet changes no observable behaviour anywhere.

That is expected. Say so plainly rather than letting the clean run imply otherwise.

---

## 6. When you are done

Fill `handoffs/1.1-casepack-schema/dod-rework-3.md` — a new file. Do not overwrite `dod.md`
or `dod-rework-2.md`. Push `build/1.1-rework-3`, verify with `git ls-remote` against your
local HEAD, and report. **Do not merge.**

**Declare every substitution.** Stop and report on anything this document does not settle.

---

## 7. A defect in this instruction — recorded 2026-08-18

§ header named `03e401c` as the branch base. **That is the commit before this document
existed.** Branching there would have cut the branch out from under its own instruction, and
the dispatch prompt — written after this file was committed — correctly named `cba47c8`. The
two documents disagreed, the builder followed the prompt, and it declared the deviation as
substitution 1.

**The authoring slip is structural, not a typo.** I write "branch from `main` @ `<sha>`" while
looking at `main`, then commit the instruction — which moves `main`. Every rework instruction
in this project is written in a state it invalidates by being saved.

**The fix, applied from here on: name the base as *the commit that adds this document*,**
never a SHA read before writing it. A SHA is only correct in a document that is never
committed.

Sixth instance of an instruction naming a route that could not be taken as written, after
1.2's pre-flight rows 3 and 4, 1.5's row 5, 1.3's row 1a, 1.2 rework-2's one-line spec
authorisation, and 1.3's "eliminate the second home".
