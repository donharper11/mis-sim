# 0.4 — Reference Mockups, Remaining Seven · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2
**Author:** Claude (design session) · **Date:** 2026-07-27
**Phase:** 0 · **Depends on:** 0.3 (merged, `3395de8`) · **Blocks:** 0.5

> 0.3's three pilots settled the grammar. These seven inherit it — they do not reinvent it.
> Every contract they need already exists: badge scale, selected state, row-opens-detail,
> two-tier tokens, self-hosted fonts.

---

## 0. Spec Basis

**Read in full:**
- `mockups/platform.html`, `components.html`, `components-detail.html`,
  `components-wizard.html`, `rollout.html`, `rollout-detail.html` — the approved grammar
- `handoffs/0.3-mockup-pilot/spec.md` v3.2 — §5.1 shell, §5.2 hierarchy method, §5.7 copy
- `handoffs/0.3-mockup-pilot/alignment.md` + addendum — every finding and its disposition
- `findings/0.3-2026-07-26-audit.md` and audit `038f54e`
- `CONTRACTS.md` — badge scale · selected state · row opens detail · design tokens
- `frontend/src/styles/theme.css` — 38 primitives, 115 roles
- `design/02-traceability-matrix.md` · `design/03-scoring-frame-options.md`
- `BECSR/reference-workbench.html`, `reference-management.html` (VM `.5`)

**Extraction sufficiency:** covered. Unlike 0.3 v1 and v2, the grammar is not predicted —
it exists as eight files on `main`.

---

## 1. Purpose and scope

Seven reference mockups completing the student surface.

**In scope:**

```
Dashboard    the read side — where the loop closes
Strategy     declare and lock; what it means once locked
Security     firm-wide and unit-level protection, and the gaps
Services     support tiers, integration services, vendor support
People       IT staffing capacity against operational load
Challenges   the inbox — events and responses
Review       the decision sheet, the warnings mirror, the lock
```

**Out of scope — do not build:**
- **Debrief.** It is a downloadable business status report, not a screen. Different
  treatment — sectioned document, print layout, PDF. Specced separately.
- Any React component — that is 0.5
- Any backend, route, or data fetch
- `theme.css`, `main.jsx`, `DevTokens.jsx`, `fonts/` — done in 0.3, do not touch
- The six 0.3 mockups — do not restyle them. The four cosmetic findings carried from 0.3
  belong to **0.5**, where those become real components

**One exception, added 2026-07-27 — `mockups/components-detail.html` IS in scope,
for one repair only.**

Finding `0.3-021` was a defect in the built file. It was dispositioned as spec-fixed with
"no rebuild required", which was wrong — the spec amendment prevents recurrence but the
artifact merged to `main` carrying the defect. `main` therefore fails this packet's **I4**
before a line is written:

```
mockups/components-detail.html:13   "entities it owns · level of detail · who else needs them"
```

`level of detail` is barred from student screens by `CONTRACTS.md`. Three and a half of the
five tab panels render their own field list as visible text.

**Repair it with the copy in §5.5a. Change nothing else in that file** — not the CSS, not
the tab list, not the close control. Those remain 0.5's.

---

## 2. Project-specific statements

**Scoring factors displayed — the inversion from 0.3.** 0.3's I9 forbade scores on decision
pages. **Dashboard is not a decision page; it is where scores live.** Everything in
`design/02-traceability-matrix.md` §E surfaces here or in Debrief and nowhere else.

The six decision screens in this packet remain score-free. I9 still applies to them.

**Casepack keys read:** none directly; content marked per 0.3 §5.6.
**Instance scoping:** N/A — static HTML.
**Business-language check:** invariant I4, now including `level of detail` and `grain`.

---

## 3. Settled decisions

1. **The grammar is inherited, not reinvented.** Same shell, same strip, same table
   pattern, same detail-with-tabs. A screen that invents a new pattern is a finding.
