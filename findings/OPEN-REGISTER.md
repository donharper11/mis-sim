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
| B9 | `1.1-r2-002` · `1.1-r2-007` | **1.1 next** | `placement_count` needs `placement` as well as `count`; `policy_contradiction` needs a second policy key. **Three of six precondition types remain unexpressible, and 1.5's pre-flight passes anyway** |
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
| C1 | `1.5` **O4** — should `W08`'s `N` track `pack.rounds` rather than being flat at 6? The audit recommends yes and showed it costs nothing on Riverside | A 4-round pack is held to a 6-card bar. Affects every future casepack, not Riverside |
| C2 | `1.2-035` · `1.1-r2-012` — **`W08` and `W03` pull in opposite directions.** The empty-affinity card that `1.5 §5.2a` sanctions as giving every strategy a draw is the same card `W03` warns about | An authoring trap with no right answer. It is a **design** conflict between two of my own specs, not a bug |
| C3 | `1.3-015` — `firm_infrastructure`'s only watch rule is presence-shaped, making it a one-shot signal | May be correct by design or may be a content gap. I do not know which |
| C4 | `1.3-016` — every card fires from one `signal_open` precondition, and five metric functions must exist for the deck to work at all | Names a hard dependency 1.5 inherits. Needs confirming as intended |

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

## Standing rule

> **A finding is closed, owned, or being fixed. There is no fourth state, and "flagged" is
> not one of them.**

Every audit from here appends its findings to this register with an owner before the packet
that produced them merges. A packet whose findings have no owner is not done.
