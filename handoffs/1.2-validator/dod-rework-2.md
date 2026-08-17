# 1.2 — Second Rework · Definition of Done

**Builder:** Claude (Opus 5) · **Date:** 2026-08-18
**Branch:** `build/1.2-rework-2`, cut from `main` @ `dfa3bc3`
**Instruction:** `handoffs/1.2-validator/rework-2.md` · **Spec:** `spec.md` v1.2

> This is a **new** file. `dod.md` (the first rework) is untouched.

---

## 0. The one line that matters

The experiment that failed after 1.1's rework now passes. A scratch Riverside declaring
`metric_kind: presence` on `wh_rollout_01` and `sec_identity_01` — nothing else changed,
which is exactly the move 1.3 must make to close `CG-1` — loses `E12 ×2` and `E21 ×2`, and
`E20` falls from six to five.

```
$ cp -r backend/packs/riverside_grocery <scratch>/p_presence
$ # add `metric_kind: presence` to wh_rollout_01 and sec_identity_01. Nothing else.
$ ./backend/bin/validate_casepack --json <scratch>/p_presence | ... Counter

  UNTOUCHED : Counter({'E07': 8, 'E20': 6, 'W08': 4, 'E12': 2, 'E21': 2,
                       'E02': 1, 'E14': 1, 'W02': 1, 'W04': 1, 'W05': 1})
  PRESENCE  : Counter({'E07': 8, 'E20': 5, 'W08': 4,
                       'E02': 1, 'E14': 1, 'W02': 1, 'W04': 1, 'W05': 1})

$ ./backend/bin/validate_casepack <scratch>/p_presence | grep -E "E12|E20|E21"
  ERROR  E20  Customer Insight                watch_rules.yaml
  ERROR  E20  Financial Reporting             watch_rules.yaml
  ERROR  E20  Marketing and Sales             watch_rules.yaml
  ERROR  E20  Service                         watch_rules.yaml
  ERROR  E20  Store Operations                watch_rules.yaml
```

`E12 ×2` **vanished**. `E21 ×2` **vanished**. `E20` **6 → 5** — `firm_infrastructure` is now
covered, because `sec_identity_01` is a presence rule and a presence rule can raise. The
sixth capability, `order_fulfilment`, was already covered by `ord_cap_01`, which is why the
fall is one and not two.

`E02 ×1` still fires, as instructed: 1.3 must declare `central_sign_on.owns_entities`. This
packet makes clearing it possible; it does not clear it.

---

## 1. The six items

| # | Item | Where | Evidence |
|---|---|---|---|
| 3.1 | `E12` exempts `metric_kind: presence` | `validate.py` `Lens.thresholdless` | §2.1 |
| 3.2 | `E20` widens to "can raise a signal" | `validate.py` `_can_raise`, `Lens.signal_covered` | §2.2 |
| 3.3 | `_raisable` consults `metric_kind` | `validate.py` `_raisable_severities` | §2.3 |
| 3.4 | `Lens.owned` unions `pack.platform.services` | `validate.py` `Lens.__init__` | §2.4 |
| 3.5 | `W08` — per-strategy draw check at `N = 6` | `validate.py` `check_strategy_draws` | §2.5 |
| 3.6 | `1.1-r2-001` — one line in `loader.py` | `loader.py` `_optional` | §2.6 |

### 2.1 `E12` exempts presence rules

```python
# Rework-2 item 3.1 narrows decision 7 to `threshold` rules only -- 1.5 section 5.1a makes
# carrying no threshold the CORRECT shape for a `presence` rule.
self.thresholdless = [
    rule
    for rule in pack.watch_rules
    if rule.metric_kind == "threshold"
    and rule.warn_above is None
    and rule.critical_above is None
]
```

A presence rule carrying a threshold cannot be constructed — `models.py`'s
`presence_rules_carry_no_thresholds` rejects it at load — so the exemption cannot hide a
real defect. The predicate is written against `metric_kind == "threshold"` rather than
`!= "presence"` so that a third kind, if one is ever added, is not silently exempted.

### 2.2 `E20` widens to include presence rules

```python
def _can_raise(rule) -> bool:
    if rule.metric_kind == "presence":
        return True
    return rule.warn_above is not None or rule.critical_above is not None

self.mute_rules     = [r for r in pack.watch_rules if not _can_raise(r)]
self.signal_covered = {r.capability for r in pack.watch_rules if _can_raise(r)}
```

