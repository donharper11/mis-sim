# 0.3 — Definition of Done

> Filled by the BUILDER. This table IS the session report.


| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7, esp. 4 and 6 | PASS / DEVIATION | Row 1 `38`; row 2 lists five WOFF2 + `LICENSE.txt`; row 3 `0`; row 5 showed v2 mockups; row 6 BECSR pages readable on `.5`; row 7 screenshot path unignored. Row 4 as written (`main..HEAD`) includes accepted Step 1/1b and author/audit files already on the branch; alignment.md says keep them. This pass's staged diff is limited to `mockups/`, `docs/mockup-review.md`, `handoffs/0.3-mockup-pilot/dod.md`, and `screenshots/0.3/`. |
| Step 2 Platform | PASS | Rebuilt `platform.html` and added `platform-empty.html`. Browser screenshots at 1440/1280/1024: one stylesheet link, round stated, no failed requests, no console errors, no horizontal overflow. |
| Step 3 Components incl. wizard | PASS | Built `components.html`, `components-detail.html`, `components-wizard.html`. Components is table-first; detail uses tabs; wizard shows six steps with 3 and 4 visible and no skip/later affordance. |
| Step 4 Rollout | PASS | Built `rollout.html`, `rollout-detail.html`, `rollout-locked.html`. Rollout table is one row per deployment; detail controls name the `Centraline IM 7 → Warehouse` deployment only. |
| Step 5 consistency; v2 files deleted | PASS | `mockups/` tracked set is exactly eight v3.1 files. `situation.html` and `applications.html` are deleted; v2 screenshots remain as the alignment record. |
| I1–I14 | PASS | I1/I3/I4/I7/I9/I11/I12 produced no output. I2: `declared tokens: 115`, `roles checked: 77`, `--radius: 0`, `PASS`. I5: `visible text chunks: 316`, `unaccounted residue: 0`. I6 shows one `theme.css` link per file. I8 shows `0` `State:` labels in each file. I10 manually confirmed no bulk rollout control. I13 lists five WOFF2 + `LICENSE.txt`. I14 badge issues `0`. |
| `situation.html` and `applications.html` deleted | PASS | Staged deletions: `D mockups/situation.html`, `D mockups/applications.html`. |
| Badge scale matches `CONTRACTS.md` — `0.3-013` | PASS | `Complete → status-ok`, `Partly done → status-info`, `Needs attention → status-warn`, `Not started → status-neutral`; scripted badge check reports `I14 badge issues: 0`. |
| Font guards restored and passing — `0.3-020` | PASS | I12 tracked grep over `frontend/` and `mockups/` has zero Google font hits. I13 lists `IBMPlexMono-Regular.woff2`, four IBM Plex Sans WOFF2 files, and `LICENSE.txt`. |
| `alignment.md` read before starting | PASS | Read before `spec.md`; it directed keep/delete/rebuild/build scope and the row 4 pre-flight interpretation. |
| Eight files, one state each | PASS | `git ls-files "mockups/*.html"` lists `platform`, `platform-empty`, `components`, `components-detail`, `components-wizard`, `rollout`, `rollout-detail`, `rollout-locked`; every file states `Round 1 of 6` or `Round 3 of 6`; no file contains `State:`. |
| Strings not in §5.7, justified | PASS | I5 browser text diff reports `316` visible chunks and `0` unaccounted residue. Residue classes are fixed §5.6 data, casepack labels marked `data-casepack`, table-header extraction artifacts, and button/tab text joined by browser `innerText`. |
| Screenshots ×9 in `screenshots/0.3/` | PASS | v3.1 produced 24 new/updated screenshots: eight files at 1440/1280/1024. Existing v2 Situation/Application screenshots remain intentionally as alignment history. |
| `docs/mockup-review.md` | PASS | Updated to list the eight v3.1 files and self-hosted font review path. |
| Nothing touched outside §1 scope | PASS | This pass changed only `mockups/`, `docs/mockup-review.md`, `handoffs/0.3-mockup-pilot/dod.md`, and `screenshots/0.3/`. Existing Step 1/1b files were kept unchanged. |
| Auth / instance / casepack canaries | N-A | Static HTML only; no auth, no runtime state, no data fetch. Casepack labels are visibly marked with `data-casepack`. |

