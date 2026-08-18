# 1.3 — Content Follow-up: make the decisions land

**Drafted by:** the AUTHOR · **Date:** 2026-08-18
**Branch to cut:** the commit that adds this document, on `main`
**Scope:** pack content only. **No engine code, no schema, no validator.**

> Driven by `design/07-decision-consequence-map.md`, not by an audit. The map applies one
> test — *a decision is real only if a stakeholder holds a view on it, a sub-factor consumes
> it, and it can move a signal or an event* — and two decision classes fail it.

---

## 1. Why this exists

1.3 closed CG-1…CG-6 and took Riverside to a clean validator run. **That proves the pack is
well-formed. It does not prove the decisions land.**

Two of the sim's nine decision classes currently change nothing a student can observe:

| Class | What a student does | What happens |
|---|---|---|
| **Information policy** | spends capital setting six switches | **nothing** — no stakeholder notices, no sub-factor moves, obligations inert |
| **Services** | upgrades support tier | a cost and a reliability number, and no human reaction |

And one class is built end to end and carries nothing: **54 of 75 purchase options complete
in zero rounds**, so *follow-through* — which has a UI, a casepack field and a Management
sub-factor — has almost nothing to score.

**All three are content. None needs a schema change.** The loader reads any YAML in
`preferences/`, and `lead_time_rounds` and `PolicyOption.options` both already exist.

---

## 2. The four items

### 2.1 `preferences/policies.yaml` — NEW FILE · highest value

Six switches × the archetypes that hold a view. Follow the shape of the three files already
in `preferences/`:

```yaml
defaults_by_archetype:
  finance:   {ideal_posture: permissive, weight: 0.9}
  regulator: {ideal_posture: strict,     weight: 1.0}
```

**The design intent, from `design/07 §3.5` — read it before authoring.** The teaching value
is that **stakeholders want incompatible things**, so no setting pleases everyone:

| Archetype | Wants | Because |
|---|---|---|
| `finance` · `c_suite` | permissive, cheap | every switch costs capital and constrains operations |
| `regulator` · `security_auditor` | strict retention, access, logging | it is their job |
| `employees` | strict on `staff_monitoring` **specifically**, indifferent elsewhere | being watched is not free |
| `customer` · `general_public` | strict on collection, retention, egress | it is their data |
| `marketing` | permissive collection | targeting needs data |
| `operations` | permissive access | strict access slows the floor down |

**Author per switch, not one blanket posture.** `employees` caring intensely about
`staff_monitoring` and barely about `data_egress` is the whole point — a single
`ideal_posture` per archetype would flatten exactly the tension this exists to create.

**The sim takes no position.** Every archetype's preference is stated as an interest, never
as a verdict. If any entry reads as "this is the right answer", rewrite it.

### 2.2 Declare each policy's `options` and `default`

`PolicyOption.options` and `.default` landed in 1.1 rework-3 and no pack uses them yet.
Riverside's six switches need vocabularies — and `obligation_rules.yaml` **already names the
permissive value of each one**, so the vocabularies are half-authored already:

```
data_retention   → obligation names 'indefinite'
data_collection  → 'everything_by_default'
data_access      → 'open_to_all_staff'
access_logging   → 'unlogged'
data_egress      → 'unrestricted'
staff_monitoring → 'untracked'
```

Each switch needs its permissive value plus at least one stricter alternative, and a
`default`. **The `default` should normally be the permissive value** — that is what makes
ignoring the screen cost something rather than being an opt-in — but say so per switch rather
than assuming it.

**Verify by hand** that every `permissive_value` in `obligation_rules.yaml` names a member of
its policy's `options`. No validator check exists yet (`B18`-adjacent; it is 1.2's next
packet), so your cross-check is the evidence.

### 2.3 Honest `lead_time_rounds`

54 of 75 placement options carry `0`. Set them to what the thing would actually take.

**A guide, not a rule:** a policy switch or a config change is 0. A departmental application
is 1. A warehouse system, an ERP module or anything touching every store is 2–3. If you
cannot justify a value, mark `TODO: calibrate` and list it — 1.7 tunes it.

**This is what gives *follow-through* something to score**, and it is what makes *"started
five things, finished none"* a teachable failure instead of an impossible one.

### 2.4 `preferences/services.yaml` — NEW FILE

Support tiers and integration tiers, per `design/07 §3.6`: `operations` and `employees` want
high support because they place the calls; `finance` and `c_suite` want low cost; `it` wants
high support because it absorbs the load otherwise — which is G1's staffing pool made
visible; `vendor` prefers the higher tier, which is honest for an external stakeholder.

---

## 3. Constraints

- **Content only.** No file outside `backend/packs/riverside_grocery/` changes. `git diff`
  on `backend/app/`, `backend/tests/` and `docs/` must be empty.
- **Riverside must stay `0 errors · 0 warnings · exit 0`.** You are adding content to a
  clean pack; if it stops validating, something is wrong with the content, not the validator.
- **Do not add a preference file for a class `design/07` does not list.** Governance and
  People are recorded there as later work with reasons.
- **`PROVENANCE.md` gets a row for every new file**, with `AUTHORED` and a rationale.
  `GOVERNANCE §4.9` — an authored value carries its reasoning or it is marked and reported.
- Anything you cannot justify: `TODO: calibrate`, and list it in your report.

---

## 4. Definition of Done

| Item | Evidence |
|---|---|
| `preferences/policies.yaml` — six switches, per-switch archetype ideals | the file, plus a note on which archetypes you gave a view and why |
| No archetype expresses a blanket posture across all six | show the variation |
| `options` + `default` on all six policies | the diff |
| Every `permissive_value` names a member of its policy's `options` | **hand-verified**, pasted — no check exists |
| `lead_time_rounds` set honestly across the 54 zeroes | the distribution, and the reasoning band you used |
| `preferences/services.yaml` | the file |
| **Riverside `0 errors · 0 warnings · exit 0`** | before and after, pasted |
| `backend/app/`, `backend/tests/`, `docs/` untouched | three empty diffs |
| `PROVENANCE.md` rows for both new files | the rows |
| Every `TODO: calibrate` listed | the list |

**One thing that is NOT in this packet:** the *information-policy discipline* Management
sub-factor (`design/07 §5` item 4). That is 1.4's spec, not content. Do not invent a scoring
rule here.

---

## 5. When you are done

Fill `handoffs/1.3-harvest/dod-followup.md` — a new file, do not overwrite `dod.md`. Push,
verify with `git ls-remote` against your local HEAD, and report. **Do not merge.**

**Declare every substitution.** Stop and report on anything this document does not settle —
particularly if authoring a stakeholder's view requires taking a position on whether a policy
setting is *right*. That would be the sim taking a stance, and it is the one thing this
packet must not do.