2. **One state per file** (0.3 I8).
3. **Every contract in `CONTRACTS.md` is honoured**: badge scale, selected state,
   row-opens-detail.
4. **Scores appear on Dashboard only** (§2).
5. **Dashboard's centrepiece is the unit-response chain** (§5.2) — not a scorecard. The
   scorecard is context; the chain is the lesson.
6. **Debrief deferred**, with a reason (§1).
7. Static HTML, `file://`, desktop-first 1440 holding 1280/1024.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

Identical to 0.3 and already proven across eight files:

```
mockups/dashboard.html
  <link rel="stylesheet" href="../frontend/src/styles/theme.css">   ← I6 permits only this
  <style> .panel { background: var(--surface-card); } </style>      roles only    → I1 ✓
                                                                    declares none → I3 ✓
  <body> … no raw hex, no var(--p-…) …                                            → I1 ✓
```

---

## 5. Design

### 5.1 Shell — unchanged from 0.3 §5.1

Sidebar, title row, capital strip. **Copy it; do not redesign it.** Every file states its
round (0.3 v3.2).

### 5.2 Hierarchy — the one question, dominant, demoted

---

**DASHBOARD**

```
ONE QUESTION   How are we doing, and what needs attention?
DOMINANT       WHAT NEEDS ATTENTION — the throttled unit and the critical signal.
               A three-second read must yield: "the warehouse got a system and
               nothing else, and the order system is out of capacity."
SECONDARY      THE UNIT RESPONSE CHAIN (§5.3). This is the screen's substance.
THIRD          Balanced Scorecard — four tiles, labelled "Balanced Scorecard"
               in words, not as a list of its own perspectives.
DEMOTED        Value chain coverage against strategy · open-signal list · inbox count
```

---

**STRATEGY**

```
ONE QUESTION   What are we optimising for, and what does that commit us to?
DOMINANT       When unlocked: four options, selected state visible (CONTRACTS).
               When locked: the declared strategy and WHAT IT MEASURES YOU ON.
SECONDARY      Capability weights — where this strategy says value lies.
               What it punishes (cost leadership punishes overprovisioning).
DEMOTED        Reopen action. Present, expensive, never inviting.
```

A locked Strategy screen is not dead space — it is where a student re-reads what they
committed to.

---

**SECURITY**

```
ONE QUESTION   What protects us, and what doesn't?
DOMINANT       A table of security components, firm-wide and unit-level.
               GAPS ARE VISUALLY EQUAL TO ENTRIES — "no central sign-on" must
               occupy the same weight as a deployed firewall.
SECONDARY      What each gap exposes, in business terms.
DEMOTED        Cost column.
```

---

**SERVICES**

```
ONE QUESTION   Who fixes it when it breaks, and who connects it?
DOMINANT       Support tier — Basic · Standard · Premium, selected state visible.
SECONDARY      Integration services tier. Per-component vendor support, as a table.
DEMOTED        Nothing.
```

---

**PEOPLE**

```
ONE QUESTION   Do we have enough people to run what we have bought?
DOMINANT       The capacity bar — staff against operational load, over-committed
               state unmissable.
SECONDARY      Where the load comes from, itemised.
               What over-commitment costs: slower recovery, patching slips,
               rollout support suffers.
DEMOTED        Hire / retain / upskill actions, and managed support as the
               alternative to headcount.
```

---

**CHALLENGES**

```
ONE QUESTION   What is happening to us, and what do we do about it?
DOMINANT       The inbox — one row per item, sender, one-line summary, age.
SECONDARY      An opened item: full text, response options, rationale tag.
DEMOTED        Resolved items, collapsed.
```

---

**REVIEW**

```
ONE QUESTION   What am I committing to, and what have I missed?
DOMINANT       The decision sheet — every decision this round, by category,
               with its cost.
SECONDARY      THE WARNINGS MIRROR. Computed, never blocking. This is the
               last honest moment before a team locks.
DEMOTED        Nothing. This screen has two jobs and both are load-bearing.
ACTION         [ Lock round ] — enabled always. Warnings inform, never gate.
```