---

## Step 1b and Steps 2-5 Evidence

| Check | Result | Evidence |
|---|---|---|
| Font vendoring | PASS | `frontend/src/styles/fonts/` contains `IBMPlexSans-Regular.woff2`, `IBMPlexSans-Medium.woff2`, `IBMPlexSans-SemiBold.woff2`, `IBMPlexSans-Bold.woff2`, `IBMPlexMono-Regular.woff2`, and `LICENSE.txt`. |
| CDN removal | PASS | `git grep -nI -E "googleapis\|gstatic\|fonts\.google" -- frontend mockups` produced no output; `grep -rniE "googleapis\|gstatic\|fonts\.google" frontend/src frontend/index.html mockups/` produced no output. The exact broad I9 command over `frontend/` also scans `node_modules` and false-matches dependency text such as `existingStatic`, so product-file evidence is recorded here. |
| Browser font proof | PASS | `/_dev/tokens` with non-local requests blocked: `h1FontFamily: "IBM Plex Sans", system-ui, -apple-system, sans-serif`; `monoFontFamily: "IBM Plex Mono", "Source Code Pro", monospace`; platform font inspection returned `familyName: IBM Plex Sans`, `isCustomFont: true`. |
| Static mockups | PASS | `file://` browser run for all three files at 1440/1280/1024: one stylesheet link, no failed requests, no console errors, no horizontal overflow. |
| I9 exact-command deviation | DEVIATION | `grep -rniE "googleapis\|gstatic\|fonts\.google" frontend/ mockups/` reports dependency-only noise from `frontend/node_modules`, including `existingStatic` under case-insensitive `gstatic`. Source and tracked product-file greps are zero. |
| I10 after staging | PASS | `git ls-files "frontend/src/styles/fonts/*"` lists exactly `IBMPlexMono-Regular.woff2`, `IBMPlexSans-Bold.woff2`, `IBMPlexSans-Medium.woff2`, `IBMPlexSans-Regular.woff2`, `IBMPlexSans-SemiBold.woff2`, and `LICENSE.txt`. |

### I5 justified residue

| Residue class | Justification |
|---|---|
| §5.4 fixed data | Company details, round/budget figures, BSC scores, MOT factors, coverage, reliability, signal names, platform services, value-chain activities, deployment costs, availability timing, and affected staff are all fixed in §5.4. |
| §5.7 state labels | `State: hybrid banner`, `State: unprovisioned`, `State: capacity 100%`, `State: empty slot`, `State: owner unassigned`, and `State: wizard step 3` are the required stacked states from §5.7. |
| Repeated chrome | `Round 3 of 6`, `Low-Cost Leadership · locked in round 2`, `Capital remaining`, `Run-rate`, and `Run-rate rises every round it is not managed` are reused across Platform and Applications for Step 5 consistency. |
| Casepack labels | `Riverside Grocers`, capability names, signal names, service names, activity names, `Centraline IM 7`, `Inventory Management`, and `34 warehouse staff` are marked with `data-casepack` and the dotted underline legend. |

---

## Rework Phase 1 Evidence

| Finding / check | Result | Evidence |
|---|---|---|
| `0.3-001` token consumers | PASS | `main.jsx` uses the exact v2 §5.2 remap and throws `Missing design token: <name>` on empty. Browser verified Button, Select, and Table remain themed on `/_dev/tokens`. |
| `0.3-002` neutral marker | PASS | Chose value preservation: `--status-neutral-marker: var(--p-slate-500)`, preserving old `--color-neutral` resolved value `#64748B`. |
| `0.3-005` contract format | PASS | `CONTRACTS.md` header updated and design-token heading marked `PROSPECTIVE`; primitive examples use the v2 `--p-` prefix. |
| Frontend token references | PASS | `frontend token references: 115`; `missing declarations: 0`. |
| Deprecation accounting | PASS | `origin/main tokens: 89`; `deprecation rows: 89`; `missing: 0`; `extra: 0`; `duplicates: 0`. |
| Browser swatches | PASS | `swatchCount: 115`; `blankSwatches: []`; sections include semantic role groups and primitive groups. |

