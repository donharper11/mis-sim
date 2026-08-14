# 1.2 — Casepack Validator · Definition of Done

**Builder:** Claude (same builder, resumed for the v1.2 rework) · **Date:** 2026-08-14
**Branch:** `build/1.2-validator` · **Base:** `78a1ee2` · **Audited at:** `e8191c5`
**Spec:** `handoffs/1.2-validator/spec.md` **v1.2** · **Rework instruction:** `rework.md`
**Audit answered:** `findings/1.2-2026-08-14-audit.md` — substance PASS WITH FINDINGS ·
spec FAIL · process PASS · 0 blocking

> Every row below carries pasted command output. An assertion without output is not
> evidence (`QUALITY_PROTOCOL.md §1`).

---

## R1 — what the spec change invalidated

`handoffs/README.md` **R1** requires the rework to name the build steps the amended spec
invalidates. **v1.2 changes §3, §5.1, §5.2, §5.3, §5.4, §5.5, §6, §7 row 2, §9 and §9.1.
In build-step terms it invalidates steps 1–5 — all of them — but only in part.** Nothing
built in the first cycle was discarded.

| Spec §8 step | Invalidated by | What actually changed |
|---|---|---|
| 1 · Structural E01–E11 | §5.1 gains `E12`, `E13`, `E14`; `E00`, `I3`, `I8` ratified as named codes | three new checks; the eleven existing ones unchanged |
| 2 · Coherence E20–E23 | §5.2 widens `E20`'s predicate (§3 decision 7) | one predicate rewritten, one new reason arm, second fixture arm added |
| 3 · Heuristics W01–W07 | §5.3 rewrites `W05` to the deck-depth form and binds `W01`'s N to 6 | the build already shipped both; the spec caught up. No code change |
| 4 · CLI, output, `--json` | §5.4 rewritten; §3 decision 3 extended to every severity; §6 rewrites I1 and widens I5 | renderer rebuilt, directory-mode JSON reworked, both invariant checks replaced |
| 5 · Fixture suite | §5.5 corrected (Riverside exits 1); three new codes need fixtures | four fixtures added, two amended, `minimal_valid` made coherent |

**R5 note.** v1.2 closed no build finding — `1.2-005`, `1.2-006` and `1.2-015` were against
the artifact and are closed here, in code, not in the document.

---

## 0. Pre-Flight Verification Register (spec v1.2 §7)

| # | Claim | Result | Evidence |
|---|---|---|---|
| 1 | 1.1 merged; `models.py` and `checks.py` exist | **PASS** | below |
| 2 | Riverside loads and parses under 1.1, **and a nonexistent path raises** | **PASS** | below |
| 3 | `checks.py` exposes **six** check functions | **PASS** | below |
| 4 | Action-type set exists as `ACTION_TYPES`, line 12, ten values | **PASS** | below |

**Row 2 is the corrected row.** v1.1's check — `python -m app.casepack.loader <pack>` —
could not fail, because `loader.py` has no `__main__`; it reported PASS against a pack that
does not exist (`1.2-004`). In the first cycle I substituted a call that works, pasted its
output honestly, and **did not declare the substitution**, which is how the vacuous row
survived. v1.2 replaces the row with the check I ran, plus a falsification arm.

```
$ ls backend/app/casepack/
checks.py  __init__.py  loader.py  models.py  seed.py  validate_messages.yaml  validate.py

$ cd backend && python3 -c "from app.casepack.loader import load_casepack; p=load_casepack('packs/riverside_grocery'); print(p.metadata.pack_key, len(p.capabilities), len(p.watch_rules))"
riverside_grocery 7 3

$ cd backend && python3 -c "from app.casepack.loader import load_casepack; load_casepack('packs/NO_SUCH_PACK')" ; echo "exit=$?"
Traceback (most recent call last):
    raise CasepackLoadError(f"{relative}: missing file")
app.casepack.loader.CasepackLoadError: pack.yaml: missing file
exit=1
                                            ← the falsification arm: the row can now fail

$ grep -c "^def check_" backend/app/casepack/checks.py
6

$ grep -n "^ACTION_TYPES" backend/app/casepack/checks.py
12:ACTION_TYPES = {
$ cd backend && python3 -c "from app.casepack.checks import ACTION_TYPES; print(len(ACTION_TYPES))"
10
```

No row deviated. No second action-type vocabulary was declared (spec §3 decision 6).

---

