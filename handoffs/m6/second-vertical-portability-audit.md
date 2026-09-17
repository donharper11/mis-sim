# M6 portability audit — second vertical and pilot boundary

Date: 2026-09-18  
Audit scope: Phase 6.1–6.2 only.  
Decision owner: supervising integration agent.

## Finding first

The casepack schema and validator are usable for a second authored content set, but the
production runtime boundary is not yet case agnostic.  The current M2 fixture is a renamed
copy of Riverside, so it is isolation evidence rather than M6 portability evidence.  A
substantive community-bank pack cannot currently be loaded through the production runtime
without either reusing Riverside machine keys and frozen initial-estate shape or changing
runtime code.  Phase 6 must therefore remain open.

This is a useful result from the audit: the content contract is ahead of the runtime
contract.  The correct next step is to close the bounded runtime portability findings before
claiming the zero-engine-change gate.

## Evidence inspected

The following artifacts were read and exercised:

| Artifact | Result |
|---|---|
| `design/05-implementation-plan.md` Phase 6 | Requires a hospital or community-bank pack using only the documented schema and validator; engine changes are prohibited. |
| `design/06-plan-index.md` 6.1–6.2 | Defines authoring and zero-engine-change verification; the M2 fixture is explicitly not the substantive second vertical. |
| `design/08-implementation-north-star.md` M6 row | Exit evidence combines second-vertical portability with Phase 7 pilot evidence. |
| `docs/casepack-schema.md` | Documents the typed YAML content files but does not list `runtime.yaml` as a required authored file. |
| `backend/app/casepack/models.py`, `loader.py`, `validate.py` | Generic seven-section content model, typed loading, cross-reference checks, and clean validator output. |
| `backend/app/simulation/content.py`, `types.py` | Production runtime supplement and typed runtime boundary; several frozen Riverside assumptions remain. |
| `backend/packs/riverside_grocery` | Baseline production pack. |
| `backend/packs/m2_isolation_fixture` | Same grocery vertical and same 7/14/11/8/13/14/4 content inventory; renamed isolation copy. |
| `backend/seeds/archetype_*.py`, `app/simulation/games.py` | Calibration and game fixtures still issue Riverside capability and asset keys. |

Commands run:

```text
PYTHONPATH=backend python3 backend/bin/validate_casepack backend/packs/riverside_grocery
  0 errors · 0 warnings · exit 0
PYTHONPATH=backend python3 backend/bin/validate_casepack backend/packs/m2_isolation_fixture
  0 errors · 0 warnings · exit 0
```

Both packs load through `load_runtime_pack()` today.  Both have the same content inventory:
7 capabilities, 14 catalog items, 11 platform services, 8 entities, 8 watch rules, 13
events, 14 stakeholders, 4 strategies, 6 policies, 3 questions, and five preference files.
The fixture therefore proves registration and instance isolation, not a different domain.

## Recommended candidate: community bank

Use a community bank as the first substantive vertical.  It can exercise the same generic
MIS teaching thesis—estate, capability coverage, data ownership, risk, people, governance,
capital and realised value—without requiring clinical terminology or a new interaction
class.  It is also a lower-risk portability test than a hospital because hospital content
would immediately pressure the model with clinical workflows, patient safety, and a wider
regulated-data vocabulary.

The bank must be substantively authored.  It should have a distinct company narrative,
economics, demand curves, entities, policy tensions, events, stakeholder roster,
strategies, labels, and runtime drivers.  It must not be a Riverside copy with display names
replaced.

The current engine exposes seven canonical capability slots.  Until that seam is made
content-driven, a provisional bank mapping can use the same machine-key vocabulary while
changing the labels and business meaning:

| Canonical slot | Community-bank display concept | Acceptance condition |
|---|---|---|
| `order_fulfilment` | account and payment servicing | Demand, entities, applications, and events describe servicing transactions. |
| `store_operations` | branch operations | Branch workload and staff adoption drive the operational curve. |
| `financial_reporting` | regulatory and management reporting | Reporting entities and audit obligations are bank-specific. |
| `customer_insight` | member/customer insight | Customer data, consent, retention, and service effects are bank-authored. |
| `marketing_sales` | relationship growth | Product acquisition and outreach use bank-specific demand. |
| `service` | member support and complaints | Support capacity and event responses are bank-authored. |
| `firm_infrastructure` | secure banking infrastructure | Identity, resilience, recovery, and data controls are bank-authored. |

This mapping is a compatibility bridge, not a final domain model.  If M6 requires the
machine keys themselves to express bank concepts, the fixed capability seam must be
reworked and the finding returns to Phase 1 as the plan requires.

## Portability findings

### M6-001 — runtime catalog and initial estate are frozen to Riverside (BLOCKER)

`backend/app/simulation/content.py` `_validate_against_casepack()` requires the runtime
catalog to match the pack, then separately requires the exact catalog set
`pos_system_2011`, `order_mgmt_v42`, `accounting_package`, `store_spreadsheets`,
`order_db_cluster`, and `store_back_office_pc`.  It also requires the exact service set
`client_network`, `compute_pool`, `storage_pool`, and `backup_recovery`, ten initial assets,
on-premise placement, `core` catalog configuration, and the `initial_<source_key>` identity.

This prevents a bank pack from authoring a meaningful initial banking estate through the
documented runtime path.  The M2 fixture passes only because it retains that same source
set.  The remedy is to make initial-estate cardinality and identity pack-authored, with
generic structural checks (known source, valid placement, valid config, unique IDs,
primary references) and no Riverside key allow-list.

