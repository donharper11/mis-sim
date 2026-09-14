# M1 preference/event source follow-up

2026-09-14. Read-only source check, not spec acceptance or a balance verdict.
Original content: `/tmp/mis-sim-m1-content`, base `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`
(the worktree's later commit adds only the content-basis document).
Draft inspected: `/tmp/mis-sim-m1-author/handoffs/recovery/decision-evolution/spec.md`,
§6 lines 552–613 and §7 lines 701–739. Observed draft SHA256:
`d3aad74e0bb6947b0e5029e27763c537f56af612d88d59e6d478d5434cc5525b`.
This is WIP; line numbers/digest identify the inspected text, not a frozen contract.

Result: the ten stakeholder rows' **33 views have matching source weights and declared
tier/placement names under the approved NEW interpretations**. All 13 response event
keys and fund prices exactly match the source. One source-leaf disposition is omitted;
the exact-once disposition rule needs a narrower definition before it is executable.

## Source omissions / ambiguity

**SF-01 — 14 platform preference-weight leaves have no explicit disposition.**
`backend/packs/riverside_grocery/preferences/platform.yaml:31–37` contains both
`defaults_by_archetype.<archetype>.cloud_weight` and `.on_prem_weight` for:

| Archetype | cloud_weight | on_prem_weight |
|---|---:|---:|
| c_suite | 1.2 | 0.7 |
| finance | 1.1 | 0.8 |
| employees | 1.0 | 1.0 |
| operations | 0.7 | 1.2 |
| it | 0.7 | 1.3 |
| hr | 1.0 | 1.0 |
| marketing | 1.3 | 0.8 |

Draft §6:598–612 gives dispositions for `ideal_placement` and the general ideals,
but never names these leaves. The source distinguishes these harvested preference
weights from the separate authored archetype `weight` (`platform.yaml:3–7,23–24`).
The draft is entitled to use exact ideal-placement matching, but should explicitly retain
these 14 values as source context/provenance if it does not consume their magnitudes.
They are not covered merely by consuming the archetype's ordinary `weight`.

**SF-02 — “every original leaf exactly once” lacks an exact source universe/target rule.**
The draft requires this at §6:575–576,610–611 without defining whether “leaf” includes
`provenance.source/note`, empty override lists, or only preference payload scalars.
Excluding provenance and counting scalar leaves under defaults/overrides produces
**131** leaves: catalog 37, platform 52, training 14, services 28. This is a reproduced
source inventory, not a proposed schema or required count if a different universe is ruled.

One source `weight` can support multiple live views: catalog c_suite's single `.8` weights
both cost and reliability (`preferences/catalog.yaml:2`); a services archetype weight
supports two tier views (`preferences/services.yaml:66–75`, for example). One source
leaf should therefore be able to identify multiple consuming views without violating
exact-once disposition coverage. Conversely, operations' platform availability is explicitly
aliased to its existing catalog reliability view (§6:601–602), whose source ideals are
`high` versus `.99` (`preferences/platform.yaml:34`; `preferences/catalog.yaml:5`).
The approved alias can be recorded once; it should be a stated exception to §6:580–582's
blanket claim that duplicate domain interests remain separate. `source_note` can distinguish
identical tuples, but the disposition target/reference grammar is not yet specified here.

Minor wording clarification: §6:553 says “one row per actual stakeholder,” while
§6:577–578,606–608 intentionally excludes four unsupported-only stakeholders. The source
has 14 stakeholders, the table has 10. “At most one row per eligible actual stakeholder”
would describe the intended table without implying four missing rows.

## Checks that matched

All source paths below are relative to `/tmp/mis-sim-m1-content/`.

- **Keys and caring sets:** every table stakeholder exists, including `senior_management`
  for archetype `c_suite` and `it_department` for `it`
  (`backend/packs/riverside_grocery/stakeholders.yaml:1–14`). Every explicit caring key and
  all seven `ALL` expansions exists in `capabilities.yaml:1–66`. Operations order/store,
  finance reporting and customer insight/service match the historical seed caring sets
  (`backend/seeds/riverside_r3.py:246–255`). Other caring sets are correctly treated as
  NEW authored choices, not facts in the original preference files.
- **Catalog/platform/training weights:** all table weights match
  `backend/packs/riverside_grocery/preferences/catalog.yaml:2–15`,
  `preferences/platform.yaml:31–45`, and `preferences/training.yaml:2–6` under the draft's
  stated numeric interpretations, deferred fields and operations alias. The numeric
  reliability ideals `.98`/`.99` match the source's `0.98`/`0.99`.
- **Services:** all 11 tier views have the exact source ideal and the exact two-level
  product. In support/integration order: operations `.72/.40`; employees `.49/absent`;
  IT `.80/.64`; finance `.81/.72`; senior management `.48/.32`; vendor `.56/.70`.
  Sources: `preferences/services.yaml:66–124`. `basic`, `premium`, `advanced`,
  `vendor_managed` are real tier keys (`platform.yaml:201–239`). Vendor's three `.7`
  integration views correspond to catalog, platform and services; they are not an accidental
  extra source row under the draft's explicit duplicate-view policy.
- **Deferred/excluded interests:** finance training cost `medium`, IT change volume
  `medium`, marketing customer-data, and all named risk/privacy/recovery/visibility ideals
  exist and fit the stated context/M4 dispositions. Employees and HR really have
  `no_preference` for platform placement. The five original item overrides are exactly
  catalog 2, platform 2, training 1; services/policies have none. Their item references are
  real catalog/platform keys (`catalog.yaml:65,87,184`; `platform.yaml:75,103`).
- **Policy remains separate:** `preferences/policies.yaml:97–224` contains the nine
  policy archetypes already consumed by the frozen scorer and `overrides: []`. The
  excluded non-policy `security_auditor`, `regulator`, `general_public` have existing policy
  views; `media` has none. No missing media policy view should be fabricated from the
  phrase “their existing policy preferences remain live.”

## Event key/price check

Exact source equality: 13 keys, 13 fund prices, total **182,000**. Every original event
has the option keys fund/defer/reject; all defer/reject prices are zero. The following
line numbers point to fund option rows in
`backend/packs/riverside_grocery/events.yaml`:

| Key | Price | Source line |
|---|---:|---:|
| inventory_audit_question | 6000 | 30 |
| warehouse_rollout_gap | 6000 | 45 |
| pos_support_ending | 6000 | 60 |
| ransomware_on_finance | 40000 | 76 |
| crm_data_exposed | 20000 | 99 |
| phishing_on_staff_accounts | 12000 | 120 |
| privacy_regulator_letter | 15000 | 142 |
| financial_audit_deadline_missed | 18000 | 163 |
| unlogged_system_change | 9000 | 182 |
| checkout_queues_lengthen | 14000 | 203 |
| service_backlog_builds | 11000 | 224 |
| supplier_portal_request | 15000 | 245 |
| analytics_request_from_board | 10000 | 267 |

The original EventOption model contains only key/tags/cost
(`backend/app/casepack/models.py:410–414`), so the thirteen `prevent_current_round`
interpretations are correctly labelled NEW rather than claimed as harvested effects.
This check does not approve their transition semantics or assess balance. The draft
uses original option tags instead of inventing rationale keys; implementation must keep
that lookup option-specific, since fund/defer/reject have different tag sets.

Evidence method: direct YAML/source inspection plus a local Python read-only comparison
of the draft table to loaded YAML dictionaries, Decimal weight products, stakeholder and
capability key membership, event map equality, and recursive scalar-leaf counts. No
repository file changed, no service/database accessed, no subagent dispatched.