`Lens.watched_with_threshold` is **renamed** to `Lens.signal_covered`, because the name was
the proxy the check kept mistaking for the rationale. `check_unwatched_capabilities` now
consults `signal_covered` and reports through `mute_rules`.

### 2.3 `_raisable` consults `metric_kind` — `1.1-r2-006`

```python
def _raisable_severities(rule) -> set[str]:
    if rule.metric_kind == "presence":
        return {"critical"}          # 1.5 decision 10: critical, and NEVER warning
    severities = set()
    if rule.warn_above is not None:    severities.add("warning")
    if rule.critical_above is not None: severities.add("critical")
    return severities
```

`E21`'s wording forks with it. The existing reason tells an author to set the missing
threshold; on a presence rule that is an instruction to author a shape `models.py` rejects.
A second reason, `severity_unreachable_presence`, is added to `validate_messages.yaml`:

```
it waits for '{signal}' to reach {severity}, and that rule watches for a condition simply
being present, which is always raised as critical and never as a warning
```

`reasons` is not the `codes` map, so this adds no code and does not disturb `I1`.

### 2.4 `Lens.owned` unions platform services — `1.1 rework-2 R2`

```python
self.owned: dict[str, int] = {}
for item in [*pack.catalog, *pack.platform.services]:
    for held in item.owns_entities:
        ...
```

`E02` and `E23` both consult `Lens.owned`, so both are unblocked by the one change. The
asymmetry it removes was two lines up: `filled_roles` already unioned the services.

### 2.5 `W08` — the per-strategy draw check

```python
W08_MIN_DRAWS = 6      # 1.5 section 5.2a at its O4 default. A flat constant, not pack.rounds.

for strategy in lens.pack.strategies:
    draws = [e for e in lens.pack.events
             if not e.strategy_affinity or strategy.key in e.strategy_affinity]
    if len(draws) < W08_MIN_DRAWS:
        -> W08
```

`WARN`, not `ERROR`. Riverside raises it four times — see §3.

### 2.6 `1.1-r2-001` — one line in `loader.py`

```diff
 def _optional(pack_dir: Path, relative: str, default: Any) -> Any:
     path = pack_dir / relative
     if not path.exists():
         return default
-    return _read_yaml(path)
+    return _read_yaml(path) or default
```

One changed line, plus a three-line comment naming the finding. **Nothing else in
`loader.py` was touched** — the full `git diff` for the file is in the report and is those
four added lines and one removed.

Proved on a scratch Riverside outside `backend/packs/`, in both shapes the finding names:

```
$ : > <scratch>/p_empty/obligation_rules.yaml                 # 0 bytes
$ ./backend/bin/validate_casepack --json <scratch>/p_empty | ... Counter
Counter({'E07': 8, 'E20': 6, 'W08': 4, 'E12': 2, 'E21': 2, 'E02': 1, 'E14': 1,
         'W02': 1, 'W04': 1, 'W05': 1})

$ printf '# authored in the next pass\n' > <scratch>/p_empty/obligation_rules.yaml
$ ./backend/bin/validate_casepack --json <scratch>/p_empty | ... Counter
Counter({'E07': 8, 'E20': 6, 'W08': 4, 'E12': 2, 'E21': 2, 'E02': 1, 'E14': 1,
         'W02': 1, 'W04': 1, 'W05': 1})
```

Before this line, both of those were a single pack-wide `E00` and every other finding was
lost. Now the file's presence changes nothing, which is what an optional section means.

---

## 3. Riverside — before and after

**The ERROR profile is unchanged**, as the instruction requires. `backend/packs/` is not
this packet's, Riverside declares no `metric_kind` and no ownership, and under the default
(`threshold`) both its rules stay illegal — so `E12 ×2` and `E20 ×6` are still the correct
answers.

```
BEFORE  (main @ dfa3bc3)
  E07 ×8 · E20 ×6 · E12 ×2 · E21 ×2 · E02 ×1 · E14 ×1 · W02 · W04 · W05
  20 errors · 3 warnings · exit 1

AFTER   (build/1.2-rework-2)
  E07 ×8 · E20 ×6 · E12 ×2 · E21 ×2 · E02 ×1 · E14 ×1 · W02 · W04 · W05 · W08 ×4
  20 errors · 7 warnings · exit 1
```

