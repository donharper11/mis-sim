# 0.3 — Token Map + Mockup Pilot · Build Spec

**Version 3.2** · **Authored under** `SPEC_PROTOCOL.md` v1.2
**Author:** Claude (design session) · **Date:** 2026-07-27
**Phase:** 0 · **Depends on:** 0.2 (merged) · **Blocks:** 0.4, 0.5

> **v3.1 folds in the 0.3 audit.** Read `alignment.md` in this folder first — it states
> what survives, what is discarded, and what each finding became.
>
> **v3 replaces Steps 2–5. Steps 1 and 1b stand — do not redo them.**
>
> The token map (`--p-` primitives + 115 roles) and the self-hosted fonts are built,
> verified, and correct. What changes is *which three screens the pilot builds and how
> they are structured.*
>
> v2 specced **Situation · Platform · Applications** as content inventories — "must show
> A, B, C" with no hierarchy — and got three dense screens where a student cannot find
> what they own, cannot add anything, and cannot change anything. That is a spec defect,
> not a build defect. v3 respecs the pilot as **Platform · Components · Rollout**, built
> on the list→detail→tabs pattern the house already uses.

---

## 0. Spec Basis

**Read in full:**
- `frontend/src/styles/theme.css` @ branch — the built two-tier map, 38 primitives, 115 roles
- `screenshots/0.3/situation-1440.png`, `applications-1440.png` — the v2 output, examined
- **`BECSR/reference-workbench.html`** (VM `.5`) — sidebar grouped **Company results** /
  **Decisions**; workbench = title → budget strip → **table of owned programs** with
  attribute columns
- **`BECSR/reference-management.html`** — detail page as **tabs**: Implementation ·
  Basics · Resources · Media · Geography · Supplier, each holding its settings, then Close
- `BECSR/becsr-design-system.md` 1–70
- `design/02-traceability-matrix.md` · `design/03-scoring-frame-options.md` ·
  `design/04-decisions-g1-g6.md`
- `findings/0.3-2026-07-26-audit.md`

**Extraction sufficiency:** covered. The BECSR reference pages were the missing input in
v1 and v2 — the design system doc was read, the pages it described were not.

---

## 1. Purpose and scope

Three reference mockups establishing the **decision-page grammar** the other seven copy.

**In scope:**
- `mockups/platform.html` · `mockups/components.html` · `mockups/rollout.html`
- One file per screen **state** (v3 — see §3 decision 3)
- `docs/mockup-review.md`

**Out of scope — do not build:**
- Dashboard. It displays what these three produce, so it comes after they settle
- Strategy · Security · Services · People · Challenges · Review · Debrief — that is 0.4
- Any React component — 0.5
- Any backend, route, or data fetch
- `theme.css`, `main.jsx`, `DevTokens.jsx`, `frontend/src/styles/fonts/` — **done in
  Step 1/1b, do not touch**

---

## 2. Project-specific statements

**Scoring factors displayed:** none of these three show a score. They are decision pages —
they show what you have, what you can add, and what it costs. **Scores appear on Dashboard
and in Debrief only.** A capability percentage or an MOT term on any of these three is a
finding.

That is a deliberate reversal of v2, which put realised value on a decision page and
produced a screen students could read but not act on.

**Casepack keys read:** none directly; sample content marked per §5.6.
**Instance scoping:** N/A — static HTML.
**Business-language check:** invariant I4.

---

## 3. Settled decisions

1. **The three pilots are Platform, Components, Rollout** — the three stages where money is
   spent. Dashboard is the read side and depends on all three.
2. **List → detail → tabs**, per BECSR. A decision page opens as a **table of what you
   own**, a row opens a detail view, the detail view uses **tabs** for its settings.
3. **One state per file.** `platform.html`, `platform-empty.html`, `platform-locked.html`.
   v2's stacked-states-in-one-file was my Open Decision O2 and it made every screen
   unreadable — three pages appeared glued together.
4. **Hierarchy is specified, not left to the builder.** Every screen declares its one
   question, what dominates, and what is demoted (§5.2). A content list produces a content
   dump; that is what v2 proved.
5. **Platform is the FIRM-WIDE stage.** Hosting posture plus firm-wide components and
   services. Data warehouse and lake live here.