## 1. Definition of Done — spec v1.2 §9

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–4 | **DONE** | §0, all PASS, row 2 now falsifiable |
| `E00`–`E14` implemented, each with a fixture | **DONE** | §3, §4 |
| `E20`–`E23` implemented, each with a fixture | **DONE** | §3, §4; `E20` has one fixture per arm |
| `I3`, `I8` emitted as codes | **DONE** | §3 — `I3` has a fixture; `I8` is unfixturable and declared, `1.2-019` |
| `W01`–`W07` implemented, `W05` in its §5.3 deck-depth form | **DONE** | §4, §7 |
| CLI output matches §5.4 — business name leading, `Fix:` at **every** severity | **DONE** | §5 |
| `--json` mode, including directory mode (I5) | **DONE** | §6 |
| I1–I5 | **DONE** | §6, each with a falsification |
| O1, O2 recorded | **DONE** | §8 |
| `ARCHETYPES` relocated to `checks.py` beside `ACTION_TYPES` | **DONE** | §2 |
| **Seed** — fixture packs, one per error code, all exercised | **DONE** | §3 |
| **Riverside fails with exactly the known content gaps** — §9.1 | **DONE** | §9 — matches §9.1 line for line |
| Browser / auth / instance canaries | **N-A** | headless CLI, no state, no UI |
| Re-run sequence for the auditor (§9.2) | **DONE** | `backend/tests/check_fixture_matrix.py`, §3 |

### 1.1 Rework instruction §4 — the additional rows

| Item | Status | Evidence |
|---|---|---|
| `E12`, `E13`, `E14` implemented, each firing alone | **DONE** | §4.1 — three pasted runs, one error each |
| `E20` fires on both arms | **DONE** | §4.2 — `broken_E20` and `broken_E20_mute` |
| §5.4 shape, `Fix:` at every severity | **DONE** | §5 — pasted WARN block carrying its fix |
| Directory-mode `--json` parity | **DONE** | §6 — tuple sequences diffed, identical, plus a falsification |
| `ARCHETYPES` in `checks.py` | **DONE** | §2 — `grep -n` in both files |
| `I1` set-equality, `I5` widened | **DONE** | §6 — both re-run, both falsified, before/after stated |
| `O2` message distinct from `E10` | **DONE** | §8 — both pasted |
| `dod.md` §3 regenerated verbatim | **DONE** | §4.3 — unedited command output |
| Riverside matches v1.2 §9.1 exactly | **DONE** | §9 |
| `check_fixture_matrix.py` green | **DONE** | §3 |
| **R1 note** | **DONE** | top of this file |

---

## 2. What changed in this rework

```
backend/app/casepack/checks.py             + ARCHETYPES, + REVIEW_AREAS
backend/app/casepack/validate.py           E12/E13/E14, E20 widened, renderers rebuilt,
                                           Run replaces the second directory-mode path
backend/app/casepack/validate_messages.yaml  subject per code, fix at every severity,
                                           new codes, E20 reasons, E10 pack-key variant
backend/tests/check_fixture_matrix.py      + I1 set-equality, + I5 two-mode parity
backend/tests/fixtures/packs/              + broken_E12/E13/E14/E20_mute,
                                           minimal_valid made coherent, 2 fixtures narrowed
```

**No new dependency.** `PyYAML==6.0.2` and `pydantic==2.10.4` were already pinned; nothing
was added.

**`ARCHETYPES` relocated** — spec §3 decision 9. Sourcing was verified correct by the
auditor; only its home changed.

```
$ grep -n "^ARCHETYPES\|^ACTION_TYPES\|^REVIEW_AREAS" backend/app/casepack/checks.py
12:ACTION_TYPES = {
31:ARCHETYPES = {
50:REVIEW_AREAS = {
$ grep -n "^ARCHETYPES" backend/app/casepack/validate.py
                                                    (no output — it no longer lives there)
$ grep -n "base_checks.ARCHETYPES" backend/app/casepack/validate.py
601:        if person.archetype not in base_checks.ARCHETYPES:
610:                    count=len(base_checks.ARCHETYPES),
611:                    known=", ".join(sorted(base_checks.ARCHETYPES)),
```

`REVIEW_AREAS` is **new vocabulary this rework had to introduce** — see §10, item 2.

**One duplication removed.** The audit's Part C2 noted `1 if any(... ERROR) else 0` had two
homes, against `SPEC_PROTOCOL §3`. Both callers now share `exit_code_for()`.

---

## 3. The fixture suite and the re-run artifact

`minimal_valid` remains real content under `GOVERNANCE §4.9` — Harbour Veterinary Group,
four practices and an out-of-hours clinic, capital arithmetic derived rather than authored
twice. The audit read it in full and ruled it *"seed, not stub, and comfortably so."*

**One coherence repair, unrequested, declared.** The audit noted
(*"`minimal_valid` under GOVERNANCE §4.9"*) that `value_chain_coverage` named
`firm_infrastructure`, which this pack does not have. It is now keyed by value chain
activity, matching each capability's `chain_position`, with every activity the pack does
not cover reported honestly as `none` rather than named as though it were covered.

**Two fixtures narrowed, unrequested, declared.** The audit found the trailing `E07` in
`broken_E01` and `broken_E22` *"avoidable — adding one line to each fixture's `labels.yaml`
would remove that arm cleanly."* Done. Both now raise only their own code plus the
`E22 ⊆ E01 ∪ E02` superset the audit ruled inherent.

