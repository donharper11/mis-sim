# 0.3 — Definition of Done

> Filled by the BUILDER. This table IS the session report.


| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–8, especially row 3 | PASS | v2 gate passed before edits: `HEAD c3a2709`; `handoffs/0.3-mockup-pilot/spec.md` line 3 reads `**Version 2**`. Row 3 condition rechecked by consumer scan: only `frontend/src/main.jsx`, `frontend/src/pages/DevTokens.jsx`, and `frontend/src/styles/theme.css` reference token names. |
| Step 1 — map, consumers, guard, deprecation table | PASS | `theme.css` rewritten as 38 `--p-` primitives + 77 v2 roles; `main.jsx` remapped to 11 live semantic roles and throws on empty token; `DevTokens.jsx` lists roles by category and primitives separately; 89-row deprecation table below has no missing, extra, or duplicate old tokens. |
| `npm run build` clean after the consumer rewrite | PASS | `vite build` completed; output assets `index-Gy2TMCAE.css` and `index-DzAF3_YJ.js`; only the existing chunk-size warning appeared. |
| antd still themed — screenshot | PASS | Browser at `http://127.0.0.1:5200/_dev/tokens`, viewport 1280: Button background `rgb(30, 64, 175)`, Select border `rgb(217, 217, 217)`, Table header bg `rgb(250, 250, 250)`, header text `rgb(15, 23, 42)`, zero console errors, zero failed requests. Screenshot: `screenshots/0.3/devtokens-rework-1280.png`. |
| Phases 2–5 | N-A | Hard stop after Phase 1 per v2 §8; mockups not started. |
| I1–I8 | PASS | I2: `declared tokens: 115`, `required roles: 77`, `I2 one-hop role resolution: PASS`. I3: `grep -rn -- "^[[:space:]]*--[a-z-]*:" frontend/src mockups \| grep -v styles/theme.css` produced no output. I8: `main.jsx token refs: 11`, `missing roles: 0`, `primitive refs: 0`, `PASS`. I1/I4/I5/I6/I7 are not exercisable until mockups exist. |
| Strings not in §5.6, listed and justified | N-A | No mockups built in Phase 1. |
| Screenshots ×9 in `screenshots/0.3/` | N-A | No mockups built in Phase 1; one dev-token proof screenshot produced for the Phase 1 consumer check. |
| `docs/mockup-review.md`, including font install | N-A | Step 1 rework only; no mockups or review doc started. |
| Files touched: only those named in §1 | PASS | Source/doc changes limited to `frontend/src/styles/theme.css`, `frontend/src/main.jsx`, `frontend/src/pages/DevTokens.jsx`, `CONTRACTS.md`, and this DoD; one verification screenshot added under `screenshots/0.3/`. |
| Auth / instance / casepack canaries | N-A | Static, no state, no auth. |

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
| `--font-body` | `--font-body` | role retained |
| `--font-mono` | `--font-mono` | role retained |
| `--space-xs` | `--space-xs` | role retained |
| `--space-sm` | `--space-sm` | role retained |
| `--space-md` | `--space-md` | role retained |
| `--space-lg` | `--space-lg` | role retained |
| `--space-xl` | `--space-xl` | role retained |
| `--space-2xl` | `--space-2xl` | role retained |
| `--space-3xl` | `--space-3xl` | role retained |
| `--space-4xl` | `--space-4xl` | role retained |
