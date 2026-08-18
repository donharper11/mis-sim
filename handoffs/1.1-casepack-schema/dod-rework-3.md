# 1.1 — Third Rework · Definition of Done

**Packet:** `handoffs/1.1-casepack-schema/rework-3.md`
**Branch:** `build/1.1-rework-3`, cut from `cba47c8`
**Builder:** BUILDER agent · **Date:** 2026-08-18
**Closes:** `1.3-012` · 1.5 spec §10 item 5

> This file is new. `dod.md` and `dod-rework-2.md` are untouched.

---

## 0. The headline

**This packet changes no observable behaviour anywhere.**

Two optional fields exist on one model. No pack declares them, so no pack behaves
differently, so `obligation_rules.yaml` stays exactly as inert today as it was before this
branch. The clean runs below prove *nothing was broken*; they do not and must not be read as
a working ethics layer.

```
1.1 rework-3   the fields exist                                        THIS PACKET  ✔
1.3 follow-up  Riverside's six policies declare options and defaults   NOT DONE
1.2 follow-up  the validator checks permissive_value against options   NOT DONE
```

The engine can be built as soon as step 2 lands; step 3 is defence in depth, not a
dependency.

---

## 1. DoD table

| Item | Status | Evidence |
|---|---|---|
| `options` and `default` on `PolicyOption`, both optional | **DONE** | §2 |
| The membership constraint, enforced at the model | **DONE** | §3 — all four cases, plus a fifth edge case and a pack-level negative |
| No pack declares `options` today | **DONE** | §4, run before the model was touched |
| Riverside unchanged: `0 errors · 0 warnings · exit 0` | **DONE** | §5, before and after |
| `check_fixture_matrix.py` green, all 29 | **DONE** | §6, exit 0 |
| `backend/packs/` byte-identical | **DONE** | §7 |
| `backend/tests/` and `validate.py` byte-identical | **DONE** | §7 |
| `docs/casepack-schema.md` updated | **DONE** | §8 |
| 1.1's I1–I8 re-run | **DONE** | §9 |
| **The shape proof** | **DONE** | §10 |

---

## 2. The two fields

`backend/app/casepack/models.py`, `PolicyOption`. Comments elided here; the file carries
them in full.

```python
class PolicyOption(StrictModel):
    key: SnakeKey
    category: SnakeKey
    cost: int = Field(ge=0)
    effects: dict[SnakeKey, float | int | str]
    options: list[SnakeKey] = Field(default_factory=list)   # NEW
    default: SnakeKey | None = None                          # NEW
    provenance: Provenance

    @model_validator(mode="after")
    def default_is_a_declared_option(self) -> PolicyOption:
        if self.options and self.default is not None and self.default not in self.options:
            raise ValueError(
                f"policies.{self.key}.default '{self.default}' must be one of options {self.options}"
            )
        return self
```

Both optional, with defaults that preserve today's behaviour exactly. A policy with no
`options` is the legacy shape and loads as it always did.

**No third field was added.** Nothing in the packet required one.

---

## 3. The constraint — all four cases

`options` non-empty → `default` MUST be a member of `options`. Nothing else is enforced.

```
PASS  case 1  no options (legacy shape)
        input   : {}
        expected: ACCEPTED
        got     : ACCEPTED -- options=[] default=None
PASS  case 2  options + valid default
        input   : {'options': ['minimal', 'standard', 'indefinite'], 'default': 'indefinite'}
        expected: ACCEPTED
        got     : ACCEPTED -- options=['minimal', 'standard', 'indefinite'] default='indefinite'
PASS  case 3  options + default NOT a member
        input   : {'options': ['minimal', 'standard', 'indefinite'], 'default': 'forever'}
        expected: REJECTED
        got     : REJECTED -- Value error, policies.data_retention.default 'forever' must be one of options ['minimal', 'standard', 'indefinite']
PASS  case 4  options, no default
        input   : {'options': ['minimal', 'standard', 'indefinite']}
        expected: ACCEPTED
        got     : ACCEPTED -- options=['minimal', 'standard', 'indefinite'] default=None

edge: no options but a default is set (not constrained, must ACCEPT)
PASS  case 5  default with empty options
        input   : {'default': 'indefinite'}
        expected: ACCEPTED
        got     : ACCEPTED -- options=[] default='indefinite'
```

Case 5 is not in the packet's list. It is the fourth quadrant of the two-by-two and the one
place a careless implementation would over-enforce, so it was constructed and is recorded.

