# MIS Simulation — Quality Protocol

Mandatory for all coding and specification tasks. Companion to `GOVERNANCE.md`
(principles) and `SPEC_PROTOCOL.md` (authoring).

---

## 1. Completion standard

```
The intended user workflow works in the browser, with real data and real contracts,
without visible technical errors, and with audit evidence recorded.
```

"Code written" is not completion. "Build passes" is not completion. "Route returns 200"
is not completion.

**And an action is not done because the command exited 0.** Verify the resulting state,
not the exit code. `git push` succeeds silently when the ref has not moved; a migration
"runs" against the wrong database; a container restarts without picking up the change.
Check the thing you claim to have changed:

```
  claimed          verify with
  ─────────────────────────────────────────────────────────
  pushed           git ls-remote origin <branch>   — compare to local SHA
  migrated         \d on the table, not the alembic exit code
  deployed         the running artifact's version, not the deploy log
  fixed            re-run the failing check, not the build
```

**Proven, 2026-07-26:** four consecutive "pushed" claims were false. The working
directory was on a feature branch, so `git push origin main` pushed an unmoved `main`
and exited 0 each time. Nothing reached `main` for four commits. Same error class as
`SPEC_PROTOCOL.md §2.1` — asserting state from a proxy signal instead of checking it.

---

## 2. The verification ladder

Use the full ladder unless the task explicitly states why a rung is not applicable.
State the reason — do not silently skip.

### Rung 1 — Contract verification
- Inspect migrations, models, routes, services **before writing code**
- Confirm table and column names against the actual database
- Confirm API request/response shape
- Confirm auth and context requirements
- Confirm every field you touch against `CONTRACTS.md`

### Rung 2 — Implementation verification
- Typecheck / lint / build
- Backend tests where applicable
- Migration dry-run or schema check
- **Casepack validator passes** on all packs the change could affect

### Rung 3 — Runtime verification
- Start the actual dev servers
- Confirm health / readiness endpoints
- **Auth canary** — browser login + one authenticated API call on the same host pair
- Perform the intended workflow in the browser

### Rung 4 — Browser diagnostics
- Zero console errors
- Zero failed network requests
- No user-facing technical error state anywhere in the flow

### Rung 5 — UX / navigation verification
- The intended user can reach the workflow from normal navigation
- Primary and secondary actions are clear
- Loading, empty, ready, blocked, and completed states all present where relevant
- No overlapping or clipped text/controls at supported viewports (desktop 1440, 1280;
  tablet 1024)
- Diagnostics are not the primary interface
- **Language check:** UI text uses business vocabulary, not engine vocabulary. No
  "articulation point," "instance_id," "capability_key," "fit multiplier" on a student
  screen
- Screenshots recorded

### Rung 6 — Audit verification
- Independent pass by an agent with **fresh context**
- Playthrough Script re-run end to end in a real browser
- Changed files verified against the spec
- Findings recorded with stable IDs in `findings/`

---

## 3. Playthrough Scripts

The primary defence against both agent negligence and unusable screens.

### 3.1 Rules

1. **Authored before any code exists**, by the spec's author, from the spec.
2. **Written in student language**, describing what a person does — not what a test
   asserts. "Click *Add application*, choose Centraline IM 7, leave sponsor blank."
3. **Every step carries an `EXPECT`.** A step without one is not a test.
4. **The negligent path is included deliberately.** Leave the sponsor blank. Fund no
   training. Ignore the open signal. Lock anyway. That is where the teaching lives and
   where the engine is most likely wrong.
5. **Executed in a real browser with a real session** by the auditor. Playwright where
   automatable; agent-driven clicking where not.
6. **Zero console errors** required to pass.
7. **Screenshots attached** for every `EXPECT` that concerns how a screen reads.

### 3.2 Where they live

```
handoffs/<module>/playthrough.md      the script
findings/<module>-YYYY-MM-DD.md       what the audit found
screenshots/<module>/                 evidence
```

### 3.3 Full-game playthroughs

Per-screen scripts miss engine defects. Two additional scripts, run before any cohort:

- **PT-GAME-COMPETENT** — one team, six rounds, declared strategy followed coherently
- **PT-GAME-NEGLIGENT** — buys everything, trains nobody, assigns no owners, ignores
  every signal. Must produce low realised value **with a correct causal trace**

The calibration harness proves the maths. These prove a student can reach it.

---

## 4. Findings format

> **Before filing, read `SPEC_PROTOCOL.md §2.1–2.2.` Every finding carries its proof —
> `file:line`, a grep with output, or a command with output. Any claim about external
> state (registries, advisories, upstream versions, live services) is **queried during
> the session**, never recalled. A finding is an instruction in practice, and a builder
> following it has no standing to push back.**

Adopted from `aide-platform/TEST_ISSUES_LOG.md`, which worked.

Stable IDs, grouped by area, one line each, root cause where known:

```markdown
# Findings — S3 Applications
Date: 2026-08-14 · Auditor: <agent id> · Spec: handoffs/S3-applications/spec.md

## Blocking
- S3-001: Purchase wizard step 3 returns 500 when deployment=saas — integrations
  lookup assumes a platform placement row exists (services/purchase.py:142)

## Functional
- S3-002: Sponsor dropdown lists archived personas

## UX
- S3-003: Slot names render as capability_key ("wms_integration") not display label
- S3-004: Cost column clips at 1280 viewport

## Data
- S3-005: TCO checklist shows 8 options; casepack defines 6 — two are hardcoded
```

Severity order: **Blocking → Functional → UX → Data → Report.** Blocking means the
workflow cannot complete.

---

## 5. Pre-merge gate

Before any module lands:

```
□  Pre-Flight Verification Register run and reported (builder)
□  Definition-of-Done table filled with evidence (builder)
□  Ladder rungs 1–5 complete or explicitly N/A with reason
□  Playthrough Script passes end to end, zero console errors
□  Screenshots attached
□  Auth canary passed (if browser-gated)
□  Instance-isolation canary passed (if state-touching)
□  Casepack validator clean
□  Design-system canary clean (no hardcoded colours/fonts)
□  Independent audit pass complete, findings filed
□  CONTRACTS.md updated if any cross-cutting field changed
```

Any unchecked box = not landed.

---

## 6. What a builder agent does when it gets stuck

In order:

1. **Read the source.** Everything is inspectable — see `GOVERNANCE.md §4.1`.
2. **Check `CONTRACTS.md`.** The field may already have a canonical format.
3. **Check the spec's Open Decisions.** It may already be flagged.
4. **Stop and report.** Do not improvise. A reported blocker costs an hour; an
   improvised architecture costs a rebuild.

Never: infer a schema from nearby code, invent an identifier, resolve a spec/code
conflict, or mark something done that was not verified in a browser.

---

## Changelog

- **1.2** (2026-07-26) — §1: an action is not done because the command exited 0; verify
  resulting state. Prompted by four false "pushed" claims.
- **1.1** (2026-07-26) — §4 now requires findings to carry their proof; cross-references
  `SPEC_PROTOCOL.md` §2.1–2.2.
- **1.0** (2026-07-26) — initial. Adapted from `worklab/docs/QUALITY_PROTOCOL.md`.
