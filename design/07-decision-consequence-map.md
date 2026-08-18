# 07 — Decision → Preference → Score → Consequence

**Authored 2026-08-18. Status: proposal for the gaps, record for the settled.**

`02-traceability-matrix.md` maps every **scoring factor** back to the UI that captures it.
This document runs the other way: it starts from every **decision a student makes** and asks
whether that decision actually lands anywhere.

It exists because that question had never been asked systematically, and the answer turned
out to be *no* for two whole decision classes. Both were found by an audit tripping over a
symptom rather than by anyone checking the design — which is the failure this document is
meant to stop recurring.

---

## 1. The three-path test

> **A decision is real only if all three paths exist. Two out of three is decoration.**

| Path | What it is | What the student experiences |
|---|---|---|
| **PREFERENCE** | stakeholders hold an ideal position on the decision (`preferences/*.yaml`) | *someone is happier or angrier* — immediate, visible, and the reason the decision felt like a trade-off |
| **SCORE** | the decision feeds a named sub-factor of Tech, Org or Mgmt | *it moved the scorecard* — delayed, quantified, argued about in the debrief |
| **CONSEQUENCE** | the decision can raise a signal, or arm/disarm an event | *something happened because of it* — discrete, narrative, memorable |

The three are not redundant. **Preference is how a decision feels; score is how it counts;
consequence is how it bites.** A decision with a score but no preference is a number that
moves for no visible reason. A decision with a preference but no consequence is an opinion
poll. A decision with a consequence but no preference ambushes the student — which is the
thing *"signals are the game telling you what is coming"* exists to prevent.

**The mechanism for PREFERENCE is already settled** — `design/04` G6 adopted layer 1,
*decisions → alignment against each stakeholder's ideal*, and the pack implements it as
`preferences/<class>.yaml` keyed by archetype:

```yaml
defaults_by_archetype:
  c_suite:   {ideal_cost_posture: low,             weight: 0.8}
  employees: {ideal_training_coverage: high,       weight: 0.7}
```

The loader reads **any** YAML in `preferences/`, so adding a class needs **no schema change**.
Every gap below is content, not engineering.

---

## 2. The map

Fourteen archetypes are available to every class: `c_suite · finance · employees ·
operations · it · hr · marketing · investor · customer · vendor · security_auditor ·
regulator · general_public · media`.

| # | Decision class | PREFERENCE | SCORE | CONSEQUENCE |
|---|---|---|---|---|
| 0 | **Strategy** | *n/a by design — see §3.0* | sets `capability_weights`, the frame everything else is measured against | reopen cost + resistance spike |
| 1 | **Platform** — hosting posture, firm-wide services | ✅ `preferences/platform.yaml` | **Tech**: capacity pool, path availability | capacity signals · SPOF events |
| 2 | **Components** — unit-level purchases | ✅ `preferences/catalog.yaml` | **Tech**: coverage, capacity draw, data adequacy | capacity signals · EOL events |
| 3 | **Rollout** — training · process · communication mix | ✅ `preferences/training.yaml` | **Org**: training coverage, process fit, resistance | adoption signals |
| 4 | **Governance** — ownership, sponsor, in-flight portfolio | ⚠️ none — **§3.4** | **Mgmt**: governance coverage, follow-through | *(none today)* — **§3.4** |
| 5 | **Security / Information policy** — the six switches | ❌ **none — §3.5** | ❌ **nothing** — **§3.5** | ⚠️ `obligation_rules` exist but are inert |
| 6 | **Services** — support tier, integration tier, vendor support | ❌ **none — §3.6** | **Tech**: reliability; **Org**: staff load | vendor-support-ending events |
| 7 | **People** — IT staffing against operational load | ⚠️ partial — `it.ideal_staff_load` sits in `catalog.yaml` | **Org**: IT staffing pool (G1) | staffing-overload signals |
| 8 | **Challenges** — fund · defer · reject + rationale | *n/a — the response IS to a consequence* | **Mgmt**: signal responsiveness, rationale consistency | the event's own outcome |

**Two classes fail the three-path test outright.** Policy has one of three. Services has two
of three. Governance has two of three and is defensible.

---

## 3. The gaps, and what each should be

### 3.0 Strategy — no preference, and that is correct

Strategy is the **frame**, not a decision stakeholders grade. Its weights are what every
other decision is measured against, so giving stakeholders an ideal strategy would score the
same choice twice — once as alignment and once as the weights doing the aligning.

Recorded here so nobody later reads its blank cell as a gap.

### 3.5 Information policy — one path of three · **highest priority**

