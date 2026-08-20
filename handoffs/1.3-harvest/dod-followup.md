# 1.3 follow-up — Definition of Done

**Packet:** `handoffs/1.3-harvest/followup.md` · **Branch:** `build/1.3-followup`, cut from
`main` at the commit that adds the dispatch prompt · **Date:** 2026-08-18

**Scope held:** pack content only. Nothing outside
`backend/packs/riverside_grocery/` changed. No engine code, no schema, no validator.

---

## 0. The DoD table

| Item | Evidence | Status |
|---|---|---|
| `preferences/policies.yaml` — six switches, per-switch archetype ideals | the file · §2 · §3 | **done** |
| No archetype expresses a blanket posture across all six | §3 | **done** |
| `options` + `default` on all six policies | §4 | **done** |
| Every `permissive_value` names a member of its policy's `options` | §5, hand-verified and pasted | **done** |
| `lead_time_rounds` set honestly across the 54 zeroes | §6 | **done** |
| `preferences/services.yaml` | the file · §7 | **done** |
| Riverside `0 errors · 0 warnings · exit 0` | §1, before and after | **done** |
| `backend/app/`, `backend/tests/`, `docs/` untouched | §8 | **done** |
| `PROVENANCE.md` rows for both new files | §9 | **done** |
| Every `TODO: calibrate` listed | §10 | **done** |

**Not in this packet, and not done:** the *information-policy discipline* Management
sub-factor. That is 1.4's spec (`design/07` §5 item 4). No scoring rule was invented here.

---

## 1. Validator — before and after

Before, on `f812e4d` with none of this packet applied:

```
$ ./backend/bin/validate_casepack backend/packs/riverside_grocery

  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  13 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  0 errors · 0 warnings · exit 0

$ echo $?
0
```

After, with all four items applied:

```
$ ./backend/bin/validate_casepack backend/packs/riverside_grocery


  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  13 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  0 errors · 0 warnings · exit 0

$ echo $?
0
```

The 1.2 fixture matrix also still passes end to end, which is the check that would notice
if the new content changed what the validator says about any other pack:

```
$ python3 backend/tests/check_fixture_matrix.py   # (read-only; the file is untouched)
...
I5  riverside_grocery                  text=  0 json=  0 identical=yes
I5  packs/  (directory mode)           text= 77 json= 77 identical=yes

all 29 fixtures behave as named; 28 of 29 codes exercised, ['I8'] recorded as unfixturable
I1 set-equal against the spec; I5 identical in single-pack and directory mode
$ echo $?
0
```

The pack is also proved to **load**, not merely to parse — the preference domains below are
read back through `app.casepack.loader.load_casepack`, which is the path the engine uses:

```
preference domains loaded: ['catalog', 'platform', 'policies', 'services', 'training']
policies archetypes: 9 · services archetypes: 6
finance / data_retention -> {'ideal_posture': 'standard_period', 'weight': 0.3}
staff_monitoring options -> (['untracked', 'aggregate_only', 'individual_activity'], 'untracked')
```

---

## 2. Item 2.1 — `preferences/policies.yaml`

**New file.** 9 archetypes, 36 per-switch rows.

**Who was given a view, and why those nine.** Exactly the nine `design/07` §3.5 names:
`c_suite`, `finance`, `marketing`, `operations`, `employees`, `customer`, `general_public`,
`regulator`, `security_auditor`.

**Who was not.** `hr`, `investor`, `it`, `media`, `vendor` have no rows. The design does not
give them a view on this class, and authoring one would be inventing content past the
design rather than implementing it. Two are worth a later look and are recorded in the file
rather than guessed at:

- **`it`** absorbs the staff load that `data_access` and `access_logging` create — both
  carry a positive `staff_load` term in `policies.yaml`. This is the strongest candidate
  for a tenth archetype and is left for the auditor or 1.4 to rule on.
- **`hr`** is the department that would own a staff-monitoring position in a real firm.

**The shape, and it is a new authoring convention** — declared here and in the file header:

