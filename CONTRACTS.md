# Field & API Contracts

> **For any session (human or agent) about to touch a field listed here: read this file
> first. Quote the relevant entry in your work. Do not infer the format from nearby
> code** — it may be one of the producers or consumers below that has the wrong end of
> the contract.

Canonical source of truth for cross-cutting fields that have drifted, or are likely to.
Kept short by design.

**Last updated:** 2026-07-27 (design-token two-tier contract; status badge scale added — finding `0.3-013`).
Entries marked **PROSPECTIVE** are contracts declared in advance; convert to normal
entries with producer/consumer lists as code lands.

---

## `instance_id` — PROSPECTIVE

**Canonical:** `integer`, FK → `simulation_instance.instance_id`. Present on **every**
runtime table without exception. Never nullable.

**Rule:** every query that reads or writes game state filters on it. A query without an
`instance_id` predicate is a defect, not an optimisation.

**Why:** two sections may run different casepacks simultaneously. BECSR retrofitted this
and carries the standing note *"No data should ever leak between sections."*

**Verify:** `GOVERNANCE.md §5` instance-isolation canary.

---

## `placement` — PROSPECTIVE

**Canonical values:** `on_prem` · `cloud` · `saas`. Lower snake case. Exactly these three.

**NOT:** `on-prem`, `onprem`, `On-Premise`, `On-Premises`, `hybrid`.

**On hybrid:** hybrid is **not a placement value.** It is a derived condition — a firm is
hybrid when its shared services hold more than one distinct placement. Never store it.

**Display:** UI labels come from the casepack (`placement_labels`), not from the stored
value. mis_lite used "On-Premise" while BECSR-lineage screens say "On-Premises"; neither
is the storage format.

---

## `capability.required_roles[]` — PROSPECTIVE

**Canonical:** array of bare role keys, lower snake case.
e.g. `["transaction_store", "order_app", "client_access", "network_path"]`

**NOT** display names. **NOT** catalog item ids — a role is filled by *any* catalog item
declaring that role in `roles_filled[]`.

