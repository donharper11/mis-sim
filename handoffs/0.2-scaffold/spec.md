# 0.2 — Repository Scaffold, Backend Skeleton, Design Tokens · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1
**Author:** Claude (design session) · **Date:** 2026-07-26
**Phase:** 0 · **Depends on:** none · **Blocks:** 0.3 mockups, 0.6 component library
**Reference mockup:** none — no product screens in this module. See §4 O1.

---

## 0. Spec Basis

**Read in full:**

- `~/projects/mis-tutor/backend/requirements.txt` — established the FastAPI dependency set
- `~/projects/mis-tutor/backend/app/main.py` — established the app-factory, lifespan, router
  registration, and `IntegrityError` handler patterns
- `~/projects/mis-tutor/backend/app/config.py` — established the pydantic-settings pattern
  and the Qdrant/LLM settings block
- `~/projects/mis-tutor/backend/app/models/course.py`, `team.py` — established the
  Course/CourseSection/CourseEnrollment/Team/TeamMember hierarchy that already exists
- `~/projects/mis-tutor/frontend/vite.config.js` + `package.json` (dependency block) —
  established Vite 6 + React 19 + Tailwind
- `globalstrat/frontend/globalstrat-frontend/package.json` (dependency block) — established
  antd ^5.23, React 18, CRA (`react-scripts` 5.0.1), FontAwesome, i18next, recharts
- `globalstrat/.../components/design-system/index.js` — the 12 exported components
- `globalstrat/.../components/design-system/theme.css` lines 1–80 — the CSS variable set
- `BECSR/becsr-design-system.md` lines 1–70 — the BECSR palette and font
- `~/projects/mis-tutor/mis-design-system.md` (sampled, lines 70–110) — a third token set

**Cited from summary or prose:** none.

**Extraction sufficiency:** covered all load-bearing surfaces for a scaffold. Two areas
deliberately not extracted because this module does not touch them: the globalstrat
component *implementations* (needed at 0.6, not now) and mis-tutor's alembic migration
history (this repo starts a fresh migration chain).

---

## 1. Purpose and scope

Stand up the repository so that later modules have a place to land: a bootable FastAPI
backend, a bootable React + Ant Design frontend, the design tokens, and a single sample
page that proves the tokens render.

**In scope:**
- Monorepo layout (`backend/`, `frontend/`)
- FastAPI skeleton: config, async DB session, health endpoint, alembic initialised
- Docker Compose for local dev (api, db)
- React + Vite + Ant Design skeleton with routing and an API client
- `theme.css` design tokens
- One sample page rendering a token swatch and three Ant Design controls
- CI-less local quality scripts (lint, typecheck, build)

**Out of scope — do not build these, even if it seems helpful:**
- Any domain model (capability, catalog, casepack, round, decision, signal)
- Any product screen from `design/05-implementation-plan.md §1.3`
- The design-system component library — that is module 0.5
- Porting mis-tutor's AI services — that is A1/A2/A4 in Phase 4
- Auth beyond a stub route that returns 501
- Any casepack loading or validation

---

## 2. Project-specific statements *(SPEC_PROTOCOL §9)*

**Scoring factors touched:** none. This module captures and displays no scoring factor.
It exists to make later modules possible. *(Justified exception to the traceability rule
— see `design/02-traceability-matrix.md`.)*

**Casepack keys read:** none. **Casepack-identity branching:** none — falsification check
in §6 invariant I3.

**Instance scoping:** N/A — this module creates **no runtime state tables**. The first
table carrying `instance_id` arrives in module P1. Invariant I4 enforces that 0.2 creates
none.

**Business-language check:** the sample page is a developer artifact, not a student
screen. It is reachable only at `/_dev/tokens` and MUST NOT be linked from any
navigation. Invariant I5.

---

## 3. Settled decisions

1. **Backend: FastAPI.** Confirmed by the user 2026-07-26. Rationale recorded in
   `design/05-implementation-plan.md` — mis-tutor's ~1,240 lines of AI-layer code and its
   Course/Team models port directly; BECSR's contributions are schema designs that port
   as concepts to any framework.
2. **Frontend UI kit: Ant Design.** Confirmed by the user 2026-07-26. `antd ^5.23`,
   matching globalstrat `[V]`.