**Errors: 20 → 20, code for code.** **Warnings: 3 → 7.** The four new ones are `W08`, and
they are `CG-2` visible for the first time — the counts are exactly those 1.5 §5.2a
predicted:

| Strategy | Cards it can be dealt | Needs |
|---|---|---|
| Cost Leadership | 3 | 6 |
| Customer and Supplier Intimacy | 2 | 6 |
| Differentiation | 1 | 6 |
| Focus Strategy | 1 | 6 |

`W05` (deck depth, 3 events for 6 rounds) still fires alongside them, which is the point:
depth and per-strategy draw are different checks and Riverside fails both.

---

## 4. Fixtures — paired, both halves asserted

Nine of §4's rows, plus one more that guards 1.5 decision 10's other edge. Every pack is
derived from `minimal_valid` and differs from it minimally; the diffs are in the report.

| Pair | Fixture | Shape | Asserted |
|---|---|---|---|
| **3.1 / 3.2** | `broken_E12` | threshold rule, no thresholds | `E12` fires · `E20` **forbidden** |
| | `broken_E20_mute` | capability watched only by a thresholdless threshold-rule | `E12` + `E20` fire |
| | `ok_presence_rule` | presence rule, no thresholds, covering its capability | **no finding at all** |
| **3.3** | `broken_E21` | event needing `critical` from a rule that cannot reach it | `E21` fires · `E12`, `E20` **forbidden** |
| | `ok_presence_rule` | its deck waits on the presence rule at `critical` | **`E21` silent** |
| | `broken_E21_presence_warning` | event needing **`warning`** from a presence rule | **`E21` fires** · `E12`, `E20` forbidden |
| **3.4** | `broken_E02` | entity required at a level nothing owns | `E02` fires |
| | `ok_service_owns_entity` | `client` held by the **platform service**, by nothing in the catalog | **no finding at all** |
| **3.5** | `minimal_valid` | 7 cards, every strategy drawn by 6 | **`W08` silent** |
| | `broken_W08` | 7 cards, **all affine to one strategy** | **`W08` fires · `W05` forbidden** |
| **3.6** | `minimal_valid` | no `obligation_rules.yaml` at all | no finding |
| | `ok_obligations_empty` | comment-only `obligation_rules.yaml` | **no `E00`**, no finding at all |

`ANY` in `check_fixture_matrix.py` forbids every code, which is what "passes clean" means
and is stricter than the old `(set(), 0)` — that row could not tell a clean pack from a
noisy one that happened to exit 0.

**The suite is not vacuous, and here is the falsification.** The new fixtures and the new
matrix were run against the **pre-rework** `validate.py` / `loader.py` / message catalogue
taken from `dfa3bc3`:

```
ok_presence_rule                0    1  +[-] -[*] got[E12,E20,E21]   FAIL
broken_E21_presence_warning     1    1  +[E21] -[E12,E20] got[E12,E20,E21]   FAIL
ok_service_owns_entity          0    1  +[-] -[*] got[E02,E22,E23]   FAIL
broken_W08                      0    0  +[W08] -[W05] got[-]   FAIL
ok_obligations_empty            0    1  +[-] -[*] got[E00]   FAIL
I1  set equality      : FAIL     (spec names W08, that build does not implement it)
EXIT=1
```

Every new assertion fails without the change and passes with it. The old suite passed in
both worlds.

---

## 5. Invariants

| # | Check | Result |
|---|---|---|
| **I1** | implemented codes vs spec-named codes, set equality | **PASS**, 29 = 29, `W08` on both sides |
| **I2** | exit 1 whenever ≥1 ERROR | **PASS** — `broken_E12` → exit 1 |
| **I3** | exit 0 with warnings only | **PASS** — `broken_W08` (W08 only) → 0; `warn_heuristics` → 0 |
| **I4** | no pack-identity branching | **PASS** — `grep -rniE "riverside\|grocer" backend/app/casepack/validate*` → zero |
| **I5** | text and JSON identical, in both modes | **PASS** — 0/8/27/77 findings, identical sequences, every directory record attributed |

`I4` caught a defect in this packet's own first draft: a comment on `W08_MIN_DRAWS` named
the pack the constant was ruled against. It is reworded and the invariant is green.

