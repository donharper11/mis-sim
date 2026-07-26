# 0.3 — Canonical Token Map + Mockup Pilot (3 screens) · Build Spec

**Version 2.1** · **Authored under** `SPEC_PROTOCOL.md` v1.2
**Author:** Claude (design session) · **Date:** 2026-07-26
**Phase:** 0 · **Depends on:** 0.2 (merged) · **Blocks:** 0.4, 0.6

> **v2 supersedes v1 entirely.** v1 was unbuildable: it forbade touching files that consume
> the tokens it rewrote, shipped three jointly unsatisfiable invariants, required a metric
> it also forbade, and omitted numbers and strings its own checks demanded. 17 defects,
> found by audit before a builder was harmed. Full disposition in §12.
>
> **Phase 1 was already built against v1 (commit `76d5e3a`) and must be reworked.**

---

## 0. Spec Basis

**Read in full:**
- `frontend/src/styles/theme.css` @ `main` — 89 declarations over 38 distinct values
- **`frontend/src/main.jsx` lines 10–35** — reads 11 token names at runtime via
  `getPropertyValue` to build the antd `ConfigProvider` theme *(missed in v1)*
- **`frontend/src/pages/DevTokens.jsx`** — enumerates all 89 names as string literals
  *(missed in v1)*
- `.gitignore` — line 16 `screenshots/**/*.png`, line 17 negates `0.2` only
- `BECSR/becsr-design-system.md` 1–70 · `globalstrat/.../design-system/{index.js,theme.css}`
  · `globalstrat/.../Sidebar.js` 1–120
- `design/02-traceability-matrix.md` · `design/03-scoring-frame-options.md`
- `findings/0.2-2026-07-26-author-review.md` (0.2-003, the defect this resolves)

**Verified commands, this session:**
```
fc-match "IBM Plex Sans"                    → NotoSans-Regular.ttf  (not installed)
git check-ignore -v screenshots/0.3/x.png  → .gitignore:16         (was blocked)
echo '<a href="#add-to-plan">' | grep -cE "#[0-9a-fA-F]{3,8}"  → 1  (v1 I1 false positive)
```

**Extraction sufficiency:** covered all load-bearing surfaces, **including the consumers
v1 omitted**.

---

## 1. Purpose and scope

1. Replace the flat 89-token set with a two-tier map — one name per semantic role.
   Resolves finding `0.2-003`.
2. Update every existing consumer of the old names so the application keeps working.
3. Build three static reference mockups — Situation, Platform, Applications — using role
   tokens only.

**In scope — explicitly including the consumers:**
- `frontend/src/styles/theme.css` — rewritten
- **`frontend/src/main.jsx`** — antd token mapping updated to the new role names
- **`frontend/src/pages/DevTokens.jsx`** — enumeration updated
- `mockups/` — three HTML files
- `CONTRACTS.md` — the two-tier entry
- `docs/mockup-review.md` — how to view them
- **`frontend/index.html`** — remove the Google Fonts CDN call *(v2.1)*
- **`frontend/src/styles/fonts/`** — vendored WOFF2 + OFL licence *(v2.1)*

**Out of scope:**
- Mockups 4–10 — that is 0.4, after the review gate
- Any React component — that is 0.6
- Any backend, route, or data fetch
- Any file under `frontend/src/` **other than the three named above**
  *(pre-flight row 3 proves no others consume tokens)*
- `.gitignore` — **already fixed on main**; do not touch

---

## 2. Project-specific statements

**Scoring factors displayed** — every number on a mockup traces to
`design/02-traceability-matrix.md`:

| Factor | Mockup | Matrix ref |
|---|---|---|
| Realised value + MOT decomposition | Situation | §A/B/C |
| Coverage · capacity · reliability · SPOF count | Situation, Applications | §A |
| Open signals with first-shown round | Situation | §C |
| **Balanced Scorecard, four perspectives** | Situation | **§E — row added 2026-07-26** |
| Platform capacity utilisation | Platform | §A |
| Capex remaining · opex run-rate | all three | §D |
| Governance coverage | Applications | §C |

**Casepack keys read:** none directly; all sample content is marked per §5.5.
**Instance scoping:** N/A — static HTML, no state.
**Business-language check:** invariant I4.

---

## 3. Settled decisions