6. **Components is the UNIT-LEVEL stage**, entered through a six-step wizard. Data marts
   live here. Its catalog is **conditional on what Platform provides**.
7. **Rollout is per deployment, never bulk.** One row per (component × unit) pin, each with
   its own mix. There is no "train everyone" control. A marketing mix is product-specific.
8. **No scores on these screens** (§2).
9. **MOT stays under the hood.** BSC is the visible score, and it appears on Dashboard —
   not here.
10. Ant Design is not used in mockups; static HTML; desktop-first 1440, holding 1280/1024.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

```
mockups/platform.html
  <link rel="stylesheet" href="../frontend/src/styles/theme.css">   ← I6 permits only this
  <style> .ws-table th { background: var(--surface-table-header); } </style>
                                                       roles only          → I1 ✓
                                                       declares no token   → I3 ✓
  <body> … sidebar · title · budget strip · table · no raw hex, no var(--p-…) …  → I1 ✓
```

Unchanged from v2.2 and still the only compliant route.

---

## 5. Design

### 5.1 The shell — identical on all three

```
SIDEBAR (dark navy, --surface-sidebar)
  Riverside Grocers
  Dashboard
  DECISIONS            ← section label, not a link
    Strategy
    Platform
    Components
    Rollout
    Security
    Services
    People
  Challenges
  Review
  Debrief

TOP        page title · "Round 3 of 6" · strategy chip right-aligned
STRIP      Capital remaining · Run-rate · trend        ← one line, never a panel
BODY       the page
```

The sidebar grouping is BECSR's own (**Company results** / **Decisions**). "Review", not
"Review & Lock" — the lock is a button on that page.

### 5.2 Hierarchy — stated per screen, non-negotiable

Each screen declares **the one question**, **what dominates**, **what is demoted**. A
builder that gives every region equal weight has not met the spec.

---

**PLATFORM — the firm-wide foundation**

```
ONE QUESTION   What runs where across the whole firm, and what are we missing?
DOMINANT       The two hosting panels — Cloud | On-Premises — side by side,
               each listing the firm-wide services placed there.
               These are the screen.
SECONDARY      Not provisioned — an explicit list of absences, visually distinct
               from the panels. "Central sign-on" and "Data platform" must read
               as MISSING, not as empty space.
DEMOTED        Capacity percentages, integration count and cost — one line.
               Split-rule selector appears only when both panels hold something.
ACTION         [ + Add firm-wide component ]   [ + Add firm-wide service ]
```

Three seconds should yield *"we run almost everything on-premises and we have no central
sign-on."*

---

**COMPONENTS — unit-level, the workbench**

```
ONE QUESTION   What do we have, and what do I add?
DOMINANT       ONE TABLE of every unit-level component owned.
               Not cards. Not a value chain. A table.
               Item · Category · Runs on · Serves · For whom · Users ·
               Capacity · $/round · Status
SECONDARY      Category filter chips — Hardware · Software · Database · Network.
               Filtering is a view, not a navigation.
DEMOTED        Everything else.
ACTION         [ + Add component ]  → opens the six-step wizard (§5.3)
               Clicking a row → detail with tabs (§5.4)
```

A student asking *"what do we own?"* gets the answer in one view. v2's Applications page
could not answer that at all.

---

**ROLLOUT — implementing into units**

```
ONE QUESTION   Which of our systems have actually landed with the people using them?
DOMINANT       ONE TABLE of deployments, one row per (component × unit) pin.
               System · Unit · People · Trained · Process · Communication · Adoption
               Rows needing attention are visually obvious.
SECONDARY      nothing
DEMOTED        nothing
ACTION         Clicking a row → allocate the mix FOR THAT DEPLOYMENT ONLY (§5.5)
```

Three seconds should yield *"the warehouse got a system and nothing else."*

### 5.3 The Components wizard — six steps

Entered by `[ + Add component ]`. One step visible at a time, back permitted, cost running.

