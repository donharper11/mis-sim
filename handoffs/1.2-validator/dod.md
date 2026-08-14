# 1.2 — Casepack Validator · Definition of Done

**Builder:** Claude · **Date:** 2026-08-14 · **Branch:** `build/1.2-validator` (from `78a1ee2`)
**Spec:** `handoffs/1.2-validator/spec.md` v1.1 (amended 2026-08-14, pre-dispatch)

> Every row below carries pasted command output. An assertion without output is not
> evidence (`QUALITY_PROTOCOL.md §1`).

---

## 0. Pre-Flight Verification Register (spec §7)

| # | Claim | Result | Evidence |
|---|---|---|---|
| 1 | 1.1 merged; `models.py` and `checks.py` exist | **PASS** | below |
| 2 | Skeleton pack loads clean under 1.1 | **PASS** | below |
| 3 | `checks.py` exposes **six** check functions | **PASS** | below |
| 4 | Action-type set exists as `ACTION_TYPES`, line 12, ten values | **PASS** | below |

```
$ ls backend/app/casepack/
checks.py
__init__.py
loader.py
models.py
seed.py

$ cd backend && PYTHONPATH=. python3 -c "
from app.casepack.loader import load_casepack
cp = load_casepack('packs/riverside_grocery')
print('loaded OK:', cp.metadata.pack_key, cp.metadata.pack_version, 'capabilities:', len(cp.capabilities))"
loaded OK: riverside_grocery 0.1.0 capabilities: 7
exit=0

$ grep -c "^def check_" backend/app/casepack/checks.py
6
$ grep -n "^def check_" backend/app/casepack/checks.py
37:def check_snake_case_keys(casepack: Casepack) -> list[str]:
45:def check_required_roles_fillable(casepack: Casepack) -> list[str]:
56:def check_strategy_weight_sums(casepack: Casepack) -> list[str]:
65:def check_cleared_by_resolves(casepack: Casepack) -> list[str]:
74:def check_demand_curve_lengths(casepack: Casepack) -> list[str]:
83:def check_yaml_round_trip(casepack: Casepack) -> list[str]:

$ grep -n "^ACTION_TYPES" backend/app/casepack/checks.py
12:ACTION_TYPES = {
10 values: ['add_node', 'add_policy', 'add_service_tier', 'add_training', 'fund_response',
           'move_to_cloud', 'redesign_process', 'retire_component', 'scale_node',
           'upgrade_component']
```

No row deviated. No second action-type vocabulary was declared (spec §3 decision 6).

---

## 1. Definition of Done table (spec §9)

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–4 | **DONE** | §0 above, all PASS |
| E01–E11 implemented, each with a fixture | **DONE** | §2, §3 |
| E20–E23 implemented, each with a fixture | **DONE** | §2, §3 |
| W01–W07 implemented | **DONE** | §2, §4 |
| CLI output matches §5.4 shape | **DONE** | §5 |
| `--json` mode | **DONE** | §5, invariant I5 |
| I1–I5 | **DONE** | §6 |
| O1, O2 recorded | **DONE** | §7 |
| **Seed** — fixture packs, one per error code, all exercised | **DONE** | §3, `backend/tests/check_fixture_matrix.py` |
| **Riverside fails with exactly the known content gaps, and no others** (§9.1) | **PARTIAL — reported, not fixed** | §8. Five errors trace to `CG-1`; eleven do **not** trace to any logged gap and are findings against 1.1; three logged gaps are **not caught** and are findings against this spec |
| Browser / auth / instance canaries | **N-A** | headless CLI, no state, no UI |

---

## 2. What was built

```
backend/app/casepack/validate.py             the checks, the two renderers, the CLI
backend/app/casepack/validate_messages.yaml  every string the validator prints
backend/bin/validate_casepack                executable entry point
backend/tests/check_fixture_matrix.py        re-runs the whole fixture matrix
backend/tests/fixtures/packs/                20 fixture packs
```

**No new dependency.** `PyYAML==6.0.2` and `pydantic==2.10.4` were already pinned in
`backend/requirements.txt`; nothing was added, so nothing needed reporting there.

**Why the strings live in a YAML file.** 1.1's invariant I2 requires zero displayed English
in `backend/app/casepack/*.py`, and this module's whole output is displayed English. Putting
the wording in `validate_messages.yaml` keeps I2 green (§6) and lets a non-engineer review
what an instructor will read. The file name matches the glob `backend/app/casepack/validate*`
that spec invariants I1 and I4 grep, deliberately.

