# Open Findings Register

**Authored by the author, 2026-08-18. This is not an audit** — it is the ledger that should
have existed from the first carried finding and did not.

**Seventy-five findings are on record across Phase 1. There has never been a list of which
are open.** Each individual deferral was defensible; the sum was never reviewed, and several
findings were filed by auditors and never surfaced to the user at all. `GOVERNANCE §8` names
the failure exactly: *unapplied deltas are letters nobody opened.*

**Rule from here: no finding is "carried" without a row in this file naming its owner.** A
finding with no owner is either fixed now or explicitly closed with a reason.

**Last swept: 2026-08-21.** Every section-B row was re-tested against the working tree by the
1.5 readiness audit (section I), after the 1.2 validator rework was found to have fixed five of
them without updating a single row. Seven were already fixed; nine are genuinely open; none
blocks 1.5. **A row that has never been re-tested is not a status — it is a claim.**

**Last reconciled: 2026-08-21**, by the consolidated catch-up rework
(`handoffs/rework/catch-up-2026-08-21.md`, branch `build/catch-up-rework`, DoD
`handoffs/rework/dod-catch-up.md` §8). All **nine** rows the 2026-08-21 sweep left open were
re-tested: six were built and are **CLOSED** with their closing check pasted (`B5` `B7` `B10`
`B11` `B13` `B17`), and three were **ruled and not built** (`B14` `B15` `B16`). This is the
first packet to run §I amendment 3 — the register updated in the same commit as the DoD.

---

## A. Fix now — no packet required

Cheap, self-contained, and blocking nothing. **These are being done rather than carried.**

| # | Finding | What |
|---|---|---|
| A1 | `1.3-006` | **FIXED 2026-08-18.** `I1` now matches SQL write verbs in statement position, not bare substrings. Proven both ways: zero hits on the real scripts, and a planted `DELETE FROM strategy` is caught |
| A2 | `1.3-009` | **RECLASSIFIED to B — not an author fix.** `PROVENANCE.md` is 1.3's artifact and the six dispositions are content judgements about what was extracted and why. Writing them myself would be authoring into another role's deliverable. Moved to B17 |
| A3 | `1.2-033` | **FIXED 2026-08-18.** 1.2 spec bumped to v1.3 with a changelog entry; header code list now reads `W01`–`W08`. `I1` re-run and still set-equal |
| A4 | — | **FIXED.** This register did not exist. It does now, and the standing rule below is what it is for |

## B. Owned by a named packet — genuinely sequenced

Cannot be fixed where they were found, because packet boundaries are what make audits mean
anything. Each names the packet that closes it.