```yaml
defaults_by_archetype:
  <archetype>:
    weight: <float>            # how much this archetype's policy views count in aggregate
    by_decision:
      <policy key>:            # a key from the pack's top-level policies.yaml
        ideal_posture: <value> # a member of that policy's `options`
        weight: <float>        # how much THIS switch matters to THIS archetype
```

Two deliberate departures from the sketch in `design/07` §3.5, both declared in §11 below:
there is **no archetype-wide `ideal_posture`** (a single posture per archetype cannot
express `employees` caring about one switch and nothing else), and `ideal_posture`
**names an option value** rather than the abstract word `strict`/`permissive`.

**The sim takes no position.** Every row is an interest. Nothing in the file states or
implies that a setting is correct — §11 records the one place where authoring nearly
required a verdict, and what was done instead.

---

## 3. The variation — no archetype holds a blanket posture

```
# generated from preferences/policies.yaml, read with yaml.safe_load
ideal_posture per archetype per switch, weight alongside; '-' = holds no view

archetype        data_collection    data_retention     data_access        access_logging     data_egress        staff_monitoring   
-----------------------------------------------------------------------------------------------------------------------------------
finance          everything 0.5     std_period 0.3     open_all 0.4       unlogged 0.6       approved_dst 0.5   untracked 0.2      
c_suite          everything 0.5     indefinite 0.3     open_all 0.4       unlogged 0.5       approved_dst 0.3   -                  
marketing        everything 1.0     indefinite 0.8     open_all 0.3       -                  unrestricted 0.6   -                  
operations       -                  -                  open_all 1.0       unlogged 0.4       unrestricted 0.5   -                  
employees        -                  -                  -                  -                  -                  untracked 1.0      
customer         minimal 0.9        minimal 0.8        -                  -                  no_export 1.0      -                  
general_public   minimal 0.7        minimal 0.5        -                  -                  no_export 0.8      -                  
regulator        purpose_lim 0.7    std_period 1.0     role_based 0.9     full_audit 1.0     approved_dst 0.5   -                  
security_auditor minimal 0.5        minimal 0.6        need_know 0.9      full_audit 1.0     approved_dst 0.7   individual 0.8     

archetype         switches held  distinct postures  distinct weights  blanket?
--------------------------------------------------------------------------------
finance           6              6                  5                 no
c_suite           5              5                  3                 no
marketing         4              4                  4                 no
operations        3              3                  3                 no
employees         1              1                  1                 no
customer          3              2                  3                 no
general_public    3              2                  3                 no
regulator         5              5                  4                 no
security_auditor  6              5                  6                 no

A blanket posture would be: all six switches held, one posture, one weight. Nobody is.

Per switch -- the disagreement:
  data_collection   3 distinct positions across 7 archetypes
      everything_by_default    finance, c_suite, marketing
      minimal                  customer, general_public, security_auditor
      purpose_limited          regulator
  data_retention    3 distinct positions across 7 archetypes
      standard_period          finance, regulator
      indefinite               c_suite, marketing
      minimal                  customer, general_public, security_auditor
  data_access       3 distinct positions across 6 archetypes
      open_to_all_staff        finance, c_suite, marketing, operations
      role_based               regulator
      need_to_know             security_auditor
  access_logging    2 distinct positions across 5 archetypes
      unlogged                 finance, c_suite, operations
      full_audit_trail         regulator, security_auditor
  data_egress       3 distinct positions across 8 archetypes
      approved_destinations    finance, c_suite, regulator, security_auditor
      unrestricted             marketing, operations
      no_export                customer, general_public
  staff_monitoring  2 distinct positions across 3 archetypes
      untracked                finance, employees
      individual_activity      security_auditor
```

Reading the top table: `finance` holds a view on all six switches and is permissive on four
of them, restrictive on two — and both exceptions are read off this pack rather than off an
opinion. A retention position is the only one of the six whose effect vector *reduces* a
running cost (`storage_cost: -0.05`), and `ledger_egress_unrestricted` is the obligation
that ends in a missed financial audit, which lands on finance. `employees` hold exactly one
view, which is the sharpest possible demonstration that the authoring is per switch.

`regulator` and `security_auditor` disagree with **each other** on `data_retention` —
`standard_period` against `minimal` — while both ask the firm to constrain itself. Two
"strict" archetypes that do not agree is the clearest evidence that no single posture was
applied.