**Structure (spec §3.1, the one compliant route).** `Finding` carries `code · severity ·
file · line · field · message · fix`; `__post_init__` rejects an empty `fix`, `file` or
`field`, so a fix-less ERROR is unconstructible rather than merely discouraged (I1).
`validate()` produces the list, `render_text()` and `render_json()` consume it, so I5
cannot drift from the human output. Exit code is one expression over that list (I2, I3).
No message names a case (I4).

**Two-stage loading, and why.** `models.py` *raises* on a bad strategy-weight sum and on a
wrong-length demand curve, so a pack broken in either way never becomes a `Casepack` and
E03/E04 could never fire from a typed check. The validator therefore parses raw YAML first
(E10, E11 always; E03, E04 on the load-failure path), then loads typed and runs the rest.

**1.1's `checks.py` is wrapped, not reimplemented** (spec §3 decision 4). `check_inherited()`
calls `run_all_checks()` and maps I3→`I3`, I4→`E01`, I5→`E03`, I6→`E05`, I7→`E04`, I8→`I8`.

---

## 3. Fixture suite — every code fires against a purpose-broken pack

`minimal_valid` is **real content under GOVERNANCE §4.9**: Harbour Veterinary Group, four
practices and an out-of-hours clinic, two capabilities (`appointment_booking`,
`clinical_records`), two strategies, two catalog items, one shared platform service, four
event cards, four rounds. Deliberately a different vertical from `riverside_grocery`, so a
pack passing with zero engine changes is also evidence for GOVERNANCE §4.6. Its capital
figures are internally derived, not authored twice: review lines sum to
`capital_committed` (30000 + 56000 + 12000 = 98000), `capital_available − capital_committed`
equals **both** `review.capital_remaining` and `budget.capital_remaining` (150000 − 98000 =
52000), and `run_rate_before` + the `run_rate_effect` column equals `run_rate_after`
(21400 + 2500 = 23900). That is the shape `CG-6` says Riverside does not have (§8).

Each `broken_*` pack is `minimal_valid` with **one** targeted mutation:

| Fixture | The one mutation | Named code fires |
|---|---|---|
| `broken_E00` | `capabilities.yaml` deleted | E00 |
| `broken_E01` | `appointment_booking` requires `sms_gateway`, which nothing fills | E01 |
| `broken_E02` | `appointment_booking` requires `client` at `individual_person`, a level nothing owns | E02 |
| `broken_E03` | `low_cost_care` weights sum to 0.900 | E03 |
| `broken_E04` | `appointment_booking.demand_curve` has 3 values, pack plays 4 rounds | E04 |
| `broken_E05` | `book_cap_01.cleared_by` names `open_on_sunday` | E05 |
| `broken_E06` | `saturday_overflow` waits on `book_cap_99` | E06 |
| `broken_E07` | `clinical_records` removed from `labels.capabilities` | E07 |
| `broken_E08` | `clinical_team` cast as `veterinary_nurse` | E08 |
| `broken_E09` | `records_system.must_be_fed_by` names `reception_desk` | E09 |
| `broken_E10` | a second watch rule authored under key `book_cap_01` | E10 |
| `broken_E11` | `schema_version: 2` | E11 |
| `broken_E20` | `rec_adopt_01` re-pointed at `appointment_booking`, leaving `clinical_records` unwatched | E20 |
| `broken_E21` | `rec_adopt_01.critical_above: null`, while an event waits for it at critical | E21 |
| `broken_E22` | `clinical_records` requires `imaging_link`, and it is `continuity_of_care`'s top weight | E22 |
| `broken_E23` | `client_visit_history` needs `visit` at `procedure_step` | E23 |
| `broken_I3` | an event option key written `FundNow` | I3 |
| `warn_W01` | six preference rows at `ideal_value 85.00, weight 0.80` — the `design/01 §4` shape | W01 |
| `warn_heuristics` | reweighted strategies, one untargeted event, one dead item, a three-card deck, a flat training ladder, no decoy costs | W02–W07 |

Some fixtures raise more than the named code, and that is inherent rather than sloppy: E22's
condition is by definition a superset of E01's and E02's, and an unlabelled new role is
by definition also an E07. The matrix asserts the **named** code is present.