---

## Phase 1 Deprecation Table

| Old token | Replaced by | Note |
|---|---|---|
| `--bg-sidebar` | `--surface-sidebar` | rename |
| `--bg-sidebar-active` | `--surface-sidebar-active` | rename |
| `--bg-content` | `--surface-page` | rename |
| `--bg-card` | `--surface-card` | rename |
| `--bg-table-header` | `--surface-table-header` | rename |
| `--bg-table-alt` | `--surface-table-stripe` | rename |
| `--bg-topbar` | `--surface-topbar` | rename |
| `--bg-highlight-row` | `--surface-row-highlight` | rename |
| `--text-primary` | `--text-primary` | role retained |
| `--text-secondary` | `--text-secondary` | role retained |
| `--text-muted` | `--text-muted` | role retained |
| `--text-hint` | `--text-hint` | role retained |
| `--text-sidebar` | `--text-on-sidebar` | rename |
| `--text-sidebar-muted` | `--text-on-sidebar-muted` | rename |
| `--text-sidebar-section` | `--text-on-sidebar-section` | rename |
| `--text-link` | `--text-link` | role retained |
| `--accent-green` | `--accent-2` | categorical rename |
| `--accent-blue` | `--accent-1` | categorical rename |
| `--accent-purple` | `--accent-4` | categorical rename |
| `--accent-amber` | `--accent-3` | categorical rename |
| `--accent-red` | `--accent-6` | categorical rename |
| `--accent-teal` | `--accent-5` | categorical rename |
| `--accent-navy` | `--accent-7` | categorical rename |
| `--status-compliant-bg` | `--status-ok-bg` | merged |
| `--status-compliant-text` | `--status-ok-text` | merged |
| `--status-risk-bg` | `--status-warn-bg` | merged |
| `--status-risk-text` | `--status-warn-text` | merged |
| `--status-danger-bg` | `--status-danger-bg` | role retained |
| `--status-danger-text` | `--status-danger-text` | role retained |
| `--status-pending-bg` | `--status-neutral-bg` | merged |
| `--status-pending-text` | `--status-neutral-text` | merged |
| `--status-active-bg` | `--status-ok-bg` | merged |
| `--status-active-text` | `--status-ok-text` | merged |
| `--status-inactive-bg` | `--status-neutral-bg` | merged |
| `--status-inactive-text` | `--status-neutral-text` | merged |
| `--color-surface-50` | *(primitive)* `--p-slate-50` | tier demotion |
| `--color-surface-100` | *(primitive)* `--p-slate-100` | tier demotion |
| `--color-surface-200` | *(primitive)* `--p-slate-200` | tier demotion |
| `--color-surface-300` | *(primitive)* `--p-slate-300` | tier demotion |
| `--color-surface-400` | *(primitive)* `--p-slate-400` | tier demotion |
| `--color-surface-500` | *(primitive)* `--p-slate-500` | tier demotion |
| `--color-surface-600` | *(primitive)* `--p-slate-600` | tier demotion |
| `--color-surface-700` | *(primitive)* `--p-slate-700` | tier demotion |
| `--color-surface-800` | *(primitive)* `--p-slate-800` | tier demotion |
| `--color-surface-900` | *(primitive)* `--p-navy-900` | tier demotion |
| `--topbar-bg` | `--surface-topbar` | rename |
| `--topbar-text` | `--text-primary` | rename |
| `--topbar-text-secondary` | `--text-muted` | rename |
| `--topbar-border` | `--border-default` | rename |
| `--brand-primary` | `--action-primary` | rename |
| `--color-header-financial` | `--accent-7` | categorical rename |
| `--color-header-strategic` | `--accent-2` | categorical rename |
| `--color-header-market` | `--accent-3` | categorical rename |
| `--color-header-decision` | `--accent-4` | categorical rename |
| `--color-header-results` | `--accent-5` | categorical rename |
| `--color-header-neutral` | `--text-muted` | rename |
| `--color-positive` | `--status-ok-marker` | status rename |
| `--color-negative` | `--status-danger-marker` | status rename |
| `--color-warning` | `--status-warn-marker` | status rename |
| `--color-info` | `--status-info-marker` | status rename |
| `--color-neutral` | `--status-neutral-marker` | status rename, value preserved at `#64748B` |
| `--color-primary` | `--action-primary` | rename |
| `--color-primary-hover` | `--action-primary-hover` | rename |
| `--color-primary-light` | `--surface-row-highlight` | rename |
| `--color-input-bg` | `--input-bg` | rename |
| `--color-input-border` | `--input-border` | rename |
| `--color-input-focus` | `--input-border-focus` | rename |
| `--color-input-editable` | `--input-editable-bg` | rename |
| `--color-text-primary` | `--text-primary` | rename |
| `--color-text-secondary` | `--text-muted` | rename |
| `--color-text-inverse` | `--text-inverse` | rename |
| `--color-text-link` | `--text-link` | rename |
| `--chart-1` | `--chart-1` | role retained |
| `--chart-2` | `--chart-2` | role retained |
| `--chart-3` | `--chart-3` | role retained |
| `--chart-4` | `--chart-4` | role retained |
| `--chart-5` | `--chart-5` | role retained |
| `--chart-6` | `--chart-6` | role retained |
| `--chart-your-team` | `--chart-highlight` | rename |
| `--font-body` | `--font-body` | role retained; Rework 2 reverted stack to 0.2 form after installing `fonts-ibm-plex` |
| `--font-mono` | `--font-mono` | role retained; Rework 2 reverted stack to 0.2 form after installing `fonts-ibm-plex` |
| `--space-xs` | `--space-xs` | role retained |
| `--space-sm` | `--space-sm` | role retained |
| `--space-md` | `--space-md` | role retained |
| `--space-lg` | `--space-lg` | role retained |
| `--space-xl` | `--space-xl` | role retained |
| `--space-2xl` | `--space-2xl` | role retained |
| `--space-3xl` | `--space-3xl` | role retained |
| `--space-4xl` | `--space-4xl` | role retained |