**Today:** six switches, each with a stated cost. A student can spend capital on all six or
none. **Nothing differs.** No stakeholder notices, no sub-factor moves, and the obligation
rules that would bite are inert until `PolicyOption.options` is declared in content.

This is the largest hole in the game, and it is the whole of Laudon Ch 4.

**PREFERENCE — `preferences/policies.yaml`, new file, no schema change.** The six switches
are `data_collection · data_retention · data_access · access_logging · data_egress ·
staff_monitoring`. The teaching value is that **stakeholders want incompatible things**:

| Archetype | Wants | Because |
|---|---|---|
| `finance` · `c_suite` | permissive, cheap | every switch costs capital and constrains operations |
| `regulator` · `security_auditor` | strict retention, access, logging | it is their job |
| `employees` | **`untracked`** on `staff_monitoring`, no view elsewhere | being watched is not free — see §3.5a |
| `customer` · `general_public` | strict on collection, retention, egress | it is their data |
| `marketing` | permissive collection | targeting needs data |
| `operations` | permissive access | strict access slows the floor down |

That table is the point. **Set every switch to strict and Finance, Marketing and Operations
are unhappy and you are poorer. Set none and the Regulator and your customers are.** There is
no position that pleases everyone — which is exactly `GOVERNANCE`'s *"ships attributes and
consequences, never a stance."* The sim never says which is right; the stakeholders disagree
and the student lives with it.

### 3.5a `staff_monitoring` runs the opposite way, and that is the point

**Corrected 2026-08-18.** The table above originally read *"employees want **strict** on
`staff_monitoring`"*. In the pack's own vocabulary that is false, and it says the opposite of
what was meant.

Five of the six switches share an axis: moving away from the default means **the firm
constrains its handling of other people's data** — collect less, keep it less long, restrict
who sees it, log more, export less. `staff_monitoring` does not. Its permissive value is
`untracked`, so moving away from the default means **the firm watches its own people more**.

```
data_collection    everything_by_default → purpose_limited → minimal        firm constrains itself
data_retention     indefinite            → standard_period → minimal        firm constrains itself
data_access        open_to_all_staff     → role_based      → need_to_know   firm constrains itself
access_logging     unlogged              → sampled         → full_audit     firm constrains itself
data_egress        unrestricted          → approved_dsts   → no_export      firm constrains itself
staff_monitoring   untracked             → aggregate_only  → individual     firm constrains ITS PEOPLE
```

**This is not a modelling error and must not be "fixed" by re-framing the switch.** Laudon
Ch 4 covers both halves of information policy — the firm's duty to the people whose data it
holds, *and* the firm's power over the people who work for it. They are genuinely different
obligations pointing in opposite directions, and putting them on one screen with opposite
axes is the honest model.

**It is also the sharpest teaching moment on the screen.** A student who sets every switch to
its strictest value has not "done the right thing" — they have protected customers *and*
placed every employee under individual surveillance. There is no column of the table where
maximum strictness is uniformly good, which is precisely why the sim cannot take a stance.

`employees` therefore want `untracked` and are **the one archetype aligned with doing
nothing** on their switch. `security_auditor` wants `individual_activity` on the same switch,
because that setting reduces insider risk — the thing they are employed to look at — while
the same setting reduces employee trust. Both are true; neither is endorsed.

### 3.5b `options` is ORDINAL — permissive at index 0

**Ruled 2026-08-18.** `PolicyOption.options` is ordered, **least constrained first**, and all
six of Riverside's vocabularies are already authored that way.

This matters because alignment scoring depends on it. Without an order, a stakeholder's
`ideal_posture` can only be matched **exactly** — so a team that set `minimal` retention when
the Regulator wanted `standard_period` would score identically to one that left it
`indefinite`. **Being stricter than asked would count the same as ignoring the ask**, which is
not a defensible model of anyone's preference.

With an order, alignment is **distance**, and overshooting costs less than ignoring.

Two consequences, both filed:

- **`CONTRACTS.md` needs the entry** (`1.1-r3-005` / register `B21`). Its only sibling
  per-pack vocabulary, `entity.level_of_detail`, already declares itself ordinal — this
  follows the precedent rather than inventing one.
- **`models.py`'s docstring says order carries no meaning** and must be corrected, or the
  next builder will read the schema and the design as contradicting each other. **1.1.**