---

## 6. Untouched, verified

```
$ git diff f5125f4..HEAD -- backend/packs/                  -> empty
$ git diff dfa3bc3     -- backend/packs/                    -> empty
$ git diff dfa3bc3     -- backend/app/casepack/models.py    -> empty
```

`loader.py` carries item 3.6 and nothing else.

---

## 7. Spec edit, and the one place it went beyond the letter

Authorised: `W08` named in `spec.md` §5.3.

```
W08  a strategy fewer than 6 event cards can be dealt to — the per-strategy draw check
     of 1.5 §5.2a at its O4 default of N = 6                              NEW rework-2
```

**A second line had to change, and it is declared here rather than slipped in.** `I1` does
not read §5.3's block as its authority — `spec_named_codes()` reads the **header's code-list
line** and then asserts that every code appearing in §5.1–5.3 falls inside it, raising
`SystemExit("spec.md disagrees with itself")` otherwise. Adding `W08` to §5.3 alone
therefore does not make `I1` pass; it makes `I1` **hard-exit**. So the header moved too:

```
- ... · `E20`–`E23` · `W01`–`W07` · `I3` · `I8`
+ ... · `E20`–`E23` · `W01`–`W08` · `I3` · `I8`
```

That is the same list, versioned as `SPEC_PROTOCOL §3` requires. Nothing else in `spec.md`
changed — no changelog entry, no DoD row, no §9.1 edit.

---

## 8. Declared substitutions and decisions

Listed because `1.2-004` exists on this project for a correct substitution made silently.

1. **`ok_presence_arms_event` is `ok_presence_rule`.** §4's table names them separately.
   Built minimally from `minimal_valid`, they are the same pack: a presence rule that
   covers its capability *and* arms the event waiting on it at `critical` is one coherent
   pack, and a byte-identical second directory would be a vacuous fixture. `ok_presence_rule`
   carries all three assertions (`E12`, `E20`, `E21` forbidden). In its place, and as a
   strictly better use of the slot, **`broken_E21_presence_warning`** was added — an event
   waiting for `warning` from a presence rule, which must **still fire**, and which is the
   only fixture that guards 1.5 decision 10's *"never warning"* half against an
   over-widened `_raisable`.

2. **`broken_W08` is a starved strategy, not a short deck.** §4's table says "a strategy
   drawn by < 6 events", and a four-card deck would satisfy the words. It would also be
   caught by `W05`, and would prove nothing `W05` does not already prove. The fixture is
   instead `minimal_valid`'s **seven**-card deck with every card made affine to one
   strategy: `W05` is silent because depth is fine, and only `W08` sees that the other
   strategy draws nothing. That is `CG-2`'s literal shape as 1.5 §5.2a describes it.

3. **`minimal_valid` gained three event cards.** At `N = 6` its four-card deck raised
   `W08 ×2`, and a fixture documented as *"a small coherent pack that passes clean"* that
   emits two warnings is no longer that. Three cards were authored — `out_of_hours_overflow`,
   `duplicate_client_records`, `weekend_phone_bookings`, each with a label, a reachable
   precondition and both strategies in its affinity — bringing every strategy to six draws.
   The pack is finding-free again and is `W08`'s silent half. **This is a fixture, not
   content**: `backend/packs/` is byte-identical.

4. **`W08`'s `N` is pack-independent, and that is a real edge.** 1.5's O4 fixes `N = 6`
   ("one per round") against six-round packs. `minimal_valid` plays **four** rounds and is
   still held to six, which is why it needed a seven-card deck for a four-round game. It is
   implemented exactly as ruled and flagged rather than improvised — **for 1.5/1.7, not for
   this packet**: if `N` should track `pack.rounds`, that is an author's ruling on O4.

5. **`Lens.watched_with_threshold` → `Lens.signal_covered`.** A rename, not a behaviour
   change. The old name is the proxy `E20` twice mistook for its rationale, and leaving it
   on the widened predicate would have made the same mistake available a third time.

6. **`E02`'s and `E23`'s `Fix:` copy was NOT changed, and now under-describes the remedy.**
   Both still say "add a catalog item whose `owns_entities` holds …". After item 3.4 a
   *platform service* can hold it too — as `E01`'s fix already says for roles ("an item in
   `catalog.yaml` or a service in `platform.yaml`"). The messages are not wrong, only
   incomplete, and message copy is outside this packet's six items. **Recorded as a small
   finding against this build** rather than fixed unasked.