### M6-002 — capability vocabulary is fixed in the runtime state model (BLOCKER)

`backend/app/simulation/types.py` defines a module-level `CAPABILITIES` tuple containing
the seven Riverside capability keys.  `CheckpointStateV1` rejects primary and governance
keys outside that tuple.  A bank can therefore only pass by reusing the compatibility
mapping above.  The validator itself permits arbitrary snake-case capability keys, so the
documented schema and the production state boundary disagree.

The remedy is to validate capability references against the bound casepack, not a global
tuple.  Any fixed vocabulary that is genuinely platform-level should remain explicit and
separate from business capabilities.

### M6-003 — runtime preferences have a hidden Riverside cardinality contract (HIGH)

`content.py` requires exactly 131 preference disposition leaves and the runtime model admits
a fixed metric/categorical vocabulary.  The helper `_preference_content()` also constructs a
Riverside-specific set of stakeholder views and asserts the 131-leaf count.  The authored
casepack preference files are generic enough to describe another vertical, but the runtime
supplement authoring contract is not documented and cannot safely be derived by a new
author from `docs/casepack-schema.md`.

The remedy is to derive preference dispositions from the pack's actual leaves, allow zero or
more supported runtime views per disposition, and document the closed runtime metrics and
their units.  A bank pack should still include a complete disposition for every authored
preference leaf, with an explicit `live_v1`, `context_m4`, or `no_preference` decision.

### M6-004 — runtime supplement is absent from the documented pack contract (HIGH)

`load_runtime_pack()` refuses a pack without `runtime.yaml`, while the required-file list in
`docs/casepack-schema.md` omits `runtime.yaml` and the casepack validator does not validate
the runtime supplement.  An author following the documented schema can produce a validator-
clean pack that cannot run in production.

The remedy is either to make `runtime.yaml` a documented and validator-checked part of the
production pack contract, or to generate a typed runtime supplement from documented pack
fields.  The M6 acceptance path must invoke both validators, not only
`validate_casepack`.

### M6-005 — helper and fixtures retain Riverside-specific assumptions (HIGH)

`_default_runtime()` contains Riverside catalog ceilings, initial assets, drivers, primary
assignments, event explanations, preference views, and fixed staffing options.  The game and
calibration fixtures also issue Riverside capability and asset keys.  Some of these helpers
are test/seeding conveniences rather than the runtime loader itself, but they make a second
vertical appear portable only when it mimics Riverside.

The remedy is to move archetype plans and initial-estate choices behind a pack-authored
fixture adapter.  The core runner may continue to be generic; a pack-specific seed module
may author content and plans, but it must not require a code change in the engine packages.

### M6-006 — event response prose has a hardcoded fallback map (MEDIUM)

`RESPONSE_EXPLANATIONS` in `content.py` names Riverside event keys.  A manually authored
runtime supplement can provide a response disposition for another event set, but the default
runtime construction path can raise a key error for a new event key.  Event labels and
response explanations should be content-owned and required by the pack contract.

## Bounded M6 acceptance plan

The gate should be run in this order:

1. **Close the portability seam findings.** Remove the exact Riverside allow-lists and
   fixed capability tuple from production runtime validation. Preserve structural checks and
   reject unknown references against the currently bound pack. Document `runtime.yaml` or
   generate it from pack content.
2. **Author `community_bank` v0.1.0.** Create all required casepack files and runtime
   content with a distinct bank narrative, content inventory, labels, strategies, entities,
   policies, events, preference dispositions, drivers, and initial estate. Keep the same six
   rounds and generic command vocabulary so the comparison isolates domain content.
3. **Run both validation layers.** `validate_casepack` must report zero errors and zero
   warnings; `load_runtime_pack` must bind a digest; every runtime registry pointer must
   resolve; no source key, entity, capability, policy, event, stakeholder, or strategy may
   be dangling.
4. **Run the same engine without changing engine files.** Run the four registered
   calibration archetypes, a six-round balanced playthrough, a negligent playthrough, and
   event/precondition and financial/freshness checks. The pack-specific seed/fixture may be
   authored as content support, but the scoring, consequences, estate, organisation,
   round-runner, and persistence packages must remain unchanged.
5. **Compare the evidence.** Verify six persisted rounds, deterministic replay, pack digest
   pinning, instance isolation against Riverside, nonzero coherent rounds where the bank
   estate supports them, zero negative-control scores where the controls intentionally omit
   required evidence, and causal traces whose labels are bank-specific.
6. **Audit portability mechanically.** A clean `git diff` over
   `backend/app/simulation`, `backend/app/round`, and scoring modules is required after the
   pack lands. The only allowed product changes are the new pack, its pack-specific seed or
   fixture content, schema/runtime documentation, and tests that prove the boundary.

## M6 gate decision

**Status: NOT READY / BLOCKED pending bounded runtime portability work.** The content
validator passes Riverside and the M2 isolation fixture, but no substantive second vertical
has yet passed the production runtime boundary. M6 should not be marked complete from the
existing fixture.

The recommended implementation sequence is to resolve M6-001 and M6-002 first, then
M6-003–M6-006 as the runtime authoring contract is exercised. If the team elects to avoid
those seam changes, the only honest alternative is a compatibility-mapped community-bank
pack that preserves the frozen machine-key and initial-estate sets; that would be a useful
content demonstration, but it should be labelled a constrained portability probe rather
than full proof of a case-agnostic domain model.
