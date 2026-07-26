# 0.4a — Canonical Token Map + Mockup Pilot (3 screens) · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1
**Author:** Claude (design session) · **Date:** 2026-07-26
**Phase:** 0 · **Depends on:** 0.2 (merged, `d638939`) · **Blocks:** 0.4b, 0.6
**Reference mockup:** none — **this module produces them.** Acceptance is §10's checklist.

---

## 0. Spec Basis

**Read in full:**

- `frontend/src/styles/theme.css` @ `origin/main` — all 89 declarations extracted and
  analysed for value collisions (§5.1)
- `BECSR/becsr-design-system.md` lines 1–70 — palette, IBM Plex Sans, zero-radius
- `globalstrat/.../design-system/index.js` — the 12 components 0.6 will port
- `globalstrat/.../design-system/theme.css` lines 1–80 — the variable grouping 0.2 adopted
- `globalstrat/.../components/Sidebar.js` lines 1–120 — menu grouping, per-category status
  badges via `getDecisionSummary`, `canLock` derivation, server-supplied `sidebarLabels`
- `BECSR/frontend/csr-sim-frontend/src/components/` — file listing only
- `design/05-implementation-plan.md §1.3` — the ten student screens
- `findings/0.2-2026-07-26-author-review.md` — finding 0.2-003, which this module resolves

**Cited from summary or prose:** none.

**Extraction sufficiency:** covered all load-bearing surfaces. Deliberately not extracted:
globalstrat component *implementations* (needed at 0.6) and BECSR's `reference-*.html`
mockups — I have the design system doc they were built to, and copying their layout would
import a CSR sim's information architecture into an MIS sim.

---

## 1. Purpose and scope

Two deliverables, in order. The first must be right before the second is built, because
the mockups are how the first gets tested.

1. **A canonical token map** — replaces the flat 89-token set with a two-tier system, one
   name per semantic role. Resolves finding 0.2-003.
2. **Three static reference mockups** — Situation, Platform, Applications — built using
   only canonical role tokens.

These three establish the visual grammar the other seven copy. They are the pilot for a
review gate, not the start of a batch.

**In scope:**
- Rewrite `frontend/src/styles/theme.css` as primitives + semantic roles
- A deprecation table for every removed or renamed token
- `CONTRACTS.md` entry making the tier rule binding
- Three self-contained HTML mockups in `mockups/`
- Verbatim student-facing copy for all three (§5.6)
- Every screen state each mockup needs (§5.7)

**Out of scope — do not build these:**
- The other seven mockups — that is 0.4b, after the review gate
- Any React component — that is 0.6
- Any backend, route, or data fetch. Mockups are static HTML with inline sample data
- Interactivity beyond what §5.7 requires to display a state
- Changing `docker-compose.yml`, `backend/`, or anything under `frontend/src/` except
  `styles/theme.css`
- Fixing anything else noticed in 0.2. File it; do not repair it

---

## 2. Project-specific statements *(SPEC_PROTOCOL §9)*

**Scoring factors touched:** none captured — mockups are static. Factors **displayed**,
which constrains what each screen must show:

| Factor | Mockup | Direction |
|---|---|---|
| Realised value per capability (Tech × Org × Mgmt) | Situation | displays |
| Coverage, capacity, reliability, SPOF count | Situation, Applications | displays |
| Open signals with round-first-shown | Situation | displays |
| Platform capacity utilisation | Platform | displays |
| Capex committed / opex run-rate | all three (budget strip) | displays |
| Governance coverage (owner/sponsor assigned) | Applications | displays |

Every number shown must be one the engine will actually produce. **Inventing a metric
that has no home in `design/02-traceability-matrix.md` is a finding.**

**Casepack keys read:** none directly — but all sample data is Riverside Grocers, and
**every label that a casepack would supply must be visibly marked** (§5.5).
**Casepack-identity branching:** N/A, no code. Invariant I4 checks the mockups do not
present Riverside as structural.

**Instance scoping:** N/A — no state, no tables, no queries.

**Business-language check:** the whole point. Every string on every mockup passes the
standing filter (`GOVERNANCE.md §2.1`). Invariant I3 greps for engine vocabulary.