```
1  WHERE WILL IT RUN?
   Your platform: On-premises (4 services) · Cloud (1 service)
   Or: Bought as a service — bypasses your platform entirely
   Shows remaining capacity for each. An option the platform cannot support
   is shown DISABLED with the reason, never hidden.

2  WHAT ARE YOU ADDING?
   Hardware · Software · Database · Network
   Catalog filtered to what Step 1 can support.

3  FOR WHAT PURPOSE?
   Which value-chain activity does this serve?
   Support:  Firm infrastructure · Human resources · Technology · Procurement
   Primary:  Inbound logistics · Operations ▸ · Outbound logistics ▸ ·
             Marketing & sales · Service
   ▸ = weighted by your declared strategy

4  FOR WHOM?
   Which unit will use it?
   Warehouse (34) · Store operations (140) · Finance (8) · Head office (21)
   This is the pin. It is REQUIRED — there is no "firm-wide" option here;
   that is what the Platform stage is for.

5  HOW IS IT CONFIGURED?
   Config tier · capacity · data it will own · what it must connect to

6  WHAT WILL IT COST?
   Capex · opex · "what else do you expect to pay?" checklist
   [ Add to plan ]
```

Steps 3 and 4 are the load-bearing ones. They are what make the unit's response
computable — you declared what it is for and who it is for, so alignment can be measured.
**Neither may be skippable.**

### 5.4 Component detail — tabs

> **STRUCTURAL DESCRIPTION, NOT COPY.** The lines below say what each tab *contains*.
> They are not strings to render. Rendering them verbatim was finding `0.3-021` — three
> and a half of five panels shipped their own field list as visible text. The strings and
> the values belong in §5.7 and §5.6.

Clicking a table row. Tabs per BECSR's management page:

```
Overview · Deployment · Data · Connections · Lifecycle        [ Close ]

Overview     what it is, what it serves, who it is for, current status
Deployment   where it runs, config tier, capacity drawn
Data         entities it owns, level of detail, who else needs them
Connections  what feeds it, what it feeds, cost per connection
Lifecycle    installed round, service life, vendor support horizon,
             [ upgrade ] [ retire ]
```

### 5.5 Rollout detail — the mix, per deployment

```
Centraline IM 7 → Warehouse · 34 people
  Training        ○ none $0   ○ basic 8h $12,000   ○ full 24h $34,000
  Process         ○ keep current $0   ○ redesign picking $22,000
  Communication   ○ none $0   ○ programme $8,000
  Current: 0 trained · process unchanged · no communication
  [ Apply to this deployment ]
```

**No control on this page affects more than one deployment.** A bulk action is a finding.

### 5.6 Fixed data — exact, invent nothing

```
Riverside Grocers · 8 stores · round 3 of 6 · Low-Cost Leadership (locked R2)
Capital remaining $44,000 of $220,000        ← round 3
  (round-1 empty state: $400,000 of $400,000 — budget curve [400000, 260000, 220000, …])
Run-rate  R1 $47,000 → R2 $53,000 → R3 $58,300

PLATFORM — firm-wide
  On-premises   Compute pool          100% used
                Storage pool           70% used
                Network & WAN          10 single points of failure
                Backup & recovery      never restore-tested
  Cloud         End-user email         placed R2
  Not provisioned   Central sign-on · Data platform
  7 connections between systems · $3,100 per round

COMPONENTS — unit level
  Item                 Category  Runs on   Serves              For whom      Users  $/round  Status
  Order Mgmt v4.2      Software  on-prem   Outbound logistics  Store ops      140   $2,400   Partly done
  POS System 2011      Software  on-prem   Marketing & sales   Store ops       62   $3,100   Support ends R4
  Accounting Package   Software  on-prem   Firm infrastructure Finance          8     $900   Complete
  Store spreadsheets   Software  —         Operations          Store ops      140       $0   Needs attention
  Order DB cluster     Database  on-prem   Outbound logistics  Store ops        —     $600   Complete
  Store back-office PC Hardware  on-prem   Operations          Store ops        8     $200   Complete

ROLLOUT — deployments
  System              Unit         People  Trained  Process     Communication  Adoption
  Order Mgmt v4.2     Store ops      140     35%    partial     done             61%
  POS System 2011     Store ops       62    100%    redesigned  done             97%
  Accounting Package  Finance          8    100%    redesigned  done             94%
  Store spreadsheets  Store ops      140      —     unchanged   none             48%   ⚠

WIZARD (components-wizard.html)
  Adding: Centraline IM 7 · Database · serves Operations · for Warehouse (34)
    On our on-premises platform   $86,000 + $1,900/round · available in 2 rounds
                                  ⚠ would use all remaining platform capacity
    On our cloud subscription     $12,000 + $7,400/round · available now
    Bought as a service           $0 + $9,100/round · available now
                                  ⚠ inventory data would leave your systems
                                  ⚠ a fourth separate login — no central sign-on
```