### 5.3 The unit-response chain — Dashboard's centrepiece

This is what makes a score an explanation. One block per unit:

```
WAREHOUSE · 34 people
  Running        Centraline IM 7 · core configuration · pinned round 2
  Implemented    no training · process unchanged · no communication
  Responding     adoption 22% · picking 20 minutes slower per truck than June
  Contributing   Outbound logistics — 25% of what it could deliver

STORE OPERATIONS · 140 people
  Running        Order Mgmt v4.2 · POS System 2011 · store spreadsheets
  Implemented    partial training · picking process partly redesigned
  Responding     adoption 61% · spreadsheets still in daily use
  Contributing   Operations — 44% of what it could deliver

FINANCE · 8 people
  Running        Accounting Package
  Implemented    fully trained · process redesigned · communicated
  Responding     adoption 94%
  Contributing   Firm infrastructure — 81% of what it could deliver
```

A student reads down one block and sees cause and effect without any theory attached.
**Rows must be ordered worst first.**

### 5.4 Fixed data — exact, invent nothing

Riverside Grocers · round 3 of 6 · Low-Cost Leadership (locked round 2)
Capital this round: **$44,000 remaining of $220,000** · Run-rate **$58,300**

```
DASHBOARD
  Balanced Scorecard   Financial 61 · Customer 48 · Internal Process 39 ·
                       Learning & Growth 27
  Needs attention      Order system near capacity — critical, raised R2, open 2 rounds
                       Warehouse: system deployed, nothing implemented
  Unit chain           per §5.3
  Value chain          Inbound 1/4 · Operations 2/4 ▸ · Outbound 4/5 ▸ ·
                       Marketing & sales 5/5 · Service 0/4
                       Firm infrastructure 3/4 · HR ok · Technology — · Procurement 0/3
  Signals              3 open · Inbox 3 items waiting

STRATEGY  (locked)
  Declared   Low-Cost Leadership, round 2
  Measured on   cost per transaction
  Weights    Outbound logistics 0.35 · Operations 0.30 · Firm infrastructure 0.15
             · Customer insight 0.10 · Marketing & sales 0.10
  Punishes   overprovisioning — unused headroom is waste, not safety
  Reopen     $80,000 and a resistance spike across every unit

SECURITY
  Component              Scope      Placement  Status
  Next-gen firewall      firm-wide  on-prem    Complete
  Backup & recovery      firm-wide  on-prem    Needs attention — never restore-tested
  Central sign-on        firm-wide  —          Not started
  Intrusion detection    firm-wide  —          Not started
  Store till access      unit       on-prem    Complete
  Exposure: 4 separate logins · no record of who views customer data ·
            recovery would take 2 days and lose up to a day of transactions

SERVICES
  Support tier        ● Basic $20,000   ○ Standard $50,000   ○ Premium $100,000
  Integration tier    ● Basic $50,000   ○ Advanced $120,000  ○ Vendor-managed $200,000
  Vendor support      POS System 2011 — ends round 4
                      Order Mgmt v4.2 — current
                      Accounting Package — current

PEOPLE
  Staff       2.0 FTE          Load  3.4        Over-committed 170%
  Load from   platform services 1.9 · applications 1.5
  Effects     incident recovery slower · patching slips · rollout support thin
  Hire        +1.0 FTE $31,000/round, available in 1 round
  Retain      $9,000/round     Upskill  $14,000
  Alternative managed support adds 0.6 FTE-equivalent, immediately, no knowledge retained

CHALLENGES  (3 waiting)
  Tom Beckett, COO — "The auditors asked how we know our inventory numbers are
    right. I did not have an answer."  · raised R3 · responds by lock
  Dana Ruiz, Warehouse Manager — "My crew found out about the new system when the
    tablets arrived."  · raised R3 · responds by lock
  Centraline (vendor) — "Support for your point-of-sale version ends in one round."
    · raised R3 · responds by lock

REVIEW
  Platform      1 change      $0 capex        +$0/round
  Components    2 changes     $98,000 capex   +$3,900/round
  Rollout       1 change      $34,000
  Services      1 change      $30,000
  People        0 changes     $0
  Governance    2 assignments $0
  Challenges    2 responses   $14,000
  ───────────────────────────────────────────────────────
  Capital       $176,000 of $220,000        Remaining $44,000
                (v0.4-002 fix: was $174,000/$46,000, which contradicted the
                 strip's $44,000 on the same screen. The line items were
                 internally correct; they simply did not reconcile with the
                 state every other mockup shows. Challenges 12,000 → 14,000.)
  Run-rate      $62,200 per round           was $58,300
  Warnings      You added capacity to Order Fulfilment and funded no training.
                Two open signals received no action this round.
                Customer Insight carries 0.10 of your strategy weight and $0 of spend.
```