---

## 3. Settled decisions

1. **Two-tier tokens.** Primitives (value-named) and semantic roles (role-named).
   **Components may reference only roles.** This is the 0.2-003 fix and it is not
   optional — see §5.1.
2. **Static HTML, no build step.** Each mockup opens in a browser from the filesystem.
   No bundler, no npm, no framework, no external requests (`GOVERNANCE.md` — mockups must
   be reviewable by a person with no toolchain).
3. **One shared data state: Riverside Grocers, round 3 of 6, strategy = Low-Cost
   Leadership.** All three mockups show the same company at the same moment, so they can
   be read as one product. Numbers are in §5.4 and are **fixed** — do not invent others.
4. **Ant Design is not used in the mockups.** Mockups define the target; 0.6 makes antd
   match it. Hand-write the markup.
5. **Desktop-first at 1440.** Must also hold at 1280 and 1024. No mobile in this phase.
6. **`theme.css` is rewritten in place**, not forked. The 0.2 file is superseded.

---

## 4. Open decisions

| # | Question | Decision criteria | Reporting obligation |
|---|---|---|---|
| **O1** | Sidebar shows five Decisions items with per-category status badges (globalstrat pattern). Should the pilot render badges for **all** states, or only the states round 3 would actually produce? | **Default: all four** (`configured` / `partial` / `error` / `empty`) even if round 3 wouldn't show all — the mockup's job is to define the vocabulary, and 0.6 needs to see every badge. Annotate the ones that are illustrative | Record in `dod.md` |
| **O2** | Multiple screen states per screen: separate HTML files, or one file with visually stacked labelled sections? | **Default: stacked labelled sections in one file per screen.** A reviewer comparing empty-vs-ready shouldn't have to switch files. Label each section clearly as a state, not as page content | Record in `dod.md` |
| **O3** | The Situation screen's capability cards show a realised-value figure. Two decimal (`0.25`) or percentage (`25%`)? | **Default: percentage.** `GOVERNANCE.md §2.1` — a business reader reads 25%, not 0.25. But show the three-factor decomposition as decimals since they are multiplied | Record in `dod.md` |

---

## 5. Design

### 5.1 The canonical token map — the load-bearing deliverable

**The problem, measured.** `theme.css` @ `origin/main` declares **89 tokens over 38
distinct literal values**. Collisions are not merely redundant, they are semantically
wrong:

```
#F1F5F9   4 names   --bg-content · --color-surface-100 · --status-inactive-bg
                    · --status-pending-bg
#64748B   4 names   --color-surface-500 · --status-inactive-text
                    · --status-pending-text · --text-muted
--accent-navy  5 aliases  --brand-primary · --chart-your-team
                          · --color-header-financial · --color-input-focus
                          · --color-primary
```

That last group is the dangerous one. "Your team on a chart", "a financial section
header", and "an input focus ring" are three unrelated roles sharing one value. The first
time one needs to change independently, whoever changes it silently breaks the other two.

**The fix — two tiers.**

```
TIER 1  PRIMITIVES     named for what they ARE.       --navy-900: #0F1724
        The palette. May repeat values freely.
        Components NEVER reference these.

TIER 2  SEMANTIC ROLES named for what they DO.        --surface-page: var(--slate-100)
        Every role has exactly ONE definition.
        Components reference ONLY these.
```

**Required roles.** The builder defines each as `var(--primitive)`. This list is the
contract; adding a role requires a `CONTRACTS.md` entry, removing one requires this spec
to change.

