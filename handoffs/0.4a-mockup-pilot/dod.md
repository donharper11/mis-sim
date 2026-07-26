# 0.4a — Definition of Done

> Filled by the BUILDER. This table IS the session report.


| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–7 reported | PASS | Reported before edits. Row 2 verified `token declarations: 89` and `resolved distinct literal values: 38`. |
| Phase 1 — token map + deprecation table + CONTRACTS entry | PASS | `frontend/src/styles/theme.css` rewritten as 38 primitives + 75 required semantic roles; `CONTRACTS.md` has `Design tokens — two-tier`; deprecation table below accounts for 89 original tokens. |
| Phase 2 — Situation | N-A | Hard stop after Phase 1 per module instruction; not started. |
| Phase 3 — Platform | N-A | Hard stop after Phase 1 per module instruction; not started. |
| Phase 4 — Applications | N-A | Hard stop after Phase 1 per module instruction; not started. |
| Phase 5 — consistency pass | N-A | Hard stop after Phase 1 per module instruction; not started. |
| I1 no primitives or raw values in mockups | N-A | No mockups built in Phase 1. |
| I2 roles resolve to primitives, one level | PASS | `primitive declarations: 38`; `required semantic roles: 75`; `all required roles declared exactly once: true`. `--radius: 0` is direct per spec §5.1. |
| I3 no engine vocabulary | N-A | No mockups built in Phase 1. |
| I4 Riverside is content, not structure | N-A | No mockups built in Phase 1. |
| I5 no external requests | N-A | No mockups built in Phase 1. |
| I6 every visible string is in §5.6 | N-A | No mockups built in Phase 1. |
| I7 no tokens declared outside `theme.css` | PASS | `grep -rn -- "--[a-z-]*:" frontend/src mockups/ \| grep -v "styles/theme.css"` produced no output. |
| O1 badge states — decision recorded | PASS | Default recorded for Phase 2+: all four states (`configured` / `partial` / `error` / `empty`), with illustrative states annotated. |
| O2 state presentation — decision recorded | PASS | Default recorded for Phase 2+: stacked labelled sections in one file per screen. |
| O3 percentage vs decimal — decision recorded | PASS | Default recorded for Phase 2+: realised value as percentage; decomposition factors as decimals. |
| Screenshots ×9 (3 screens × 3 viewports) in `screenshots/0.4a/` | N-A | No mockups built in Phase 1. |
| Every displayed metric traced to `design/02-traceability-matrix.md` | N-A | No metrics displayed in Phase 1. |
| No files touched outside `theme.css`, `mockups/`, `CONTRACTS.md`, `dod.md` | PASS | `git diff --name-only` limited to `CONTRACTS.md`, `frontend/src/styles/theme.css`, and this DoD. |
| Auth canary | N-A | Static HTML, no auth. |
| Instance-isolation canary | N-A | No state. |
| Casepack validator | N-A | No casepacks yet. |

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
| `--color-surface-50` | *(primitive)* `--slate-50` | tier demotion |
| `--color-surface-100` | *(primitive)* `--slate-100` | tier demotion |
| `--color-surface-200` | *(primitive)* `--slate-200` | tier demotion |
| `--color-surface-300` | *(primitive)* `--slate-300` | tier demotion |
| `--color-surface-400` | *(primitive)* `--slate-400` | tier demotion |
| `--color-surface-500` | *(primitive)* `--slate-500` | tier demotion |
| `--color-surface-600` | *(primitive)* `--slate-600` | tier demotion |
| `--color-surface-700` | *(primitive)* `--slate-700` | tier demotion |
| `--color-surface-800` | *(primitive)* `--slate-800` | tier demotion |
| `--color-surface-900` | *(primitive)* `--navy-900` | tier demotion |
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
| `--color-neutral` | `--status-neutral-marker` | status rename |
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