### 5.5 Every visible string

Shell strings are 0.3 §5.7 — reuse, do not restate. New strings only:

```
DASHBOARD
  title           Dashboard
  sub             "Where the business stands this round"
  attention       "Needs attention"
  scorecard       "Balanced Scorecard"
  chain           "How each unit is responding"
  chain labels    "Running" · "Implemented" · "Responding" · "Contributing"
  chain unit      "34 people"
  valuechain      "Coverage across the value chain"
  weighted        "Weighted by your strategy"
  signals         "Open signals"
  inbox           "3 items waiting"
  empty           "No results yet — your first round runs at the deadline."

STRATEGY
  title           Strategy
  sub             "What the business is optimising for"
  locked          "Locked in round 2"
  measured        "You are measured on"
  weights         "Where this strategy says value lies"
  punishes        "What this strategy punishes"
  reopen          "Reopen strategy"
  reopen warn     "Reopening costs $80,000 and unsettles every unit."
  unlocked prompt "Choose what this business competes on."

SECURITY
  title           Security
  sub             "What protects the business, and what does not"
  columns         Component · Scope · Placement · Status
  scope firm      "Firm-wide"     scope unit "Unit"
  gap             "Nothing provides this yet"
  exposure        "What this leaves exposed"

SERVICES
  title           Services
  sub             "Who fixes it when it breaks, and who connects it"
  support         "Support tier"      integration "Integration services"
  vendor          "Vendor support by component"
  ends            "Ends round 4"      current "Current"

PEOPLE
  title           People
  sub             "The people who run what the business has bought"
  capacity        "IT capacity"
  over            "Over-committed"
  loadfrom        "Where the load comes from"
  effects         "What over-commitment costs you"
  hire            "Hire"  ·  retain "Retain"  ·  upskill "Upskill"
  alt             "Or buy support instead of hiring"

CHALLENGES
  title           Challenges
  sub             "What is happening to the business this round"
  from            "From"      age "Raised round 3"     due "Responds by lock"
  respond         "Fund" · "Defer" · "Reject"
  why             "Why?"
  why options     "Capacity risk" · "Strategic priority" · "Cost containment"
                  · "Compliance" · "Not aligned with strategy"
                  · "Insufficient information"
  resolved        "Resolved this round"

REVIEW
  title           Review
  sub             "What you are committing to this round"
  columns         Area · Changes · Capital · Run-rate effect
  totals          "Capital committed" · "Run-rate after this round"
  mirror          "Before you lock"
  mirror note     "These do not stop you. They are what a careful reader would notice."
  lock            "Lock round"
  locked          "This round is locked. Decisions reopen when the round advances."
```

Anything not listed goes in `dod.md` with a justification.

### 5.5a Component detail tabs — the copy 0.3 never had *(repair of `0.3-021`)*

0.3 §5.4 described what each tab *contains*; no copy block ever gave what it *says*. This
is that copy, for `Order Mgmt v4.2`. Only `Deployment` is currently correct — it is
included so the pattern is unambiguous.