3. **Build tool: Vite, not CRA.** globalstrat uses `react-scripts` 5.0.1 `[V]`, which is
   deprecated. mis-tutor already uses Vite 6 `[V]`. globalstrat's design-system components
   are plain React and port to Vite without change. **This decision is the author's, not
   the user's — it is recorded here rather than left open because the cost of being wrong
   is one config file.**
4. **React 18, not 19.** globalstrat's components are written against React 18 `[V]`;
   mis-tutor uses React 19 `[V]`. Module 0.6 ports globalstrat's components, so match the
   source. Revisit only if a dependency forces it.
5. **No Tailwind.** Ant Design plus CSS variables is the styling system. Mixing Tailwind
   with Ant Design produces two competing systems — the exact drift `GOVERNANCE.md §4.3`
   forbids.
6. **Fresh alembic chain.** This repo does not inherit mis-tutor's migration history.
7. **Python 3.12**, matching the `cpython-312` bytecode observed in mis-tutor `[V]`.

---

## 4. Open decisions

| # | Question | Decision criteria | Reporting obligation |
|---|---|---|---|
| **O1** | **Which token set is canonical?** Three exist and they have drifted. BECSR: sidebar `#0F1724`, IBM Plex Sans `[V]`. globalstrat: brand `#1E3A5F`, body `Source Sans 3`, display `Rajdhani` `[V]`. mis-tutor: a third accent set `[V]`. `GOVERNANCE.md §4.3` currently names **BECSR's** values. | **Default: follow GOVERNANCE — port globalstrat's *variable names and structure*, re-pointed to BECSR's *values*.** The component structure is the reusable asset; the values are branding. Choosing globalstrat's palette instead requires a `GOVERNANCE.md` amendment with a version bump — do not change one without the other. | Builder implements the default. If the user directs otherwise, record the direction and the GOVERNANCE amendment in `dod.md`. |
| **O2** | **Dev database location.** Local docker-compose Postgres, or the existing instance on `192.168.50.38` where `mis_lite` lives? | **Default: local docker-compose.** The scaffold must boot with no network dependency. The `mis_lite` harvest (Phase 1) reads `.38` remotely and read-only; that is a separate connection, not the app DB. | Report the `DATABASE_URL` actually used. |
| **O3** | **i18n at scaffold time or later?** globalstrat ships `react-i18next` with en + zh-CN `[V]`. | **Default: install and initialise `react-i18next` now with an `en` bundle only.** Retrofitting i18n across ten screens costs far more than carrying an empty second locale. Do not author zh-CN strings. | Confirm `i18n.js` present and `t()` used on the sample page's one string. |

---

## 5. Design

### 5.1 Repository layout

```
mis-sim/
  backend/
    app/
      __init__.py
      main.py            app factory, lifespan, health, IntegrityError handler
      config.py          pydantic-settings
      database.py        async engine + session
      api/
        __init__.py
        health.py
        auth.py          stub only — every route returns 501
      models/
        __init__.py
        base.py          DeclarativeBase
    alembic/             initialised, one empty baseline revision
    alembic.ini
    requirements.txt
    Dockerfile
  frontend/
    src/
      main.jsx
      App.jsx            router only
      api/client.js      axios instance, baseURL /api
      i18n.js
      styles/
        theme.css        design tokens  ← the deliverable
      pages/
        DevTokens.jsx    the sample page
    index.html
    vite.config.js
    package.json
    Dockerfile
  docker-compose.yml
  .env.example
```

Governance docs, `design/`, `handoffs/`, `findings/`, `mockups/`, `screenshots/` already
exist at the root. **Do not move or rename them.**

### 5.2 Backend requirements.txt