```
$ python3 backend/tests/check_fixture_matrix.py
fixture          want  got  codes raised
minimal_valid       0    0  -   PASS
broken_E00          1    1  E00   PASS
broken_E01          1    1  E01,E07,E22   PASS
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
broken_E20          1    1  E20   PASS
broken_E21          1    1  E21   PASS
broken_E22          1    1  E01,E07,E22   PASS
broken_E23          1    1  E23   PASS
broken_I3           1    1  I3   PASS
warn_W01            0    0  W01   PASS
warn_heuristics     0    0  W02,W03,W04,W05,W06,W07   PASS

all 20 fixtures behave as named; 24 of 25 codes exercised, ['I8'] recorded as unfixturable
exit=0
```

**`I8` has no fixture, and that is stated rather than hidden.** I8 is 1.1's round-trip
invariant: load → dump → reload → compare. It is a property of `models.py`, not of authored
content, so there is no pack an author could write that provokes it. The check runs on every
pack; it simply cannot be provoked from the fixture side. This is the one gap in
"every code has a fixture" and it is recorded here and in `check_fixture_matrix.py`.

### Verbatim per-code output (spec §8 steps 1–3)

```
$ validate_casepack backend/tests/fixtures/packs/broken_E00      -> exit 1
   ERROR E00  capabilities.yaml  capabilities
         this pack could not be read: capabilities.yaml is not in the pack directory

$ validate_casepack backend/tests/fixtures/packs/broken_E01      -> exit 1
   ERROR E01  capabilities.yaml:3  appointment_booking.required_roles.sms_gateway
         capability 'Appointment Booking' needs sms_gateway, and nothing in the catalog or the shared platform provides it.

$ validate_casepack backend/tests/fixtures/packs/broken_E02      -> exit 1
   ERROR E02  capabilities.yaml:4  appointment_booking.required_entities.client
         capability 'Appointment Booking' needs client information at 'individual_person' detail, and no catalog item can hold it.

$ validate_casepack backend/tests/fixtures/packs/broken_E03      -> exit 1
   ERROR E03  strategies.yaml:3  low_cost_care.capability_weights
         strategy 'low_cost_care' spreads 0.900 of its emphasis across capabilities; it has to spread exactly 1.000.

$ validate_casepack backend/tests/fixtures/packs/broken_E04      -> exit 1
   ERROR E04  capabilities.yaml:7  appointment_booking.demand_curve
         capability 'appointment_booking' forecasts demand for 3 rounds, but this company plays 4.

$ validate_casepack backend/tests/fixtures/packs/broken_E05      -> exit 1
   ERROR E05  watch_rules.yaml:6  book_cap_01.cleared_by.open_on_sunday
         watch rule 'book_cap_01' says it is cleared by 'open_on_sunday', which is not something a team can actually do.

$ validate_casepack backend/tests/fixtures/packs/broken_E06      -> exit 1
   ERROR E06  events.yaml:2  saturday_overflow.preconditions.book_cap_99
         event 'saturday_overflow' waits on 'book_cap_99', which this company does not have.

$ validate_casepack backend/tests/fixtures/packs/broken_E07      -> exit 1
   ERROR E07  capabilities.yaml:10  clinical_records
         the capability 'clinical_records' has no wording anyone can read, so a screen would show the raw key instead.

$ validate_casepack backend/tests/fixtures/packs/broken_E08      -> exit 1
   ERROR E08  stakeholders.yaml:13  clinical_team.archetype
         persona 'Clinical Team' is cast as 'veterinary_nurse', which is not one of the 14 roles this platform knows how to play.

$ validate_casepack backend/tests/fixtures/packs/broken_E09      -> exit 1
   ERROR E09  catalog.yaml:43  records_system.must_be_fed_by.reception_desk
         catalog item 'records_system' declares that information flows to or from 'reception_desk', which this company does not have.

$ validate_casepack backend/tests/fixtures/packs/broken_E10      -> exit 1
   ERROR E10  watch_rules.yaml:1  watch_rules.book_cap_01
         'book_cap_01' is declared 2 times, so only the last one would ever be used.

$ validate_casepack backend/tests/fixtures/packs/broken_E11      -> exit 1
   ERROR E11  pack.yaml:6  schema_version
         this pack is written against schema version 2; this validator only understands up to 1.

$ validate_casepack backend/tests/fixtures/packs/broken_E20      -> exit 1
   ERROR E20  watch_rules.yaml  capability.clinical_records
         nothing watches capability 'Clinical Records', so it can never raise a signal, nobody is ever told when it is in trouble, and a team gets no credit for looking after it.

$ validate_casepack backend/tests/fixtures/packs/broken_E21      -> exit 1
   ERROR E21  events.yaml:44  vaccination_recall_missed.preconditions
         event 'vaccination_recall_missed' can never happen: it waits for 'rec_adopt_01' to reach critical, and that watch rule sets no critical_above threshold, so the signal can never get there.

$ validate_casepack backend/tests/fixtures/packs/broken_E22      -> exit 1
   ERROR E22  strategies.yaml:14  continuity_of_care.capability_weights.clinical_records
         strategy 'Continuity of Care' leans hardest on capability 'Clinical Records', and a team declaring it could never cover that capability with what this company can buy.

$ validate_casepack backend/tests/fixtures/packs/broken_E23      -> exit 1
   ERROR E23  questions.yaml:5  client_visit_history.requires_entities.visit
         management question 'client_visit_history' needs visit information at 'procedure_step' detail, and nothing this company can buy produces it.

$ validate_casepack backend/tests/fixtures/packs/broken_I3      -> exit 1
   ERROR I3  labels.yaml  key.FundNow
         'FundNow' is a machine key, so it has to be lower case words joined by underscores.
```

