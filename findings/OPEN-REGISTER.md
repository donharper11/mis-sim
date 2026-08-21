# Open Findings Register

**Authored by the author, 2026-08-18. This is not an audit** — it is the ledger that should
have existed from the first carried finding and did not.

**Seventy-five findings are on record across Phase 1. There has never been a list of which
are open.** Each individual deferral was defensible; the sum was never reviewed, and several
findings were filed by auditors and never surfaced to the user at all. `GOVERNANCE §8` names
the failure exactly: *unapplied deltas are letters nobody opened.*

**Rule from here: no finding is "carried" without a row in this file naming its owner.** A
finding with no owner is either fixed now or explicitly closed with a reason.

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
| B4 | `1.2-037` · `1.1-r2-005` | **1.2 next** | `obligation_rules` is entirely unvalidated; 1.3's `I11` has no executable check. A validator change |
| B5 | `1.1-r2-003` · `1.1-r2-004` · `1.2-024` | **1.2 next** | The four `Labels` sections are consulted by no message, and they silently widened `E07`'s `misc` catch-all |
| B6 | `1.3-012` follow-through | **1.3 content, then 1.2** | `PolicyOption.options` now exists (1.1 rework-3). Riverside must declare them; then the validator checks `permissive_value` against them |
| B7 | `E00` mis-mapping | **1.2 next** | A semantic failure reports *"Unreadable pack — restore or repair"* for a file that parsed fine. `GOVERNANCE §4.10` |
| B8 | `harvested_raw_fit` proximity | **1.2 next** | It ships inside `strategies.yaml`, one field from the weights it must never become, with nothing behind `CONTRACTS`' "do not mix the two" |
| B9 | `1.1-r2-002` · `1.1-r2-007` | **1.5 readiness closeout** | Field names are now frozen as `placement` and `other_policy`; implementation and per-type validator coverage are specified in `handoffs/1.5-event-signal-engine/readiness-spec.md`. Still blocks the 1.5 engine until built and audited |
| B10 | `1.3-001` / CG-6 | **1.1 next** | Both `capital_remaining` fields are schema-required, so the second home cannot be eliminated by authoring |
| B11 | `1.3-004` | **1.3 follow-up** | `erp_suite.config_tiers` claims a derivation no grouping reproduces |
| B12 | `1.3-005` | **1.3 follow-up / 1.6** | 54 of 75 placements carry `lead_time_rounds: 0`, so CG-3's *abandoned mid-flight* is undefined for 72% of the ladder |
| B13 | `1.3-008` | **0.4 or 1.3** | `pos_system_2011.people_affected` is 140; `components.html` pins 62 |
| B14 | 16 mockups at `$44,000` | **0.4 rework** | Derivation says `46000`; `review.html` contradicts itself inside one file. Recommended, never authorised |
| B15 | `1.3-011` / row 5 | **any future harvest** | 630 mapping rows are placeholder-seeded; four tables have one distinct tuple repeated |
| B16 | 27 `TODO: calibrate` | **1.7** | Permitted under `§4.9`. `1.3-014` names the five watch-rule thresholds the gate actually turns on |
| B17 | `1.3-009` | **1.3 follow-up** | Six extracted tables named in §5.1's transform map have no `PROVENANCE.md` disposition. Content judgement, belongs to whoever authors the pack |
| B18 | **`1.1-r3-002`** | **1.2 next** | **One bad value hides every other error.** A `default` outside its own `options` collapses the entire report to a single `E00 "Unreadable pack"` — proved on `broken_E05`, where a real `E05` and two `W08`s vanished. An author with one typo loses all their other diagnostics. Upgrades `B7`, which had only the wording |
| B19 | `1.1-r3-003` | **1.2 next** | `options: ["Indefinite", "NOT snake!", "9lives"]` validates clean. `SnakeKey` is a bare alias and `I3` cannot reach these fields, so machine keys students never see are unconstrained |
| B20 | `1.1-r3-006` | **1.2 or docs** | `options: [on, off]` is parsed by YAML as booleans and rejected as "restore or repair policies.yaml". A pack author writing the most natural two-state switch gets a misleading error |
| B21 | `1.1-r3-005` | **`CONTRACTS.md`** | `PolicyOption.options` has no CONTRACTS entry, and its only sibling per-pack vocabulary (`entity.level_of_detail`) declares itself **ordinal** — the opposite rule. 1.5 and 4.3 both need to know which |
| B22 | `1.1-r3-007` | **1.2 next** | Duplicate and empty-string members of `options` are accepted |

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

## Standing rule

> **A finding is closed, owned, or being fixed. There is no fourth state, and "flagged" is
> not one of them.**

Every audit from here appends its findings to this register with an owner before the packet
that produced them merges. A packet whose findings have no owner is not done.