Start from mis-tutor's set `[V]`, minus what this module does not need. Pin exactly:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.1
pydantic==2.10.4
pydantic-settings==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.20
httpx==0.28.1
```

**Deliberately omitted** (arrive with their modules): `sentence-transformers`,
`qdrant-client` (A1), `reportlab` (reporting).

### 5.3 Backend patterns to carry from mis-tutor

- **App factory + `lifespan`** context manager `[V]`
- **`IntegrityError` handler** returning a 409 with a human-readable message `[V]` — port
  this verbatim; it is exactly `GOVERNANCE.md §4.9` (no raw technical errors to users)
- **`pydantic-settings` config** with `model_config = {"env_file": ".env"}` `[V]`

**Do NOT carry:** `Base.metadata.create_all` on startup `[V]`. mis-tutor creates tables at
boot and notes *"use Alembic for real migrations later."* This repo uses Alembic from the
first migration. Schema creation at startup is forbidden — invariant I2.

### 5.4 `theme.css`

Port globalstrat's variable **names and grouping** `[V]` — surface scale, topbar, brand,
section headers, status, interactive, text, charts, fonts, spacing. Re-point **values** to
BECSR per O1:

```css
:root {
  --bg-sidebar:        #0F1724;   /* BECSR */
  --bg-sidebar-active: #1E293B;
  --bg-content:        #F1F5F9;
  --bg-card:           #FFFFFF;
  --font-body: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', 'Source Code Pro', monospace;
  /* …full set per BECSR/becsr-design-system.md… */
}
```

No `--font-display` — BECSR has no display face, and introducing one is a new visual
pattern requiring approval (`GOVERNANCE.md §4.3`).

Configure Ant Design's `ConfigProvider` theme so antd components inherit these tokens
rather than fighting them. Ant's `token.colorPrimary`, `token.fontFamily`,
`token.borderRadius: 0` (BECSR is zero-radius `[V]`).

### 5.5 The sample page

Route `/_dev/tokens`. Not linked from any navigation. Renders:
1. A swatch grid of every CSS variable, each labelled with its variable name and value
2. Three Ant Design controls (Button, Select, Table) so token inheritance is visible
3. One string rendered through `t()` to prove i18n is wired

### 5.6 Student-facing copy

None. This module ships no student-facing strings. The sample page uses developer labels.

### 5.7 Null paths and negative cases

| Case | Expected behaviour | Verify step |
|---|---|---|
| DB unreachable at boot | API starts; `/api/health` returns `{"status":"degraded","db":"unreachable"}` with HTTP 200. **It must not crash the process** | Stop the db container, restart api, curl health |
| `/api/health` before any migration | Returns ok — health must not depend on schema | Fresh volume, curl health |
| Any `auth` route called | HTTP 501 with `{"detail":"Not implemented — module P4"}` | `curl -i /api/auth/login` |
| Unknown frontend route | Router renders a plain 404 view, no blank screen | Visit `/nonsense` |
| `.env` absent | Config falls back to declared defaults; app boots | `mv .env .env.bak && docker compose up` |

---

## 6. Invariants and their falsification checks

| # | Invariant | Falsification check | Expected |
|---|---|---|---|
| I1 | No hardcoded colours or font families outside `theme.css` | `grep -rniE "#[0-9a-f]{3,8}\|font-family" frontend/src --include=*.jsx --include=*.js --include=*.css \| grep -v "styles/theme.css"` | zero hits |
| I2 | No schema creation outside Alembic | `grep -rn "create_all" backend/` | zero hits |
| I3 | No casepack identity anywhere | `grep -rniE "riverside\|grocer\|casepack" backend/ frontend/src/` | zero hits |
| I4 | This module creates no runtime state tables | `ls backend/alembic/versions/` then read each; baseline revision contains no `create_table` beyond alembic's own | one baseline revision, empty upgrade body |
| I5 | Dev page not reachable from navigation | `grep -rn "_dev/tokens" frontend/src/ \| grep -v "pages/DevTokens\|App.jsx"` | zero hits |
| I6 | No Tailwind | `grep -rn "tailwind" frontend/` | zero hits |

---

## 7. Pre-Flight Verification Register

**Run every row before writing code. Report each. A FAIL means STOP and report.**

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | Repo exists with governance docs at root, `main` tracked to origin | `[V]` | `cd ~/projects/mis-sim && git log --oneline \| head -3 && ls *.md` | 2 commits; GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS, README |
| 2 | mis-tutor requirements pin set as quoted in §5.2 | `[V]` | `cat ~/projects/mis-tutor/backend/requirements.txt` | matches §5.2 versions |
| 3 | mis-tutor `main.py` has the `IntegrityError` handler to port | `[V]` | `grep -n "IntegrityError" ~/projects/mis-tutor/backend/app/main.py` | handler present |
| 4 | globalstrat pins `antd ^5.23`, React 18, CRA | `[V]` | `sshpass -p ubuntu ssh ubuntu@192.168.50.5 'grep -E "antd\|\"react\"\|react-scripts" ~/projects/globalstrat/frontend/globalstrat-frontend/package.json'` | antd ^5.23.0, react 18, react-scripts 5.0.1 |
| 5 | globalstrat `theme.css` variable groups as listed in §5.4 | `[V]` | `sshpass -p ubuntu ssh ubuntu@192.168.50.5 'grep -c "^  --" ~/projects/globalstrat/frontend/globalstrat-frontend/src/components/design-system/theme.css'` | ≥ 45 variables |
| 6 | BECSR palette values as quoted in §5.4 | `[V]` | `sshpass -p ubuntu ssh ubuntu@192.168.50.5 'grep -n "bg-sidebar\|IBM Plex Sans" ~/projects/BECSR/becsr-design-system.md'` | `#0F1724`; IBM Plex Sans |
| 7 | Python 3.12 available | `[A]` | `python3 --version` | ≥ 3.12 |
| 8 | Docker + compose available | `[A]` | `docker --version && docker compose version` | both present |
| 9 | Node ≥ 18 available | `[A]` | `node --version` | ≥ 18 |
| 10 | Port 8000/3000/5432 free locally | `[A]` | `ss -ltn \| grep -E ":8000\|:3000\|:5432"` | no conflicts, or report which |