7. **The existing `broken_E*` fixtures now also emit `W08`**, because they carry the
   four-card deck they were derived from. Their assertions are unaffected and the matrix
   states what each must and must not raise. They were deliberately **not** rewritten:
   propagating a deck extension through twenty fixtures is diff and risk for no coverage,
   and incidental extra findings are already the suite's norm (`broken_E01` raises `E22`).

---

## 9. Stopped on / not done

Nothing was stopped on. Item 3.6 was the one flagged as a stop-if-it-grows, and it did not
grow: one changed line.

**Not this packet's, and still open after it:**

- `E02 ×1` on Riverside — 1.3 declares `central_sign_on.owns_entities`. Now possible.
- `E12 ×2`, `E20 ×6`, `E21 ×2` on Riverside — 1.3 declares `metric_kind` on both rules. §0
  proves that now works.
- `CG-2` — visible as `W08 ×4`. 1.3's to close.
- 1.5 §10's to-1.2 item 4's first clause is dead code by construction (`1.1-r2-007`); it is
  not among the six and was not built.

---

## 11. Follow-up: `1.2-030` and `1.2-031` — message copy

**Date:** 2026-08-18 · **Scope:** `backend/app/casepack/validate_messages.yaml` only.
Appended after the rework audit (`findings/1.2-rework-2-2026-08-18-audit.md`, PASS WITH
FINDINGS, 0 blocking). Items 3.1–3.6 above are unchanged and are not restated.

Items 3.1, 3.2, 3.3 and 3.4 each made something legal that had not been legal before. Five
strings still described the world before them. All five are read by pack authors, and 1.3's
builder is the next person to read them.

### 11.1 What changed — five strings, rendered from a real run

**`E21.fix` — `1.2-030`.** Item 3.3 forked the *reason* and left the *fix* shared, so the
reason said *there is no threshold here* and the next line said *set the threshold* — an
edit `models.py` rejects with a pack-wide `E00`. One fix, true of both arms, naming the
goal rather than one arm's remedy:

```
  ERROR  E21  Event records_left_on_paper     events.yaml:30
         Can never happen: it waits for 'rec_adopt_01' to reach warning, and that rule
         watches for a condition simply being present, which is always raised as critical
         and never as a warning.
         Fix: change the severity this event waits for in events.yaml, or make the rule in
              watch_rules.yaml one that can reach it — a rule with metric_kind: threshold
              needs the matching threshold set, and a rule with metric_kind: presence only
              ever raises at critical.
```

The threshold arm reads correctly from the same string (`broken_E21`): *"…sets no
critical_above threshold…"* followed by the same fix, which names that remedy first.

**`E02.message` and `E02.fix` — `1.2-031`.** Phrased to match `E01`, which has carried the
two-place wording for roles all along:

```
  ERROR  E02  Appointment Booking             capabilities.yaml:4
         Needs client information at 'individual_person' detail, and nothing in the catalog
         or the shared platform can hold it.
         Fix: add client at 'individual_person' or finer to owns_entities on an item in
              catalog.yaml or a service in platform.yaml, or lower min_level_of_detail in
              capabilities.yaml.
```

**`E23.fix` — `1.2-031`.**

```
  ERROR  E23  Question client_visit_history   questions.yaml:5
         Needs visit information at 'procedure_step' detail, and nothing this company can
         buy produces it.
         Fix: add visit at 'procedure_step' or finer to owns_entities on an item in
              catalog.yaml or a service in platform.yaml, or lower the requirement in
              questions.yaml.
```

**`E12.fix` and `E20.fix` — found here, not in the findings file.** See §11.3.

```
  ERROR  E12  Watch rule rec_adopt_01         watch_rules.yaml:8
         Watches 'Clinical Records' but sets neither a warning nor a critical threshold, so
         it can never fire. It counts towards coverage while watching nothing.
         Fix: in watch_rules.yaml, set warn_above or critical_above on 'rec_adopt_01' — or,
              if this rule watches for a condition that is simply present or absent rather
              than a level being crossed, declare metric_kind: presence on it, which
              carries no threshold at all. Otherwise remove the rule.

  ERROR  E20  Clinical Records                watch_rules.yaml:8
         Can never raise a signal — the only rule that names it (rec_adopt_01) sets neither
         a warning nor a critical threshold, so it can never fire. Nobody is ever told when
         it is in trouble, and a team gets no credit for looking after it.
         Fix: add a watch rule in watch_rules.yaml naming 'Clinical Records' and the actions
              that clear it — either metric_kind: threshold with warn_above or
              critical_above set, or metric_kind: presence for a condition that is simply
              true or false.
```