---

## 4. W01 against the real harvest shape (spec §8 step 3)

`design/01-mis_lite-harvest.md §4`: *"`business_process_mapping` — rows 71–76 show identical
`ideal_value` 85.00 and identical OAR weights across all six stakeholders for process 1."*
`warn_W01` reproduces exactly that: six override rows, one item, six archetypes, all at
`ideal_value: 85.00, weight: 0.80`. The threshold `W01_MIN_IDENTICAL_ROWS = 6` is derived
from that six-row case, which is the smallest group that must fire.

```
$ validate_casepack backend/tests/fixtures/packs/warn_W01

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  4 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  WARN   preferences/catalog.yaml:9  overrides.ideal_value
         6 preference rows carry the same ideal value 85.0 and the same weight 0.8, which looks like placeholder seeding rather than authored judgement.

  0 errors · 1 warning · exit 0

exit=0
```

That run is also the evidence for **O1** (a WARN did not block) and for invariant **I3**
(exit 0 with warnings only).

---

## 5. The three required runs

```
$ validate_casepack backend/tests/fixtures/packs/minimal_valid

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  4 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  0 errors · 0 warnings · exit 0

exit=0
```

```
$ validate_casepack backend/tests/fixtures/packs/broken_E20

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  4 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  ERROR  watch_rules.yaml  capability.clinical_records
         nothing watches capability 'Clinical Records', so it can never raise a signal, nobody is ever told when it is in trouble, and a team gets no credit for looking after it.
         Fix: add a watch rule for 'Clinical Records' in watch_rules.yaml with a threshold and the actions that clear it.

  1 error · 0 warnings · exit 1

exit=1
```

The Riverside run is §8. `--json` piped through `python -m json.tool` parses:

```
$ validate_casepack --json backend/tests/fixtures/packs/warn_W01 | python3 -m json.tool
[
    {
        "code": "W01",
        "severity": "WARN",
        "file": "preferences/catalog.yaml",
        "line": 9,
        "field": "overrides.ideal_value",
        "message": "6 preference rows carry the same ideal value 85.0 and the same weight 0.8, which looks like placeholder seeding rather than authored judgement.",
        "fix": "vary ideal_value and weight per stakeholder in preferences/catalog.yaml, or state in provenance that the uniformity is deliberate."
    }
]
json.tool exit=0
```

---

## 6. Invariants

| # | Invariant | Result |
|---|---|---|
| I1 | Every ERROR message names a file and a fix | **PASS** — 18 = 18 |
| I2 | Exit 1 whenever ≥1 ERROR | **PASS** |
| I3 | Exit 0 with warnings only | **PASS** |
| I4 | No pack-identity branching | **PASS** — zero hits |
| I5 | `--json` is parseable | **PASS** |