**SCORE.** Alignment feeds Org (via stakeholder alignment, G6 layer 1). Additionally propose
a **Mgmt** sub-factor — *information-policy discipline*: has the team taken a position at all,
or is every switch still on its default? A team that has never opened the screen is not
neutral, it is unmanaged. This is the sub-factor that makes ignoring the screen cost
something, and it is the missing half of `1.5 §5.4`'s `default` field.

**CONSEQUENCE.** Already designed — obligation rules arm privacy events. Needs Riverside to
declare each policy's `options` and `default`, which is content and now unblocked.

### 3.6 Services — two paths of three

Support tiers, integration tiers and vendor support all feed Tech reliability and Org staff
load, and vendor-support-ending events already exist in the deck. **No stakeholder holds a
view**, so a student upgrading from Basic to Premium support sees a cost and a reliability
number and no human reaction.

**Propose `preferences/services.yaml`:** `operations` and `employees` want high support
because they are the ones who call it; `finance` and `c_suite` want low cost; `it` wants high
support because it absorbs the load otherwise (this is the G1 staffing pool made visible);
`vendor` prefers the higher tier for obvious reasons, which is a nice piece of honesty for an
external stakeholder.

### 3.4 Governance — two paths, and the missing one is deliberate-ish

Governance costs nothing and feeds Mgmt directly. Its blank **CONSEQUENCE** cell is the
interesting one: today, assigning nobody as owner of a capability has no discrete
consequence, only a lower score.

**Propose one:** an unowned capability with an open critical signal should arm an event —
*"nobody has answered the alert on the ordering system for two rounds."* That converts
governance from a score into a story, and it is the cheapest possible demonstration of the
BATTLECARD's *"governance is free, and teams still skip it — that is the lesson."*

**Preference is arguably not needed** — but `employees` plausibly hold a view on whether
anyone owns the system they use daily. Low priority; recorded, not proposed.

### 3.7 People — preference exists but is filed in the wrong place

`it.ideal_staff_load` lives in `preferences/catalog.yaml`, because staffing was modelled as a
property of what you buy. Under G1, staffing is its own decision class with its own pool. The
preference should move to `preferences/people.yaml` when 4.5 builds the screen; `hr` and
`employees` both hold views on hiring versus over-loading the existing team.

Not urgent. Recorded so 4.5 does not re-derive it.

---

## 4. Two cross-cutting findings this map produces

**A decision class with no preference file is invisible to the persona layer.** Personas
speak from stakeholder state (`4.8`, numbers injected never recalled). A stakeholder with no
opinion on policy has nothing to say when a student asks about it — so the Ch 4 material is
absent from the interview channel too, not just from scoring. **One missing content file
silently removes a topic from three subsystems.**

**`lead_time_rounds` is the same shape of problem in the CONSEQUENCE column.** 54 of 75
purchase options complete in zero rounds, so *follow-through* — a named Mgmt sub-factor with
a UI (`Governance › continue/pause/kill`) and a casepack field — has almost nothing to act
on. The path exists end to end and the content zeroes it out.

Both are content defects that look like engine gaps. **That is the pattern this document
exists to catch: a path can be fully built and still carry nothing.**

---

## 5. What to do, in order

| Priority | Action | Owner | Why now |
|---|---|---|---|
| 1 | `preferences/policies.yaml` — six switches × archetype ideals | **1.3 follow-up** | Largest hole; no schema change; unblocks Ch 4 in scoring *and* personas |
| 2 | Riverside declares each policy's `options` + `default` | **1.3 follow-up** | Unblocked as of 1.1 rework-3; makes obligations live |
| 3 | Honest `lead_time_rounds` across the 54 zeroes | **1.3 follow-up** | Gives follow-through something to score |
| 4 | *information-policy discipline* as a Mgmt sub-factor | **1.4 spec** | Must exist before 1.4 scores anything |
| 5 | `preferences/services.yaml` | **1.3 follow-up** | Cheap, completes Services |
| 6 | Unowned-capability-with-open-signal event | **1.5** | Converts governance from score to story |
| 7 | Move `ideal_staff_load` to `preferences/people.yaml` | **4.5** | Filing, not function |

**Items 1–3 should land before 1.4 scores anything and before 1.7 calibrates it.** A
calibration harness tuned against a pack where policy does nothing and everything completes
instantly would be tuning the wrong game — and it would pass, which is worse.

---

## 6. The standing test

> **Before any decision class ships: name its preference file, its scoring sub-factor, and
> the signal or event it can move. If one of the three is blank, say so in the spec.**

Every ✅ in `02-traceability-matrix.md` means *a factor has a capture point*. It does not mean
*a decision has a consequence*. Those are different questions, and only this document asks
the second one.