1. **Two-tier tokens.** Primitives `--p-<family>-<step>`; roles unprefixed and semantic.
   **Components and mockups reference roles only.** The `--p-` prefix is mandatory and
   makes the check exact — v1's grep guessed at family names and both false-negatived
   (`--gray-100` passed) and false-positived (`href="#add-to-plan"`).
2. **Mockups link `theme.css` with one relative `<link>`.** This is the named compliant
   route (§4). v1 forbade it, making its invariant set unsatisfiable.
3. **Static HTML, opened with `file://`.** No server, no bundler, no framework.
4. **IBM Plex is self-hosted. The CDN call is removed.** *(v2.1 — supersedes v2's
   "install the system package". Closes finding `0.3-011`.)* Both faces ship in-repo; see
   §5.8. No third-party font request reaches a student's browser, and the mockups render
   correctly from `file://` with no network.
5. **One shared data state:** Riverside Grocers, round 3 of 6, Low-Cost Leadership.
   All figures fixed in §5.4 — including the three states v1 left numberless.
6. **Ant Design is not used in the mockups.** Mockups define the target; 0.6 makes antd
   match it.
7. **Desktop-first at 1440**, holding at 1280 and 1024.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

One concrete implementation satisfying **every** invariant simultaneously. If the builder
finds that it does not, that is a spec defect: **STOP and report.**

```
mockups/situation.html
  <link rel="stylesheet" href="../frontend/src/styles/theme.css">   ← I6 permits exactly this
  <style> .card { background: var(--surface-card); } </style>       ← roles only     → I1 ✓
                                                                      declares nothing → I3 ✓
  <body> … no raw hex, no var(--p-…) …                                               → I1 ✓
```

Declaring a token inside the mockup breaches I3; a raw hex breaches I1; any other external
reference breaches I6. This one route passes all eight.

---

## 5. Design

### 5.1 The token map

**Measured basis:** 89 tokens over 38 distinct values. `--accent-navy` alone carries five
unrelated roles — brand, chart-your-team, financial header, input focus, primary action.

```
TIER 1  PRIMITIVES   --p-<family>-<step>        e.g.  --p-navy-900: #0F1724
        The palette. May repeat values freely.
        NEVER referenced outside theme.css.

TIER 2  SEMANTIC ROLES   --surface-page: var(--p-slate-100)
        Exactly one definition each.
        The only tier anything else may reference.
        Resolves to a primitive in exactly ONE step.
```

**Required roles.** This list is the contract; adding one needs a `CONTRACTS.md` entry and
a spec change.

```
SURFACE   --surface-page · --surface-card · --surface-raised · --surface-sunken
          --surface-sidebar · --surface-sidebar-active · --surface-topbar
          --surface-table-header · --surface-table-stripe · --surface-row-highlight
          --overlay-scrim                       ← NEW in v2 (wizard modal)

TEXT      --text-primary · --text-secondary · --text-muted · --text-hint
          --text-inverse · --text-link
          --text-on-sidebar · --text-on-sidebar-muted · --text-on-sidebar-section

BORDER    --border-default · --border-strong · --border-focus
          --border-annotation                   ← NEW in v2 (§5.5 casepack marking)

STATUS    for each of ok · warn · danger · info · neutral:
          --status-<n>-bg · --status-<n>-text · --status-<n>-marker

ACCENT    --accent-1 … --accent-7      categorical only. NOT status, NOT chart.
CHART     --chart-1 … --chart-6 · --chart-highlight      series only.

ACTION    --action-primary · --action-primary-hover · --action-primary-text
          --action-secondary · --action-secondary-hover
          --action-disabled · --action-disabled-text

INPUT     --input-bg · --input-border · --input-border-focus · --input-text
          --input-editable-bg · --input-disabled-bg

FONT      --font-body · --font-mono
SPACE     --space-xs … --space-4xl
RADIUS    --radius: 0
```

**`--action-primary-hover` must be a darker shade of `--action-primary`, same hue**
(finding `0.2-002`).

**Deprecation table** in `dod.md` accounting for all 89 original tokens: old name →
replacement, or → primitive, or → merged, or → removed with reason.

### 5.2 Consumer updates — the part v1 omitted

**`frontend/src/main.jsx` lines 17–27** reads 11 token names. Eight are deleted by §5.1.
`getPropertyValue` returns `""` for a missing name, so antd falls back to its defaults
**silently** — the application looks subtly wrong with no error anywhere. Remap:

```
colorPrimary        --accent-navy          →  --action-primary
colorPrimaryHover   --color-primary-hover  →  --action-primary-hover
colorInfo           --accent-blue          →  --status-info-marker
colorSuccess        --accent-green         →  --status-ok-marker
colorWarning        --accent-amber         →  --status-warn-marker
colorError          --accent-red           →  --status-danger-marker
colorText           --text-primary         →  --text-primary       (unchanged)
colorTextSecondary  --text-secondary       →  --text-secondary     (unchanged)
colorBgLayout       --bg-content           →  --surface-page
colorBgContainer    --bg-card              →  --surface-card
fontFamily          --font-body            →  --font-body          (unchanged)
```

**Add a guard:** `token()` must throw on an empty result rather than returning `""`.
A silently-missing design token is precisely the failure this module exists to prevent,
and it is what would have made this defect invisible in testing.

**`frontend/src/pages/DevTokens.jsx`** enumerates all 89 names as literals. Rewrite it to
enumerate the role list grouped by §5.1's categories, plus a separate primitives section,
so both tiers are visible and the distinction is legible.

### 5.3 The three screens

**A · Situation** — round, strategy, countdown · budget strip (capex remaining, opex
run-rate, R1–R3 trend) · **Balanced Scorecard, four perspectives** · capability cards with
realised value and the MOT decomposition naming the throttle · open signals with
first-shown round and age · inbox count.

**B · Platform** — Cloud and On-Premises panels · hybrid banner and split-rule selector ·
unprovisioned services as an explicit absence · capacity as a **percentage** · integration
count and its **per-round** cost.

**C · Applications** — value chain, support above and primary below, coverage per activity,
strategy-weighted activities marked · one capability expanded showing five slots with one
**empty** · owner and sponsor controls with one **unassigned** · purchase wizard step 3
with three deployment modes and their warnings.

### 5.4 Fixed data — use these exact figures, invent nothing

```
Riverside Grocers · 8 stores · round 3 of 6 · Low-Cost Leadership (locked R2)
Capex remaining $44,000 of $220,000
Opex  R1 $47,000 → R2 $53,000 → R3 $58,300

BALANCED SCORECARD (0–100)                    ← added v2, fixes defect 3
  Financial 61 · Customer 48 · Internal Process 39 · Learning & Growth 27

ORDER FULFILMENT   realised 25%   Tech 0.75 · Org 0.51 · Mgmt 0.65
                   coverage 4/5 · reliability 94.0% · 4 single points of failure
                   throttle: Organisation — 49 of 140 trained, process not redesigned
CUSTOMER INSIGHT   not built · coverage 0/4 · strategy weight 0.10
POINT OF SALE      stable · coverage 5/5 · reliability 97.2%

SIGNALS   display name                          raised   age        severity
  Order system near capacity                    R2       2 rounds   critical
  Product data inconsistent                     R2       2 rounds   warning
  Point-of-sale vendor support ending           R3       1 round    warning

PLATFORM  cloud:    end-user email
          on-prem:  compute 100% · storage 70% · network · backup
          not provisioned: central sign-on, data platform
          10 single points of failure · 7 connections · $3,100 per round

VALUE CHAIN coverage
  Support   Firm infrastructure 3/4 · Human resources ok
            Technology — · Procurement 0/3
  Primary   Inbound logistics 1/4 · Operations 2/4 ▸ · Outbound logistics 4/5 ▸
            Marketing & sales 5/5 · Service 0/4
  ▸ = weighted by declared strategy

STATE — Situation, round 1, before any results     ← added v2, fixes defect 4
  Capex remaining $400,000 of $400,000 · Opex $47,000 · no trend line
  Scorecard: all four perspectives show the empty-state copy
  Capabilities: coverage shown, realised value absent
  Signals: the three above, all raised R1, age "Open 0 rounds"

STATE — Situation, round locked                    ← added v2
  Identical figures to round 3 ready.
  Locked banner per §5.6. All inputs visibly disabled.

STATE — Applications, wizard step 3                ← added v2, fixes defect 4
  Item: Centraline IM 7 · serves Inventory Management · affects 34 warehouse staff
    On our on-premises platform   $86,000 + $1,900/round · available in 2 rounds
    On our cloud subscription     $12,000 + $7,400/round · available now
    Bought as a service           $0      + $9,100/round · available now
```

### 5.8 Font delivery — self-hosted, no CDN *(v2.1)*