---

## 8. Build steps

### Step 1 — Backend skeleton
- `backend/` per §5.1; requirements per §5.2; config, database, models/base
- `main.py` with app factory, lifespan, health, `IntegrityError` handler (§5.3)
- `auth.py` stub returning 501
- Alembic initialised with one empty baseline revision
- **Verify:** `docker compose up -d` → `curl -s localhost:8000/api/health` returns
  `{"status":"ok"}`; `alembic upgrade head` exits 0; `alembic current` shows the baseline

### Step 2 — Design tokens
- `frontend/src/styles/theme.css` per §5.4 and O1
- Ant Design `ConfigProvider` mapped to the tokens
- **Verify:** invariant I1 check returns zero hits

### Step 3 — Frontend skeleton
- Vite + React 18 + antd ^5.23 + react-router-dom + axios + react-i18next (en only)
- `api/client.js` with baseURL `/api`; Vite dev proxy to the backend
- Router with `/_dev/tokens` and a 404 view
- **Verify:** `npm run build` exits 0; `npm run dev` serves; browser loads
  `/_dev/tokens` with zero console errors

### Step 4 — Null paths
- Implement every row of §5.7
- **Verify:** each row's verify step, individually, output pasted

### Step 5 — Invariants
- **Verify:** run all six checks in §6, paste output

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10 reported | | |
| Step 1 verify — health + alembic | | |
| Step 2 verify — I1 zero hits | | |
| Step 3 verify — build + browser | | |
| Step 4 verify — all 5 null-path rows | | |
| I1 no hardcoded colours/fonts | | |
| I2 no `create_all` | | |
| I3 no casepack identity | | |
| I4 no runtime state tables | | |
| I5 dev page unlinked | | |
| I6 no Tailwind | | |
| O1 token set — decision + rationale recorded | | |
| O2 `DATABASE_URL` used — reported | | |
| O3 i18n present, `en` only | | |
| Ladder rung 2 — build/lint clean | | |
| Ladder rung 3 — runtime, servers up | | |
| Ladder rung 4 — zero console errors | | |
| Ladder rung 5 — 1440/1280/1024, no clipping | | |
| Playthrough passes end to end | | |
| Screenshots in `screenshots/0.2/` | | |
| Auth canary | | **N-A** — no auth in this module (P4) |
| Instance-isolation canary | | **N-A** — no runtime state (I4) |
| Casepack validator | | **N-A** — no casepacks yet (E3) |
| `CONTRACTS.md` updated if needed | | |
| `.env.example` committed; no secrets in git | | |

Status values: **PASS · FAIL · DEVIATION · N-A**.

---

## 10. Playthrough Script

`playthrough.md` in this folder.