### 11.2 Every remedy the new copy names is one that works

Copy that names a remedy is a claim, and the claim is checked against a fixture rather than
asserted. Each `Fix:` above is the edit that turns the firing fixture into the silent one:

| The fix says | The edit | Result |
|---|---|---|
| `E12` / `E20`: declare `metric_kind: presence` | `broken_E20_mute` → `ok_presence_rule`, which is that line plus a metric renamed to the condition it names | `0 errors · 0 warnings · exit 0` |
| `E02` / `E23`: `owns_entities` on a service in `platform.yaml` | `minimal_valid` → `ok_service_owns_entity`, which moves `client` off the catalog item and onto the shared service | `0 errors · 0 warnings · exit 0` |
| `E21` presence arm: change the severity the event waits for | `broken_E21_presence_warning` → `ok_presence_rule`, `severity: warning` → `critical` | `E21` silent |

The remedy the old `E21` fix named — adding a threshold to a presence rule — is the one
edit with no fixture, because `models.py` refuses to load the result.

### 11.3 The fifth and sixth strings, and one deliberate non-change

**Found beyond the findings file: `E12.fix` and `E20.fix`.** `1.2-030` and `1.2-031` are
filed against items 3.3 and 3.4. Items **3.1 and 3.2** have the identical defect and no
finding: they made a presence rule a legal shape and legal coverage, and both fixes still
named thresholds as the only remedy.

These two matter more than the four that were filed. `E12 ×2` and `E20 ×6` are eight of
Riverside's twenty errors and the whole of `CG-1`, and 1.5 §10 tells 1.3 to close them by
**declaring `metric_kind`** — which is precisely the remedy neither fix mentioned. A 1.3
author following `E20`'s old fix would author six more threshold rules, and `E12`'s old fix
offered *"or remove the rule"* for two rules that should exist and now have a legal form.
Both fixes now name both kinds, and neither instructs blindly: each is conditioned on the
metric actually being a condition rather than a level.

**Deliberately NOT changed: `E23.message`** — *"…and nothing this company can buy produces
it."* `1.2-031`'s closing condition says *"both codes' `message` and `fix`"*, so this is a
recorded dissent, not an oversight.

`E02`'s message was falsified by item 3.4 because it named catalog items specifically and
offered that as the reason the requirement is unsatisfiable. `E23`'s does not: it speaks of
everything the company can buy, and after 3.4 a shared platform service is something the
company buys, so the sentence is exactly as true as it was and is true for the right reason.
`E23` fires only when neither the catalog nor the platform can produce the entity, which is
what the sentence says. Changing it would be churn on correct copy, and it is already the
better business language of the two.

### 11.4 Scope and invariants

| Claim | Evidence |
|---|---|
| One file changed | `git status` → `M backend/app/casepack/validate_messages.yaml`, nothing else |
| `validate.py`, `models.py`, `loader.py`, `backend/packs/`, `spec.md`, `backend/tests/` untouched | `git diff 880ca6b -- <each>` → **0 lines** each |
| No new code, no code removed | `I1` set-equal at **29 = 29** |
| Riverside unchanged | `E07 ×8 · E20 ×6 · E12 ×2 · E21 ×2 · E02 ×1 · E14 ×1 · W02 · W04 · W05 · W08 ×4` — **20 errors · 7 warnings · exit 1** |
| Fixture matrix green | 29 fixtures, `I1` PASS, `I5` identical in both modes, **exit 0** |

`I5` is the invariant most exposed by a copy change — the text renderer and the JSON
renderer must stay in step. It holds at 0 / 8 / 27 / 77 findings across single-pack and
directory mode, with every directory record attributed.

**No fixture needed adding or amending.** Every changed string already had a pack that
renders it and a paired pack that proves the remedy, from the packet above. That is the
paired-fixture design paying for itself on the first change made after it.