`frontend/index.html:6-8` makes three requests to Google Fonts and asks for **IBM Plex
Sans only**, while `theme.css:32` declares `--p-font-mono: 'IBM Plex Mono'`. Mono is
declared and never delivered — every monospace surface silently renders Courier New.
That is finding `0.3-011`.

**Source.** `@ibm/plex@6.4.1` on npm carries the official WOFF2 web fonts. Extract the
files; **do not add a runtime dependency** — vendor them.

**Location — `frontend/src/styles/fonts/`.** Not `public/`. `theme.css` references them
relative to itself (`url('./fonts/…')`), which resolves for **both** the Vite build and a
mockup opened over `file://`. An absolute `/fonts/…` would work in the app and break the
mockups — and mockups rendering in the house font with no toolchain is the point of this
module.

**Faces — five files, WOFF2 only.** Every target browser supports WOFF2; shipping WOFF or
TTF alongside doubles the payload for nothing.

```
IBMPlexSans-Regular.woff2      400
IBMPlexSans-Medium.woff2       500
IBMPlexSans-SemiBold.woff2     600
IBMPlexSans-Bold.woff2         700
IBMPlexMono-Regular.woff2      400
```

**`@font-face` blocks** go in `theme.css` above the token declarations, each with
`font-display: swap` to preserve the CDN's current behaviour.

**Remove** `frontend/index.html` lines 6–8 — both `preconnect` hints and the stylesheet
link. Nothing replaces them; `theme.css` is already imported by the app.

**Licence.** IBM Plex is OFL 1.1. Self-hosting obliges us to ship it as
`frontend/src/styles/fonts/LICENSE.txt`, copied from the package. Not optional.

**Fallback stacks stay.** `--p-font-sans` and `--p-font-mono` keep their fallbacks so a
missing file degrades noticeably rather than silently — silent degradation is how
`0.3-011` hid in the first place.

### 5.5 Casepack-supplied labels are visibly marked

Any string a casepack supplies — company name, capability names, value-chain activity
names, persona names, signal display names — carries `data-casepack` and renders with
`--border-annotation` as a dotted underline, plus a legend entry. A reviewer must be able
to see at a glance what is chrome and what is content. This directly serves the Phase 6
gate.

### 5.6 Every visible string — complete

```
CHROME
  sidebar          Situation · Platform · Applications · Organisation · Governance
                   · Challenges · Review & Lock · Debrief · People
  badges           Complete · Partly done · Needs attention · Not started
  legend           "Dotted underline = supplied by the case, not the platform"
  state sections   "State: ready"
                   "State: round 1, before any results"
                   "State: round locked"

SITUATION
  title            Situation
  round            "Round 3 of 6"
  strategy         "Low-Cost Leadership · locked in round 2"
  budget capex     "Capital remaining"
  budget opex      "Run-rate"
  budget trend     "Run-rate rises every round it is not managed"
  scorecard        Financial · Customer · Internal Process · Learning & Growth
  scorecard empty  "No results yet — your first round runs at the deadline."
  decomposition    "Technology × Organisation × Management"
  throttle         "Held back by: Organisation"
  signal age       "Open 2 rounds" · "Open 1 round" · "Open 0 rounds"
  signal severity  "Critical" · "Warning"
  inbox            "3 items waiting"
  locked banner    "This round is locked. Decisions reopen when the round advances."

PLATFORM
  title            Platform
  panels           Cloud · On-Premises
  hybrid banner    "You are running a hybrid platform."
  hybrid sub       "1 service in cloud · 4 on-premises"
  split prompt     "What determines the split?"
  split options    "Workload profile — steady on-premises, bursty in cloud"
                   "Data sensitivity — regulated on-premises, rest in cloud"
                   "Lifecycle — legacy stays, new builds go to cloud"
                   "Cost profile — high-utilisation workloads on-premises"
                   "No rule yet — case by case"
  unprovisioned    "Not provisioned"
  capacity label   "Capacity used"
  capacity warning "No headroom. The next application will not fit."
  fragility        "10 single points of failure"
  integrations     "7 connections between systems · $3,100 per round"

APPLICATIONS
  title            Applications
  chain headings   Support activities · Primary activities
  strategy marker  "Weighted by your strategy"
  slots            Hardware · Software · Database · Network · Integration
  empty slot       "Nothing fills this yet"
  owner            "No owner assigned"
  sponsor          "No business sponsor"
  wizard title     "How will this run?"
  wizard modes     "On our on-premises platform"
                   "On our cloud subscription"
                   "Bought as a service"
  onprem warning   "This would use all remaining platform capacity."
  saas warning 1   "Inventory data would leave your systems."
  saas warning 2   "A fourth separate login — you have no central sign-on."
  add button       "Add to plan"
```