```
$ grep -c "Fix:" $(grep -rl "ERROR" backend/app/casepack/validate*)
backend/app/casepack/validate_messages.yaml:18
backend/app/casepack/validate.py:0
$ cd backend && PYTHONPATH=. python3 -c "from app.casepack.validate import error_codes; print('ERROR codes:', len(error_codes()))"
ERROR codes: 18
                                                                     I1  18 == 18  PASS

$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/broken_E20 >/dev/null; echo $?
1                                                                    I2  PASS

$ ./backend/bin/validate_casepack backend/tests/fixtures/packs/warn_W01 >/dev/null; echo $?
0                                                                    I3  PASS

$ grep -rniE "riverside|grocer" backend/app/casepack/validate* | wc -l
0                                                                    I4  PASS

$ ./backend/bin/validate_casepack --json backend/tests/fixtures/packs/warn_W01 | python3 -m json.tool >/dev/null; echo $?
0                                                                    I5  PASS
```

**1.1's invariants were not broken by this build** (checked with `git ls-files | xargs grep`,
never `grep -r`):

```
$ git ls-files backend/app/casepack/ | xargs grep -rniE "riverside|grocer|pack_key *==" | wc -l
0
$ grep -rniE "riverside|grocer|pack_key *==" backend/app/casepack/validate.py backend/app/casepack/validate_messages.yaml backend/bin/validate_casepack | wc -l
0                                                                    1.1 I1  PASS

$ grep -rnE '"[A-Z][a-z]+ [a-z]+' backend/app/casepack/*.py | grep -v '#\|"""\|log\|raise' | wc -l
0                                                                    1.1 I2  PASS
```

**Exit code 2** is reserved for the validator itself failing, and is reachable:

```
$ ./backend/bin/validate_casepack
usage: validate_casepack [--json] <pack_dir>
no args exit=2
$ ./backend/bin/validate_casepack /nonexistent/path
usage: validate_casepack [--json] <pack_dir>
bad path exit=2
```

---

## 7. Open decisions — recorded, not re-litigated

**O1 — should WARN block a production section?** Implemented as the spec's default: **no.**
`Report.exit_code` is `1 if self.errors else 0`; `self.errors` filters on `severity == ERROR`
only, so a WARN can never change the exit code. `warn_W01` and `warn_heuristics` both exit 0
with warnings present (§4, §3). WARN also prints no `Fix:` line in text mode, matching
spec §5.4's shape; the `fix` is still carried and is visible under `--json`.

**O2 — validate cross-pack `pack_key` uniqueness?** Implemented as the spec's default:
**yes when given a directory of packs, skipped for a single pack.** If the given path has a
`pack.yaml` it is one pack; otherwise its child directories that have one are each validated
and their `pack_key`s compared. A collision is reported as `E10` — the existing
"duplicate key within a collection" code, treating the directory as the collection — rather
than as a new code.

```
$ ./backend/bin/validate_casepack --json backend/tests/fixtures/packs
total findings across the directory: 30
  E10 pack.yaml pack_key.harbour_vet_group | 'harbour_vet_group' is declared 17 times, so only the last one would ever be used.
exit=1
```

---

## 8. Riverside — the §9.1 gate

```
$ validate_casepack backend/packs/riverside_grocery   ->   exit 1
  16 errors · 3 warnings
```

### 8.1 Errors that trace to a logged content gap

| Count | Code | Subject | Gap |
|---|---|---|---|
| 5 | `E20` | `store_operations` · `financial_reporting` · `customer_insight` · `marketing_sales` · `service` have no watch rule | **CG-1** |

Exactly the five capabilities named in `findings/content-coverage-2026-07-27.md` CG-1, and
exactly the five predicted in spec §9.1. E20 firing here is the validator working
(`content-coverage-2026-07-27.md`, *Sequencing*).

| Count | Code | Subject | Gap |
|---|---|---|---|
| 1 | `W05` (WARN) | the deck holds 3 events for 6 rounds | **CG-2** |

`CG-2` produces a **warning, not an error**, so it does not contribute to the exit code.

### 8.2 Errors that do NOT trace to any logged gap — findings against 1.1

These are reported, not fixed. Repairing packs is out of scope (spec §1) and is 1.3's work.

