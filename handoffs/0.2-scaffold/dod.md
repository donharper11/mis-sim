# 0.2 — Definition of Done

> Filled by the BUILDER. This table IS the session report.


| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10 reported | PASS | Reported before code. Rows 1, 2, and 10 were DEVIATION: expected commit count stale; mis-tutor source includes later-module deps; ports 8000/3000 occupied by existing containers. No FAIL rows. |
| Phase 1 verify — health + alembic | PASS | `API_PORT=18000 POSTGRES_PORT=15432 docker compose ps` showed api/db healthy; `curl -s localhost:18000/api/health` -> `{"status":"ok"}`; `docker compose exec -T api alembic current` -> `20260726_0001 (head)`; `alembic upgrade head` rerun idempotent. |
| Phase 2 verify — I1 zero hits | PASS | `grep -rniE "#[0-9a-f]{3,8}\|font-family" frontend/src --include=*.jsx --include=*.js --include=*.css \| grep -v "styles/theme.css"` returned zero hits. |
| Phase 3 verify — build + browser | PASS | `npm ci && npm run lint && npm run build` exited 0. Browser at `http://localhost:13000/_dev/tokens` rendered swatches and Ant Design controls with no console issues or failed requests. Typecheck is N-A: this module is JSX-only and has no TypeScript files. |
| Phase 4 verify — all 5 null-path rows | PASS | DB stopped + API restarted: `{"status":"degraded","db":"unreachable"}` HTTP 200. DB restarted: `{"status":"ok"}` HTTP 200 without API restart. `.env` absent path booted. `/api/auth/login` returned HTTP 501 with specified body. `/nonsense` rendered 404. Fresh-volume health returned ok. |
| I1 no hardcoded colours/fonts | PASS | Exact I1 grep returned zero hits outside `frontend/src/styles/theme.css`. |
| I2 no `create_all` | PASS | After removing local ignored venv, `grep -rn "create_all" backend/` returned zero hits. |
| I3 no casepack identity | PASS | After removing local ignored venv, `grep -rniE "riverside\|grocer\|casepack" backend/ frontend/src/` returned zero hits. |
| I4 no runtime state tables | PASS | `backend/alembic/versions/20260726_0001_baseline.py` is the only revision; `upgrade()` and `downgrade()` contain only `pass`. |
| I5 dev page unlinked | PASS | `grep -rn "_dev/tokens" frontend/src/ \| grep -v "pages/DevTokens\|App.jsx"` returned zero hits. |
| I6 no Tailwind | PASS | `grep -rn "tailwind" frontend/` returned zero hits. |
| O1 token set — decision + rationale recorded | PASS | Implemented default: globalstrat variable grouping with BECSR values (`--bg-sidebar: #0F1724`, IBM Plex Sans, no `--font-display`). No governance amendment needed. |
| O2 `DATABASE_URL` used — reported | PASS | Default/local compose DB: `postgresql+asyncpg://mis_sim:mis_sim@db:5432/mis_sim`. Host verification used `POSTGRES_PORT=15432` because local 5432/8000/3000 were occupied. |
| O3 i18n present, `en` only | PASS | `frontend/src/i18n.js` defines only `en`; `DevTokens.jsx` renders `t("dev.tokens.title")`; browser showed `Design tokens`, raw key count 0. |
| Ladder rung 2 — build/lint clean | DEVIATION | Frontend `npm ci && npm run lint && npm run build` exited 0. Typecheck N-A: JSX-only project, no TypeScript. `npm audit fix` was run without `--force`; package-lock stayed unchanged because currently published `react-router-dom@7.18.1` still depends on vulnerable `react-router@7.18.1` and no patched `react-router-dom` release exists. Audit split: 2 shipped React Router advisories remain (`npm audit --omit=dev`); 6 dev-only eslint/minimatch/brace-expansion advisories remain and require a breaking forced eslint-chain change. Vite reported bundle-size warning. |
| Ladder rung 3 — runtime, servers up | PASS | Docker api/db healthy on alternate ports; Vite dev server ran on `http://localhost:13000/`; health/current verified. Auth canary N-A because auth is stubbed only. |
| Ladder rung 4 — zero console errors | PASS | Playwright browser pass for `/_dev/tokens`, `/nonsense`, backend-down, hover, and Slow 3G collected `consoleIssues: []` and `failedRequests: []`. |
| Ladder rung 5 — 1440/1280/1024, no clipping | PASS | Playwright screenshots `tokens-1440.png`, `tokens-1280.png`, `tokens-1024.png`; each reported `horizontalOverflow: false`, 89 swatches, zero-radius button, IBM Plex Sans. Button hover verified: normal `rgb(30, 64, 175)` darkened to `rgb(30, 58, 138)` (`#1E3A8A`). |
| Playthrough passes end to end | DEVIATION | Re-run after 0.2 findings fixes on alternate ports (`api:18000`, frontend `13000`) due pre-flight row 10 conflicts. Functional EXPECTs passed; `/api/health` ok, Alembic current `20260726_0001 (head)`, DB degraded/recovery ok, `/nonsense` 404 ok, backend-down frontend ok, Slow 3G completed with no console/network issues. `npm audit fix` did not clear React Router because the patched `react-router-dom` release is not published. |
| Screenshots in `screenshots/0.2/` | PASS | `404-1280.png`, `tokens-1024.png`, `tokens-1280.png`, `tokens-1440.png`, `tokens-backend-down-1280.png`, `tokens-button-hover-1280.png`, `tokens-slow3g-1280.png`. |
| Auth canary | N-A | **N-A** — no auth in this module (P4); auth route is a 501 stub by scope. |
| Instance-isolation canary | N-A | **N-A** — no runtime state tables; I4 passed. |
| Casepack validator | N-A | **N-A** — no casepacks or validator in this module. |
| `CONTRACTS.md` updated if needed | N-A | No cross-cutting field contract changed. |
| `.env.example` committed; no secrets in git | PASS | `.env.example` added. `git ls-files \| grep -x ".env"` returned no tracked file; `git log --all --format=%H -S"password" -- .env` returned no commits. |

Status values: **PASS · FAIL · DEVIATION · N-A**.