Any string not listed here must be added to `dod.md` with a justification (I5).

### 5.7 States required *(stacked, labelled, one file per screen)*

| Screen | States |
|---|---|
| Situation | ready · round-1-empty · locked |
| Platform | ready · hybrid banner · unprovisioned · capacity 100% |
| Applications | ready · empty slot · owner unassigned · wizard step 3 |

---

## 6. Invariants — executable, and jointly satisfiable via §4

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Mockups use roles only | `grep -nE "var\(--p-" mockups/*.html` **and** `grep -nE ":[[:space:]]*#[0-9a-fA-F]{3,8}\|rgb\(\|hsl\(" mockups/*.html` | zero from both. *(Declaration context only — `href="#…"` no longer matches)* |
| I2 | Roles resolve to primitives in one step | script: every `--<role>: var(--x)` must have `--x` matching `^--p-` | all pass |
| I3 | No token declared outside `theme.css` | `grep -rn -- "^[[:space:]]*--[a-z-]*:" frontend/src mockups \| grep -v styles/theme.css` | zero |
| I4 | No engine vocabulary visible | `grep -niE "capability_key\|instance_id\|articulation\|fit.multiplier\|SPOF\|RTO\|RPO\|EOL\b" mockups/*.html` | zero |
| I5 | Every visible string is in §5.6, or justified in `dod.md` | extract text nodes, diff against §5.6; residue must appear in `dod.md` | zero unaccounted |
| I6 | Exactly one external reference, and it is `theme.css` | `grep -nE "<link\|@import\|src=\|https?://" mockups/*.html` | one `<link>` per file, `href` ending `styles/theme.css` |
| I7 | Riverside is marked content, not structure | `grep -niE "riverside\|grocer" mockups/*.html \| grep -v "data-casepack"` | zero |
| I9 | No third-party font request anywhere | `grep -rniE "googleapis\|gstatic\|fonts\.google" frontend/ mockups/` | zero |
| I10 | Both faces delivered, licence shipped | `git ls-files "frontend/src/styles/fonts/*"` | 5 `.woff2` + `LICENSE.txt` |
| I8 | antd reads only live role names | script cross-checking `main.jsx` token names against declared roles in `theme.css` | zero missing |

I4 no longer greps `casepack` — v1's I3/I4 contradiction, since `data-casepack` is required
by §5.5.

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | `theme.css` on main: 89 tokens | `[V]` | `grep -cE "^\s+--" frontend/src/styles/theme.css` | 89 |
| 2 | `main.jsx` consumes 11 token names | `[V]` | `grep -c 'token("--' frontend/src/main.jsx` | 11 |
| 3 | **No other file under `frontend/src` reads tokens** | `[V]` | `grep -rn "getPropertyValue\|var(--" frontend/src --include=*.jsx --include=*.js \| grep -v "main.jsx\|DevTokens.jsx"` | zero — **this is the check whose absence made v1 unbuildable** |
| 4 | `DevTokens.jsx` enumerates literals | `[V]` | `grep -c '"--' frontend/src/pages/DevTokens.jsx` | ≥ 80 |
| 5 | `screenshots/0.3/*.png` is committable | `[V]` | `git check-ignore -v screenshots/0.3/x.png` | **no match** |
| 6 | `@ibm/plex@6.4.1` reachable, carries WOFF2 | `[V]` | `npm view @ibm/plex version` | `6.4.1` *(verified 2026-07-26)* |
| 6b | CDN call present to remove | `[V]` | `grep -n "fonts.googleapis\|gstatic" frontend/index.html` | lines 6, 7, 8 |
| 6c | No font files tracked yet | `[V]` | `git ls-files "*.woff2"` | zero |
| 6d | `.gitignore` does not block `woff2` | `[V]` | `git check-ignore -v frontend/src/styles/fonts/x.woff2` | no match |
| 7 | `mockups/` has no HTML | `[V]` | `ls mockups/*.html 2>&1` | no such file |
| 8 | `design/02` carries a BSC row | `[V]` | `grep -n "Balanced Scorecard" design/02-traceability-matrix.md` | present |