```
SURFACE     --surface-page · --surface-card · --surface-raised · --surface-sunken
            --surface-sidebar · --surface-sidebar-active · --surface-topbar
            --surface-table-header · --surface-table-stripe · --surface-row-highlight

TEXT        --text-primary · --text-secondary · --text-muted · --text-hint
            --text-inverse · --text-link
            --text-on-sidebar · --text-on-sidebar-muted · --text-on-sidebar-section

BORDER      --border-default · --border-strong · --border-focus

STATUS      for each of: ok · warn · danger · info · neutral
            --status-<name>-bg · --status-<name>-text · --status-<name>-marker
            (marker = the dot / left border / icon tint)

ACCENT      --accent-1 … --accent-7
            Categorical only — for left-border cards and section headers.
            MUST NOT be reused for status. Status has its own scale

CHART       --chart-1 … --chart-6 · --chart-highlight
            Series colours only. MUST NOT be reused for status or accent

ACTION      --action-primary · --action-primary-hover · --action-primary-text
            --action-secondary · --action-secondary-hover
            --action-disabled · --action-disabled-text

INPUT       --input-bg · --input-border · --input-border-focus · --input-text
            --input-editable-bg · --input-disabled-bg

FONT        --font-body · --font-mono
SPACE       --space-xs … --space-4xl   (existing scale, unchanged)
RADIUS      --radius: 0    (BECSR is zero-radius; declared so 0.6 has a name to use)
```

**Deprecations.** Every token in the current file that is not a primitive or a role above
is removed. The builder produces a table in `dod.md`:

| Old token | Replaced by | Note |
|---|---|---|
| `--bg-content` | `--surface-page` | rename |
| `--color-surface-100` | *(primitive)* `--slate-100` | tier demotion |
| `--status-pending-bg` | `--status-neutral-bg` | merged |
| … | … | … |

**Invariant:** no semantic role may be defined as another semantic role. Roles resolve to
primitives, one level. Checked by I2.

**Why not a flat rename.** Because the collisions carry information: four names on
`#F1F5F9` means four roles genuinely exist and happen to share a value *today*. The two
tiers preserve that — the roles stay distinct and separately changeable, and only the
primitive is shared.

### 5.2 `CONTRACTS.md` entry

The builder adds, in the file's existing format:

```
## Design tokens — two-tier

Canonical: components reference SEMANTIC ROLES only (--surface-page, --text-muted,
--status-danger-bg). Never primitives (--slate-100, --navy-900), never raw values.

Roles resolve to primitives in exactly one step. A role defined as another role is a
defect — it reintroduces the aliasing this replaced.

Producers: frontend/src/styles/theme.css — the only file that may declare either tier.
Consumers: every component, every mockup.

Adding a role: entry here + spec change. Adding a primitive: theme.css only.
```

### 5.3 The three screens

Content is settled from the design conversation; layout is the builder's craft within the
design system.

**MOCKUP A — Situation.** The round-open briefing. Must show:
- Round + strategy + countdown; persistent budget strip (capex remaining, opex run-rate,
  run-rate trend across R1–R3)
- Balanced Scorecard summary: Financial · Customer · Internal Process · Learning & Growth
- Capability cards, each with realised value and the **three-factor decomposition**
  naming the throttling factor
- Open signals, each with the round it was first shown and how long it has been open
- Inbox summary count

**MOCKUP B — Platform.** The shared foundation. Must show:
- Two panels, **Cloud** and **On-Premises**, with services placed in each
- The hybrid banner and the split-rule selector (§5.6 copy)
- Unprovisioned services (`Identity & access`, `Data platform`) as an explicit absence,
  not an omission
- Capacity utilisation as a **percentage**, never cores or terabytes
  (`GOVERNANCE.md §2.1`)
- Boundary/integration count and its monthly cost

**MOCKUP C — Applications.** Value chain and the purchase entry point. Must show:
- Porter's value chain — support activities above, primary below — with each activity's
  coverage and the strategy-weighted ones marked
- One expanded capability showing its slots (Hardware / Software / Database / Network /
  Integration) with one **empty** slot
- Owner and sponsor assignment controls, one of them **unassigned**
- The purchase wizard step 3 — the three deployment modes with their warnings

### 5.4 Fixed sample data — use these exact figures