**Consumers:** coverage scorer (set difference against the team's graph), Applications
screen slot renderer, casepack validator.

**Display:** slot labels resolve through the casepack's `role_labels` map. A student must
never see `wms_integration` on screen — see `GOVERNANCE.md §2.1`.

---

## `entity.level_of_detail` — PROSPECTIVE

**Canonical:** a controlled vocabulary defined per casepack, ordered coarse → fine.
e.g. `["daily_store_total", "order_header", "order_line", "individual_transaction"]`

**Rule:** comparisons are **ordinal**, not string equality. A capability requiring
`order_line` is satisfied by anything at that level *or finer*.

**Never** call this "grain" in student-facing text. Business language: *"you can see
daily store totals — not individual baskets."*

---

## `decision_line.category` — PROSPECTIVE

**Canonical:** fixed enum shared by engine, UI, and every scorer.

```
platform_service · application · integration · lifecycle
training · process_redesign · communication · staffing
governance · policy · event_response · capital_request
```

**Why fixed:** portfolio discipline, the Run/Grow/Transform mix, and the maintenance
floor all aggregate on this. A new category added on one side silently breaks three
scorers.

**Adding a category requires:** an entry here, a version bump, and a stated effect on
each scorer that aggregates it.

---

## `signal.cleared_by[]` — PROSPECTIVE

**Canonical:** array of action-type keys, matched **exactly** by the responsiveness
scorer.
e.g. `["scale_node", "add_node", "move_to_cloud"]`

**Match key:** the action type, not the decision category, not the catalog item.

**Why this matters:** signal responsiveness is computed by asking whether a *resolving*
action was taken between `first_shown_round` and `fire_round`. A mismatch between the
key the UI writes and the key the watch rule declares silently produces a
responsiveness score of zero for a team that did everything right.

**Validator must check:** every `cleared_by` entry resolves to a real action type.

---

## `strategy.capability_weights{}` — PROSPECTIVE

**Canonical:** map of `capability_key → numeric`, summing to `1.0` per strategy.

**Validator must check** the sum, per strategy, to 3 decimal places. mis_lite's
equivalent (`component_strategy_fit.fit_multiplier`) was un-normalised multipliers
around 1.0 — a different scheme. **Do not mix the two.** Harvested multipliers are
converted on ingest, not stored raw.

---

## Casepack identifiers — PROSPECTIVE

**Canonical:** `pack_key` is lower snake case and stable forever
(e.g. `riverside_grocery`). `pack_version` is semver.

**Rule:** engine code **never** branches on `pack_key`. Enforced by the Phase 6 gate and
by the falsification check in `SPEC_PROTOCOL.md §4`.

---

## Design tokens — two-tier — PROSPECTIVE

Canonical: components reference SEMANTIC ROLES only (`--surface-page`, `--text-muted`,
`--status-danger-bg`). Never primitives (`--p-slate-100`, `--p-navy-900`), never raw
values.

Roles resolve to primitives in exactly one step. A role defined as another role is a
defect — it reintroduces the aliasing this replaced.

Producers: `frontend/src/styles/theme.css` — the only file that may declare either tier.
Consumers: every component, every mockup.

Adding a role: entry here + spec change. Adding a primitive: `theme.css` only.

---

## Status badge scale — PROSPECTIVE

**Canonical: four values, four DISTINCT role tokens.** Used by every screen, and the
acceptance contract for module 0.5's `StatusBadge`.

```
Complete          --status-ok-bg / -text / -marker        green    done, nothing needed
Partly done       --status-info-bg / -text / -marker      blue     underway, on track
Needs attention   --status-warn-bg / -text / -marker      amber    action needed this round
Not started       --status-neutral-bg / -text / -marker   grey     nothing here yet
```

**NOT** `Partly done` sharing `--status-ok-*` with `Complete`. That was finding `0.3-013`:
a capability at 25% realised and explicitly throttled carried the same green as one at
5/5, so colour-scanning could not distinguish them.

**Signal severity is a SEPARATE scale** and must not be conflated:
`Critical → --status-danger-*` · `Warning → --status-warn-*`. An item's *status* and a
signal's *severity* answer different questions.

**Rule:** every status-bearing item shows a badge. An item with a status and no badge is a
defect — inconsistent application is how `0.3-013` hid.

---

## Selected state — PROSPECTIVE

**Two named patterns. No third.** The earlier version of this entry named tokens without
naming a grammar, and three files each invented one — finding `0.4-001`. A contract that
specifies a palette is not a contract.

**Which pattern applies is determined by the option's shape, not by the author's taste.**

### Pattern A — option row
*A list of mutually exclusive choices, each a single line of text.*

```
selected     ● label · detail          --text-primary · marker --action-primary
unselected   ○ label · detail          --text-secondary · marker --border-default
disabled     ○ label · reason          --action-disabled-text, reason stated
```

Filled and hollow circle glyphs, `●` / `○`. Applies to: Services tiers, Rollout mix
(training · process · communication), Challenges rationale tags, any radio-shaped choice.

### Pattern B — option card
*Choices carrying more than one line — a price, a lead time, a warning.*

```
selected     2px --border-focus outline · --surface-row-highlight fill · check mark
unselected   1px --border-default · --surface-card
disabled     --action-disabled bg · --action-disabled-text · reason stated on the card
```

Applies to: Strategy options, the wizard's deployment modes, Fund/Defer/Reject.

### Rules

1. **One line of text → Pattern A. Multiple lines → Pattern B.** No judgement call.
2. **A choice with no visible selection is a defect** — findings `B9`, `0.3-025`.
3. **A commit action stays disabled until every required choice has a selection**, and
   states why. `--action-disabled` / `--action-disabled-text`.
4. **Where the mockups and this entry disagree, this entry wins.** The 0.3 and 0.4 mockups
   predate it; module 0.5 implements the contract, not the files.

---

## Row opens detail — PROSPECTIVE

**Canonical:** in any table whose rows open a detail view, the row carries a visible
affordance — a trailing chevron plus `--text-link` on the first cell, and a hover state
using `--surface-row-highlight`.

**Rule:** a clickable row that looks unclickable is a defect. Found as `0.3` finding
**B3** — nothing on the Components table signalled that a row opened anything.

---

## Harvested mis_lite content — NOTE, not a contract

- Every mis_lite table carries a `trialNNN char(1)` column, uniformly `'T'`. It is a
  software-migration carryover. **Drop on harvest. Never model it.** BECSR's `CLAUDE.md`
  carries the same instruction for the CSR database.
- mis_lite `component_types_master` (45 rows) is a **Chapter 5 vocabulary list**, not a
  parts list. Only ~19 entries are buildable catalog items; the rest are concepts and
  belong in curriculum reference, not the catalog. See `design/01-mis_lite-harvest.md §3`.

---

## How to add an entry

Add when a field is consumed in more than one place and its format could plausibly be
guessed wrong. Include: canonical format, explicit NOTs, producers, consumers, and why
it matters. Keep it short — this file only stays useful if it stays readable.