```
$ python3 backend/tests/check_fixture_matrix.py
fixture          want  got  codes raised
minimal_valid       0    0  -   PASS
broken_E00          1    1  E00   PASS
broken_E01          1    1  E01,E22   PASS
broken_E02          1    1  E02,E22   PASS
broken_E03          1    1  E03   PASS
broken_E04          1    1  E04   PASS
broken_E05          1    1  E05   PASS
broken_E06          1    1  E06   PASS
broken_E07          1    1  E07   PASS
broken_E08          1    1  E08   PASS
broken_E09          1    1  E09   PASS
broken_E10          1    1  E10   PASS
broken_E11          1    1  E11   PASS
broken_E12          1    1  E12   PASS
broken_E13          1    1  E13   PASS
broken_E14          1    1  E14   PASS
broken_E20          1    1  E20   PASS
broken_E20_mute     1    1  E12,E20,E21   PASS
broken_E21          1    1  E21   PASS
broken_E22          1    1  E01,E22   PASS
broken_E23          1    1  E23   PASS
broken_I3           1    1  I3   PASS
warn_W01            0    0  W01   PASS
warn_heuristics     0    0  W02,W03,W04,W05,W06,W07   PASS

I1  implemented codes : 28 ['E00', 'E01', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07', 'E08', 'E09', 'E10', 'E11', 'E12', 'E13', 'E14', 'E20', 'E21', 'E22', 'E23', 'I3', 'I8', 'W01', 'W02', 'W03', 'W04', 'W05', 'W06', 'W07']
I1  spec-named codes  : 28 ['E00', 'E01', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07', 'E08', 'E09', 'E10', 'E11', 'E12', 'E13', 'E14', 'E20', 'E21', 'E22', 'E23', 'I3', 'I8', 'W01', 'W02', 'W03', 'W04', 'W05', 'W06', 'W07']
I1  set equality      : PASS

I5  minimal_valid                      text=  0 json=  0 identical=yes
I5  warn_heuristics                    text=  6 json=  6 identical=yes
I5  riverside_grocery                  text= 23 json= 23 identical=yes
I5  packs/  (directory mode)           text= 35 json= 35 identical=yes
I5  directory-mode pack attribution    every record names its pack

all 24 fixtures behave as named; 27 of 28 codes exercised, ['I8'] recorded as unfixturable
I1 set-equal against the spec; I5 identical in single-pack and directory mode
EXIT=0
```

Per spec §9.2 this script is the auditor's re-run artifact, and it now carries I1 and I5 as
well as the matrix. **That is an extension of §9.2 and is declared as one:** the section
describes the script as asserting codes, exit codes and fixture coverage. Folding the two
rewritten invariants into the same executable keeps one artifact rather than three.

---

## 4. The new and changed checks

### 4.1 `E12`, `E13`, `E14` — each firing alone

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E12

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  4 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  ERROR  E12  Watch rule book_noshow_01       watch_rules.yaml:15
         Watches 'Appointment Booking' but sets neither a warning nor a critical threshold, so it can never fire. It counts towards coverage while watching nothing.
         Fix: set warn_above or critical_above on 'book_noshow_01' in watch_rules.yaml, or remove the rule.
         Field: book_noshow_01

  1 error · 0 warnings · exit 1

EXIT=1
```

The `broken_E12` mutation adds a thresholdless rule **beside** an intact one, so the
capability stays watched and `E12` is isolated from `E20` and `E21`.

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E13

  ERROR  E13  Opening position                pack.yaml:25
         The opening position names the strategy 'premium_care', which this company does not have.
         Fix: in pack.yaml, name a strategy the pack declares, or remove the reference from initial_state.
         Field: initial_state.declared_strategy

  1 error · 0 warnings · exit 1

EXIT=1


$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E14

  ERROR  E14  Opening position                pack.yaml:29
         The opening position states budget.capital_remaining as 40000, but capital available minus capital committed leaves 52000. The same number is authored in two places and they disagree.
         Fix: in pack.yaml, correct budget.capital_remaining to 52000, or correct the figures it is derived from. Better, derive it rather than authoring it twice.
         Field: initial_state.budget.capital_remaining

  1 error · 0 warnings · exit 1

EXIT=1
```

**`E14`'s tolerance is zero** (rework §1 ruling 1). Seven derivations are checked: review
lines' capital against `capital_committed`; `available − committed` against
`review.capital_remaining` and against `budget.capital_remaining`; `run_rate_before` plus
the review lines' run-rate effects against `run_rate_after`; `budget.capital_available`
against `review.capital_available` and against `capex_per_round[round − 1]`;
`budget.run_rate` against `review.run_rate_before`.

**Neither code fires on a pack with no `initial_state`** (ruling 3). Absence is not a defect.

### 4.1a The auditor's own probe, re-run