```
Overview      "Order management for the eight stores. Serves outbound logistics.
               Used by 140 people in store operations."

Deployment    "Runs on-premises · standard configuration · uses 35% of platform capacity"
              (already correct — do not change)

Data          "Holds every order, line by line. You can see what each customer
               ordered — not what they browsed.
               Inventory counts live here too, and the warehouse system needs them."

Connections   "Fed by the point-of-sale system — product records.
               Feeds financial reporting and the warehouse.
               3 connections · $900 per round"

Lifecycle     "Installed round 2 · expected to last 6 rounds.
               Vendor support current, no end date announced."
              buttons: "Upgrade"  ·  "Retire"
```

**Note the register on Data.** `CONTRACTS.md` bars `level of detail` and `grain` from
student screens and requires the business form instead — *"you can see what each customer
ordered, not what they browsed"* rather than *"ORDER at order_line grain."*

### 5.6 Files to produce

```
mockups/dashboard.html              ready
mockups/dashboard-empty.html        round 1, before any results
mockups/strategy.html               locked
mockups/strategy-unlocked.html      round 1, four options, none chosen
mockups/security.html
mockups/services.html
mockups/people.html
mockups/challenges.html             inbox list
mockups/challenges-item.html        one item opened, response options
mockups/review.html
mockups/review-locked.html

mockups/components-detail.html   REPAIRED, not rebuilt — §5.5a only
```

Eleven files, one state each.

---

## 6. Invariants

Phrased as **positive requirements** wherever possible. 0.3's I11 read as the absence of a
control and passed while the requirement failed — see `alignment.md` addendum.

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Roles only | `git ls-files "mockups/*.html" \| xargs grep -nE "var\(--p-"` and the declaration-context hex check | zero both |
| I3 | No token declared outside `theme.css` | `git ls-files "mockups/*.html" \| xargs grep -n -- "^[[:space:]]*--[a-z-]*:"` | zero |
| I4 | No engine vocabulary | `git ls-files "mockups/*.html" \| xargs grep -niE "capability_key\|instance_id\|articulation\|SPOF\|RTO\|RPO\|EOL\b\|MOT\|level of detail\|grain"` | zero |
| I5 | Every string in §5.5 or 0.3 §5.7, or justified in `dod.md` | text-node diff | zero unaccounted |
| I6 | One external reference per file, `theme.css` | `git ls-files "mockups/*.html" \| xargs grep -nE "<link\|@import\|src=\|https?://"` | one `<link>` each |
| I7 | Riverside marked as content | `git ls-files "mockups/*.html" \| xargs grep -niE "riverside\|grocer" \| grep -v data-casepack` | zero |
| I8 | One state per file | `git ls-files "mockups/*.html" \| xargs grep -cE "State:"` | zero in every file |
| I9 | **Scores appear on Dashboard only** | grep the six decision screens for a realised percentage or scorecard value | zero outside `dashboard*.html` |
| I12 | No third-party font request | `git ls-files \| grep -E "frontend/\|mockups/" \| xargs grep -niE "googleapis\|gstatic"` | zero |
| I13 | Fonts and licence still shipped | `git ls-files "frontend/src/styles/fonts/*"` | 5 `.woff2` + `LICENSE.txt` |
| I14 | Badge scale per `CONTRACTS.md` | `getComputedStyle` across all files: one label, one colour, four mutually distinct | confirmed |
| I15 | **Selected state present** wherever a choice is offered — Strategy options, Services tiers, Challenges rationale tags | each: chosen visibly distinct from unchosen | confirmed |
| I16 | **Rows that open a detail view look like it** — Security, Services vendor table, Challenges inbox | chevron + `--text-link` + hover highlight | confirmed |
| I17 | **The Review mirror is present and non-blocking** | all three §5.4 warnings render; `[ Lock round ]` is enabled beside them | confirmed |
| I18 | **The unit chain is ordered worst first** | read `dashboard.html`: Warehouse before Store operations before Finance | confirmed |
| I19 | **Gaps carry the same visual weight as entries** on Security | "Not started" rows are full rows, not greyed footnotes | confirmed |
| I20 | **Review reconciles with the strip** *(finding `0.4-002`)* | strip remaining == `220,000 − capital committed`; line items sum to the committed total | both hold |
| I21 | **One selection grammar per option shape** *(`CONTRACTS.md`; finding `0.4-001`)* | `git ls-files "mockups/*.html" \| xargs grep -c "●\|○"` — Pattern A files only; Pattern B files show outline + fill + check | no file mixes the two; no third pattern anywhere |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 0.3 merged; eight mockups on `main` | `[V]` | `git ls-tree -r --name-only origin/main -- mockups/ \| wc -l` | 8 |
| 2 | Token map intact | `[V]` | `grep -c '^\s*--p-' frontend/src/styles/theme.css` | 38 |
| 3 | Fonts and licence present | `[V]` | `git ls-files "frontend/src/styles/fonts/*"` | 6 files |
| 4 | Three contracts exist | `[V]` | `grep -c "Status badge scale\|Selected state\|Row opens detail" CONTRACTS.md` | 3 |
| 5 | **Nothing outside `mockups/` and `docs/` is touched** *(§4.2)* | `[V]` | after building: `git diff --name-only main..HEAD` | only `mockups/*`, `docs/*`, `handoffs/0.4-mockups-remaining/dod.md`, `screenshots/0.4/*` |
| 6 | `screenshots/0.4/` is committable | `[A]` | `git check-ignore -v screenshots/0.4/x.png` | **`.gitignore` negates `0.2` and `0.3` only — add `!screenshots/0.4/*.png` before shooting, and report it** |
| 6b | **`main` currently FAILS I4** — this is known and is repaired by §5.5a, not a reason to stop | `[V]` | `git ls-files "mockups/*.html" \| xargs grep -c "level of detail"` | one hit, in `components-detail.html`. **After the §5.5a repair: zero** |
| 7 | 0.3's grammar readable | `[V]` | `ls mockups/*.html` | 8 files. **Open `components.html` and `components-detail.html` before building — they are the pattern** |