---

## 4. Item 2.2 — `options` and `default` on all six policies

```diff
  - key: data_collection
+   options: [everything_by_default, purpose_limited, minimal]
+   default: everything_by_default
  - key: data_retention
+   options: [indefinite, standard_period, minimal]
+   default: indefinite
  - key: data_access
+   options: [open_to_all_staff, role_based, need_to_know]
+   default: open_to_all_staff
  - key: access_logging
+   options: [unlogged, sampled, full_audit_trail]
+   default: unlogged
  - key: data_egress
+   options: [unrestricted, approved_destinations, no_export]
+   default: unrestricted
  - key: staff_monitoring
+   options: [untracked, aggregate_only, individual_activity]
+   default: untracked
```

Three states each: the permissive value `obligation_rules.yaml` already named, a middle
position, and the most restrictive. **The default is the permissive value on all six, and
the reason is stated per switch in the file rather than assumed** — in every case it is the
state the case is actually in today, which is what makes never opening the screen cost
something instead of being an opt-in. Full table with the per-switch reasons in
`PROVENANCE.md` §10.1.

**Order carries no meaning.** `models.py` is explicit — *"do not infer strictness from
position"*. The lists read permissive-to-restrictive for a human only, and on
`staff_monitoring` that reading would be actively wrong: its permissive end is the
*low*-surveillance end.

> **SUPERSEDED 2026-08-19 (audit `1.3-f-001`).** `design/07 §3.5b` was ruled after this
> build: `options` **is ordinal**, least constrained at index 0. The lists were already
> authored that way, so no values change — but "order carries no meaning" is no longer
> true. On `staff_monitoring` the ordinal *more-constrained* end means the firm watches its
> own people more (`§3.5a`), which is why its permissive end is still the low-surveillance
> end. The pack comments in `policies.yaml` and `preferences/policies.yaml` were corrected;
> this report is left as-written with this note.

---

## 5. Hand-verification — no machine check exists

`grep -n obligation backend/app/casepack/validate.py` still returns zero; the check is
1.2's next packet. This cross-check is therefore the evidence. Sections B and C are not
asked for by the packet and are included because they are the same class of unvalidated
reference, newly created by this packet.