**`1.2-F1` — `E02` × 1. No catalog item or platform service owns `user_account`.**
`capabilities.yaml:55` declares `firm_infrastructure` requiring `user_account` at
`named_user`. `entities.yaml:25` declares the entity. Nothing in `catalog.yaml` lists it
under `owns_entities` — the `central_sign_on` platform service fills the `identity_access`
*role* but platform services carry no `owns_entities` field in the schema at all. So the
capability's data requirement is unsatisfiable as authored. Either a catalog item must own
`user_account`, or `PlatformService` needs an `owns_entities` field, or the requirement
comes out. That is a 1.1/1.3 decision, not this packet's.

**`1.2-F2` — `E07` × 8. Eight referenced label keys are absent from `labels.yaml`.**
Seven `process_option.label_key` values (`redesign_checkout`, `redesign_picking`,
`redesign_close`, `redesign_customer_followup`, `redesign_reporting`,
`redesign_online_fulfilment`, `redesign_service_queue`) and one role
(`inventory_app`, filled by `centraline_im7` at `catalog.yaml:46`). A student's Rollout
screen would render `redesign_picking` where a sentence belongs — precisely the failure
`GOVERNANCE §2.1` and `CONTRACTS.md` (`required_roles[]` → *Display*) forbid.

**`1.2-F3` — `E21` × 2. Two of the three event cards can never fire.**
`watch_rules.yaml:8` declares `wh_rollout_01` with `warn_above: null` **and**
`critical_above: null`. `events.yaml` has `inventory_audit_question` and
`warehouse_rollout_gap` both waiting on `{signal_open, wh_rollout_01, severity: critical}`.
A rule with no `critical_above` cannot raise a critical signal, and the schema offers no
other mechanism, so two of Riverside's three cards are dead. Note the interaction with
CG-2: the deck is not three cards, it is effectively **one**.

This one may be a *schema* gap rather than a content gap — `sec_identity_01` has the same
null/null shape with a presence-style metric (`missing_identity_access`), which suggests
1.5 may intend non-threshold watch rules that `WatchRule` cannot currently express. Either
way it needs a decision from 1.1/1.5 before 1.3 authors more rules in that shape. Flagged
rather than resolved, per `GOVERNANCE §4.4`.

### 8.3 Logged gaps the validator does NOT catch — findings against this spec

Spec §9.1 predicted errors tracing to `CG-5` and `CG-6`. Neither is detectable by any check
in spec §5.1–5.3, so the check set is incomplete.

**`1.2-F4` — `CG-5` is undetectable.** `obligation_rules.yaml` is not a section the 1.1
schema defines, so its absence is not a missing *file* from the loader's point of view — it
is a section that does not exist yet. No code in E01–E11 or E20–E23 covers "a designed layer
was never given a schema section." Catching CG-5 needs 1.1 to define the section first;
until then, a validator cannot know it is missing.

**`1.2-F5` — `CG-6` is undetectable, and the two authored homes currently disagree.** The
spec's check set has no consistency check over derived figures. Evidence:

```
$ python3 - <<'PY'  (against backend/packs/riverside_grocery/pack.yaml)
capex_per_round[round 3]                = 220000
initial_state.budget.capital_available  = 220000
review.capital_available                = 220000
sum(review line capital)                = 174000
review.capital_committed                = 174000
available - committed                   = 46000
review.capital_remaining                = 46000
initial_state.budget.capital_remaining  = 44000
DISAGREEMENT                            = 2000
```

Round-3 remaining capital is authored twice and the two values differ by 2000. This is
exactly what `CG-6` predicted (`findings/1.1-2026-07-27-audit.md`, finding `1.1-002`),
it is live in the pack today, and **1.2 as specified cannot see it.** Closing CG-6 in 1.3
by deriving the roll-ups would remove the disagreement; adding a coherence check
(`E24`: an authored figure that contradicts a figure derived from the same pack) would let
the validator prove it stayed removed. Adding that code is a spec change and is **not**
done here.

`CG-3` (nothing defines project duration) and `CG-4` (three policies, six designed) are
likewise invisible to this check set, for the same reason: both are *absences of authored
content the schema never required*, and no E-code covers an absence the schema permits.

### 8.4 Warnings on Riverside

