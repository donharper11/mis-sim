# 0.5 — Coverage Gaps · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2
**Author:** Claude (design session) · **Date:** 2026-07-27
**Phase:** 0 · **Depends on:** 0.4 (merged, `172de97`) · **Blocks:** 0.6, Phase 3

> Closes the six factors that `findings/field-coverage-2026-07-27.md` found have no
> capture point. Five of them cannot be wired later because there is nothing to wire —
> the control does not exist.
>
> **The structural one: Management Quality currently has no screen.** Two of its six
> sub-factors need student input and both are homeless, so a student cannot *do*
> management, only have it inferred. In a sim resting on `Tech × Org × Mgmt`, where
> Management was specified as the term you cannot buy, that is a hole in the model.

---

## 0. Spec Basis

**Read in full:**
- `findings/field-coverage-2026-07-27.md` — the scan, its method, and its method's limits
- `design/02-traceability-matrix.md` §C and §D — the homeless factors
- `mockups/security.html`, `components-wizard.html`, `components.html`, `rollout.html` —
  the grammar being extended
- `handoffs/0.4-mockups-remaining/spec.md` §5.1–5.2 — shell and hierarchy method
- `CONTRACTS.md` — badge scale · selected state (two patterns) · row opens detail
- `GOVERNANCE.md` §4.9 — seed data, never stubs

**Extraction sufficiency:** covered.

---

## 1. Purpose and scope

**In scope — one new screen, two additions, one shell change:**

```
NEW       mockups/governance.html          FC-1 ownership · FC-2 in-flight portfolio
ADD       mockups/security.html            FC-3 information policy, 6 switches
ADD       mockups/components-wizard.html   FC-5/FC-6 step 6 TCO checklist
SHELL     the capital strip, ALL files     FC-4 request additional capital
```

**Out of scope:**
- Any React component — that is 0.6
- Any backend or wiring
- Restyling anything not named above
- FC-7 (rationale free text) — remains open as **G2**; the only LLM-scored surface in the
  design, and cutting it stays defensible

**Deliberately rejected:** one Governance screen carrying all four gaps. Ownership,
portfolio, privacy policy and a capital request are four unrelated jobs. Putting them on
one page is how the discarded v2 Situation screen got built.

---

## 2. Project-specific statements

**Scoring factors captured** — this packet exists to create these:

| Factor | Matrix | Lands on |
|---|---|---|
| Governance coverage | §C | `governance.html` |
| Follow-through | §C | `governance.html` |
| Information policy | §D | `security.html` |
| Additional capital request | §D | shell strip, every file |
| TCO forecast accuracy | §D | wizard step 6 |
| Over-forecast penalty | §D | same control |

**Casepack keys read:** none directly; content marked per 0.3 §5.6.
**Instance scoping:** N/A — static HTML.
**Business-language check:** invariant I4.

---

## 3. Settled decisions

1. **Governance carries ownership and portfolio only.** Two jobs, one question.
2. **Information policy belongs to Security**, not Governance. Consent, retention, who can
   see records, whether access is logged, whether data may leave, staff monitoring — that
   is what Security is about.
3. **The capital request lives on the strip**, so it is reachable from wherever a team
   discovers they are short. Not buried on one screen.
4. **Governance costs nothing but attention.** Assigning an owner is free and teams will
   still skip it — the screen must not imply a price.
5. **Sidebar gains Governance** after People. Every file's sidebar updates.
6. Grammar inherited. One state per file. All `CONTRACTS.md` contracts honoured.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

Unchanged from 0.3/0.4, proven across nineteen files: one relative `<link>` to
`theme.css`, roles only, no declared tokens, no raw colour.

---

## 5. Design

### 5.1 GOVERNANCE — new screen

```
ONE QUESTION   Who owns what, and what are we still carrying?
DOMINANT       The ownership table — one row per capability, owner and sponsor.
               UNASSIGNED ROWS ARE VISUALLY LOUD. Free to fix, easy to skip,
               and skipping it is the lesson.
SECONDARY      In-flight work — what was started and not finished, with
               continue / pause / kill per row.
DEMOTED        Nothing. Two jobs, both load-bearing.
```

**Ownership table**

```
Capability            Owner            Business sponsor      Status
Outbound logistics    — unassigned —   — unassigned —        Needs attention
Operations            Priya Nandakumar Dana Ruiz             Complete
Firm infrastructure   Priya Nandakumar — unassigned —        Partly done
Marketing & sales     Tom Beckett      Tom Beckett           Complete
Inbound logistics     — unassigned —   — unassigned —        Needs attention
Service               — unassigned —   — unassigned —        Not started
```

Both selectors are Pattern A per `CONTRACTS.md`. Assigning costs nothing — no price
column, no confirmation step.

**In-flight work**

