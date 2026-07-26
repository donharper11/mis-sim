# 0.2 — Definition of Done

> Filled by the BUILDER. This table IS the session report.


| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10 reported | PASS | Reported before code. Rows 1, 2, and 10 were DEVIATION: expected commit count stale; mis-tutor source includes later-module deps; ports 8000/3000 occupied by existing containers. No FAIL rows. |
| Phase 1 verify — health + alembic | PASS | `API_PORT=18000 POSTGRES_PORT=15432 docker compose ps` showed api/db healthy; `curl -s localhost:18000/api/health` -> `{"status":"ok"}`; `docker compose exec -T api alembic current` -> `20260726_0001 (head)`; `alembic upgrade head` rerun idempotent. |
| Phase 2 verify — I1 zero hits | PASS | `grep -rniE "#[0-9a-f]{3,8}\|font-family" frontend/src --include=*.jsx --include=*.js --include=*.css \| grep -v "styles/theme.css"` returned zero hits. |
| Phase 3 verify — build + browser | PASS | `npm ci && npm run lint && npm run typecheck && npm run build` exited 0. Browser at `http://localhost:13000/_dev/tokens` rendered swatches and Ant Design controls with no console issues or failed requests. |
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
| Ladder rung 2 — build/lint clean | PASS | Frontend `npm ci && npm run lint && npm run typecheck && npm run build` exited 0; backend `python -m compileall app` exited 0 before removing local venv. Vite reported bundle-size warning; npm audit reported 8 high vulnerabilities in dependency tree. |
| Ladder rung 3 — runtime, servers up | PASS | Docker api/db healthy on alternate ports; Vite dev server ran on `http://localhost:13000/`; health/current verified. Auth canary N-A because auth is stubbed only. |
| Ladder rung 4 — zero console errors | PASS | Playwright browser pass for `/_dev/tokens`, `/nonsense`, backend-down, and Slow 3G collected `consoleIssues: []` and `failedRequests: []`. |
| Ladder rung 5 — 1440/1280/1024, no clipping | PASS | Playwright screenshots `tokens-1440.png`, `tokens-1280.png`, `tokens-1024.png`; each reported `horizontalOverflow: false`, 89 swatches, zero-radius button, IBM Plex Sans, BECSR navy primary. |
| Playthrough passes end to end | DEVIATION | Passed on alternate ports (`api:18000`, frontend `13000`) due pre-flight row 10 conflicts. All functional EXPECTs passed; Slow 3G render took over 60s but completed with no console/network issues. |
| Screenshots in `screenshots/0.2/` | PASS | `404-1280.png`, `tokens-1024.png`, `tokens-1280.png`, `tokens-1440.png`, `tokens-backend-down-1280.png`, `tokens-slow3g-1280.png`. |
| Auth canary | N-A | **N-A** — no auth in this module (P4); auth route is a 501 stub by scope. |
| Instance-isolation canary | N-A | **N-A** — no runtime state tables; I4 passed. |
| Casepack validator | N-A | **N-A** — no casepacks or validator in this module. |
| `CONTRACTS.md` updated if needed | N-A | No cross-cutting field contract changed. |
| `.env.example` committed; no secrets in git | PASS | `.env.example` added. `git ls-files \| grep -x ".env"` returned no tracked file; `git log --all --format=%H -S"password" -- .env` returned no commits. |

Status values: **PASS · FAIL · DEVIATION · N-A**.