**And the constraint bites at pack load, not only in a constructor** — a scratch pack whose
`default` is outside its own `options`:

```
  ERROR  E00  Unreadable pack                 policies.yaml
         This pack could not be read: policies.yaml: policies.0: Value error,
         policies.client_record_retention.default 'forever' must be one of options
         ['minimal', 'standard', 'indefinite']
         Fix: restore or repair policies.yaml in the pack directory, then run the validator again.
         Field: casepack

  1 error · 0 warnings · exit 1
```

Noted for 1.2, not acted on: the *message* is precise, but the code is `E00 Unreadable pack`
and the fix line says "restore or repair", which reads oddly for a pack that parsed fine and
failed one semantic rule. That is `validate.py`'s error mapping and this packet must not
touch it.

---

## 4. No pack declares `options` today

Run **before** the model was changed, on the branch point.

```
$ git ls-files '*policies.yaml' | wc -l
30

$ git ls-files '*policies.yaml' | xargs grep -nE '^[[:space:]]*(options|default)[[:space:]]*:' | wc -l
0

$ git ls-files '*policies.yaml' | xargs grep -nc 'options\|default' | grep -v ':0' | wc -l
0
```

30 = 29 fixture packs + `riverside_grocery`. Zero declarations of either field, as a key or
even as a substring anywhere in any of them. The membership constraint therefore cannot be
violated by an existing pack, which is what made it safe to enforce.

---

## 5. Riverside — before and after

**Before** (branch point `cba47c8`, model unchanged):

```
$ ./backend/bin/validate_casepack backend/packs/riverside_grocery

  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  13 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  0 errors · 0 warnings · exit 0

EXIT=0
```

**After** (both fields and the constraint in place):

```
$ ./backend/bin/validate_casepack backend/packs/riverside_grocery

  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  13 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  0 errors · 0 warnings · exit 0

EXIT=0
```

Byte-identical. Riverside went clean for the first time in the packet that just merged and
this packet did not disturb it.

---

## 6. `check_fixture_matrix.py` — all 29, exit 0

```
minimal_valid                   0    0  +[-] -[*] got[-]   PASS
broken_E00                      1    1  +[E00] -[-] got[E00]   PASS
broken_E01                      1    1  +[E01] -[-] got[E01,E22,W08]   PASS
broken_E02                      1    1  +[E02] -[-] got[E02,E22,W08]   PASS
broken_E03                      1    1  +[E03] -[-] got[E03]   PASS
broken_E04                      1    1  +[E04] -[-] got[E04]   PASS
broken_E05                      1    1  +[E05] -[-] got[E05,W08]   PASS
broken_E06                      1    1  +[E06] -[-] got[E06,W08]   PASS
broken_E07                      1    1  +[E07] -[-] got[E07,W08]   PASS
broken_E08                      1    1  +[E08] -[-] got[E08,W08]   PASS
broken_E09                      1    1  +[E09] -[-] got[E09,W08]   PASS
broken_E10                      1    1  +[E10] -[-] got[E10,W08]   PASS
broken_E11                      1    1  +[E11] -[-] got[E11,W08]   PASS
broken_E12                      1    1  +[E12] -[E20] got[E12,W08]   PASS
broken_E13                      1    1  +[E13] -[-] got[E13,W08]   PASS
broken_E14                      1    1  +[E14] -[-] got[E14,W08]   PASS
broken_E20                      1    1  +[E20] -[-] got[E20,W08]   PASS
broken_E20_mute                 1    1  +[E12,E20] -[-] got[E12,E20,E21,W08]   PASS
broken_E21                      1    1  +[E21] -[E12,E20] got[E21,W08]   PASS
broken_E22                      1    1  +[E22] -[-] got[E01,E22,W08]   PASS
broken_E23                      1    1  +[E23] -[-] got[E23,W08]   PASS
broken_I3                       1    1  +[I3] -[-] got[I3,W08]   PASS
warn_W01                        0    0  +[W01] -[-] got[W01,W08]   PASS
warn_heuristics                 0    0  +[W02,W03,W04,W05,W06,W07] -[-] got[W02,W03,W04,W05,W06,W07,W08]   PASS
ok_presence_rule                0    0  +[-] -[*] got[-]   PASS
broken_E21_presence_warning     1    1  +[E21] -[E12,E20] got[E21]   PASS
ok_service_owns_entity          0    0  +[-] -[*] got[-]   PASS
broken_W08                      0    0  +[W08] -[W05] got[W08]   PASS
ok_obligations_empty            0    0  +[-] -[*] got[-]   PASS

I1  set equality      : PASS
I5  minimal_valid                      text=  0 json=  0 identical=yes
I5  warn_heuristics                    text=  8 json=  8 identical=yes
I5  riverside_grocery                  text=  0 json=  0 identical=yes
I5  packs/  (directory mode)           text= 77 json= 77 identical=yes
I5  directory-mode pack attribution    every record names its pack

all 29 fixtures behave as named; 28 of 29 codes exercised, ['I8'] recorded as unfixturable
I1 set-equal against the spec; I5 identical in single-pack and directory mode
EXIT=0
```