### 5.7 Every visible string

```
SHELL
  sidebar     Riverside Grocers · Dashboard · DECISIONS · Strategy · Platform ·
              Components · Rollout · Security · Services · People ·
              Challenges · Review · Debrief
  round       "Round 3 of 6"   ·   empty-state files: "Round 1 of 6"
              EVERY file states its round (v3.1). $400,000 and $220,000 are both
              correct — rounds 1 and 3 of the budget curve — and read as a
              contradiction only when the round is unstated
  strategy    "Low-Cost Leadership · locked in round 2"
              round-1 empty state: "Strategy not yet declared"
              (v3.2 - platform-empty showed "Round 1 of 6" beside "locked in
               round 2", an event that had not happened yet.)
  strip       "Capital this round" · "Run-rate"
              value reads "$44,000 remaining of $220,000"
              (v3.2 - finding 0.3-018. The denominator is THIS ROUND'S allocation,
               not a programme total. "Capital remaining $X of $Y" with Y changing
               per round read as two programme totals for one company.)
  trend       "Run-rate rises every round it is not managed"
  legend      "Dotted underline = supplied by the case, not the platform"
  locked      "This round is locked. Decisions reopen when the round advances."

PLATFORM
  title       Platform
  sub         "What the whole firm runs on"
  panels      Cloud · On-Premises
  missing     "Not provisioned"
  missing sub "Nothing provides this yet"
  capacity    "Capacity used"
  warning     "No headroom. The next component will not fit."
  fragility   "10 single points of failure"
  links       "7 connections between systems · $3,100 per round"
  hybrid      "You are running a hybrid platform."
  hybrid sub  "1 service in cloud · 4 on-premises"
  split ask   "What determines the split?"
  split opts  "Workload profile — steady on-premises, bursty in cloud"
              "Data sensitivity — regulated on-premises, rest in cloud"
              "Lifecycle — legacy stays, new builds go to cloud"
              "Cost profile — high-utilisation workloads on-premises"
              "No rule yet — case by case"
  actions     "Add firm-wide component" · "Add firm-wide service"
  empty       "Nothing is provisioned yet. Start with somewhere to run things."

COMPONENTS
  title       Components
  sub         "What each part of the business runs"
  columns     Item · Category · Runs on · Serves · For whom · Users ·
              Capacity · Cost per round · Status
  filters     All · Hardware · Software · Database · Network
  action      "Add component"
  empty       "No components yet. Everything the business runs is added here."
  statuses    Complete · Partly done · Needs attention · Not started
  detail tabs Overview · Deployment · Data · Connections · Lifecycle
  close       "Close"

WIZARD
  1  "Where will it run?"          "Bought as a service — bypasses your platform"
     disabled reason  "Your platform has no capacity for this"
  2  "What are you adding?"
  3  "For what purpose?"           "Weighted by your strategy"
     groups  "Support activities" · "Primary activities"
  4  "For whom?"                   "Which unit will use this?"
  5  "How is it configured?"
  6  "What will it cost?"          "What else do you expect to pay?"
     button  "Add to plan"
  deployment-mode copy — ALL THREE, one set each (v3.1; the third had none in v2
  and the gap got filled rather than reported)
     on-premises  "This would use all remaining platform capacity."
     cloud        (no warning — this option is unconstrained here. Stated so a
                   builder does not invent one)
     as a service "Inventory data would leave your systems."
                  "A fourth separate login — you have no central sign-on"
  back "Back"   cancel "Cancel"

ROLLOUT
  title       Rollout
  sub         "Getting systems into the hands of the people who use them"
  columns     System · Unit · People · Trained · Process · Communication · Adoption
  detail      "Training" · "Process" · "Communication"
  training    "none" · "basic, 8 hours" · "full, 24 hours"
  process     "keep current" · "redesign picking"
  comms       "none" · "programme"
  current     "Current: 0 trained · process unchanged · no communication"
  apply       "Apply to this deployment"
  empty       "Nothing has been rolled out yet."
```