```
# generated from policies.yaml, obligation_rules.yaml, preferences/*.yaml

A. obligation_rules.permissive_value  ->  policies.options

obligation rule                  policy             permissive_value       in options?  is default?
----------------------------------------------------------------------------------------------------
customer_pii_retention           data_retention     indefinite             YES          YES
customer_pii_collection          data_collection    everything_by_default  YES          YES
sale_detail_open_to_all_staff    data_access        open_to_all_staff      YES          YES
user_account_changes_unlogged    access_logging     unlogged               YES          YES
ledger_egress_unrestricted       data_egress        unrestricted           YES          YES
staff_activity_untracked         staff_monitoring   untracked              YES          YES
----------------------------------------------------------------------------------------------------
RESULT: 6 of 6 permissive_values name a member of their policy's options.

   options declared, per policy:
     data_collection    ['everything_by_default', 'purpose_limited', 'minimal']   default: everything_by_default
     data_retention     ['indefinite', 'standard_period', 'minimal']   default: indefinite
     data_access        ['open_to_all_staff', 'role_based', 'need_to_know']   default: open_to_all_staff
     access_logging     ['unlogged', 'sampled', 'full_audit_trail']   default: unlogged
     data_egress        ['unrestricted', 'approved_destinations', 'no_export']   default: unrestricted
     staff_monitoring   ['untracked', 'aggregate_only', 'individual_activity']   default: untracked

   policies with no obligation rule : none -- all six covered
   obligations naming no policy     : none


B. preferences/policies.yaml ideal_posture  ->  policies.options

  finance            access_logging     unlogged               policy=YES  option=YES
  finance            data_collection    everything_by_default  policy=YES  option=YES
  finance            data_retention     standard_period        policy=YES  option=YES
  finance            data_egress        approved_destinations  policy=YES  option=YES
  finance            data_access        open_to_all_staff      policy=YES  option=YES
  finance            staff_monitoring   untracked              policy=YES  option=YES
  c_suite            data_collection    everything_by_default  policy=YES  option=YES
  c_suite            access_logging     unlogged               policy=YES  option=YES
  c_suite            data_access        open_to_all_staff      policy=YES  option=YES
  c_suite            data_retention     indefinite             policy=YES  option=YES
  c_suite            data_egress        approved_destinations  policy=YES  option=YES
  marketing          data_collection    everything_by_default  policy=YES  option=YES
  marketing          data_retention     indefinite             policy=YES  option=YES
  marketing          data_egress        unrestricted           policy=YES  option=YES
  marketing          data_access        open_to_all_staff      policy=YES  option=YES
  operations         data_access        open_to_all_staff      policy=YES  option=YES
  operations         data_egress        unrestricted           policy=YES  option=YES
  operations         access_logging     unlogged               policy=YES  option=YES
  employees          staff_monitoring   untracked              policy=YES  option=YES
  customer           data_egress        no_export              policy=YES  option=YES
  customer           data_collection    minimal                policy=YES  option=YES
  customer           data_retention     minimal                policy=YES  option=YES
  general_public     data_egress        no_export              policy=YES  option=YES
  general_public     data_collection    minimal                policy=YES  option=YES
  general_public     data_retention     minimal                policy=YES  option=YES
  regulator          access_logging     full_audit_trail       policy=YES  option=YES
  regulator          data_retention     standard_period        policy=YES  option=YES
  regulator          data_access        role_based             policy=YES  option=YES
  regulator          data_collection    purpose_limited        policy=YES  option=YES
  regulator          data_egress        approved_destinations  policy=YES  option=YES
  security_auditor   access_logging     full_audit_trail       policy=YES  option=YES
  security_auditor   data_access        need_to_know           policy=YES  option=YES
  security_auditor   staff_monitoring   individual_activity    policy=YES  option=YES
  security_auditor   data_egress        approved_destinations  policy=YES  option=YES
  security_auditor   data_retention     minimal                policy=YES  option=YES
  security_auditor   data_collection    minimal                policy=YES  option=YES

RESULT: 36 rows checked, 0 unresolved: none


C. preferences/services.yaml ideal_tier  ->  platform.yaml tier keys

   declared tiers: {'support_tier': ['basic', 'standard', 'premium'], 'integration_tier': ['basic', 'advanced', 'vendor_managed']}

  operations         support_tier       premium            tier=YES
  operations         integration_tier   advanced           tier=YES
  employees          support_tier       premium            tier=YES
  it                 support_tier       premium            tier=YES
  it                 integration_tier   vendor_managed     tier=YES
  finance            support_tier       basic              tier=YES
  finance            integration_tier   basic              tier=YES
  c_suite            support_tier       basic              tier=YES
  c_suite            integration_tier   advanced           tier=YES
  vendor             integration_tier   vendor_managed     tier=YES
  vendor             support_tier       premium            tier=YES

RESULT: 11 rows checked, 0 unresolved: none
```

---

## 6. Item 2.3 — honest `lead_time_rounds`

**The band, and it is a guide applied with judgement, not a formula:**

| Rounds | What it is |
|---|---|
| **0** | already running, or nothing to install and nobody to retrain |
| **1** | a departmental application or a shared platform service: procure, configure, integrate, cut one department over |
| **2** | touches every store, the warehouse or the general ledger: migration plus a period of parallel running |

**It is anchored on the source, not invented.** `mis_initiatives_master.duration_in_rounds`
was harvested but never used: 12 rows, range 1–5 — BI dashboard 1, CRM enhancements 1, data
governance 1, data quality audit 1, ERP finance module 2, endpoint security 2, training
programme 2, unit-based ERP 2, system tuning 2, data migration 3, predictive analytics 4,
supplier portal 5. **The source contains no initiative shorter than one round**, which is
the strongest single argument that 54 zeroes was a content defect rather than a modelling
choice.