`1.2-014` demonstrated a pack with three mutations validating clean at exit 0. Rebuilt from
today's `minimal_valid` and re-run:

```
$ ./backend/bin/validate_casepack <scratch>/probe_initial --json | (code | field | message)
E13 | initial_state.declared_strategy       | The opening position names the strategy 'strategy_that_does_not_exist', which this company does not have.
E14 | initial_state.budget.capital_remaining | The opening position states budget.capital_remaining as 999999, but capital available minus capital committed leaves 52000...
E14 | initial_state.review.capital_remaining | The opening position states review.capital_remaining as 999999, but capital available minus capital committed leaves 52000...

  3 errors · 0 warnings · exit 1
EXIT=1
```

(The probe's `sed` hit both occurrences of `capital_remaining: 52000`, so two `E14`s is
correct, not duplicated.) **Was 0 errors, exit 0. Now 3 errors, exit 1.**

**The auditor's third mutation — `capability_that_does_not_exist` under
`value_chain_coverage` — is still NOT caught.** That is a deliberate partial decline of
rework §1 ruling 2, with evidence, in **§10 item 1**. It is the one thing in this rework
that does not do what the instruction asked.

### 4.2 `E20`'s two arms

Arm A — a capability no watch rule names:

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E20

  ERROR  E20  Clinical Records                watch_rules.yaml
         Can never raise a signal — no watch rule names it at all. Nobody is ever told when it is in trouble, and a team gets no credit for looking after it.
         Fix: add a watch rule in watch_rules.yaml naming 'Clinical Records', with warn_above or critical_above set, and the actions that clear it.
         Field: capability.clinical_records

  1 error · 0 warnings · exit 1

EXIT=1
```

Arm B — a capability watched **only** by a rule that carries no threshold. This is the arm
that was missing, and the reason the check under-reported on real content:

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E20_mute

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  demand curves cover rounds 1–4

  ERROR  E12  Watch rule rec_adopt_01         watch_rules.yaml:8
         Watches 'Clinical Records' but sets neither a warning nor a critical threshold, so it can never fire. It counts towards coverage while watching nothing.
         Fix: set warn_above or critical_above on 'rec_adopt_01' in watch_rules.yaml, or remove the rule.
         Field: rec_adopt_01

  ERROR  E20  Clinical Records                watch_rules.yaml:8
         Can never raise a signal — the only rule that names it (rec_adopt_01) sets neither a warning nor a critical threshold, so it can never fire. Nobody is ever told when it is in trouble, and a team gets no credit for looking after it.
         Fix: add a watch rule in watch_rules.yaml naming 'Clinical Records', with warn_above or critical_above set, and the actions that clear it.
         Field: capability.clinical_records

  ERROR  E21  Event records_left_on_paper     events.yaml:30
         Can never happen: it waits for 'rec_adopt_01' to reach warning, and that watch rule sets no warn_above threshold, so the signal can never get there.
         Fix: change what the event waits for in events.yaml, or set the matching threshold in watch_rules.yaml.
         Field: records_left_on_paper.preconditions

  ERROR  E21  Event vaccination_recall_missed  events.yaml:44
         Can never happen: it waits for 'rec_adopt_01' to reach critical, and that watch rule sets no critical_above threshold, so the signal can never get there.
         Fix: change what the event waits for in events.yaml, or set the matching threshold in watch_rules.yaml.
         Field: vaccination_recall_missed.preconditions

  4 errors · 0 warnings · exit 1

EXIT=1
```

`E12`, `E20` and `E21` all fire, and per rework §1 **ruling 4 that is correct rather than
duplicate**: one root condition seen from the rule, from the capability it fails to watch,
and from the two events waiting on a signal it can never raise. Three different fixes, three
different owners. It is the same triple Riverside shows in §9.

### 4.3 Per-code output — regenerated verbatim (`1.2-015`)

The v1.1 block under this heading was reformatted: it added a code column the CLI did not
print, and dropped the header, the ✓ lines and the `Fix:` line. **The full block is
`handoffs/1.2-validator/percode-output.txt`, written by redirecting the command's stdout,
unedited.** Two entries reproduced here; the file carries all twenty-two.

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E00

  ERROR  E00  Unreadable pack                 capabilities.yaml
         This pack could not be read: capabilities.yaml is not in the pack directory
         Fix: restore or repair capabilities.yaml in the pack directory, then run the validator again.
         Field: capabilities

  1 error · 0 warnings · exit 1

EXIT=1

$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E23

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  4 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  ERROR  E23  Question client_visit_history   questions.yaml:5
         Needs visit information at 'procedure_step' detail, and nothing this company can buy produces it.
         Fix: add a catalog item owning visit at 'procedure_step' or finer, or lower the requirement in questions.yaml.
         Field: client_visit_history.requires_entities.visit

  1 error · 0 warnings · exit 1