```
Initiative              Started  Rounds run  Spent     Action
Warehouse system        R2       1 of 3      $86,000   [continue] [pause] [kill]
Data platform scoping   R3       0 of 2      $12,000   [continue] [pause] [kill]
```

Killing shows what is recovered and what is sunk, before confirming.

### 5.2 SECURITY — add information policy

Appended below the existing component table, as its own section. **Do not restructure
what is there.**

```
INFORMATION POLICY — how the business handles data about people

  Collection        ○ explicit consent        ● collect by default
  Retention         ○ 12 months  ○ 3 years    ● indefinite
  Access            ○ named roles only        ● any head-office staff
  Access logging    ○ on                      ● off
  Data may leave    ○ never                   ● vendor systems permitted
  Staff monitoring  ○ none                    ● scheduling and performance
```

Pattern A. Each strict option states its cost in the same line — *"explicit consent —
about 40% fewer customer records to work with."* The trade-off is the teaching; a switch
with no stated cost is a morality quiz.

Below it, what is currently held:

```
  CUSTOMER   individual purchase histories · 41,000 people
             held in StockFlow (vendor) and the data platform
             collected by default · kept indefinitely · 14 staff can see it ·
             no record of who looks
```

### 5.3 WIZARD STEP 6 — render the TCO checklist

`components-wizard.html` renders step 6's heading and not its content. Step 6 becomes the
visible step; step 3 collapses.

```
What will it cost?
  Centraline IM 7 · bought as a service          $0 today · $9,100 per round

  What else do you expect to pay?
    ☐ Integration with existing systems
    ☐ Migrating data off the store spreadsheets
    ☐ Training warehouse staff
    ☐ Ongoing vendor support
    ☐ Additional platform capacity
    ☐ Backup and recovery for the new data
    ☐ Redesigning the ordering process
    ☐ Ongoing administration time

  Your projected total    $0
                                                          [ Add to plan ]
```

Unticked. The point is that a student forecasts and is later shown what they missed —
a pre-ticked checklist teaches nothing. Not every item applies; over-ticking must also
cost, which the engine handles.

### 5.4 SHELL — request additional capital

The strip gains one action, on every file:

```
Capital this round    $44,000 remaining of $220,000    [ Request more ]
```

Opening it:

```
Request additional capital from the CFO
  What is it for?          [                    ]
  Expected benefit         [                    ]
  Why can't it wait?       [                    ]
                                        [ Send request ]
```

Three fields. This is where the business case survives — required when asking for **more
money**, not as a toll on every purchase. The CFO can refuse.

### 5.5 Fixed data

Riverside round 3, consistent with 0.4 §5.4. Figures above are the complete set for this
packet; invent nothing further.

### 5.6 Every visible string

```
GOVERNANCE
  title        Governance
  sub          "Who owns what, and what the business is still carrying"
  columns      Capability · Owner · Business sponsor · Status
  unassigned   "— unassigned —"
  prompt       "Assigning an owner costs nothing."
  inflight     "In-flight work"
  in-cols      Initiative · Started · Rounds run · Spent · Action
  actions      "Continue" · "Pause" · "Kill"
  kill warn    "Killing this recovers $0. $86,000 is already spent."
  empty        "Nothing is in flight."

SECURITY (added)
  policy       "Information policy"
  policy sub   "How the business handles data about people"
  rows         "Collection" · "Retention" · "Access" · "Access logging"
               · "Data may leave" · "Staff monitoring"
  opts         "explicit consent" · "collect by default"
               "12 months" · "3 years" · "indefinite"
               "named roles only" · "any head-office staff"
               "on" · "off"
               "never" · "vendor systems permitted"
               "none" · "scheduling and performance"
  costs        "about 40% fewer customer records to work with"
               "no year-on-year comparison"
               "slower customer service"
               "forecloses several bought-as-a-service options"
               "lose scheduling optimisation, higher labour cost"
  held         "What the business currently holds"
  held detail  "individual purchase histories · 41,000 people"
               "collected by default · kept indefinitely · 14 staff can see it
                · no record of who looks"

WIZARD STEP 6
  heading      "What will it cost?"
  checklist    "What else do you expect to pay?"
  items        "Integration with existing systems"
               "Migrating data off the store spreadsheets"
               "Training warehouse staff"
               "Ongoing vendor support"
               "Additional platform capacity"
               "Backup and recovery for the new data"
               "Redesigning the ordering process"
               "Ongoing administration time"
  projected    "Your projected total"
  button       "Add to plan"

SHELL (added)
  action       "Request more"
  title        "Request additional capital from the CFO"
  fields       "What is it for?" · "Expected benefit" · "Why can't it wait?"
  send         "Send request"
```

### 5.7 Files