**Placement gradient — authored, and it corrects a claim in `PROVENANCE.md` §9.** §9 said
the cloud option *"is genuinely faster than the on-premises one"*. mis_lite's own data does
not support that as a general rule: its four cloud initiatives average 2.75 rounds against
2.0 for its two on-premises ones. What survives is narrower, and it is what was applied:
placement changes the answer only where the delay was **infrastructure**. `saas` rows carry
`bypasses_platform: true` — the firm does not build the platform underneath them — so SaaS
is one round faster where that build was the wait, and no faster where the wait is
migration, training or process change.

**Only the zeroes were re-authored.** The 21 rows already carrying 1 or 2, including every
row 0.3 §5.6 pins, are untouched.

```
# `git show f812e4d:<path>` for the before column, the working tree for the after
lead_time_rounds    before (f812e4d)     after
----------------------------------------------
0                                 54        17
1                                 17        51
2                                  4         7
----------------------------------------------
total                             75        75

rows changed: 37  (every one of them was 0)
rows already non-zero and left untouched: 21

the 17 rows deliberately left at 0:
   catalog   pos_system_2011        on_prem
   catalog   accounting_package     on_prem
   catalog   store_spreadsheets     on_prem
   catalog   store_spreadsheets     cloud
   catalog   store_spreadsheets     saas
   catalog   next_gen_firewall      saas
   catalog   service_desk           saas
   catalog   store_back_office_pc   on_prem
   catalog   store_back_office_pc   cloud
   catalog   store_back_office_pc   saas
   platform  compute_pool           cloud
   platform  compute_pool           saas
   platform  storage_pool           cloud
   platform  storage_pool           saas
   platform  intrusion_detection    saas
   platform  end_user_email         cloud
   platform  end_user_email         saas

the 7 rows at 2:
   catalog   pos_system_2011        saas
   catalog   centraline_im7         on_prem
   catalog   centraline_im7         cloud
   catalog   ecommerce_site         on_prem
   catalog   erp_suite              on_prem
   catalog   erp_suite              saas
   platform  data_platform          on_prem
```

The 17 kept zeroes are each a case where zero is the honest answer, and the platform ones
are the interesting group: `compute_pool` and `storage_pool` at 0 in the cloud is capacity
on demand, which is *the* difference between the two placements — and 0.3 §5.6 pins the
compute pool at 100% used, so a team placing in the cloud relieves the pinch this round
while a team building on-premises waits a round for it. That is a real decision the pack
could not express while everything was 0.

**Honest limitation:** one round now dominates (51 of 75). That is a fair reflection of a
catalogue that is mostly departmental systems and shared services, but it means the
sharpest follow-through failures rest on the 7 two-round options. Marked `TODO: calibrate`
and listed in §10.

---

## 7. Item 2.4 — `preferences/services.yaml`

**New file.** 6 archetypes, 11 rows — exactly the six `design/07` §3.6 names:
`operations`, `employees`, `it`, `finance`, `c_suite`, `vendor`. Same shape as
`preferences/policies.yaml`, with `ideal_tier` in place of `ideal_posture` because the pack
calls these tiers and the value is always a declared tier key.

The two rows worth naming:

- **`it` wants `premium` support at weight 1.0**, and it is a capacity argument rather than
  a comfort one. `premium` carries `fte_equivalent: 2.4` against a `starting_staff_fte` of
  2.0, so the load the tier does not absorb is load the two existing IT staff carry. That
  is G1's staffing pool made visible, which is what `design/07` §3.6 asks for.
- **`c_suite` wants `advanced` integration**, not the cheap tier — the row that keeps the
  board from being a second finance. `event_board_wants_numbers` — *"The board wants to
  know which customers we are losing and why. I cannot answer that from what we hold"* — is
  a question only answerable across systems that are joined up.

`vendor` prefers the higher tier because it is their revenue, recorded plainly. `customer`
was the closest call among the eight archetypes left out: service tier does reach the shop
floor, but it reaches it through reliability, which customers already hold a view on in
`preferences/catalog.yaml` and `preferences/platform.yaml`. Stating it again would
double-count one interest.

---

## 8. Scope — three empty diffs

```
$ git diff -- backend/app/
$ git diff -- backend/tests/
$ git diff -- docs/
```