---

## 8. Build steps

**Step 1 — Dashboard.** `dashboard.html`, `dashboard-empty.html`. The unit chain is the
substance; the scorecard is context. *Verify:* I1, I3–I9, I18 · shots at 1440/1280/1024.

**Step 2 — Strategy.** `strategy.html`, `strategy-unlocked.html`. *Verify:* same, plus I15
on the four options.

**Step 3 — Security and Services.** `security.html`, `services.html`. *Verify:* same, plus
I15 on the tiers, I16 and I19 on Security.

**Step 4 — People and Challenges.** `people.html`, `challenges.html`,
`challenges-item.html`. *Verify:* same, plus I15 on rationale tags, I16 on the inbox.

**Step 5 — Review.** `review.html`, `review-locked.html`. *Verify:* same, plus I17.

**Step 6 — Consistency.** All eleven read as one product with the six from 0.3.
*Verify:* seventeen 1440 screenshots side by side; shell identical throughout.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7, esp. 5 and 6 | | |
| Steps 1–6 verified | | |
| I1, I3–I9, I12–I21 | | |
| Eleven files, one state each | | |
| `components-detail.html` repaired per §5.5a; nothing else in it changed | | |
| I4 passes across **all** tracked mockups after the repair | | |
| Strings not in §5.5 / 0.3 §5.7, justified | | |
| Screenshots ×33 (11 files × 3 viewports) in `screenshots/0.4/` | | |
| `.gitignore` negation added for `screenshots/0.4` | | |
| 0.3's six mockups untouched | | |
| Nothing touched outside §1 scope | | |
| Auth / instance / casepack canaries | | **N-A** — static, no state, no auth |

---

## 10. Review

`playthrough.md` in this folder. **Part B is run by an agent that has not read this spec**
(`handoffs/README.md` R3). 0.3's auditor is disqualified for these seven.