```
mockups/governance.html            ownership + in-flight, ready
mockups/governance-empty.html      round 1, nothing assigned, nothing in flight
mockups/security.html              MODIFIED — policy section appended
mockups/components-wizard.html     MODIFIED — step 6 rendered
mockups/capital-request.html       the request form, opened
ALL 19 existing files              sidebar gains Governance; strip gains [Request more]
```

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Roles only, no primitives, no raw colour | `git ls-files "mockups/*.html" \| xargs grep -nE "var\(--p-"` + declaration-context hex | zero both |
| I3 | No token declared outside `theme.css` | `git ls-files "mockups/*.html" \| xargs grep -n -- "^[[:space:]]*--[a-z-]*:"` | zero |
| I4 | No engine vocabulary | `git ls-files "mockups/*.html" \| xargs grep -niE "capability_key\|instance_id\|articulation\|SPOF\|RTO\|RPO\|EOL\b\|MOT\|level of detail\|grain"` | zero |
| I5 | Every string in §5.6 or an earlier copy block, or justified in `dod.md` | text-node diff | zero unaccounted |
| I8 | One state per file | `xargs grep -cE "State:"` | zero everywhere |
| I14 | Badge scale per `CONTRACTS.md` | computed style across all files | four mutually distinct |
| I15 | Selected state, correct pattern | ownership selectors and policy switches are **Pattern A**; nothing invents a third | confirmed |
| I16 | Rows that open a detail view look like it | in-flight rows, held-data row | confirmed |
| **I22** | **Every homeless factor now has a control** | FC-1 … FC-6 each locatable in a named file | 6 of 6 |
| **I23** | **Governance implies no cost** | `git ls-files "mockups/governance.html" \| xargs grep -ciE "\\\$[0-9]"` — only the in-flight *spent* column | no price on any assignment control |
| **I24** | **Every strict policy option states its cost** | read all six rows | 6 of 6, none bare |
| **I25** | **The TCO checklist ships unticked** | `grep -c "checked" components-wizard.html` | zero |
| **I26** | **Sidebar carries Governance in all files** | `git ls-files "mockups/*.html" \| xargs grep -c ">Governance<"` | every file ≥ 1 |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 0.4 merged, 19 mockups on `main` | `[V]` | `git ls-files "mockups/*.html" \| wc -l` | 19 |
| 2 | No governance screen exists | `[V]` | `ls mockups/governance.html 2>&1` | no such file |
| 3 | Governance appears once, in `review.html` | `[V]` | `git ls-files "mockups/*.html" \| xargs grep -ci governance \| grep -v ":0"` | one file |
| 4 | Wizard renders the heading, not the checklist | `[V]` | `grep -c "What else do you expect" mockups/components-wizard.html` | 0 |
| 5 | Three contracts available | `[V]` | `grep -c "Status badge scale\|Selected state\|Row opens detail" CONTRACTS.md` | 3 |
| 6 | **Nothing outside `mockups/` is touched** *(§4.2)* | `[V]` | after building: `git diff --name-only main..HEAD` | `mockups/*`, this folder's `dod.md`, `screenshots/0.5/*`, `.gitignore` |
| 7 | Screenshots committable | `[A]` | `git check-ignore -v screenshots/0.5/x.png` | **negation missing — add `!screenshots/0.5/*.png` and report** |

---

## 8. Build steps

**Step 1 — shell change first.** Sidebar gains Governance; strip gains `[ Request more ]`.
Applied to all 19 existing files plus the new ones. *Verify:* I26; the 19 differ only in
those two respects.

**Step 2 — `governance.html`, `governance-empty.html`.** *Verify:* I15, I16, I23.

**Step 3 — `security.html` policy section.** Appended, nothing restructured.
*Verify:* I24; the existing table unchanged.

**Step 4 — wizard step 6.** Step 6 visible, step 3 collapsed. *Verify:* I25.

**Step 5 — `capital-request.html`.** *Verify:* three fields, all required.

**Step 6 — consistency.** *Verify:* I22 — all six factors locatable; 24 files read as one
product.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7, esp. 6 and 7 | | |
| Steps 1–6 verified | | |
| I1, I3, I4, I5, I8, I14, I15, I16, I22–I26 | | |
| **All six homeless factors have a control** — FC-1 … FC-6 | | |
| Sidebar carries Governance in all files | | |
| 0.3/0.4 screens otherwise unmodified | | |
| Screenshots ×3 per new/changed file in `screenshots/0.5/` | | |
| `.gitignore` negation added | | |
| `findings/field-coverage-2026-07-27.md` re-run, six absences now zero | | |
| Auth / instance / casepack canaries | | **N-A** — static, no state, no auth |

---

## 10. Review

`playthrough.md`. Part B by an agent that has **not read this spec** (`README.md` R3).
Its central question: *can a student tell who owns what, and does the screen make clear
that assigning costs nothing?*