All three produce no output. Full working tree:

```
$ git status --short
 M backend/packs/riverside_grocery/PROVENANCE.md
 M backend/packs/riverside_grocery/catalog.yaml
 M backend/packs/riverside_grocery/platform.yaml
 M backend/packs/riverside_grocery/policies.yaml
?? backend/packs/riverside_grocery/preferences/policies.yaml
?? backend/packs/riverside_grocery/preferences/services.yaml
```

Six paths, all inside `backend/packs/riverside_grocery/`. No preference file was added for
a class `design/07` does not list — Governance (§3.4) and People (§3.7) are recorded there
as later work with reasons, and neither got a file here.

---

## 9. `PROVENANCE.md` rows

Four rows added to the §1 transform table:

| pack field | mis_lite source | rows in | rows out | mode | notes |
|---|---|---|---|---|---|
| `preferences/policies.yaml` | — | — | 9 archetypes · 36 rows | authored | **NEW.** design/07 §3.5. No mis_lite source: the source models stakeholder preference over infrastructure placement only and has no policy dimension |
| `preferences/services.yaml` | — | — | 6 archetypes · 11 rows | authored | **NEW.** design/07 §3.6. The tier keys and every figure the views are about are harvested and already in `platform.yaml`; who holds a view and how strongly is authored |
| `policies[].options`, `.default` | — | — | 6 × 3 states + 6 defaults | authored | the permissive value of each switch was already named by `obligation_rules.yaml` |
| `lead_time_rounds` | `mis_initiatives_master.duration_in_rounds` | 12 | 37 rows re-authored | judged | band anchored on the source's 12 durations; placement gradient authored |

Two rows added to the §7 `TODO: calibrate` table, one row updated (`catalog.yaml` 4 → 5),
the marker total updated 27 → 30, and the transform-map table count 25 → 26.

**A new §10** records the vocabularies with a per-switch justification of each `default`,
the two new preference files, and the lead-time band. **§9 was corrected**: it claimed
`lead_time_rounds` was *"authored on every row"*, which was true of presence and false of
content — 54 of 75 were `0`.

---

## 10. Every `TODO: calibrate` this packet adds — 3

| File | Marker | What is unjustified |
|---|---|---|
| `preferences/policies.yaml` | 1 | **both weight columns throughout** — the archetype-level weight and the 36 per-switch weights. Which switch matters most to whom is authored judgement. The `ideal_posture` values are deliberately **not** marked: each is either stated in `design/07` §3.5 or read off an effect vector or an obligation rule already in this pack, and every one is cited in the file |
| `preferences/services.yaml` | 1 | **both weight columns**, same footing as `preferences/platform.yaml`'s. The `ideal_tier` values are not marked — each is stated in `design/07` §3.6 or read off a figure in `platform.yaml` |
| `catalog.yaml` (band header) | 1 | **the whole lead-time band**, including the placement gradient and the resulting flat distribution |

Two specific rows are named inside that third marker and in `PROVENANCE.md` §10.4:

- `erp_suite.on_prem` is **2**, below the 3 the band would give a firm-wide replacement
  carrying both a data migration and the finance close. Left as authored because it is not
  one of the 54 zeroes.
- `central_sign_on` is **1** on all three placements. Issuing credentials to 620 staff is
  plausibly 2; the existing on-premises 1 is what holds the other two down.

Pack total: **27 → 30**.

---

## 11. Substitutions, and the one place this nearly took a stance

**Declared substitutions.**

1. **No archetype-wide `ideal_posture`.** `design/07` §3.5 and `followup.md` §2.1 both
   sketch `finance: {ideal_posture: permissive, weight: 0.9}`. Not authored that way. The
   same two documents then require per-switch authoring, and a single posture per archetype
   cannot express `employees` holding one intense view and five blanks. The nesting key
   `by_decision` is new, and is used identically in both new files so there is one shape
   for 1.4 to consume.

