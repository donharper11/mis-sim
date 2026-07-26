# 0.3 — Definition of Done

> Filled by the BUILDER. This table IS the session report.


| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–8, especially row 3 | PASS | Rows were run before writing. Row 1 baseline `89`; row 2 `11`; row 3 no output outside `main.jsx` / `DevTokens.jsx`; row 4 `>= 80`; row 5 no ignore match for `screenshots/0.3/x.png`; row 6 `npm view @ibm/plex version` returned `6.4.1`; row 6b showed Google Fonts lines 6-8 before removal; row 6c zero tracked WOFF2 before vendoring; row 6d no ignore match; row 7 no mockup HTML before writing; row 8 Balanced Scorecard present. |
| Step 1 — map, consumers, guard, deprecation table | PASS | Earlier token map and consumer remap stand. Step 1b added five IBM Plex WOFF2 files + `LICENSE.txt`, added `@font-face` blocks with `font-display: swap`, and removed the Google Fonts calls from `frontend/index.html`. |
| `npm run build` clean after the consumer rewrite | PASS | `vite build` completed; font assets emitted for IBM Plex Sans 400/500/600/700 and IBM Plex Mono 400. Existing chunk-size warning only. |
| antd still themed — screenshot | PASS | Browser at `http://127.0.0.1:5204/_dev/tokens`, viewport 1280 with non-local requests blocked: Button `rgb(30, 64, 175)`, Table header `rgb(250, 250, 250)`, header text `rgb(15, 23, 42)`, `swatchCount: 115`, `blankSwatches: []`, Sans and Mono font checks true, zero console errors, zero failed requests. Screenshot: `screenshots/0.3/devtokens-fonts-offline-1280.png`. |
| Phases 2–5 | PASS | v2.2 renames these to Steps 2-5 and removes the hard stop. Built `mockups/situation.html`, `mockups/platform.html`, and `mockups/applications.html`; ran the consistency pass across shared sidebar, header, budget strip, card grammar, zero radius, and type scale. |
| I1–I8 | PASS | I1 no `var(--p-)` and no raw hex/rgb/hsl declarations in `mockups/*.html`. I2: `declared tokens: 115`, `roles checked: 77`, `literal exceptions: --radius: 0`, `PASS`. I3 no token declarations outside `theme.css`. I4 no forbidden engine vocabulary. I5: `visible text chunks: 125`, `unaccounted residue: 0`. I6 exactly one stylesheet link per mockup, all ending `styles/theme.css`. I7 Riverside/Grocers only appears with `data-casepack`. I8 `main.jsx token refs: 11`, `missing roles: 0`, `primitive refs: 0`, `PASS`. |
| Strings not in §5.6, listed and justified | PASS | Justified residue below. All residue is from §5.4 fixed figures/content, §5.7 required state labels, repeated app chrome (`Round 3 of 6`, strategy, budget strip), or casepack-supplied labels marked with `data-casepack`. |
| Screenshots ×9 in `screenshots/0.3/` | PASS | `situation`, `platform`, and `applications` captured at 1440, 1280, and 1024. Browser output for every screenshot: `linkCount: 1`, `scrollWidth` equals viewport, Sans and Mono ready, zero console errors, zero failed requests. |
| `docs/mockup-review.md`, including font install | PASS | Added `docs/mockup-review.md`. v2.1 self-hosting means no font install is required for review; the doc states the file-open path and the in-repo font source. |
| Files touched: only those named in §1 | PASS | Changes are limited to `frontend/index.html`, `frontend/src/styles/theme.css`, `frontend/src/styles/fonts/`, `mockups/`, `CONTRACTS.md`, `docs/mockup-review.md`, this DoD, and `screenshots/0.3/`. |
| Auth / instance / casepack canaries | N-A | Static, no state, no auth. |

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