```
Riverside Grocers · 8 stores · round 3 of 6 · Low-Cost Leadership (locked R2)
Capex remaining $44,000 of $220,000 · Opex R1 $47,000 → R2 $53,000 → R3 $58,300

ORDER FULFILMENT   realised 25%   Tech 0.75 · Org 0.51 · Mgmt 0.65
                   coverage 4/5 · reliability 94.0% · 4 single points of failure
                   throttle: Organisation — 49 of 140 trained, process not redesigned
CUSTOMER INSIGHT   not built · coverage 0/4 · strategy weight 0.10
POINT OF SALE      stable · coverage 5/5 · reliability 97.2% · vendor support ends R4

SIGNALS   ORD-CAP-01  order app utilisation 111%   raised R2, open 2 rounds, critical
          DATA-INT-02 product data inconsistent    raised R2, open 2 rounds, warn
          EOL-POS-03  POS support ends R4          raised R3, open 1 round, warn

PLATFORM  cloud: end-user email
          on-prem: compute 100% used · storage 70% · network (10 SPOFs) · backup (untested)
          not provisioned: identity & access, data platform
          7 integrations · $3,100/round
```

### 5.5 Casepack-supplied labels must be visible as such

Any string a casepack would supply — capability names, value chain activity names,
persona names, company name — is marked in the mockup with a subtle annotation
(a dotted underline plus a legend entry). A reviewer must be able to tell at a glance
what is chrome and what is content. This directly serves the Phase 6 gate.

### 5.6 Student-facing copy — verbatim

```
Situation
  page title            Situation
  scorecard empty       "No results yet — your first round runs at the deadline."
  signal age            "Open 2 rounds"
  throttle line         "Held back by: Organisation"
  decomposition label   "Technology × Organisation × Management"
  budget trend label    "Run-rate — this rises every round it is not managed"

Platform
  page title            Platform
  hybrid banner         "You are running a hybrid platform."
  hybrid sub            "1 service in cloud · 4 on-premises"
  split rule prompt     "What determines the split?"
  split options         "Workload profile — steady on-premises, bursty in cloud"
                        "Data sensitivity — regulated on-premises, rest in cloud"
                        "Lifecycle — legacy stays, new builds go to cloud"
                        "Cost profile — high-utilisation workloads on-premises"
                        "No rule yet — case by case"
  unprovisioned         "Not provisioned"
  capacity warning      "No headroom. The next application will not fit."
  integration line      "7 connections between systems · $3,100 per round"

Applications
  page title            Applications
  empty slot            "Nothing fills this yet"
  unassigned owner      "No owner assigned"
  unassigned sponsor    "No business sponsor"
  strategy marker       "Weighted by your strategy"
  wizard step 3 title   "How will this run?"
  saas warning 1        "Inventory data would leave your systems"
  saas warning 2        "A fourth separate login — you have no central sign-on"
  onprem warning        "This uses all remaining platform capacity"
  add button            "Add to plan"
```

**Nothing else may appear as visible text** without being added here. Lorem ipsum is a
finding.

### 5.7 States each mockup must show (per O2, stacked and labelled)

| Screen | Required states |
|---|---|
| Situation | ready (full) · **round 1 empty** (no prior results) · locked (round submitted) |
| Platform | ready · **hybrid banner active** · a service unprovisioned · capacity at 100% |
| Applications | ready · capability with an empty slot · owner unassigned · **wizard step 3 open** |

Loading states are out of scope for static mockups — note them as annotations instead.

---