Identical to the run taken before the model was changed.

---

## 7. The three empty diffs

```
$ git diff cba47c8 -- backend/packs/
(no output)
$ git diff cba47c8 -- backend/tests/
(no output)
$ git diff cba47c8 -- backend/app/casepack/validate.py
(no output)

$ git diff --name-only cba47c8
backend/app/casepack/models.py
docs/casepack-schema.md
```

Two files. Riverside's `options` stays 1.3's content packet; the fixtures stay 1.2's; the
`permissive_value`-against-`options` check stays 1.2's next packet, correctly sequenced
after this one.

---

## 8. `docs/casepack-schema.md`

The `policies.yaml` field table gains both rows, and two new subsections follow it:

| Addition | Content |
|---|---|
| Field table | `options` and `default`, both marked not-required with their defaults stated |
| **`options` and `default` — a policy's value vocabulary** | A worked `data_retention` example carrying both; the warning that ordering is convention and not strictness; why `default` is what makes the ethics layer cost something to ignore; the one enforced rule, with a rejected example; and an explicit statement that both fields may be omitted |
| **`default` is not `permissive_value`** | A two-row table separating where each lives and what each means, then a paired `policies.yaml` / `obligation_rules.yaml` example showing a pack that starts permissive, and the contrast with a pack that starts compliant. Closes with the note that `permissive_value` should name a member of `options` and that the validator does not check it yet |
| `obligation_rules.yaml` table | The `permissive_value` row now cross-references the section above |

An instructor authors packs from this document, so the distinction is stated in the document
rather than left in the model's comments.

---

## 9. 1.1's I1–I8, re-run

Commands from `handoffs/1.1-casepack-schema/verify.md`, unchanged.

```
=== I1 (no pack-identity branching) ===
zero hits
=== I2 (no displayed English) ===
zero hits
=== I3-I8 ===
I3: PASS []
I4: PASS []
I5: PASS []
I6: PASS []
I7: PASS []
I8: PASS []
=== seed ===
7 capabilities, 14 catalog items, 4 strategies
cost_leadership weights sum 1.000
differentiation weights sum 1.000
customer_supplier_intimacy weights sum 1.000
focus_strategy weights sum 1.000
pinned figures: round 3; capital 46000 of 220000; run_rate 58300; scorecard 61/48/39/27;
signals 3; inbox 3; staff 2.0; load 3.4; over 170; review_capital 174000 of 220000;
remaining 46000; run_rate_after 62200; run_rate_before 58300
warehouse people 34 contribution 25
store_operations people 140 contribution 44
finance people 8 contribution 81
compileall_ok
```

`I8` is the round-trip check and the one that would catch a new field being dropped on dump
and reload. It passes with `options` and `default` present on the model.

**The TODO scan is not clean, and it is not this packet's doing.** It returns 32 matching lines
in `backend/packs/riverside_grocery`, landed by the 1.3 harvest at `586dcde`: 27 real
`TODO: calibrate` markers across six YAML files, one `watch_rules.yaml` comment header
describing the convention, and four `PROVENANCE.md` lines cataloguing them.
`GOVERNANCE §4.9` rule 2 permits exactly this form, `PROVENANCE.md §7` lists all 27, and `git diff
cba47c8 -- backend/packs/` (§7) is empty, so the count is identical before and after this
branch. `dod-rework-2.md §8` recorded "zero hits" because it ran before 1.3 merged.

---

## 10. The shape proof

The thing this packet exists to make possible: a policy that declares its states, and an
obligation whose `permissive_value` names one of them, loading and validating clean.

The pack is a scratch copy of `ok_obligations_empty` **outside `backend/packs/`** — under
the session scratchpad, so nothing in the repository was touched to produce it.