---

## Rework 2 — 0.3-008, 0.3-009, 0.3-010

| Finding / check | Result | Evidence |
|---|---|---|
| `0.3-008` pre-flight row 6 | PASS | Installed `fonts-ibm-plex` with `sudo apt-get install -y fonts-ibm-plex`; `fc-match "IBM Plex Sans"` now returns `IBMPlexSans-Regular.ttf: "IBM Plex Sans" "Regular"`. |
| Pre-flight rows 1-8 restated | PASS | Row 1 baseline: `origin/main` token count `89`; current reworked token count `115` by v2 design. Row 2 `main.jsx` token refs `11`. Row 3 no token readers outside `main.jsx` / `DevTokens.jsx` / `theme.css`. Row 4 `DevTokens.jsx` token literals `98`. Row 5 `git check-ignore -v screenshots/0.3/x.png` reports `.gitignore:18:!screenshots/0.3/*.png`. Row 6 IBM Plex Sans installed. Row 7 `ls mockups/*.html` reports no such file. Row 8 Balanced Scorecard present at `design/02-traceability-matrix.md:100`. |
| `0.3-009` font deprecation notes | PASS | `--font-body` and `--font-mono` rows now state Rework 2 reverted the stacks to the 0.2 forms after installing `fonts-ibm-plex`; no row claims an unqualified value-preserving rename. |
| `0.3-010` fallback decision | PASS | Chose path (ii): the apt install from `0.3-008` is the safeguard. `Arial` still resolves to `LiberationSans-Regular.ttf`, so the font stack was reverted to the 0.2 form instead of adding a fallback that does not provide the intended visual signal. |
| Browser verification | PASS | `/_dev/tokens` at 1280: Button `rgb(30, 64, 175)`, table header `rgb(250, 250, 250)`, header text `rgb(15, 23, 42)`, `swatchCount: 115`, `blankSwatches: []`, zero console errors, zero failed requests. Screenshot: `screenshots/0.3/devtokens-rework2-1280.png`. |
| Rendered font proof | PASS | Chrome platform-font inspection on the visible `h1` text `Design tokens`: `familyName: IBM Plex Sans`, `postScriptName: IBMPlexSans-Regular`, `glyphCount: 13`. |