EXIT=1
```

---

## 5. Output shape — spec v1.2 §5.4

Three changes, closing `1.2-007`, `1.2-009` and `1.2-010`:

1. **The business name leads the locator line**, with the code beside it. The schema field
   path moves below the fix — kept, not deleted.
2. **`Fix:` prints at every severity.** §3 decision 3 binds WARN and INFO. v1.1 printed it
   for ERROR only, so every warning reached the instructor as a problem with no next
   action, while `--json` carried the fix all along.
3. **`E20` renders as ERROR**, which the build already did; §5.4's v1.1 sample was the thing
   that was wrong.

A warning, now carrying its fix:

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/warn_W01

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  4 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  WARN   W01  Catalog preferences             preferences/catalog.yaml:10
         6 rows carry the same ideal value 85.0 and the same weight 0.8, which looks like placeholder seeding rather than authored judgement.
         Fix: vary ideal_value and weight per stakeholder in preferences/catalog.yaml, or state in provenance that the uniformity is deliberate.
         Field: overrides.ideal_value

  0 errors · 1 warning · exit 0

EXIT=0
```

That run is also the evidence for **O1** (a WARN did not block) and for invariant **I3**.

### 5.1 One reading of §5.4 I had to choose, and declared

**§5.4's sample omits the `Field:` line on two of its four blocks; this build prints it on
all of them.** The prose immediately above the sample is explicit — *"The path is genuinely
useful to whoever opens the YAML, so it is kept — moved, not deleted."* Where the sample and
the written decision disagree, the decision governs. That is the lesson of `1.2-009` and
`1.2-010`, both of which exist because the v1.1 build followed the picture over the prose.
Surfacing it here rather than deciding it quietly.

**Messages are not wrapped**, where §5.4's sample wraps them. Wrapping is cosmetic, and
single-line messages keep the text renderer machine-checkable for I5's parity assertion.
Declared rather than assumed.

---

## 6. Invariants

| # | Invariant | Result | Falsified? |
|---|---|---|---|
| I1 | Every code the spec names is implemented — **set equality** | **PASS** 28 = 28 | **Yes**, both directions |
| I2 | Exit 1 whenever ≥1 ERROR | **PASS** | — |
| I3 | Exit 0 with warnings only | **PASS** | — |
| I4 | No pack-identity branching | **PASS** zero hits | — |
| I5 | `--json` carries the same findings in the same order **in every mode** | **PASS** | **Yes** |

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E12 >/dev/null; echo $?
1                                                                    I2  PASS
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/warn_heuristics >/dev/null; echo $?
0                                                                    I3  PASS
$ grep -rniE "riverside|grocer" backend/app/casepack/validate* | wc -l
0                                                                    I4  PASS
$ ./backend/bin/validate_casepack --json backend/packs/riverside_grocery | python3 -m json.tool >/dev/null; echo $?
0                                                                    I5  parseable
```

### 6.1 I1 — before and after, and what it now catches

**Before.** `grep -c "Fix:" $(grep -rl "ERROR" backend/app/casepack/validate*)` against the
ERROR-code count. Both sides were read from `validate_messages.yaml`, a file this build
owns. Adding a code incremented both. It passed at 18 = 18 while the spec named 15
(`1.2-017`).

**After.** The implemented code set from `catalogue()` against the code set **parsed out of
`spec.md`** — the header's versioned code-list line, cross-checked against every code at the
head of a line in §5.1–§5.3's fenced blocks. Two sources, one of which this build does not
own, compared as set equality.

**What it now catches that it could not before — demonstrated, not asserted:**

*A spec-named code that was never implemented.* This is precisely the property the old
invariant's name promised and its check could not see:

```
$ (remove E12 from validate_messages.yaml)
I1  implemented codes : 27 [... 'E11', 'E13', 'E14', ...]
I1  spec-named codes  : 28 [... 'E11', 'E12', 'E13', 'E14', ...]
I1  set equality      : FAIL
FAIL  I1: spec names codes this build does not implement: ['E12']
```

*A code implemented that the spec does not name — undeclared scope:*

```
$ (add an invented E15 to validate_messages.yaml)
I1  set equality      : FAIL
FAIL  I1: this build implements codes the spec does not name: ['E15']
FAIL  codes declared but never exercised by a fixture: ['E15']
```

Under the **old** check that same tampering was invisible: adding `E15` added one `Fix:`
line and one ERROR code, so both sides of the equality moved together and it still balanced.
That is the defect, reproduced and then closed.

The check also fails if the spec disagrees with **itself** — a code listed in §5.1–§5.3 but
outside the header's declared range raises before the comparison runs.

### 6.2 I5 — before and after, and what it now catches

**Before.** *"`--json` is parseable"* — `| python3 -m json.tool`. Directory mode dropped
pack attribution and reordered relative to the text renderer, and still satisfied it
(`1.2-005`).

**After.** The `(code, file, field)` sequence is parsed back out of the **text** renderer's
own output and compared to the JSON list, on a single pack, on a warn-only pack, on
Riverside, **and on a directory of packs** — plus an assertion that every directory-mode
record names its pack.

```
I5  minimal_valid                      text=  0 json=  0 identical=yes
I5  warn_heuristics                    text=  6 json=  6 identical=yes
I5  riverside_grocery                  text= 23 json= 23 identical=yes
I5  packs/  (directory mode)           text= 35 json= 35 identical=yes
I5  directory-mode pack attribution    every record names its pack
```

**What it now catches that it could not before — demonstrated:** reintroducing the exact
v1.1 defect, the cross-pack finding emitted first in JSON and last in text:

```
$ (revert Run.findings to emit self.shared first)
I5  packs/  (directory mode)           text= 35 json= 35 identical=NO
FAIL  I5: .../fixtures/packs text and json differ
```

`json.tool` accepted that output. The new check does not.

**The structural fix behind it.** Directory mode was a second, unshared code path. Both
modes now build one `Run`, whose `findings` property is the single ordered list both
renderers consume, and every record carries `pack`. §3.1's one-producer-two-renderers
guarantee now holds in the mode 5.6 consumes.

### 6.3 1.1's invariants still hold

```
$ git ls-files backend/app/casepack/ | xargs grep -rniE "riverside|grocer|pack_key *==" | wc -l
0
$ grep -rniE "riverside|grocer|pack_key *==" backend/app/casepack/validate.py backend/app/casepack/validate_messages.yaml backend/app/casepack/checks.py backend/bin/validate_casepack | wc -l
0                                                                    1.1 I1  PASS