Anything not listed goes in `dod.md` with a justification.

### 5.8 Files to produce

```
mockups/platform.html            ready state
mockups/platform-empty.html      round 1, nothing provisioned
mockups/components.html          ready state, table populated
mockups/components-detail.html   one row opened, tabs
mockups/components-wizard.html   step 3 of 6 shown, others collapsed
mockups/rollout.html             ready state
mockups/rollout-detail.html      one deployment opened, mix visible
mockups/rollout-locked.html      round locked, controls disabled
```

Eight files, one state each. **No file contains more than one state.**

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Roles only, no primitives, no raw colour | `grep -nE "var\(--p-" mockups/*.html` and `grep -nE ":[[:space:]]*#[0-9a-fA-F]{3,8}\|rgb\(\|hsl\(" mockups/*.html` | zero both |
| I2 | Roles resolve to primitives in one step | script over `theme.css` | all pass |
| I3 | No token declared outside `theme.css` | `grep -rn -- "^[[:space:]]*--[a-z-]*:" mockups/` | zero |
| I4 | No engine vocabulary visible | `git ls-files "mockups/*.html" \| xargs grep -niE "capability_key\|instance_id\|articulation\|SPOF\|RTO\|RPO\|EOL\b\|MOT\|realised\|level of detail\|grain"` | zero |
| I5 | Every string in §5.7 or justified in `dod.md` | text-node diff | zero unaccounted |
| I6 | One external reference per file, `theme.css` | `grep -nE "<link\|@import\|src=\|https?://" mockups/*.html` | one `<link>` each |
| I7 | Riverside marked as content | `grep -niE "riverside\|grocer" mockups/*.html \| grep -v data-casepack` | zero |
| I8 | **One state per file** | `grep -cE "State:" mockups/*.html` | zero in every file |
| I9 | **No scores on decision pages** | `grep -nE "[0-9]{1,3}%[^ ]*realis\|Tech [0-9]\|Org [0-9]\|Mgmt [0-9]\|Held back by" mockups/*.html` | zero |
| I10 | **No bulk control on Rollout** | manual: every control in `rollout-detail.html` names one deployment | confirmed |
| I11 | **Wizard enforces steps 3 and 4** *(rewritten v3.2 — the old wording, "no skip affordance", passed while the requirement failed: the wizard showed every step at once with a live commit button)* | one step visible at a time · current choice shows a selected state · *Add to plan* **disabled** until purpose and unit are both chosen, and says why | confirmed by attempting to commit with either unset |
| I15 | **Selected state exists wherever a choice is offered** *(`CONTRACTS.md`; finding B9)* | every radio, tab, panel option and wizard step: chosen visibly distinct from unchosen | confirmed |
| I16 | **Rows that open a detail view look like it** *(`CONTRACTS.md`; finding B3)* | chevron + `--text-link` on first cell + hover highlight, on Components and Rollout | confirmed |
| I12 | **No third-party font request** *(restored — was v2.1 I9, dropped by the v3 renumber; finding `0.3-020`)* | `git ls-files \| grep -E "frontend/\|mockups/" \| xargs grep -niE "googleapis\|gstatic\|fonts\.google"` | zero |
| I13 | **Both faces and the licence still shipped** *(restored — was v2.1 I10)* | `git ls-files "frontend/src/styles/fonts/*"` | 5 `.woff2` + `LICENSE.txt`. **OFL 1.1 requires the licence to accompany the fonts** |
| I14 | **Badge scale conforms to `CONTRACTS.md`** *(finding `0.3-013`)* | `grep -oE "status-(ok\|info\|warn\|neutral\|danger)" mockups/*.html \| sort -u` then read each badge's label | `Complete→ok` `Partly done→info` `Needs attention→warn` `Not started→neutral`. **`Partly done` sharing `ok` with `Complete` is a FAIL.** Every status-bearing item carries a badge |