| # | Finding | Owner | Why it must wait |
|---|---|---|---|
| B1 | `1.2-030` `1.2-031` — closed | *(done)* | Fixed in the 1.2 rework-2 copy follow-up |
| B2 | `1.1-r2-001` — closed | *(done)* | Fixed by 1.2 rework-2 item 3.6 |
| B3 | `1.1-r2-006` — closed | *(done)* | Fixed by 1.2 rework-2 item 3.3 |
| B4 | `1.2-037` · `1.1-r2-005` | *(done)* | ✅ **CLOSED — verified 2026-08-21** by the 1.5 readiness audit sweep. `obligation_rules` is validated: `E24`–`E28` are all in `catalogue()`. Fixed by the 1.2 validator rework (`dad0989`), which did not update this row |
| B5 | `1.1-r2-003` · `1.1-r2-004` · `1.2-024` | *(done — catch-up rework)* | ✅ **CLOSED — 2026-08-21, catch-up rework `build/catch-up-rework`.** Closing check re-run: `grep -c -E "\{(entity_name\|item_name\|rule_name\|question_name)\}" backend/app/casepack/validate_messages.yaml` → **9**, was 0. Seven of the eight codes (`E05` `E09` `E12` `E23` `W04` `W06` `W07`, plus `E02`'s entity noun) now resolve their subject through `lens.label(...)` against `catalog` · `entities` · `watch_rules` · `questions`, and `E07`'s `misc` catch-all is narrowed so the fix line is the thing the check tests (`1.1-r2-004`). **Residue: `E21`** still leads with a machine key — `labels.events` holds body prose, not names, so there is nowhere to author an event NAME. Carried as **`R1`**, a schema change, below |
| B6 | `1.3-012` follow-through | *(done)* | ✅ **CLOSED — verified 2026-08-21.** Riverside declares `options` on all six switches and `E26` checks `permissive_value` against them |
| B7 | `E00` mis-mapping | **partially closed → `CU-001`** | 🟡 **INSTANCE CLOSED, CLASS OPEN.** The catch-up rework fixed the `placement` instance (`placement: hybrid` now returns a targeted `E29`). The **collapse class survives** on five other closed vocabularies — re-proved at merge: a bad `provenance.source` or `entities.sensitivity` still returns a bare `E00 "Unreadable pack"` with no field location. `provenance.source` sits on nearly every object in every file. Do **not** read this row as closed; the remainder is `CU-001` below |
| B8 | `harvested_raw_fit` proximity | *(mitigated)* | 🟡 **MITIGATED — verified 2026-08-21.** The field still ships in `strategies.yaml`, but `backend/tests/test_raw_fit_isolation.py` now guards the mixing `CONTRACTS` prohibits. Relocation remains optional, not a defect |
| B9 | `1.1-r2-002` · `1.1-r2-007` | *(done)* | ✅ **BUILT AND AUDITED 2026-08-21.** `placement` and `other_policy`, the closed eleven-type vocabulary and exact per-type `E29` validation are on `build/1.5-readiness` at `1f060b4`. Independent audit `findings/1.5-readiness-2026-08-21-audit.md` — **PASS WITH FINDINGS, mergeable**. **Merged to `main` at `caece53`.** |
| B10 | `1.3-001` / CG-6 | *(done — catch-up rework)* | ✅ **CLOSED — 2026-08-21, catch-up rework.** Closing check re-run: `grep -c "capital_remaining" backend/app/casepack/models.py` → **1**. `ReviewState.capital_remaining` removed; the round budget holds the single authored home, and `E14` still enforces it against `capital_available - capital_committed` with zero tolerance. No engine or seed path reads the field; all 44 in-repo packs migrated in the same commit, no value changed. `CONTRACTS.md` gains a `capital_remaining` entry and `docs/casepack-schema.md` a migration note |
| B11 | `1.3-004` | *(done — catch-up rework)* | ✅ **CLOSED — 2026-08-21, catch-up rework, and `1.3-004` was factually wrong.** The stated derivation reproduces **exactly** when the grouping is the source's own `module_level` column: Basic n=7 mean 44571.43 · Mid n=4 mean 70000 · Advanced n=10 mean 115000 → `1.0000 / 1.5705 / 2.5801`, which is the authored `1.00 / 1.57 / 2.58`. The audit's `R2` reading reconstructed *families* at min/mid/max; both readings give 44571 for Basic, which is why it survived review. Shown with its runnable script in `PROVENANCE.md` §2a. Closing check met both ways: `erp_suite`'s capex ladder carries a derivation, and **every other** `config_tiers` multiplier on the file now carries a `TODO: calibrate` (`catalog.yaml:41`, owner 1.7). **No numeric value changed** |
| B12 | `1.3-005` | **1.7 calibration** | 🟡 **MOSTLY FIXED — verified 2026-08-21.** Now **10 of 42**, not 54 of 75. Residual is calibration content, not a missing path |
| B13 | `1.3-008` | *(done — catch-up rework)* | ✅ **CLOSED — 2026-08-21, catch-up rework.** `mis_lite` was reachable and was **queried**: it carries no headcount, user-count or staffing column in any of its 79 tables, so `people_affected` has no harvested source and never had one (query and `(0 rows)` output in `PROVENANCE.md` §11). The authored value is **62**, which five independent homes already said — 0.3 spec `:301` and `:310`, `components.html:17`, `rollout.html:13`, and the 1.4 seed `riverside_r3.py:159`. `catalog.yaml` was the sole outlier at 140, the whole-unit size, and was corrected; the mockups were **not** edited. **The 1.4 Org pin did NOT move** — the scorer reads `DeploymentState`, the seed already carried 62, and the pin is for `order_fulfilment` (`dep_order_mgmt`, 140/49) not `store_operations`; `org == 0.507003` to `1e-6`, unchanged. Guard: `harvest_readback.py` now pins the whole Users column, 43 → **47** pinned figures |
| B14 | 16 mockups at `$44,000` | *(accepted — superseded by Phase 3)* | 🔵 **ACCEPT — ruled 2026-08-21** by `handoffs/rework/catch-up-2026-08-21.md` §2 and **not built** by the catch-up rework. 16 mockup files carry `44,000`, 2 carry `46,000`; static Phase 0 mockups Phase 3 rebuilds, and no engine or scoring path reads them. The delta stays **declared**: `harvest_readback.py` prints it as a declared conflict on every run rather than reconciling it. Reason stated, not revisited (`§I` amendment 2, `ACCEPT`) |
| B15 | `1.3-011` / row 5 | *(accepted — any future harvest)* | 🔵 **ACCEPT — ruled 2026-08-21** by the catch-up scope §2 and **not built**. No second harvest is scheduled and nothing downstream consumes the 630 placeholder rows; they stay recorded in `PROVENANCE.md` §5 with their distinct-value counts, so a future harvest inherits the evidence rather than the conclusion |
| B16 | 27 `TODO: calibrate` | **1.7** | 🔵 **OPEN BY DESIGN — DEFER to 1.7**, re-affirmed by the catch-up scope §2 and **not built**. Permitted under `§4.9`; thresholds cannot be calibrated before 1.7 has an engine to calibrate against. **Count corrected 2026-08-21 (catch-up rework):** the *38* recorded here was a `grep` over the whole pack **directory**, which counts four prose mentions inside `PROVENANCE.md` itself. Marked values in pack **YAML** were **33**; they are **34** after `B11` added one covering the non-ERP `config_tiers` multipliers. `PROVENANCE.md` §7 tabulates all 34 by file |
| B17 | `1.3-009` | *(done — catch-up rework)* | ✅ **CLOSED — 2026-08-21, catch-up rework.** Closing check re-run mechanically: `34 extracted · 34 disposed · missing: []`. `PROVENANCE.md` §5a gives the six a row each, plus the two the audit called *recorded in prose but not tabulated* (`ecommerce_features_master`, `business_processes_master`), plus the `security_incidents.probability` note. `change_management_master` (8 costed options) and `change_management_strategy_fit` (20 fit cells) are recorded as a **real gap with a named owner (1.7)**, not as a discard |
| B18 | **`1.1-r3-002`** | *(done)* | ✅ **CLOSED — verified 2026-08-21.** A `default` outside its own `options` now raises a targeted `E17`, not an `E00` collapse. Fixed by the 1.2 validator rework (`dad0989`), which did not update this row |
| B19 | `1.1-r3-003` | *(done)* | ✅ **CLOSED — verified 2026-08-21.** That exact input now raises `E15` + `E26` |
| B20 | `1.1-r3-006` | *(done)* | ✅ **CLOSED — verified 2026-08-21.** `options: [on, off]` now raises `E15`, a real diagnostic, not the "restore or repair" collapse |
| B21 | `1.1-r3-005` | *(done)* | ✅ **CLOSED — verified 2026-08-21.** `CONTRACTS.md` carries a full `PolicyOption.options` / `.default` entry declaring the ordinal, permissive-first contract |
| B22 | `1.1-r3-007` | *(done)* | ✅ **CLOSED — verified 2026-08-21.** Duplicates raise `E16`; empty-string members raise `E15` |

## C. Needs a ruling from the user — cannot be fixed by anyone until decided

| # | Question | Consequence of not deciding |
|---|---|---|
| C1 | `1.5` **O4** — W08 threshold | ✅ **CLOSED — 1.5 spec v1.2.** Use `pack.metadata.rounds`; Riverside remains six, while shorter/longer packs use their authored duration |
| C2 | `1.2-035` · `1.1-r2-012` — empty affinity and W03 | ✅ **CLOSED — 1.5 spec v1.2.** Empty means explicitly global and counts for every strategy; W03 remains a review warning. Riverside uses no empty affinities |
| C3 | `1.3-015` — `firm_infrastructure` one presence rule | ✅ **CLOSED — accepted Riverside content.** The general engine permits a later recurrence as a new ledger episode; it does not overwrite history |
| C4 | `1.3-016` — five metric functions | ✅ **CLOSED — 1.5 spec v1.2.** All five named Riverside metrics are mandatory engine functions; unknown metric keys raise rather than silently evaluating false |

## D. Reported to the user late or not at all — the honest part

These were filed by auditors and did not reach the user in my summaries. Listing them is the
point of this section.

`1.1-r2-007` · `1.1-r2-008` · `1.1-r2-009` · `1.1-r2-010` · `1.1-r2-011` · `1.1-r2-012` ·
`1.3-003` · `1.3-007` · `1.3-010` · `1.3-015` · `1.3-016`

**Added 2026-08-18 — `1.1-r3-001`, and this one is a lineage failure, not an omission.**
The dispatched prompt for 1.1 rework-3 named a different branch base than the committed
prompt file. `handoffs/_prompts/` exists so that *when a build goes wrong, the prompt is
evidence* — and it held the wrong evidence. The builder declared a deviation from an
instruction it had never received; the auditor correctly found no tracked prompt saying what
the builder claimed; and I adopted the builder's account into `main` as a governance lesson
without checking it, so three of its four factual clauses were wrong on `main` for a day.

Nobody downstream could have caught it: the builder could not see the committed file, the
auditor could not see the dispatched message. **Only the dispatcher can keep those in sync.**
Corrected in `rework-3.md` §7 and in the prompt file, with the discrepancy noted in place
rather than overwritten.

Of these, one deserves naming outright: **`1.1-r2-011` — `ObligationRule` makes seven fields
required, against `rework-2.md` §5's *absolute* prohibition on new required fields.** It is
sound in substance, because `obligation_rules` is a new optional section and no existing pack
can break on it — but it is a literal breach of an instruction I wrote as absolute, and I
neither caught it nor reported it. The auditor did both.

---

## E. Reframed by `design/07` — 2026-08-18

The design map found these are **not** the problems they were filed as. Recorded so the
register and the design agree.

| Was filed as | Actually |
|---|---|
| `B6` — "the ethics layer is inert because obligation rules do not resolve" | **Half the story.** The obligation half is one of three paths. Policy also has **no stakeholder preference file** and **no scoring sub-factor**. `design/07 §3.5`. The user identified this; the audits never could, because each saw one symptom |
| `B12` — "54 of 75 options have `lead_time_rounds: 0`" | A **content** defect in a fully-built path, not a missing feature. *Follow-through* has a UI, a casepack field and a Mgmt sub-factor; the content zeroes it out. `design/07 §4` |

**New, from the map rather than from an audit:**

| # | Item | Owner |
|---|---|---|
| E1 | `preferences/policies.yaml` does not exist — the six switches are invisible to stakeholders, to scoring, **and to the persona layer** | **1.3 follow-up** |
| E2 | *information-policy discipline* has no Mgmt sub-factor — a team that never opens the screen is not neutral, it is unmanaged | ✅ **CLOSED — 1.4 closeout (2026-08-21).** `policy_discipline` is now a Mgmt sub-factor; ignoring the screen floors it at 0.25, a decided switch lifts it. `management.policy_discipline`, tests in `test_policy_dimension.py` |
| E3 | `preferences/services.yaml` does not exist — support-tier decisions draw no human reaction | **1.3 follow-up** |
| E4 | Governance has no consequence path — an unowned capability with an open critical signal should arm an event | **1.5** |
| E5 | `it.ideal_staff_load` is filed under `catalog` preferences; under G1 staffing is its own class | **4.5** |

---

## F. From the 1.3 follow-up build — 2026-08-18

| # | Item | Owner |
|---|---|---|
| F1 | **`models.py`'s `options` docstring says order carries no meaning.** `design/07 §3.5b` now rules it **ordinal**, permissive at index 0. Schema and design contradict each other until this is corrected | **1.1 next** |
| F2 | **`CONTRACTS.md` has no `PolicyOption.options` entry**, and its only sibling vocabulary (`entity.level_of_detail`) declares itself ordinal. Same as `B21`, now with a ruling behind it | **CONTRACTS** |
| F3 | **`W01` is blind to two of five preference domains.** The placeholder-seeding heuristic only inspects rows carrying an `ideal_value` key at the top level of `defaults_by_archetype`; the two new files nest under `by_decision` and use `ideal_posture` / `ideal_tier`. Nothing was dodged — the variation table substitutes — but the check no longer covers what it claims to | **1.2 next** |
| F4 | **Alignment is exact-match until `options` ordinality is consumed.** A team stricter than a stakeholder asked scores the same as one that ignored them. `3.5b` rules the fix; 1.4 must implement distance rather than equality | ✅ **CLOSED — 1.4 closeout (2026-08-21).** `policy_alignment` consumes the ordinal distance with the asymmetric formula (stricter costs half a permissive miss of the same size). `management.policy_switch_alignment`; C2/C5 in `test_policy_dimension.py` prove asymmetry and that order (not string equality) drives the score |
| F5 | `lead_time_rounds` now has 51 of 75 at exactly 1 round, so the sharpest follow-through failures rest on only 7 two-round options | **1.7 calibration** |
| F6 | `it` has a pack-grounded interest in `data_access` and `access_logging` via their `staff_load` terms, but `design/07 §3.5` does not list it, so it was flagged rather than authored | **author / 1.3** |

**Closed by this build:** `E1` (`preferences/policies.yaml` exists), `E3`
(`preferences/services.yaml` exists), `B12` / `E2`-half (`lead_time_rounds`: 54 zeroes → 17),
and the content half of `B6` (all six policies declare `options` and `default`).

---

## G. From the 1.4 scoring-engine audit — 2026-08-21

Verdict PASS WITH FINDINGS, mergeable (`findings/1.4-2026-08-21-audit.md`); merged to `main`
at `b5f53cd`. No Blocking or Functional findings. Pin reproduced independently. The
policy-distance deferral is already owned by **F4** above — the deferred
`management.policy_switch_alignment` hook builds against the ordinal contract once the 1.1
policy-order rework merges.

| # | Item | Owner |
|---|---|---|
| G1 | **Spec §5.3 said "dot product"; engine uses cosine similarity** (the correct bounded [0,1] input for the geomean, reproduces the pin). Artifact right, spec wrong — **spec wording corrected in this commit** per R5. | **Closed** |
| G2 | **`design/02 §A` "data currency/freshness" was folded into component `currency`** without being called out as a deferral in the DoD factor map. Data-freshness as a distinct factor is not yet captured | ⏸ **DEFERRED (named) — 1.4 closeout (2026-08-21), decision 12.** `design/02` now marks the row deferred: capture/storage → **3.4 Platform**, round-to-round production → **1.6**, scoring consumption → a **future 1.4 follow-up** once both exist. Component EOL `currency` stays a distinct factor and is not relabelled. Not implemented in this packet by design |
| G3 | Pre-flight row 4 quotes a fixed-figures string (`0.75 · Org 0.51 · Mgmt 0.65`) that the 0.3 v3 respec **deleted** from the mockup; the arithmetic target is intact in the 1.4 spec but the pre-flight check points at a dead file. Repoint it | **1.4 spec** |
| G4 | Spec §5.2 references "adoption formula in §5.6"; **§5.6 has no such formula** and the schema has no adoption params. Build consumed adoption as a persisted input; the dynamic formula is deferred | **1.6 round-runner** |
| G5 | The demo CLI (`print`/`json`/dynamic import) lives inside `app/engine`; scoring functions are pure and I2 passes, but relocating the CLI would make "engine does no I/O" true by construction | **1.4 follow-up** |

**Closed by this build:** `1.4` scoring engine — Tech × Org × Mgmt computed from the Riverside
R3 seed (0.750 / 0.507 / 0.648 / realised 0.246, throttle org), invariants I1–I8, decomposition
record per capability. Unblocks 1.5, 1.6, 1.7 and all of Phase 3.

---

## H. From the 1.4 closeout re-audit — 2026-08-21

Codex re-audit (`findings/1.4-closeout-2026-08-21-codex-reaudit.md`): the 1.4 policy
arithmetic and pins passed; two **input-contract** cases (D3/D4) had been resolved without
decision authority. Spec owner froze both; applied on `build/1.4-closeout`.

| # | Item | Owner |
|---|---|---|
| CR-001 | **Archetype absence is exclusion, not a raise.** The decision-9 unknown-archetype raise was removed; one rule now across code/tests/closeout-spec/CONTRACTS/closeout. Archetype-vocabulary validity is **already owned** by validator **E08** (`check_archetypes`, `checks.py ARCHETYPES`, fixture `broken_E08`) — no new item needed | ✅ **CLOSED** — 1.4 closeout |
| CR-002 | **Policy-domain `overrides` unsupported; non-empty raises.** `policy_switch_alignment` raises before scoring on a non-empty `preferences["policies"].overrides`; not parsed/guessed/partial/ignored | ✅ **CLOSED** (fail-loud) — 1.4 closeout |
| **policy-preference overrides** | **NEW future contract.** Define the typed policy-override **shape**, stakeholder/archetype **targeting**, replacement **precedence**, duplicate/conflict handling, **validator** coverage, and **scorer** consumption. Until then non-empty policy overrides raise; override support is **not implemented**. Named owner for the future work below | **future — 1.4 follow-up / a Phase-4 policy packet (unassigned to a numbered packet yet)** |

---

---

## I. From the 1.5 readiness audit — 2026-08-21

Verdict **PASS WITH FINDINGS, mergeable** (`findings/1.5-readiness-2026-08-21-audit.md`),
candidate `1f060b4489cde1cfb86de12be5b4b55f69ed9a99`. No Blocking and no Functional findings.

| # | Item | Disposition | Closing check |
|---|---|---|---|
| `1.5-RC-001` | `E29` renders *"it type 'staffing_over' is missing ratio"* — the only ungrammatical message in the catalogue — and its `fix` lists eleven type names but never the fields the declared type requires | **FIX NOW** | a missing-field `E29` fix line names that type's required fields, and the message parses as English |
| `1.5-RC-002` | The placement vocabulary has a second home: `models.py:361` re-declares as a bare `Literal` the three values `Placement(StrEnum)` already defines at `models.py:20`. Behaviour identical. The `Literal` form was **frozen by `readiness-spec.md:14-15`**, so this needs a ruling, not a fix | **RULING REQUIRED** | `grep -c 'Literal\["on_prem"' backend/app/casepack/models.py` → `0` |
| `1.5-RC-003` | `broken_E29` covers the unknown-type branch only; `E29`'s missing-required and foreign-field branches — 22 of the 33 frozen behaviours — reach the validator through no fixture | **FIX NEXT → 1.2** | matrix contains `broken_E29_missing` and `broken_E29_foreign`, both PASS |
| `1.5-RC-004` | `pytest` collects no `check_*.py`, and there is no CI, `Makefile` or `pytest.ini`. Five of six injected mutations passed both `pytest -q` and the fixture matrix, caught only by a script someone must run by path | **WATCH → FIX** | one command runs pytest + every `check_*.py` + the matrix, non-zero if any fails |
| `1.5-RC-005` | `git diff --check cedd61f 1f060b4` exits 2 on two Markdown hard line-breaks in `readiness-spec.md`, introduced by the author's commit `1fe81c9` | **FIX NOW** | `git diff --check` over the full mergeable range exits 0 |

### Register sweep — 2026-08-21

Prompted by the discovery that the 1.2 validator rework (`dad0989`, 201 files) fixed five
section-B items and updated none of their rows. **Every section-B row was re-tested against
the tree**, not read from this file:

```
19 rows listed open  ->  7 already FIXED   (B4 B6 B18 B19 B20 B21 B22)
                         2 mitigated / mostly fixed (B8 B12)
                         1 closing on merge (B9)
                         9 genuinely open  (B5 B7 B10 B11 B13 B14 B15 B16 B17)
```

Of the nine: **`B13` touches a live scoring input** (the Org training denominator — see its row;
an earlier draft of this sweep mis-rated it as mockup-only). Three touch validator or schema code
(`B5` `B7` `B10`), four are content (`B11` `B14` `B15` `B17`), and one (`B16`) is a permitted
`§4.9` deferral. **None blocks 1.5**: Riverside validates 0/0 and 1.5 pre-flight rows 7, 9 and 10
are what `B9` just closed. `B13` and `B10` are the two with real forward cost — `B13` on any
scored playthrough, `B10` on 1.6.

**Age at sweep:** seven of the nine originate in `1.3-2026-08-18` — three days. `B5` is
4–7 days (`1.2-2026-08-14`, `1.1-rework-2-2026-08-17`). Only `B14` is genuinely old
(`0.3-2026-07-27`, 25 days) and it is static-mockup content Phase 3 rebuilds. The project
merged 1.1 rework-2, 1.2 rework-2, 1.3, 1.1 rework-3, 1.4 and the 1.5 readiness gate inside
that same window, so the open set is a working queue, not accumulated debt.

### Standing-rule amendment proposed by this audit

The failure this sweep found is not that findings were carried. It is that **"owned" was
never re-tested.** An owner fired, did the work, and no step asked whether the row was still
true. Proposed, pending the user's ruling:

1. **Every finding ships its closing check** — executable, and run at filing time to show it
   currently fails. A finding whose closing check cannot be written is a question (`SPEC_PROTOCOL §2.2`),
   not a finding.
2. **Four dispositions, no fifth:** `FIX NOW` · `FIX NEXT` (names a packet that exists, and the
   closing check is copied into that packet's DoD table) · `ACCEPT` (reason stated, never
   revisited) · `WATCH` (correct today, guard thinner than the contract — the check becomes a
   permanent test).
3. **Every DoD table ends with a Register Reconciliation row.** Before merge, run the closing
   check for every register item naming this packet; update this file **in the same commit**.
   That is the step `dad0989` skipped.
4. **The auditor re-runs the register's closing checks**, not only the packet's own DoD.

---

## J. From the consolidated catch-up rework — 2026-08-21

Branch `build/catch-up-rework`. DoD and evidence: `handoffs/rework/dod-catch-up.md`.
Not audited by its builder (`GOVERNANCE §6.1`); an independent pass reviews the branch
before it merges.

**Why this packet existed:** six findings were recorded with an owner and never dispatched,
and two were dispatched and survived unclosed. Root cause, from the scope file: *"a finding
was recorded with an owner, and no step ever converted an owner into a dispatch."*

### Register Reconciliation — every row naming this packet

| # | Closing check | Result |
|---|---|---|
| `B5` | four label-section placeholders in the catalogue, non-zero | **CLOSED** — 9, was 0 |
| `B7` | out-of-vocabulary `placement` → a targeted code, not `E00` | **CLOSED** — `E29`, file and field named |
| `B10` | `grep -c "capital_remaining" backend/app/casepack/models.py` → 1 | **CLOSED** — 1, was 2 |
| `B11` | each `config_tiers` multiplier carries a derivation or a `TODO: calibrate` | **CLOSED** — and `1.3-004` was wrong; the derivation does reproduce |
| `B13` | one authored value cited to its source, `components.html` agreeing | **CLOSED** — 62. **Org pin did not move** |
| `B17` | every table in the §5.1 transform map has a disposition line | **CLOSED** — `34 disposed · missing: []` |
| `B14` `B15` `B16` | ruled in scope §2 | **ACCEPT / ACCEPT / DEFER-1.7.** Not built |

### Raised by this packet

| # | Item | Owner |
|---|---|---|
| **J1 — `R1`** | **There is nowhere in `labels.yaml` to author an event's NAME**, so `E21` still leads with a machine key while the other seven of `1.2-024`'s eight codes no longer do. `labels.events` maps `body_key` to a paragraph of in-world prose — `docs/casepack-schema.md` says so in a call-out — so routing `E21` through it would print a persona's message as a locator line. A schema change (a new section), not a validator fix; recorded at the call site in `validate.py` as well as here. **Closing check:** an `E21` finding on a pack that authors an event title leads with that title, and `docs/casepack-schema.md` no longer says there is nowhere to author one | **1.1 next** (`labels.yaml` schema) |
| **J2** | **`preferences/training.yaml`'s provenance string overstates what was harvested.** It reads *"mis_lite change management tables reworked into training preferences"*; five archetype `ideal_training_coverage` entries are not a rework of `change_management_master`'s 8 costed rollout options plus `change_management_strategy_fit`'s 20 fit cells, none of which reached the pack. Recorded in `PROVENANCE.md` §5a with both tables' dispositions. **Closing check:** the provenance string names what it actually derives from, or the eight options are authored into the pack | **1.7 calibration** |
| **J3** | **`1.3-004` is on record as a finding and is factually wrong**, and the finding file is not rewritten by this packet. `findings/1.3-2026-08-18-audit.md:220-250` asserts the `erp_suite` derivation *"does not reproduce under any grouping"*; it reproduces exactly on `erp_modules_master.module_level` (`PROVENANCE.md` §2a). The correction lives in `PROVENANCE.md`, beside the value, rather than being edited into a dated audit — `GOVERNANCE §8`: the disagreement is recorded in the living document. **Closing check:** none needed; noted so the next reader of that audit is not misled | *(recorded — no owner required)* |


---

## K. From the catch-up rework audit — 2026-08-21

Verdict **PASS WITH FINDINGS, MERGEABLE** (`findings/catch-up-rework-2026-08-21-audit.md`),
audited code `8cb507f`, merged at `89656b2`. Zero Blocking. The auditor re-ran every closing
check on all 13 rows marked CLOSED and reproduced every one.

Owners assigned here so that no finding reaches `main` ownerless — the standing rule below.

| # | Sev | Item | Disposition | Closing check |
|---|---|---|---|---|
| `CU-001` | **Functional** | The `E00` collapse class survives on five closed vocabularies (`entities.sensitivity`, `stakeholders.stakeholder_type`, `provenance.source`, `catalog.rgt_tag`, `watch_rules.metric_kind`). B7 fixed one instance, not the class. **Re-proved at merge.** | **FIX NEXT → 1.2** | every closed vocabulary returns a targeted code naming file and field; zero bare `E00` on a pack that parses |
| `CU-003` | Data | **Mutation-proven:** reverting B5's `lens.label` routing *and* E07's narrowing both pass full pytest and 43/43. B5 has now survived two rework packets with no permanent guard. Re-confirmed at merge: no test file guards it | **WATCH → FIX (1.2)** | a shipped test fails when the label routing is reverted |
| `CU-002` | Data | `E29` gained a fourth behaviour; neither `1.2-validator/spec.md:219` nor `docs/casepack-schema.md:331` was amended, unlike the two prior variants. `I1` counts `catalogue()["codes"]` only, so it is **structurally blind to variants** — "I1 stays set-equal" is not the assurance it appears to be | **FIX NEXT → 1.2** | `I1` (or a sibling) sees variants; spec and schema doc name all four `E29` behaviours |
| `CU-004` | Data | `people_affected` still has a third home at `seeds/riverside_r3.py:159` — and it is the value the scorer actually divides by | **FIX NEXT → 1.6** | one home, or a stated reconciliation rule (`SPEC_PROTOCOL §3`) |
| `CU-006` | Report | B17's denominator is the 34-table manifest, not §5.1's 24-table map, and the check is a naive substring test | **FIX NEXT → 1.3 follow-up** | the check counts the §5.1 map and matches exactly |
| `CU-005` | Report | `J3` was filed with no owner, against this register's own standing rule | **CLOSED by this entry** — `J3` (finding `1.3-004` is factually wrong) is owned by **1.3 content**; the correction is recorded beside the value in `PROVENANCE.md` | the `1.3-004` row names an owner |
| `CU-007` | Report | DoD row 39 says "no frontend in this repo"; an 18-file Vite scaffold exists. The substance of the N-A is still correct | **ACCEPT** — wording only, in a merged builder report | — |
| `CU-008` | Report | Register row `B9` says "pending merge"; `1f060b4` is already an ancestor of `main` | **FIXED in this commit** | `B9` reads closed |
| `CU-009` | Report | `CONTRACTS.md` says "18 Phase 0 mockups"; there are 19 | **FIX NEXT → CONTRACTS** | the count matches `ls mockups/` |
| `J2` | Report | `preferences/training.yaml` provenance claims a change-management rework that did not happen | **1.7** | the provenance string matches what was actually done |

**Also noted, benign:** the builder's dispatch prompt named base `caece53` while the branch was
cut from `3ae0b6d` (which adds only that prompt file). The builder declared it rather than
resolving it silently — `GOVERNANCE §7` working as intended.

**`CU-001` is the one to watch.** It is the same shape as the failure that created the
catch-up packet: a row marked CLOSED that was closed for one instance and not for the class.
It is recorded here with an owner *before* the merge is reported, not after.

---

## L. CLOSED — audited PASS and merged (2026-08-22)

All five findings were implemented on build branches, independently audited (verdict **PASS,
mergeable** on all three — no Blocking/Functional/Data/UX/Report findings), and merged to
`main`. The auditor independently mutated each guard and confirmed it fails as intended
(vocabularies → targeted `E18` not `E00`; `I1v` fails when a variant is removed from the
register; `people_affected` 140→141 fails the reconciliation guard; reverting `E21` to the
machine key fails the title test). **Register reconciliation per `GOVERNANCE §9`.**

| # | Sev | Owner | Status | Merge |
|---|---|---|---|---|
| `CU-001` | Functional | 1.2 | ✅ **CLOSED** — `E18` closes the closed-vocabulary E00-collapse **class** (nested and future fields included). Audit mutated all five vocabularies incl. `provenance.source`; each returned targeted `E18`, none `E00` | `a2d39ca` (build `9ff9ab9`) |
| `CU-002` | Data | 1.2 | ✅ **CLOSED** — invariant `I1v` holds `catalogue()["variants"]` set-equal against the spec register; audit confirmed removing `E29_vocab` from the register fails `I1v`. All four `E29` behaviours documented | `a2d39ca` |
| `CU-003` | Data | 1.2 | ✅ **CLOSED** — `test_label_routing.py` guards both halves of B5; audit confirmed both tests non-vacuous | `a2d39ca` |
| `CU-004` | Data | 1.6 | ✅ **CLOSED** — reconciliation guard fails on any seed/catalog drift (audit mutation 140→141 named exact deployment/keys/values). **Residue for 1.6:** derive `people_affected` from the catalog and delete the duplicate seed home (1.6 spec §3 decision 8) | `b102526` (build `cfe6cd1`) |
| `J1` | Report | 1.1 | ✅ **CLOSED** — `labels.event_names`; `E21` leads with the title; audit confirmed reverting to the machine key fails the test; Riverside 0/0; `event_names` optional as stated | `edec4b7` (build `dc8b416`) |

**`CU-004` carries one explicit residue** (the catalog-derivation, owned by the 1.6 build) —
per `GOVERNANCE §9` instance-vs-class closure, the guard closes the drift risk now and the
residue is named with an owner rather than left implicit.

---

## M. Owned deferrals from the 1.5 contract-completion spec — 2026-08-22

The 1.5 contract-completion candidate (`handoffs/1.5-event-signal-engine/contract-spec.md`,
authored on `author/1.5-contract-completion`, **pending independent audit**) freezes the engine's
missing interfaces. Its §0.5 STOP register surfaces changes this packet **specifies but does not
own** — each named here with an owner before the candidate merges, per the standing rule and
`GOVERNANCE §9`.

| # | Item | Owner | Gates |
|---|---|---|---|
| `CC-D1` | **`capacity_utilisation` R2/R3 exact history numbers.** The formula is frozen (§4.1); the spec's illustrative `0.83`/`1.11` are **not reproduced** under the frozen `order_app` throughput `7225.0` (which the 1.4 tech pin fixes). Exact per-round history values are calibration. | **1.7 calibration** + seed author | the `--with-signals` demonstration numbers only; the formula is executable now |
| `CC-D2` | **`saturday_queue_collapse` is not authored content** — the two-path demo is rebound to `warehouse_rollout_gap` (real). If the fictional event's persona/body/outcomes are wanted, that is pack-content authoring. | **1.3 (pack content)** — optional | nothing (rebind already covers the demo) |
| `CC-D3` | **`CatalogItem.base_rto_hours`** (NEW schema field for outage duration; engine default 8.0). **RETAGGED v1.1 (CC-A-005): HARD PREREQUISITE, not optional** — lands + is independently audited before the 1.5 engine builder is dispatched (contract-spec §9.1), like the readiness closeout | **1.1 schema** (+ **1.2** validation) — **sequenced before dispatch** | outage-duration path; part of the "all five metrics buildable" gate |
| `CC-D4` | **`Capability.agreed_availability`** (NEW per-capability SLA target; default 0.99). **RETAGGED v1.1 (CC-A-005): HARD PREREQUISITE, not optional** — same prerequisite packet as CC-D3 (contract-spec §9.1) | **1.1 schema** (+ **1.2** validation) — **sequenced before dispatch** | `availability_shortfall`; part of the "all five metrics buildable" gate |
| `CC-D5` | **`Event.repeatable`** (NEW `bool = False`, only if authored repetition is ever wanted; Riverside needs none) | **1.1 schema** | event repetition only |
| `CC-D6` | **`TeamState.debt_ratio_by_capability`** (round-evolution input for `debt_above`; unreachable in v1 — no Riverside event uses `debt_above`) | **1.6 round** | `debt_above` only |
| `CC-D7` | **`TeamState.available_funds_by_round`** (O1 affordability input for `was_actionable`; *remaining* capital, committed spend already deducted, contract-spec §5.5.2) | **1.6 round** → 1.5 consumes (explicit `()` default) | actionability computation |
| `CC-D8` | **`ArchNode.placement`** runtime field for `placement_count` (never store derived `hybrid`) | **1.6/1.1** | `placement_count` only (unused by Riverside) |
| `CC-D9` | **No "communication" field in rollout state** — v1 `rollout_without_support` reads training + process only; a richer predicate needs the field | **1.1/1.6 (registered gap)** | a richer `rollout_without_support` |
| `CC-D10` *(new, v1.1)* | **`TeamState.action_history`** (`ActionRecord[]`: action type, `locked_round`, capability/target scope, cost) — the immutable input that decides which committed action clears which signal (contract-spec §5.5.1) | **1.6 round** → 1.5 consumes (explicit `()` default) | signal clearing / responsiveness credit |

**The metric / signal-ledger / precondition / event / blast-radius core runs on existing state plus
the two 1.6 round inputs (`action_history`, `available_funds_by_round`, both defaulted `()`).**
`CC-D3`/`CC-D4` are **no longer optional deferrals** — as of contract-spec v1.1 they are required
before the engine's availability/duration paths, which is what makes all five metric functions
buildable with no deferred-path escape (closes audit CC-A-005).

**Update 2026-08-22 — `CC-D3`/`CC-D4` FOLDED into the 1.5 engine build (`GOVERNANCE §6.3` gate
tiering, ruled by the user).** Two defaulted fields with no consumer yet are **Trivial tier** — they
are the engine build's **step 0** (`handoffs/_prompts/1.5-engine-builder.txt`), covered by the engine's
own independent audit, rather than a standalone author→review→build→audit cycle. The separate
`outage-schema-spec.md` / `author/outage-schema-prereq` packet is **retired** as disproportionate. One
finding it raised is kept:

| # | Item | Owner |
|---|---|---|
| `OS-D1` | **Numeric out-of-range collapses to `E00`** — `E18`/CU-001 closed the enum/literal class only; every numeric field (`availability`, `staff_load`, `base_rto_hours`, `agreed_availability` …) still collapses to a bare `E00` on a range violation. Targeted, field-naming coverage for numeric ranges is a separate finding | **1.2** |

**Register reconciliation 2026-08-22 — `CC-D3`/`CC-D4` CLOSED.** Both fields landed as STEP 0 of the
1.5 engine build on `build/1.5-event-signal-engine`: `CatalogItem.base_rto_hours: float | None =
Field(default=None, gt=0)` and `Capability.agreed_availability: float = Field(default=0.99, gt=0,
le=1)` (`backend/app/casepack/models.py`), documented in `docs/casepack-schema.md`, with Riverside's
two non-default values authored (`financial_reporting.agreed_availability=0.995`;
`order_db_cluster.base_rto_hours=12.0`, `next_gen_firewall.base_rto_hours=4.0`, all `TODO: calibrate`
→ 1.7). All 44 fixtures load unchanged; the 1.4 pin is byte-identical; `make check` green. Both are
consumed by the shipped engine (`availability_shortfall`, `outage_duration`). `OS-D1` remains OPEN
(owner 1.2): numeric out-of-range still collapses to `E00`.

**Reconciliation 2026-08-22 — the 1.6 spec now specifies producing CC-D6/CC-D7/CC-D8/CC-D10.**
The 1.6 round-runner spec (`handoffs/1.6-round-runner/spec.md` v1.1, branch
`author/1.6-reconcile`) was reconciled against the merged 1.5 engine. Its decision 9 specifies
1.6 *populating* the four round-evolution inputs — `TeamState.action_history` (CC-D10),
`available_funds_by_round` (CC-D7), `debt_ratio_by_capability` (CC-D6), `ArchNode.placement`
(CC-D8) — all of which **already exist on the engine snapshot with explicit defaults**
(`backend/app/engine/state.py:45-49,118-134,210-222`), so 1.6 fills them without any engine
change. **Ownership is unchanged (still 1.6);** these items stay OPEN until the 1.6 build lands
and its audit closes them. CC-D8 is 1.6/1.1 (runtime placement from the deployed item; never
store `hybrid`). No new owner, no re-home — this row records that the producing packet now has
an authored spec for the production.

**Register reconciliation 2026-08-22 — CC-D6/CC-D7/CC-D8/CC-D10 CLOSED by the 1.6 build**
(branch `build/1.6-round-runner`, pending independent Heavy-tier audit). 1.6 now *produces and
persists* all four round-evolution inputs, verified on the shipped `--full` run from a clean DB:

| # | Item | Closing evidence (branch `build/1.6-round-runner`) |
|---|---|---|
| `CC-D10` | `TeamState.action_history` | derived from committed `decision_line` rows by `app/round/actions.py` + `snapshot.action_history` (append-only across rounds); `--full` R6 snapshot shows `[(scale_node,3),(add_training,3),(fund_response,3),(add_training,4),(add_node,4),(scale_node,5),(scale_node,6)]`. Guard: `tests/test_round_runner.py`, `tests/check_round_invariants.py`. |
| `CC-D7` | `TeamState.available_funds_by_round` | `snapshot.available_funds_by_round` (budget − committed, remaining capital, never accumulated); `--full` yields `(282000,142000,18000,88000,82000,82000)`. |
| `CC-D6` | `TeamState.debt_ratio_by_capability` | `snapshot.debt_ratio_by_capability` from the `debt_item` ledger; supplied for **every** capability (never `None`, so `debt_above` reads a real number). |
| `CC-D8` | `ArchNode.placement` | persisted on `arch_node`, values `{on_prem, saas}`, `SELECT count(*) WHERE placement='hybrid'` = 0 (never the derived `hybrid`, CONTRACTS.md placement). |

Closing check (all): `cd backend && PYTHONPATH=. python3 -m app.seed.demo --full` on a clean
migrated DB, then the snapshot/DB reads above; `make check` green (incl. `check_round_invariants.py`,
`check_instance_isolation.py`). Rows remain subject to the independent 1.6 audit before merge to `main`.

---

## N. 1.5 contract-completion independent spec audit — 2026-08-22

Verdict **FAIL — do not merge or dispatch** at candidate `a38b940`. Full proof and closing
requirements: `findings/1.5-contract-completion-2026-08-22.md`. All findings return to the
**1.5 contract-completion author**; schema prerequisites retain their existing 1.1/1.2 owners.

| # | Sev | Item | Owner / closing check |
|---|---|---|---|
| `CC-A-001` | Blocking | `SignalState` projection gives no credit when a timely clear prevents `fire_round` | **1.5 contract author** — project the successful no-fire path and all three seed rows exactly |
| `CC-A-002` | Blocking | Action/funds history, target matching, and effectful clearing-price candidates are undefined | **1.5 contract author + 1.6 input owner** — executable actionability/clearing examples, including zero-cost `training.none` exclusion |
| `CC-A-003` | Blocking | `policy_contradiction` divides by zero for valid zero/one-option policies | **1.5 contract author** — explicit zero/one-option boundary tests |
| `CC-A-004` | Blocking | Empty/multi-cap events leave O2 suppression and blast-radius node binding non-total/non-deterministic | **1.5 contract author** — deterministic empty/single/multi-cap checks |
| `CC-A-005` | Blocking | “all five metrics required” contradicts deferring the schema-gated availability path | **1.5 author; 1.1/1.2 schema owners** — one satisfiable sequencing rule |
| `CC-A-006` | Blocking | §11 omits material falsification checks; CC8 does not detect I/O as claimed | **1.5 contract author** — planted-defect evidence for every load-bearing invariant |
| `CC-A-007` | Report | Candidate cites an original dispatch file absent from its tree | **1.5 contract author** — exact candidate contains or immutably reaches its dispatch scope |

**Revision status — 2026-08-22.** A **fresh author** (not the v1.0 author, `GOVERNANCE §6.2`)
revised the candidate to **contract-spec v1.1** on `author/1.5-contract-completion`, closing all seven
(§15 changelog maps each finding to its section): CC-A-001 §5.4 (total credit rule + three-row
projection, pin preserved), CC-A-002 §5.5.1-4 (`ActionRecord`/funds + target matching + effectful
filter), CC-A-003 §6.1 (`< 2`-option guard), CC-A-004 §7.1/§7.3/§8.1 (ordered attribution + total
node binding), CC-A-005 §9.1 (outage-schema prerequisite sequenced before dispatch; row 7 hard STOP),
CC-A-006 §11 (falsification register rebuilt; CC8 detects I/O), CC-A-007 §0 (dispatch prompt carried
into the tree).

**✅ CLOSED — re-audit PASS, merged 2026-08-22.** Independent re-audit
(`findings/1.5-contract-completion-reaudit-2026-08-22.md`, verdict **PASS WITH FINDINGS**)
confirmed **CC-A-001..007 all genuinely CLOSED** at `de901fe` — the projection recomputed by hand
to `1/3`, the CC8 canary tested to catch `open(`/session, no non-total case found, 1.4 pin intact.
Two Report-level miscitations it raised (`RA-001`/`RA-002`, correct values / wrong line pointers)
were fixed in v1.2 (`7d6b926`, grep-verified). Contract-spec **merged to `main` at `741d358`**
(`--no-ff`, full lineage: v1.0 → FAIL audit → v1.1 → re-audit → v1.2 preserved).

**Honest note (re-audit observation).** "Fresh author" (`GOVERNANCE §6.2`) was **contextual** — an
isolated subagent, not a fork — **not confirmable from commit metadata**, since every agent commits
under the repository git identity. A process improvement to consider: a distinguishing author/co-author
trailer on agent commits.

**Does NOT unblock the engine.** Per CC-A-005, the outage schema (`CC-D3` `base_rto_hours`, `CC-D4`
`agreed_availability`) is now a **hard prerequisite** — the 1.1/1.2 outage-schema packet must land and
be audited before the 1.5 engine builder restarts pre-flight (`contract-spec §9.1`, §12 row 7).

---

## O. 1.5 Event & Signal Engine — built, audited, merged — 2026-08-22

The engine (the Phase-1 event/signal model) is **built and merged**. Independent Heavy-tier audit
(`findings/1.5-engine-2026-08-22.md`) verdict **PASS WITH FINDINGS** at build `059e7ff` — zero
Blocking/Functional; the auditor planted 8 defects to prove the falsification checks are real, and
recomputed the 1.4 pin byte-identical. Merged to `main` at `0f1444c` (`--no-ff`); the three findings
were fixed/dispositioned in the follow-up commit.

| # | Sev | Item | Disposition |
|---|---|---|---|
| `1.5-ENG-001` | Data | Engine files carried "Riverside" in **comments**, so the spec's `-niE` I1 grep reported 3 hits (no actual identity branching) | ✅ **FIXED** — comments made pack-agnostic ("the reference pack"); both the case-sensitive purity guard and the spec's `-niE` grep now read **0** over `backend/app/engine` |
| `1.5-ENG-002` | Report | The contract-spec narrative "v1.0 rule drives the pin to 0.0" is loose — protection is actually via `test_cc4_projection_reproduces_seed_rows`, not the pin test | ⏸ **ACCEPTED** — narrative nuance; the protection is real and green. Not worth a spec edit |
| `1.5-ENG-003` | Report | Contract-spec §5.5.4 worked example said `wh_rollout_01` fix = `12000`; the engine correctly computes `3000` (its `cleared_by` also includes `redesign_process`) | ✅ **FIXED** — the illustrative figure corrected to `3000` (min across the `cleared_by` set); the build was already right |

**Closed by this build:** the five metric functions, the signal ledger + `SignalState` projection,
all eleven precondition shapes, event attribution/O2/arms, blast radius + duration, and the outage
schema (`CC-D3`/`CC-D4` landed as step 0). **Unblocks 1.6 (round-runner), 1.7, 3.2, 4.3.**
`OS-D1` (numeric out-of-range → `E00`) remains open, owner **1.2**.

## P. 1.6 Round Runner — independent audit — 2026-08-22

Verdict **PASS WITH FINDINGS** (no Blocking) at `build/1.6-round-runner` @ `57fa0b5`
(`findings/1.6-round-runner-2026-08-22.md`); Functional `1.6-A-001` and Report `1.6-A-006/007`
fixed @ `777adee`. ✅ **MERGED to `main` at `1a27394`** (Heavy-tier: build → audit → mechanical
close-out → merge; the corrected SHA was mechanically re-verified — `make check` green, 1.4 pin
byte-identical, A-001 guard passing). One Functional finding fixed on the build branch; two Report
findings addressed; the rest registered here with owners per the standing rule. The builder's three
surfaced observations were all ruled sound by the integration authority. **Unblocks 1.7** (which uses
scripted teams). CC-D6/CC-D7/CC-D8/CC-D10 CLOSED (§M).

**Fixed on `build/1.6-round-runner` (this dispatch):**

| # | Sev | Item | Closing check |
|---|---|---|---|
| `1.6-A-001` | Functional | `_missed_signals` keyed the projection by signal key, collapsing episodes so a later cleared episode could mask an earlier open-then-fired one (dropping a genuine "you were told in round N"). Re-keyed by episode identity `(key, episode_id)` (zip `ledger` with `project_signal_state`, which is per-episode). | `tests/test_round_runner.py::test_a001_missed_signals_counts_each_episode` — FAILS on the collapse, passes with the fix (shown 2026-08-22). |
| `1.6-A-007` | Report | Spec §5.5 overstated the `--full` R3 pin as "byte-identical". Corrected to the honest reading: the pin is preserved hermetically (`test_engine_scoring`) and through the projection seam (`test_round_pin`); `--full` reproduces the credited/un-credited *pattern*, not the number (R3 realised ≈0.2038 ≠ pin 0.249744). | `handoffs/1.6-round-runner/spec.md §5.5`. |
| `1.6-A-006` | Report | The spec §9 DoD table was unfilled. Filled with builder evidence. | `handoffs/1.6-round-runner/spec.md §9`. |

**Registered (owned; not fixed here — ruled out of 1.6 scope):**

| # | Sev | Item | Owner | Note |
|---|---|---|---|---|
| `1.6-A-002` | Functional | Decision-sheet estate mutation is seeded (per-round estate authored), not applied by a `decision_line`→estate-delta engine. **Ruled a legitimate deferral by the integration authority** — the delta contract is undefined and belongs to a later packet. | **Live-decision mutation — Phase 2/3** | Not a defect for 1.6; the runner implements steps 1,3,9–14 and derives 4–8. **1.7 is NOT blocked** — it uses scripted teams (authored estates), exactly what `--full` provides. |
| `1.6-A-003` | Data | The `--full` opex figures are back-distributed across nodes to hit the authored ratchet targets (47000…70000) rather than derived from real per-node cost models. | **1.7 calibration** + seed author | The recompute path (`opex = sum(live node contributions)`, I7) is real; the per-node *values* are `TODO: calibrate`. |
| `1.6-A-004` | Data | Decision 8 (`people_affected` derived from the catalog) is not yet applied — the seed still carries hand-authored `people_affected` (kept consistent by `test_people_affected_reconciliation.py`). | **1.7 / content** | Deferred derivation; the reconciliation guard prevents drift meanwhile. |
| `1.6-A-005` | Report | `team_state.cash` is vestigial (written, not read by any scoring/funds path — the funds ratchet is recomputed). | **cleanup** (a later round/persistence packet) | Harmless; remove or wire when a cash consumer exists. |
| `1.6-A-008` | Report | The instance-isolation canary runs two instances of **one** casepack, not two different casepacks (GOVERNANCE §5 wording). | **2.2 instance-scoping** | 1.6 has one pack; the canary proves per-instance partitioning + no cross-reads. Full cross-casepack canary at 2.2. |
| `1.6-A-009` | Report | Step 9's raw score is a dead computation (its output is fully discarded; only step 12 is persisted). **Spec-blessed** (O4 / finding 1.6-SR-001: step 9 is provisional). | **note** (no owner action) | Kept for spec-order fidelity; a future optimisation could skip it if events never perturb tech/org. |

**Register reconciliation 2026-08-22 (build `build/1.6-round-runner`).** Fixed + re-tested on the
shipped commit: `1.6-A-001` (guard added, reachable from `make check`), `1.6-A-007`, `1.6-A-006`.
Registered with owners: `1.6-A-002` (Phase 2/3), `1.6-A-003` (1.7), `1.6-A-004` (1.7/content),
`1.6-A-005` (cleanup), `1.6-A-008` (2.2), `1.6-A-009` (note). CC-D6/7/8/10 remain CLOSED (§M). The
1.4 pin is byte-identical and `make check` is green on the shipped commit.

**Register reconciliation 2026-08-22 (build `build/1.7-calibration-harness`).** The 1.7 calibration
**instrument** landed: four scripted archetype seed builders (`backend/seeds/archetype_*.py`) run
through the real `RoundRunner.advance` for six rounds each, and `python -m app.calibrate <pack>`
prints the score curves (four BSC dimensions + realised), the term decomposition, informational
diagnostics, and the **live** `TODO: calibrate` inventory. Guard: `tests/check_calibration_harness.py`
(I1–I6, reachable from `make check`); the 1.4 pin is byte-identical after a harness run (the harness
reads `RoundResult` and scores nothing). The harness **does not calibrate** and **does not rule** —
the calibration-review gate is the user's (spec §5.4). Status of the §12 calibration items 1.7
*owns for the human review loop* (re-tested via the live inventory, which prints them each run):
`B12`/`F5`, `CC-D1`, `1.6-A-003`, `1.6-A-004`, `J2` remain **OPEN** — they are the calibration
checklist the review loop resolves, not defects the instrument fixes. `B11`/`B17` stay **CLOSED**
(catch-up rework); `B16` stays **OPEN BY DESIGN** — the 37 pack-YAML marker sites are now printed
live by the harness rather than tracked by a hand-copied count. No pack value and no engine value
was changed by this build.

**✅ MERGED to `main` at `95f0bb0`.** Independent Heavy-tier audit
(`findings/1.7-calibration-harness-2026-08-22.md`) PASS WITH FINDINGS at `649847c` — **the curves
are confirmed TRUSTWORTHY** (digest + curves reproduced; harness scores nothing; estates faithful;
1.4 pin byte-identical). Cosmetic `1.7-A-001` (report header overflow) fixed pre-merge. All seven
Phase-1 packets' code is now built, audited, and merged.

**The Phase-1 calibration GATE is OPEN and is the user's.** The instrument is done; the ruling —
*"no dominant strategy,"* plus resolving the 42 `TODO: calibrate` items — is a human judgment on the
curves (`design/05 §5`, `GOVERNANCE §6.3` §5.4). Baseline: **no dominant strategy** (Balanced leads;
all-tech-no-org realises 0.0). Two calibration questions are with the user: (1) the Balanced↔Overspender
gap is thin and Management-only; (2) R1–R2 realise 0 for all teams because `signal_responsiveness=0`
zeroes the mgmt geomean early. Owner of the calibration loop: **integration + user**, using the merged
harness.

---

## Standing rule

> **A finding is closed, owned, or being fixed. There is no fourth state, and "flagged" is
> not one of them.**

Every audit from here appends its findings to this register with an owner before the packet
that produced them merges. A packet whose findings have no owner is not done.