$ grep -rnE '"[A-Z][a-z]+ [a-z]+' backend/app/casepack/*.py | grep -v '#\|"""\|log\|raise' | wc -l
0                                                                    1.1 I2  PASS

$ python3 -m compileall -q backend/app/casepack backend/tests backend/bin; echo "rc=$?"
rc=0
```

---

## 7. Heuristics — unchanged, and why

`W01`–`W07` needed no code change. v1.2 §5.3 **ratified what the v1.1 build had already
shipped and declared**: `W05` in its deck-depth form, and `W01`'s `N` bound to 6. Both were
declared as judgement calls last cycle and both were ruled sound (`1.2-016` items 3 and 5).

Recorded so it stays known: **a pack with five identical preference rows passes `W01`**, and
**`W05` cannot see `CG-2`'s real shape** — a deck whose cards are all affine to one strategy.
v1.2 §5.3 assigns that to 1.5.

---

## 8. Open decisions

**O1 — should WARN block?** Implemented as the spec's default: **no.** `exit_code_for()`
filters on `severity == ERROR` only. `warn_W01` and `warn_heuristics` both exit 0 with
warnings present. **Changed this cycle:** a WARN now prints its `Fix:` in the human output
as well as under `--json` (§3 decision 3, finding `1.2-009`). Not blocking and *actionable*
are different properties; v1.1 delivered the first and not the second.

**O2 — cross-pack `pack_key` uniqueness?** Implemented as the spec's default: **yes for a
directory of packs, skipped for a single pack.** It stays code `E10` — the spec's list is
`E00`–`E14` and a new code would break I1's set equality — but it now has **its own message
and fix**, closing `1.2-006`.

```
$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E10   ← E10 proper

  ERROR  E10  Repeated key book_cap_01        watch_rules.yaml:1
         'book_cap_01' is declared 2 times, so only the last one would ever be used.
         Fix: give every entry in watch_rules.yaml its own key, or delete the repeat.
         Field: watch_rules.book_cap_01


$ ./backend/bin/validate_casepack backend/tests/fixtures/packs           ← O2, same code

  ERROR  E10  Pack identity harbour_vet_group  pack.yaml
         21 packs in this directory all call themselves 'harbour_vet_group': backend/tests/fixtures/packs/broken_E01, ... , backend/tests/fixtures/packs/warn_heuristics. A section asking for 'harbour_vet_group' could be given any of them.
         Fix: give each pack its own pack_key in its pack.yaml — the key is the pack's permanent identity, so change the newer one, never the one already loaded anywhere.
         Field: pack_key.harbour_vet_group
```

The colliding directories are named in full rather than summarised: `1.2-006`'s complaint
was that *"no path is printed to say which files are involved"*, so truncating the list
would recreate the defect.

---

## 9. Riverside — the §9.1 gate

```
$ ./backend/bin/validate_casepack backend/packs/riverside_grocery   →   EXIT=1
  20 errors · 3 warnings

code counts: {'E02': 1, 'E07': 8, 'E12': 2, 'E14': 1, 'E20': 6, 'E21': 2, 'W02': 1, 'W04': 1, 'W05': 1}

E20  x6   Customer Insight · Financial Reporting · Firm Infrastructure ·
          Marketing and Sales · Service · Store Operations
E12  x2   Watch rule sec_identity_01 · Watch rule wh_rollout_01
E14  x1   Opening position
E02  x1   Firm Infrastructure
E07  x8   redesign_close · redesign_reporting · redesign_customer_followup ·
          redesign_online_fulfilment · redesign_picking · redesign_checkout ·
          redesign_service_queue · inventory_app
E21  x2   Event inventory_audit_question · Event warehouse_rollout_gap
W02  x1   Firm Infrastructure     W04  x1   store_spreadsheets     W05  x1   Event deck
```

The full run is `handoffs/1.2-validator/riverside-output.txt`, unedited.

### 9.1 Against the gate, line for line

v1.2 §9.1 predicts three lines. **All three match exactly.**

| §9.1 predicts | Reported | Match |
|---|---|---|
| `6 × E20` — five with no rule at all, plus `firm_infrastructure` watched only by a thresholdless rule → **CG-1** | 6, on exactly those capabilities | ✅ |
| `2 × E12` — `wh_rollout_01` · `sec_identity_01` → **CG-1** | 2, on exactly those rules | ✅ |
| `1 × E14` — `budget.capital_remaining 44000` vs review's derived `46000` → **CG-6** | 1, with those two figures | ✅ |

`E20`'s sixth instance is the one the widened predicate added, and it renders the distinction
in business language:

```
  ERROR  E20  Firm Infrastructure            watch_rules.yaml:15
         Can never raise a signal — the only rule that names it (sec_identity_01) sets neither
         a warning nor a critical threshold, so it can never fire. Nobody is ever told when it
         is in trouble, and a team gets no credit for looking after it.
```

`E14`'s instance, verified against the pack independently of the validator:

```
$ python3 -c "…yaml.safe_load('backend/packs/riverside_grocery/pack.yaml')…"
capex_per_round[round 3]                = 220000     pack.yaml:14
initial_state.budget.capital_available  = 220000     pack.yaml:23
review.capital_available                = 220000     pack.yaml:83
sum(review line capital)                = 174000
review.capital_committed                = 174000     pack.yaml:82
available - committed                   =  46000
review.capital_remaining                =  46000     pack.yaml:84
initial_state.budget.capital_remaining  =  44000     pack.yaml:22
DISAGREEMENT                            =   2000
```

The other six derivations pass, which is why exactly one `E14` fires rather than seven.

**`E13` reports nothing on Riverside**, correctly: `declared_strategy` is `cost_leadership`
(declared), every `unit_responses[].running` key is a real catalog item, every
`contributing` value is a declared chain position, and all seven `review.lines[].area`
values are in `REVIEW_AREAS`.

### 9.2 Errors traceable to no logged CG — findings against 1.1

Eleven errors, unchanged in substance from the v1.1 cycle and **already filed by the
auditor**. Reported, not fixed: 1.2 does not repair packs (§1).

| Count | Code | Condition | Finding |
|---|---|---|---|
| 1 | `E02` | nothing owns `user_account`, so `firm_infrastructure`'s data requirement is unsatisfiable | **`1.2-011`** — 1.1/1.3 |
| 8 | `E07` | seven `process_option.label_key` values plus role `inventory_app` absent from `labels.yaml` | **`1.2-012`** — 1.3 |
| 2 | `E21` | two of three event cards wait on `wh_rollout_01` at `critical`, which it can never reach | **`1.2-013`** — 1.1/1.5, same root as decision 7 |

**No new finding against 1.1 arises from this rework.** The eleven are the same eleven; the
three new codes added nine errors and all nine trace to `CG-1` or `CG-6`.

**`1.2-013` is now reported twice over**, which is the design working: `E12` names the
illegal rule, `E21` names the events stranded by it. Both point at `wh_rollout_01`.

### 9.3 Gaps the validator still does not catch — recorded, not fixed

Per rework §3 these are out of scope and v1.2 §9.1 records the silence deliberately.

- **`CG-2`** surfaces as `W05`, a warning, so it never reaches the error gate. `W05` cannot
  see its real shape either (§7). Closes at 1.3.
- **`CG-3`**, **`CG-4`**, **`CG-5`** are structurally invisible: the schema has no section
  for project duration, the sixth policy switch, or `obligation_rules.yaml`. **1.1's to
  add**; until then no validator can report their absence.

### 9.4 The pack was not touched

```
$ git diff --stat -- backend/packs/
$ git diff --stat 78a1ee2..HEAD -- backend/packs/
                                                    (both empty)
```

No watch rule was added, no threshold was set, no label was filled in, and the
`WatchRule` constraint was **not** added to `models.py` — doing so would make Riverside
unloadable and take this module's evidence with it. It is filed against 1.1 as the
disposition of `1.2-013`.

---

## 10. Things I stopped on, or did not do as instructed

Declared rather than resolved quietly (`GOVERNANCE §4.4`, and the standard rework §4 sets).

### 1. `E13`'s scope — a PARTIAL DECLINE of rework §1 ruling 2, with evidence

**Ruling 2 lists four reference sites. I implemented three and declined one arm of the
fourth, because implementing it as written produces false errors on correctly authored
content.**

| Ruling 2 says | Implemented? |
|---|---|
| `declared_strategy` → `strategies` | **Yes** |
| any catalog key (`unit_responses[].running`) → `catalog` | **Yes** |
| `review.lines[].area` → the seven decision areas | **Yes** |
| `unit_responses[].contributing` → `capabilities` | **Yes**, resolved against capability keys **∪ declared chain positions** |
| keys under `value_chain_coverage` → `capabilities` | **NO — declined** |
| `needs_attention` → `capabilities` | **NO — out of scope by ruling 2's own last sentence** |

**`needs_attention` is prose, and ruling 2 excludes it.** *"A value (a number, a label
string) is not a reference and is out of scope."* Riverside's entries are sentences:
`"order system near capacity"`, `"warehouse system deployed with no implementation
support"`. Checking them as capability keys would flag every one.

**`value_chain_coverage` is keyed by Porter value chain activity, not by capability.**
Riverside's nine keys are the canonical nine activities:

```
$ sed -n '55,64p' backend/packs/riverside_grocery/pack.yaml
  value_chain_coverage:
    inbound_logistics: 1/4      operations: 2/4          outbound_logistics: 4/5
    marketing_sales: 5/5        service: 0/4             firm_infrastructure: 3/4
    human_resources: ok         technology: none         procurement: 0/3
```

Riverside declares seven capabilities whose `chain_position` values cover five activities.
The other four — `inbound_logistics`, `human_resources`, `technology`, `procurement` — are
listed **precisely because nothing covers them**: `procurement: 0/3`, `technology: none`.
Reporting an activity as uncovered is the field doing its job. Checking these keys against
capability keys would raise **4 × E13 on correctly authored content**, and against
capability keys ∪ chain positions it still raises 4.

`1.1 spec` O1 settles the vocabulary: *"A capability **is** a value chain activity; the
Applications screen groups them under Porter's primary/support split via a `chain_position`
field."* So this field references the chain-position vocabulary, of which a pack's
capabilities cover only a subset by design.

**Consequence, stated plainly:** the auditor's third probe mutation
(`capability_that_does_not_exist: 3/3`) is **still not caught** — §4.1a. Closing that arm
needs the author to settle whether `value_chain_coverage` must be keyed by a closed
vocabulary of activities, and if so what that vocabulary is. `REVIEW_AREAS` had a
non-pack source; the nine value-chain activities do not have one in this repository.
**This is the item to rule on before 1.3 regenerates `initial_state`.**

### 2. `REVIEW_AREAS` — new vocabulary this rework had to introduce

Ruling 2 says `review.lines[].area` must resolve to *"the seven decision areas"*, and no
constant named them. Introduced in `checks.py` beside `ACTION_TYPES` and `ARCHETYPES`, and
sourced from **`mockups/review.html`** — the 0.4 reference mockup's review table declares
exactly Platform · Components · Rollout · Services · People · Governance · Challenges.

Taken from the mockup rather than from Riverside on purpose: deriving an engine constant
from pack content would put case knowledge in the engine. Note it is **not** the same list
as `CONTRACTS.md`'s `decision_line.category` (twelve values) — if those two vocabularies
are meant to be one, that is a `CONTRACTS.md` question and I have not assumed an answer.

### 3. `Field:` prints on every block, where §5.4's sample shows it on two of four

Declared in §5.1 above. The prose says the path is kept; the sample omits it twice. The
decision governs the picture.

### 4. `check_fixture_matrix.py` now carries I1 and I5

§9.2 describes it as the fixture matrix. Extending the one re-run artifact rather than
adding two more scripts. Declared as an extension in §3.

### 5. Two unrequested repairs, both from the audit's own text

`minimal_valid`'s `value_chain_coverage` incoherence, and the avoidable `E07` spray in
`broken_E01` / `broken_E22`. Both were observations in the audit's verification section
rather than numbered findings, so neither appeared in rework §2. Both are one-line fixes
that make the fixtures more minimal. Declared in §3.

### 6. Not done, by instruction

No legal form was invented for presence-style watch rules; `sec_identity_01` and
`wh_rollout_01` emit `E12`. No `WatchRule` constraint was added to `models.py`. No checks
were added for `CG-3`, `CG-4` or `CG-5`. `backend/packs/` was not touched.

---

## 11. Open TODOs

**None.** No `TODO` marker was left in any shipped file:

```
$ git ls-files backend/app/casepack backend/tests backend/bin | xargs grep -n "TODO" | wc -l
0
```

The six items in §10 are decisions for the author, not unfinished work. **§10 item 1 is the
one that changes what a later packet must do**, and it should be ruled on before 1.3
regenerates `initial_state`.