I8, I9, I10, I11 are new in v3 and are the ones that encode what v2 got wrong.

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | Step 1 token map built, two tiers | `[V]` | `grep -c '^\s*--p-' frontend/src/styles/theme.css` | 38 |
| 2 | Step 1b fonts vendored | `[V]` | `git ls-files "frontend/src/styles/fonts/*"` | 5 `.woff2` + LICENSE |
| 3 | CDN call removed | `[V]` | `grep -c "googleapis\|gstatic" frontend/index.html` | 0 |
| 4 | **Nothing outside `mockups/` and `docs/` is touched** *(§4.2)* | `[V]` | after building: `git diff --name-only main..HEAD` | only `mockups/*`, `docs/mockup-review.md`, `handoffs/0.3-mockup-pilot/dod.md`, `screenshots/0.3/*` |
| 5 | v2 mockups exist and are being replaced | `[V]` | `ls mockups/` | `situation.html`, `platform.html`, `applications.html` — **delete `situation.html` and `applications.html`; `platform.html` is rewritten** |
| 6 | BECSR reference pages readable | `[A]` | `sshpass -p ubuntu ssh ubuntu@192.168.50.5 'ls ~/projects/BECSR/reference-*.html'` | two files. **Open them before building — they are the grammar** |
| 7 | Screenshots committable | `[V]` | `git check-ignore -v screenshots/0.3/x.png` | no match |

---

## 8. Build steps

**Step 2 — Platform.** `platform.html`, `platform-empty.html`. §5.2 hierarchy: the two
hosting panels dominate; absences read as absences.
*Verify:* I1, I3, I4, I5, I6, I7, I8 · shots at 1440/1280/1024.

**Step 3 — Components.** `components.html`, `components-detail.html`,
`components-wizard.html`. The table is the page. The wizard is six steps with 3 and 4
mandatory.
*Verify:* same, plus I9, I11.

**Step 4 — Rollout.** `rollout.html`, `rollout-detail.html`, `rollout-locked.html`.
*Verify:* same, plus I9, I10.

**Step 5 — Consistency.** All three read as one product: same shell, same strip, same
table grammar, same type scale. Delete `situation.html` and `applications.html`.
*Verify:* three 1440 shots side by side; `mockups/` contains exactly the eight files
in §5.8.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7, esp. 4 and 6 | | |
| Step 2 Platform | | |
| Step 3 Components incl. wizard | | |
| Step 4 Rollout | | |
| Step 5 consistency; v2 files deleted | | |
| I1–I16 | | |
| `situation.html` and `applications.html` deleted | | |
| Badge scale matches `CONTRACTS.md` — `0.3-013` | | |
| Font guards restored and passing — `0.3-020` | | |
| `alignment.md` read before starting | | |
| Eight files, one state each | | |
| Strings not in §5.7, justified | | |
| Screenshots ×9 in `screenshots/0.3/` | | |
| `docs/mockup-review.md` | | |
| Nothing touched outside §1 scope | | |
| Auth / instance / casepack canaries | | **N-A** — static, no state, no auth |

---

## 10. Review checklist

`playthrough.md`, amended for v3: Part B's naïve-reader questions become
*"what do we own?"*, *"how would I add one?"*, *"where do I change its settings?"*,
*"which units have actually adopted anything?"* — the four questions v2 could not answer.

---

## 11. v2 defect disposition

| v2 defect | Fixed in v3 by |
|---|---|
| Content inventory, no hierarchy — eight equal panels | §5.2 states the one question, dominant, demoted, per screen |
| Three states stacked per file, unreadable | Decision 3 · one state per file · I8 |
| No list of what you own | Components is a table first — §5.2 |
| No way to add | `[ + Add component ]` → six-step wizard — §5.3 |
| No way to modify | Row → detail with tabs — §5.4 |
| Scores on a decision page | §2 and I9 — scores live on Dashboard and Debrief |
| Value chain used as the page | Value chain becomes Step 3 of the wizard and a Dashboard view |
| Bulk-feeling organisation page | Rollout is per deployment — decision 7 · I10 |
| Panel headers were legends ("Technology × Organisation × Management") | §5.7 gives every heading verbatim |
| Wizard floating with no entry point | Entered by the action button on Components |
