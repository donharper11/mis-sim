# DoD — 1.1 finding J1 (open item R1): event display titles

**Builder:** integration agent · **Date:** 2026-08-22 · **Branch:** `build/1.1-event-title-labels`
**Base:** `main` at `24e62fb`

Closes finding **J1 / R1** on `findings/OPEN-REGISTER.md`. Requires an independent audit
before merge. Nothing merged to `main` by this builder.

## The finding (verified)

`E21` led its finding with an event's machine key. Every other label family has a name map,
but `labels.events` maps an event's `body_key` to the persona's **prose message**, so routing
`E21` through it would print a paragraph as the locator line. There was nowhere to author an
event **title**. `validate.py`'s E21 call site carried the gap as an in-code comment (R1).

## The fix — a schema change, not a validator hack

| Change | File |
|---|---|
| New optional label section `event_names`, keyed by the event's own key | `backend/app/casepack/models.py` (`Labels`) |
| `E21` subject routes through `lens.label("event_names", event.key)`; comment updated | `backend/app/casepack/validate.py` |
| Riverside authors a title for all 13 events | `backend/packs/riverside_grocery/labels.yaml` |
| Callout rewritten (`events` prose vs `event_names` titles); `event_names` row added | `docs/casepack-schema.md` |
| §5.8 documents the new section and why | `handoffs/1.1-casepack-schema/spec.md` |
| Regression guard (mutation-style, non-vacuous) | `backend/tests/test_event_title_labels.py` |

**Optional by design.** An event with no authored title falls back to its key
(`Lens.label`'s existing behaviour), so every existing pack and fixture loads unchanged. It
was NOT made an `E07`-required reference — making titles mandatory is a separate ruling for
the pack author, out of scope for closing J1.

## Verification

| Check | Result |
|---|---|
| E21 on a pack that authors a title leads with it | subject `Event Inventory Accuracy Challenged`, not `inventory_audit_question` |
| Riverside still clean | `0 errors · 0 warnings` |
| Docs no longer say there is nowhere to author a name | callout rewritten |
| `pytest` | **36 passed** (+1 J1 guard) |
| `check_fixture_matrix` / `check_event_preconditions` / `check_policy_options` / `check_w08_rounds` | all exit 0 |
| I4 canary (`grep riverside\|grocer` in validate/models) | clean |
| `git diff --check` | clean |
| Scope | schema + validator subject + Riverside labels + docs + spec + one test; E21 logic unchanged |

## Closing check (register)

> an E21 finding on a pack that authors an event title leads with that title, and
> `docs/casepack-schema.md` no longer says there is nowhere to author one — **both met.**