---

## 8. Build steps

**Step 1 — token map + consumers + fonts.** *Rework of commit `76d5e3a`.* Also vendor the
five WOFF2 files and the OFL licence per §5.8, add the `@font-face` blocks, and delete
`frontend/index.html` lines 6–8. Rewrite `theme.css`;
apply the §5.2 remap to `main.jsx` **and add the throw-on-empty guard**; rewrite
`DevTokens.jsx`; produce the deprecation table; add the `CONTRACTS.md` entry.
**Verify:** I2, I3, I8 · `npm run build` exits 0 · `/_dev/tokens` renders both tiers ·
antd Button/Select/Table still themed, with a screenshot proving it ·
**I9, I10** · `/_dev/tokens` renders Plex Sans **and** Plex Mono **with the network
disconnected**.
**>>> STOP AND REPORT. Do not start Phase 2. <<<**

**Step 2 — Situation.** **Verify:** I1, I4, I5, I6, I7 · all three states · shots at
1440/1280/1024.
**Step 3 — Platform.** Same.
**Step 4 — Applications.** Same.
**Step 5 — consistency pass.** Three 1440 shots side by side: shared header, budget strip,
card grammar, type scale.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–8, especially row 3 | | |
| Step 1 — map, consumers, guard, deprecation table | | |
| `npm run build` clean after the consumer rewrite | | |
| antd still themed — screenshot | | |
| Steps 2–5 | | |
| I1–I8 | | |
| Strings not in §5.6, listed and justified | | |
| Screenshots ×9 in `screenshots/0.3/` | | |
| `docs/mockup-review.md`, including font install | | |
| Files touched: only those named in §1 | | |
| Auth / instance / casepack canaries | | **N-A** — static, no state, no auth |

---

## 10. Review checklist

`playthrough.md`, with two v2 amendments: Part A gains a consumer check (does the app still
build, and is antd still themed?), and the D-series references §5.4's now-complete data.

---

## 11. Doc deltas landed with this spec

- `design/02-traceability-matrix.md` §E — Balanced Scorecard row **added**
- `handoffs/README.md` — Phase 0 table corrected to match `design/06-plan-index.md`
- `CONTRACTS.md` — design-token entry marked **PROSPECTIVE**, `Last updated` bumped
- `.gitignore` — `!screenshots/0.3/*.png` added
- `SPEC_PROTOCOL.md` v1.2 — §4.1 named compliant route, §4.2 out-of-scope dependency check

---

## 12. v1 defect disposition

| # | v1 defect | Fixed in v2 by |
|---|---|---|
| 1 | Token rewrite broke `main.jsx` / `DevTokens.jsx`, both out of scope | §1 scope · §5.2 remap + guard · pre-flight row 3 |
| 2 | I1+I5+I7 jointly unsatisfiable | §4 named compliant route · I6 permits one `theme.css` link |
| 3 | BSC required by §5.3 and forbidden by §2 | matrix row added · values in §5.4 |
| 4 | Three required states had no numbers | §5.4 STATE blocks |
| 5 | I6 unsatisfiable — ~30 strings listed, ~70 needed | §5.6 complete · I5 permits justified residue |
| 6 | I3 vs I4 contradiction on `casepack` | I4 no longer greps it |
| 7 | "No headroom" vs "uses all remaining capacity" | §5.6 wording aligned |
| 8 | Screenshots gitignored | `.gitignore` fixed on main · pre-flight row 5 |
| 9 | Badge vocabulary was engine language; "error" breached GOVERNANCE §4.9 | §5.6 student labels; "Needs attention" |
| 10 | No overlay/annotation roles despite being required | added to §5.1 |
| 11 | I1 grep false negative and false positive | `--p-` prefix mandated · declaration-context hex check |
| 12 | "monthly cost" vs "$3,100 per round" | "per round" throughout |
| 13 | I2/I6 shipped prose, not commands | all eight invariants executable |
| 14 | README numbering conflicted with the spec | README corrected |
| 15 | CONTRACTS entry lacked PROSPECTIVE and a date bump | both applied |
| 16 | Signal codes mandated visible but unlisted; "EOL" was IT vocabulary | §5.4 display names · I4 greps EOL/RTO/RPO |
| 17 | IBM Plex absent, would vanish silently | install documented · pre-flight row 6 · visible fallback |
