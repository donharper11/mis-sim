# MIS Simulation — Build Status & Context

> Historical UI notes below. Current status is in [BATTLECARD.md](BATTLECARD.md),
> [TODO.md](TODO.md), and the [paused handoff](handoffs/readiness-2026-10-06/NEXT-AGENT.md).
> Barlow now ships locally; do not restore the external Google Fonts request.
> Market-share charts are not an implemented or approved scoring model.

## Project Overview
Markstrat-style MIS simulation app. React frontend (Vite + Ant Design) with a Python backend.
The UI is being iteratively refined to match a set of sample screenshots in `sample_screen_images/`.

## What Has Been Completed (UI Refinement Rounds 1 & 2)

### Round 1 (prior commits)
- Green primary action buttons, rounded corners (4px radius), card shadows
- Sidebar with lucide icons for nav items, teal-navy color scheme
- Phase-based sidebar navigation with numbered/icon items
- Modal-based application editing (replaced separate detail page)
- Antd Slider for rollout controls (replaced radio buttons)

### Round 2 (commit `2f73b9e`)
- **A. Font**: Switched to Barlow Semi Condensed via Google Fonts (`index.html` link + `theme.css` var)
- **B. Page titles**: Topbar h1 → 28px/600, section h2s → 17px
- **C. Table striping**: Alternating row colors on `.setup-table` and `.detail-table`
- **D. Page icons**: Topbar shows lucide icon next to page title. `Shell.jsx` has `viewIcons` map → passes `pageIcon` prop to `AppShell.jsx`
- **E. Rollout cards**: Refactored `RolloutSlider.jsx` from flat 4-column grid rows to 3-column card layout (icon + label + numeric 0-100 slider + live description + cost/coverage + budget input)
- **F. Centered buttons**: Modal, wizard, and rollout action buttons are centered. Rollout has "Reset" + "Save Changes" buttons
- **G. Dashboard charts**: Deferred (donut/line/bar charts not yet implemented)

## What Remains

### Deferred from Round 2
- **Dashboard charts** — The Dashboard page currently shows placeholder cards. The sample images (`sample1.png`, etc.) show donut charts, line charts, and bar charts. These are deferred to a future iteration.

### Known Items to Verify Against Sample Images
- Compare all pages against `sample_screen_images/` for any remaining gaps
- Mobile responsiveness at 720px breakpoint (cards stack, sidebar collapses)
- Font rendering — Barlow Semi Condensed should appear lighter/semi-condensed vs the old IBM Plex Sans

### Potential Future Work
- Dashboard visualization charts (donut for market share, line for trends, bar for comparison)
- Any remaining color/spacing tweaks after visual comparison with samples
- Performance: the JS bundle is >1MB — could benefit from code-splitting via dynamic imports

## Key Files

| File | Role |
|------|------|
| `frontend/index.html` | Google Fonts link for Barlow Semi Condensed |
| `frontend/src/styles/theme.css` | All design tokens, component CSS. Single file — no CSS modules |
| `frontend/src/components/AppShell.jsx` | Main layout shell: sidebar + topbar + content. Accepts `pageIcon` prop |
| `frontend/src/pages/Shell.jsx` | Route-level wrapper. Fetches data, maps `view` → component. Has `viewIcons` and `viewTitles` maps |
| `frontend/src/components/RolloutSlider.jsx` | Rollout category cards (Training/Process/Communication) with sliders, Reset, Save |
| `frontend/src/pages/Rollout.jsx` | Rollout page with app tabs + ownership tab |
| `frontend/src/pages/Dashboard.jsx` | Dashboard page (charts deferred) |
| `frontend/src/components/index.js` | Barrel exports for shared components (StatusBadge, ContextBanner, RolloutSlider, etc.) |
| `sample_screen_images/` | Reference screenshots the UI is being matched against |

## Architecture Notes
- No CSS modules or styled-components — all styles in `theme.css` using BEM-ish class names
- Design tokens in `:root` as CSS custom properties (primitives `--p-*`, semantic `--surface-*`, `--text-*`, etc.)
- Lucide React for all icons
- Antd used selectively (Slider, Select, Table) — not as full design system
- API client in `frontend/src/api/client.js` (axios-based)
