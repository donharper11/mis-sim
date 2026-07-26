# MIS Simulation — Spec Authoring Protocol

Discipline for **drafting** specs. Companion to `GOVERNANCE.md` (principles) and
`QUALITY_PROTOCOL.md` (executing and verifying them).

> Drift between intent and build usually originates in the spec: an unverified assumption
> stated as fact, an invented identifier, an undefined edge case resolved silently.
> Every spec in this project is authored under this protocol and says so in its header.

**Mandatory spec anatomy:**

```
Spec Basis → Pre-Flight Verification Register → Settled / Open Decisions →
Build Phases with verify steps → Definition-of-Done table → Playthrough Script
```

Hypothesis declared → hypothesis tested → work performed → completion evidenced.

---

## 1. Spec Basis — every spec opens with it

A declaration of what the author actually read:

- **Files and extracts read in full.** The only basis on which design decisions may rest.
- **Anything cited from a summary, header map, or prose:** target zero. Any such entry is
  downgraded to `[A]` and gets a pre-flight row.
- **An extraction sufficiency statement**, one of:
  - "covered all load-bearing surfaces", or
  - "insufficient for `<X>` — targeted extraction requested before authoring", or
  - "deferred to pre-flight rows N–M"

Authoring around an acknowledged gap without one of those dispositions is an author
violation.

> **Skim-then-write is prohibited.** It produces confident fiction.

---

## 2. Evidence discipline

Every claim about existing code, schema, or behaviour carries a tag:

| Tag | Meaning | Requirement |
|---|---|---|
| `[V]` | **Verified** — read directly in the codebase, database, or a dated extraction's quoted artifact | Must cite the primary artifact: quoted code, schema output, or command output. Cite file and lines where useful |
| `[A]` | **Assumption** — believed but not read | Must name its confirmation step, which becomes a Pre-Flight row |

Rules:

- **Extractor prose, summaries, headlines, and code comments are not verification
  sources.** When a summary conflicts with the quoted source beneath it, the quoted
  source wins — and the conflict is reported.
- **No invented identifiers.** Names are quoted from verified code or explicitly marked
  **NEW**. Neither = violation.
- **Extractions expire.** State the extraction date. Builders re-verify against the
  working tree.

---

## 3. Decision discipline

- **Settled vs Open, exhaustively.** Anything a builder might decide silently is either
  settled here or listed Open with decision criteria and a reporting obligation.
  **"Obvious" is not a category.**
- **One source of truth per fact.** Never introduce a second home for the same state
  without a reconciliation rule — and prefer elimination over reconciliation.
- **Interface freezes are explicit.** Response shapes, route grammars, component props,
  casepack schema keys: FROZEN or VERSIONED. Silent changes forbidden.

---

## 4. Behaviour discipline

- **Define the null path** for every context, parameter, and mode. Unspecified absence is
  where agents improvise. What happens with no strategy declared? No sponsor assigned?
  An empty capability? A casepack with zero events this round?
- **Negative cases specified, not implied:** invalid input, collisions, permissions,
  timeouts, locked rounds, expired deadlines — each with expected behaviour and a verify
  step.
- **Every shipped behaviour has a verify step; every verify step is executable as
  written.** Frontend behaviour is verified in the browser. No verify step = not in
  scope.
- **Falsifiable invariants.** Every *must / never / only / zero / all* ships with its
  concrete falsification check — the grep, the negative input, the break-it-then-confirm-
  the-test-fails step. If you cannot write the check, the invariant is underspecified and
  the spec does not ship.

  *Example:* "no engine code branches on casepack identity" ships with
  `grep -rniE "riverside|grocer" engine/ → expect zero hits; paste output.`

- **Copy is spec'd.** Student-facing strings are written out, not described. Vocabulary
  drift starts in paraphrase.
- **Visual-acceptance rule.** Any spec whose acceptance is how a screen reads MUST ship
  with acceptance images — the reference mockup. Prose UX standards alone are prohibited.

---

## 5. Pre-Flight Verification Register

Author writes it; **builder runs it before writing any code** and reports every row.

One row per load-bearing `[V]` and per `[A]`:

| # | Claim | Check (executable command or precise inspection step) | Expected result |
|---|---|---|---|
| 1 | `arch_node` has column `availability` | `psql … -c "\d arch_node"` | column present, `numeric(4,3)` |
| 2 | `[A]` design-system exports `PanelCard` | `grep -n "PanelCard" frontend/src/components/design-system/index.js` | named export present |

Writing the check is the **author's** job. A `[V]` with no executable check is either not
load-bearing or mis-tagged — fix one.

A builder that finds a row fails **stops and reports**. It does not adapt the code to the
surprise.

---

## 6. Definition-of-Done table

Author derives it mechanically from the spec body; builder fills it. Anything in the body
without a DoD row either gets a row or gets cut.

| Item | Status | Evidence |
|---|---|---|
| *(verify step / `[A]` / test / doc delta / report obligation)* | PASS / FAIL / DEVIATION / N-A | *(command output, screenshot path, file:line)* |

The filled table **is** the builder's session report.

---

## 7. Playthrough Script

Every user-facing spec ships one. Rules and format in `QUALITY_PROTOCOL.md §3`.
Template at `handoffs/_PLAYTHROUGH_TEMPLATE.md`.

Authored **before** the build, in student language, with an `EXPECT` on every step, and
the negligent path included deliberately.

---

## 8. Scope discipline

- **Out-of-scope enumerated**, especially adjacent features an agent might helpfully
  extend. Name them.
- **Document deltas land with the change.** Exact replacement text included, applied in
  the same session, merged into the living document with a version bump — never shipped
  as a standalone delta file.
- **Conflict rule:** spec vs README vs code disagreement → stop, surface with evidence,
  await direction.

---

## 9. Project-specific requirements

Every spec in this project additionally states:

1. **Which scoring factors it touches**, keyed to `design/02-traceability-matrix.md`.
   A UI element that feeds no factor and displays no factor must justify its existence.
2. **Which casepack keys it reads**, and confirmation that no case identity is branched
   on (`GOVERNANCE.md §4.6`).
3. **Instance-scoping statement** — every new table and every new query names its
   `instance_id` handling (`GOVERNANCE.md §4.5`).
4. **Business-language check** — student-facing strings reviewed against the standing
   filter (`GOVERNANCE.md §2.1`). No engine vocabulary on student screens.

---

## 10. Author self-check before a spec ships

1. Zero untagged claims about existing code
2. Every `[A]` has a confirmation step and a register row
3. Every NEW identifier marked; every frozen interface declared
4. Null paths and negative cases covered, each with a verify step
5. Open decisions have criteria and a reporting obligation
6. Every invariant has its falsification check
7. Student-facing copy written out verbatim
8. Reference mockup attached if acceptance is visual
9. DoD table derived from the body, nothing orphaned
10. Playthrough Script written, including the negligent path
11. §9 project-specific statements present

---

## Changelog

- **1.0** (2026-07-26) — initial. Adapted from
  `nexus/handoffs_v2/nexus-spec-authoring-protocol.md` v2.0.