## 6. Invariants and their falsification checks

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Mockups reference no primitives and no raw values | `grep -nE "#[0-9a-fA-F]{3,8}\|var\(--(slate\|navy\|blue\|green\|amber\|red\|teal\|purple)" mockups/*.html` | zero hits |
| I2 | No semantic role resolves to another semantic role | For each `--<role>: var(--x)` in `theme.css`, assert `--x` is declared in the primitives block | all resolve to primitives |
| I3 | No engine vocabulary on any mockup | `grep -niE "capability_key\|instance_id\|articulation\|fit.multiplier\|casepack\|_id\b\|SPOF\b" mockups/*.html` | zero hits (`single point of failure` spelled out is fine) |
| I4 | Riverside appears as content, never as structure | `grep -niE "riverside\|grocer" mockups/*.html \| grep -viE "data-casepack\|sample\|legend"` | only inside marked content regions |
| I5 | No external requests | `grep -niE "https?://\|src=\|@import\|<link" mockups/*.html` | zero, except an inline data-URI font fallback |
| I6 | Every visible string is in §5.6 | Manual diff of rendered text against §5.6 | no unlisted strings |
| I7 | No token declared outside `theme.css` | `grep -rn -- "--[a-z-]*:" frontend/src mockups/ \| grep -v "styles/theme.css"` | zero hits |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 0.2 is merged; `theme.css` on `main` | `[V]` | `git ls-tree --name-only origin/main -- frontend/src/styles/theme.css` | path returned |
| 2 | `theme.css` declares 89 tokens over 38 distinct literal values | `[V]` | `git show origin/main:frontend/src/styles/theme.css \| grep -cE "^\s+--"` then the distinct-value count from §5.1 | 89 and 38 |
| 3 | The 5-alias `--accent-navy` group exists as quoted | `[V]` | `git show origin/main:frontend/src/styles/theme.css \| grep -n "var(--accent-navy)"` | 5 occurrences |
| 4 | `mockups/` exists and is empty | `[V]` | `ls -la mockups/` | present, no `.html` |
| 5 | `CONTRACTS.md` has no design-token entry yet | `[V]` | `grep -n "token" CONTRACTS.md` | no design-token section |
| 6 | Finding 0.2-003 is the one being resolved | `[V]` | `grep -n "0.2-003" findings/0.2-2026-07-26-author-review.md` | present |
| 7 | A browser is available to render and screenshot | `[A]` | `which chromium \|\| ls /snap/bin/chromium \|\| npx playwright --version` | one succeeds |

---

## 8. Build phases

### Phase 1 — Token map *(must complete and be reviewed before Phase 2)*
- Rewrite `theme.css` as primitives + roles per §5.1
- Produce the deprecation table in `dod.md`
- Add the `CONTRACTS.md` entry per §5.2
- **Verify:** I2 and I7 pass; every role in §5.1's list is declared exactly once;
  deprecation table accounts for all 89 original tokens

### Phase 2 — Mockup A · Situation
- Build per §5.3, §5.4, §5.6, §5.7
- **Verify:** renders from the filesystem; I1, I3, I5, I6 pass; screenshots at 1440 /
  1280 / 1024

### Phase 3 — Mockup B · Platform
- Same. **Verify:** same, plus the hybrid banner and split-rule selector are present and
  legible

### Phase 4 — Mockup C · Applications
- Same. **Verify:** same, plus wizard step 3 shows all three deployment modes with the
  §5.6 warnings

### Phase 5 — Consistency pass
- All three read as one product: same header, same budget strip, same card grammar, same
  type scale
- **Verify:** the three 1440 screenshots side by side; I4 and the §10 checklist

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7 reported | | |
| Phase 1 — token map + deprecation table + CONTRACTS entry | | |
| Phase 2 — Situation | | |
| Phase 3 — Platform | | |
| Phase 4 — Applications | | |
| Phase 5 — consistency pass | | |
| I1 no primitives or raw values in mockups | | |
| I2 roles resolve to primitives, one level | | |
| I3 no engine vocabulary | | |
| I4 Riverside is content, not structure | | |
| I5 no external requests | | |
| I6 every visible string is in §5.6 | | |
| I7 no tokens declared outside `theme.css` | | |
| O1 badge states — decision recorded | | |
| O2 state presentation — decision recorded | | |
| O3 percentage vs decimal — decision recorded | | |
| Screenshots ×9 (3 screens × 3 viewports) in `screenshots/0.4a/` | | |
| Every displayed metric traced to `design/02-traceability-matrix.md` | | |
| No files touched outside `theme.css`, `mockups/`, `CONTRACTS.md`, `dod.md` | | |
| Auth canary | | **N-A** — static HTML, no auth |
| Instance-isolation canary | | **N-A** — no state |
| Casepack validator | | **N-A** — no casepacks yet |

---

## 10. Review checklist

`playthrough.md` in this folder. **Adapted:** static mockups have no browser workflow, so
the playthrough is a structured review. Fresh auditor mandatory
(`GOVERNANCE.md §6.1` — this module has a visual surface).