| Code | Subject | Trace |
|---|---|---|
| `W02` | no strategy weights `firm_infrastructure` above 0.05 | not logged; a real observation — `strategies.yaml` never mentions it |
| `W04` | `store_spreadsheets` fills no required role | not logged; it `serves: [store_operations]` but fills only `spreadsheet_workaround`, which no capability requires |
| `W05` | 3 events for 6 rounds | **CG-2** |

`W02` and `W04` are informational and belong with 1.3's authoring pass.

### 8.5 Summary against §9.1

```
16 errors:   5 -> CG-1                      (as predicted)
            11 -> no logged gap             (1.2-F1, 1.2-F2, 1.2-F3 — findings against 1.1)
 3 warnings:  1 -> CG-2, 2 unlogged
not caught:  CG-3, CG-4, CG-5, CG-6         (1.2-F4, 1.2-F5 — findings against this spec)
```

**The pack was not touched.** No watch rule was added, no `obligation_rules.yaml` was
authored, no label was filled in. `git status` shows zero modifications under
`backend/packs/`.

---

## 9. Things the spec did not settle, and what was done

Recorded rather than resolved silently (`GOVERNANCE §4.4`).

**`E00` — a pack that cannot be read at all.** Spec §5.1 has no code for a missing or
unparseable file, and exit 2 is reserved for the validator itself failing, not for a broken
pack. Rather than let the CLI raise a traceback at an instructor, a code `E00` was added,
carrying a file, a field and a fix like every other ERROR, with fixture `broken_E00`.
**This is an addition to the spec's code list and needs the author's ruling.**

**`ARCHETYPES` — the 14 platform archetypes had no home in code.** Spec §3 decision 6 points
E05 at the existing `ACTION_TYPES`; there is no equivalent statement for E08, and no
constant existed. The set was defined in `validate.py` from
`design/05-implementation-plan.md §1.4.1` (the platform layer, named in full) cross-checked
against `design/01-mis_lite-harvest.md §2` (`stakeholders`, 14 rows) and the keys already
used in `backend/packs/riverside_grocery/stakeholders.yaml`. **If 1.4/1.5 wants this
vocabulary elsewhere, it should move, exactly as `ACTION_TYPES` lives in `checks.py`.**

**`W05` — the schema has no per-round event binding.** Spec §5.3 says *"the deck contains no
event for a round"*, but `Event` in `models.py` carries no round field and events draw by
`strategy_affinity` (`1.1 spec §5.6`, `CG-2`). W05 was therefore implemented in the only
schema-grounded form available: a deck with fewer cards than rounds cannot supply one per
round. **This is a spec/schema conflict, reported not reconciled.** It fires correctly on
Riverside (3 for 6) and traces to CG-2, but it is a weaker check than the spec describes.

**`E21` with a single precondition.** *"Preconditions can never all be true simultaneously"*
reduces, for a one-precondition event, to *"the precondition can never be true."* Both
readings are implemented: an unreachable severity, and two preconditions demanding different
severities of the same signal. Under the strict pairwise-contradiction reading alone the
check would be vacuous on Riverside, where every event has exactly one precondition.

**`W01`'s `N` is not stated in the spec.** Set to 6, derived from `design/01 §4`'s six-row
case, which spec §8 step 3 requires W01 to catch. Constant `W01_MIN_IDENTICAL_ROWS`.

**`E07`'s reference set is not enumerated.** Scoped to what the schema documents as
displayed: capability keys, role keys (required ∪ filled), strategy keys, policy keys, and
every documented `*_key` label reference (`display_name_key` → `labels.stakeholders`,
`role_key` → `labels.misc`, `body_key` → `labels.events`, `process_option.label_key` →
undocumented, so accepted anywhere in `labels.yaml`). `sidebar` labels are engine-side and
are not treated as pack references.

**`labels.yaml` has no `entities` section.** So E02 and E23 name entities and levels by their
machine key (`user_account`, `named_user`) where the spec's §2 example implies a business
phrase. That is a schema limit, not an implementation choice — noted for 1.1/1.3.

**Two raw-path messages name a machine key.** E03 and E04, when reached on the load-failure
path, cannot resolve labels because no `Casepack` exists to read them from. They still name
file, field and fix.

## 10. Open TODOs left in this build

**None.** No `TODO` marker was left in any shipped file:

```
$ git ls-files backend/app/casepack backend/tests backend/bin | xargs grep -n "TODO" | wc -l
0
```

(The four items in §9 are decisions for the author, not unfinished work.)