```yaml
# policies.yaml
- key: client_record_retention
  category: data_governance
  cost: 4000
  effects: {privacy_risk: -0.2, staff_load: 0.05}
  options: [minimal, standard, indefinite]
  default: indefinite
  provenance: {source: AUTHORED, note: "..."}

# obligation_rules.yaml
- key: client_pii_retention
  entity: client
  condition: policy_permits
  policy: client_record_retention
  permissive_value: indefinite
  severity: critical
  cleared_by: [add_policy, retire_component]
  arms: [duplicate_client_records]
  provenance: {source: AUTHORED, note: "..."}
```

```
$ ./backend/bin/validate_casepack <scratchpad>/shape_proof_pack

  harbour_vet_group 1.0.0 (schema 1) — veterinary_care, 4 rounds

  ✓  2 capabilities · all required roles resolve
  ✓  2 strategies · weights sum to 1.000
  ✓  7 events · all preconditions resolve
  ✓  demand curves cover rounds 1–4

  0 errors · 0 warnings · exit 0

EXIT=0
```

A clean validator run alone would be weak evidence — it is consistent with the fields being
silently dropped. So the loaded object was inspected (`GOVERNANCE §4.9`: prove the path from
data to display actually runs):

```
loaded policies:
  client_record_retention    options=['minimal', 'standard', 'indefinite'] default='indefinite'
  access_review              options=[] default=None

obligations resolved against the policy's vocabulary:
  client_pii_retention: policy=client_record_retention permissive_value='indefinite'
    names a declared state : True
    pack starts permissive : True  (default='indefinite')
```

`permissive_value` now has a referent. `access_review` in the same file declares neither
field and loads on the legacy shape alongside it, which is the compatibility rule
demonstrated rather than asserted.

The last line — `pack starts permissive` — is the one 1.5 needs. It is the computation the
engine performs to decide whether a team has moved off the default, and it was impossible
before this branch because `PolicyOption` had no value field at all.

**It is a scratch pack, not a shipped one.** No pack in the repository does this yet. That
is 1.3's follow-up.

---

## 11. Substitutions

| # | Declared | Why |
|---|---|---|
| 1 | **Branched from `cba47c8`, not `03e401c`.** `rework-3.md` §head names `03e401c`; the dispatch prompt names `cba47c8` | `cba47c8` is `03e401c`'s immediate child and adds only `rework-3.md` and the builder prompt — `git show --stat` confirms two files, both under `handoffs/`, zero code. Branching from `03e401c` would have cut the branch from under its own instruction. The dispatch prompt is the later document; all diffs in §7 are taken against `cba47c8`, so the "byte-identical" claims cover every code commit either SHA contains |
| 2 | **Constraint case 5 added.** The packet lists four cases; five were run | The four listed leave out "no `options`, but a `default` set". It is the quadrant an over-strict implementation breaks, and §2's rule says do not require `options`. Constructed and recorded rather than assumed |
| 3 | **A negative pack-level run added.** The packet asks for the rejected case as a constructed model | A `ValidationError` from a Python constructor does not prove the rule fires through YAML and the loader. The `E00` run in §3 does |
| 4 | **The loaded-object inspection in §10 added.** The packet asks for "load and validate clean" | Clean-and-silently-dropped is indistinguishable from clean-and-working at the validator's output. `GOVERNANCE §4.9` is explicit that a result must be shown computed *from* the data |
| 5 | **Shape-proof pack derived from `backend/tests/fixtures/packs/ok_obligations_empty`** | Read-only copy to the scratchpad; `backend/tests/` is byte-identical per §7. Building a valid pack from scratch would have added risk without adding evidence |
| 6 | **`validate.py` read as `backend/app/casepack/validate.py`** | The only file of that name in the repository. `backend/bin/validate_casepack` (the entry script) is also untouched |

Nothing was stopped on. The packet settled every question it raised.

---

## 12. What this packet does not finish

Restating §0 because a clean DoD invites the opposite reading.

- **Riverside declares no `options` and no `default`.** All six of its policies are still on
  the legacy shape. That is 1.3's content packet.
- **`obligation_rules.yaml` is still inert.** Its six rules still read a `permissive_value`
  that no shipped pack's policy enumerates. Nothing changed for them on this branch.
- **The validator still does not check `permissive_value` against `options`.** That is 1.2's
  next packet, and it is correctly sequenced after this one.
- **The Security screen (4.3) still cannot render a switch's positions** from any shipped
  pack, because no shipped pack has any.

The schema can now hold the thing. Nothing in the repository holds it yet.