2. **`ideal_posture` names an option value, not `strict`/`permissive`.** `models.py` states
   that option order carries no meaning — *"do not infer strictness from position"* — so an
   abstract posture would have required exactly the strictness ordering the schema refuses
   to supply. Naming the option makes alignment computable without one. **Consequence for
   1.4:** with no declared ordering, alignment against these ideals is an exact match, not
   a distance. If partial credit is wanted, the ordering has to be declared somewhere first,
   and that is a schema question, not a content one.

   > **SUPERSEDED 2026-08-19 (audit `1.3-f-001`).** `design/07 §3.5b` now declares the
   > ordering: `options` is ordinal, least constrained at index 0. So the "Consequence for
   > 1.4" above is reversed — **alignment WILL be a distance along that order, not an exact
   > match**, and partial credit becomes available without a schema change once 1.4's
   > policy-switch dimension is built (it is deferred today —
   > `management.policy_switch_alignment` raises NotImplementedError). Naming the option
   > value stays exact and unambiguous; nothing in the data changes.

3. **`ideal_tier` in `services.yaml`** rather than reusing `ideal_posture`, because the pack
   calls them tiers.

4. **`data_retention` options are `[indefinite, standard_period, minimal]`**, where
   `models.py`'s illustrative docstring says `[minimal, standard, indefinite]`. `standard`
   alone does not say what it is standard *of*; the docstring is an "e.g." and not a
   contract.

5. **Only the 54 zeroes were re-authored**, not all 75 rows. `followup.md` §2.3 scopes the
   defect to the zeroes, and re-litigating the 21 values another packet set — several of
   them pinned by 0.3 §5.6 — would have been a different change. The one row where this
   leaves a value below its own band, `erp_suite.on_prem`, is marked.

6. **`overrides: []` in both new files.** Every row is an archetype-level interest that
   would read the same in any pack; nothing in Riverside's situation makes a switch mean
   something different. `overrides` is for the case, and the case has nothing to add here.

**Where authoring nearly required a verdict — reported, not decided.**

`design/07` §3.5's table reads *"`employees` — strict on `staff_monitoring`"*. Five of the
six switches share an axis where "strict" means the firm constrains what it does with data.
**`staff_monitoring` does not.** Its permissive value is `untracked`
(`obligation_rules.yaml`), so on that switch the undecided end is the *low*-surveillance
end, and "more restrictive" would mean watching people **more**, not less. Read literally,
`design/07` says employees want to be watched more.

Deciding which reading is correct on the merits would have been the sim taking a position.
It was not decided that way. **The reason column governs**: `design/07`'s own justification
is *"being watched is not free"*, which is an interest, and interests are what this file
records. So `employees` want `untracked` — and they are the one archetype already aligned
with doing nothing, which is itself worth a debrief. `security_auditor` wants
`individual_activity` on the same switch because `staff_monitoring`'s effect vector carries
`insider_risk: -0.25`, the risk that archetype is employed to look at, while the same vector
carries `employee_trust: -0.20`. Both facts are true at once and neither side is endorsed.

**This is the one item a fresh auditor should look at first.** The ambiguity is in
`design/07`'s wording, not in this file, and it is resolved here only for authoring
purposes. Whether `design/07` §3.5's table should be reworded is an AUTHOR decision, and no
design document was edited by this packet.

**Two things stopped short of, deliberately.**

- **The *information-policy discipline* Mgmt sub-factor.** `design/07` §5 item 4, `1.4`'s
  spec. Not invented here. `default` is now declared on all six switches, which is the
  content half that sub-factor needs; the rule that reads it is not content.
- **A tenth archetype in `preferences/policies.yaml`.** `it` has a real, pack-grounded
  interest in `data_access` and `access_logging` through their `staff_load` terms.
  `design/07` §3.5 does not list it, so it was not authored. Flagged for the auditor.

**One thing worth a validator packet, found while doing this.** `W01` — the placeholder-
preference heuristic — only inspects rows that carry an `ideal_value` key, and only at the
top level of `defaults_by_archetype` and `overrides`. It cannot see either new file: the
ideals are nested under `by_decision` and named `ideal_posture` / `ideal_tier`. Nothing was
dodged — the variation table in §3 is the substitute — but the heuristic is now blind to
two of the five preference domains, and that is a real gap for 1.2's next packet alongside
the `permissive_value` check.
