# M1 authority and execution rulings

Date: 2026-09-14. Supervisor: Codex. Base: `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`.
The user explicitly instructed **“Proceed with M1”** after the audited M0 closeout.
The north star defines M1's outcome: one initial estate, six rounds of typed decisions,
actual state/cost/organisation consequences, and proven failure/retry/isolation behavior.
These are supervisor decisions under that authorization. They are not builder discretion
or a claim that the implementation/spec-review gates have already passed.

## Architecture rulings

- **M1-R1 — Production boundary.** Introduce a versioned `SimulationService` with typed
  sheets, deterministic reducers and immutable persisted transition checkpoints. Preserve
  the legacy `RoundRunner` and scripted games as historical regression paths. Production
  decisions never call a per-round seed or rely on caller-authored estate snapshots. M2
  scheduling/API consumers must use the new service; the legacy path is not a fallback.
- **M1-R2 — One state authority.** The transition checkpoint is the authoritative state;
  `TeamState` is its derived, in-memory scorer projection. Do not also maintain a second
  editable set of legacy estate rows. Reuse existing `RoundResult` for scored JSON where
  the reviewed contract permits. Reject initialization over occupied legacy/production
  scope. New tables and every operation are scoped by instance and team, with a real
  migration and verified schema. Persist pack identity, content fingerprint and contract
  version; do not silently accept a changed pack during play.
- **M1-R3 — Transactions and retries.** The public service owns a fresh connection and
  transaction for each operation; callers cannot catch an error and commit partial work.
  Serialize PostgreSQL operations on the run row, and SQLite writes with BEGIN IMMEDIATE.
  Initialization races, stale revisions, lock/edit races and concurrent duplicate advance
  have explicit outcomes. Same-input advance retries return the same immutable result
  without replaying effects. All failed writes, including late publication failures, roll
  back. The spec must freeze the exact revision and legal-round rules before dispatch.
- **M1-R4 — Reopening.** Only the current locked, unadvanced round may return to draft.
  Advanced history is immutable in production v1. A future instructor reset creates or
  explicitly manages a separate run; it is not an incomplete in-place rewind. This resolves
  the conflicting old 1.6/2.3 directions for the new production interface.
- **M1-R5 — Reuse and necessary input extensions.** Reuse the pure scorer, ledger and
  event functions. Mechanical extraction of the M0 scorecard helper is allowed with exact
  legacy-result equivalence. One physical asset remains one node: do not duplicate it into
  capability facets that inflate placement counts or change physical outage identity.
  The verified scalar-throughput limitation permits a separately reviewed additive
  capability-capacity input and catalog/RTO identity seam, with default legacy behavior.
  Stable graph traversal must be proved across process hash seeds. Scoring equations and
  weights remain unchanged; historical pins/results are not rewritten to make checks pass.

## Business-model rulings for the contract author

These are **NEW provisional simulation parameters**, not empirical findings or a balance
verdict. Their exact field shapes, equations, null paths, rounding and example outputs
belong in the independently reviewed spec. Content additions must carry rationale and
`TODO: calibrate` ownership (M1/M4); existing authored pack numbers are not overwritten.

- **M1-R6 — Content.** Production requires a distinct versioned runtime supplement.
  Historical `initial_state` is R3 dashboard context and must not be repurposed as R0
  operational state. Catalog identities/roles/entities/people/prices/lead times retain
  their existing sources. Explicit runtime capacity, resource supply/driver and initial
  estate facts fill genuinely absent fields. No runtime coefficient may be reverse
  engineered from a desired score. Missing required content rejects initialization.
- **M1-R7 — Organisation.** Approved initial parameter proposals: training retention .90;
  resistance retention .90, arrival/change shock .10, strategy-change shock .10, resistance
  ceiling .90; adoption adjustment .35; sponsor factor 1/.75; placement staff-load factors
  on-prem 1/cloud .6/SaaS .2. Reuse the existing process-fit and staffing rules. Prices for
  communications require verified source or explicit authored-estimate labeling. The
  +1 FTE/$31,000 recurring/one-round hire proposal is grounded in design/04. Exact ordering,
  affected-unit counts, numeric bounds and duplicate/no-op behavior need executable examples.
- **M1-R8 — Money.** Keep capital and operating appropriations distinct. Capital receives
  the authored per-round grant and carries unused funds. Operating reserve starts at zero
  with a NEW estimated $100,000 IT operating allowance per round, debited by real recurring
  costs and event losses; it is not company revenue or full Financial scoring. New commitment
  checks must include pending liabilities, while unavoidable losses cannot make an empty
  round impossible to resolve. All cost/grant/loss entries reconcile. No back-distributed
  opex target. Technical debt is separately identified, never an invented financial loan.
- **M1-R9 — Lifecycle.** Cancellation before arrival stops the pending order; paid capital
  is sunk with no refund. No prepaid rollout before arrival in v1; a sheet may target an
  order actually due in that resolution. One live/pending asset per source key is an explicit
  v1 constraint. Incumbent zero-price POS/accounting on-prem modes may initialize inherited
  assets, but cannot provide free new purchases/renewals. An identical configuration/mode
  selection never refreshes currency. Pool quantity ceiling 8 must be authored in content;
  unit prices and effects are proportional under the reviewed rule.
- **M1-R10 — Integration and responses.** Entity-access projection may extend the source
  node's serving set only through a validated data integration satisfying authored source,
  entity and receiver requirements, with traceable provenance and one physical identity.
  Buying a response must not fabricate a training purchase or clear a signal without an
  effect. Event-specific funded-response effects/prevention, rationale and actual money
  consequences remain author proposals requiring a concrete ruling before code.

Product choices reserved by the north star remain reserved: no LLM scoring/advisor,
reflection-grading decision, substantive second vertical or pedagogical-balance verdict.
Full Financial scoring stays M4. Unsupported controls must be refused and owned explicitly;
the contract cannot declare M1 complete by deferring its required state transitions.

## Controlled execution

`m1_contract_author` is documentation-only in `/tmp/mis-sim-m1-author`, exact base above;
only new `spec.md`, `verify.md`, and (explicit scope amendment)
`engine-inputs/spec.md` in this handoff are allowed. The small engine-input packet may
receive independent review while the master contract is completed; this does not authorize
estate/organisation builders before their complete contract review. Independent
`m1_content_basis` may add only `content-basis.md` in its own worktree. Neither may code,
subdelegate, alter shared contracts or publish. A fresh spec reviewer follows the author.
Builders then receive individually frozen interfaces, exact bases and file lists, with no
more than two implementation tracks. The supervisor owns shared contracts/register/status
integration and requires an independent build audit behind each implementation packet.

## Response ruling and initial-content clarification

**M1-R10a — APPROVED for specification.** Each runtime event may explicitly author the
`prevent_current_round` funded-response effect. A valid funded response pays the existing
option price, prevents that event's current-round consequence, and expires at round end.
It creates neither a training purchase nor a permanent fix, does not clear the underlying
signal, and does not mark an event falsely fired. Persist the prevention's scope, rationale
and price separately from fired/suppressed evidence. Later unfunded fire retains original
outcomes. Eligibility must use the canonical state and all committed costs consistently
in preview/lock/advance; the author must define the exact checks and ordering. The transient
filtered event deck cannot mutate the bound pack or change other events' ordering/caps.
All thirteen event-specific explanations are NEW authored effect semantics, not facts
inferred from the existing option labels.

The independently checked content basis is accepted as research (`content-review.md`).
$14,200 is the proposed initial references' actual recurring price before wages; inherited
2 FTE at the NEW wage treatment produces $76,200 total, not the historical $47,000 target.
Explicit runtime supply/driver/throughput defaults require unit/rationale/calibration labels.
Affordability must include projected pending liabilities, rather than admitting unlimited
zero-capex hiring before arrival. Existing price/weight files and historical fixtures remain
protected except for an independently reviewed, explicitly necessary compatibility seam.

## Final accounting, action and content rulings for master review

**M1-R11 — Initial integrations.** Use the actual receiver requirements: POS product data
feeds order management; order-management order data feeds accounting. Each basic connection
has NEW provisional recurring cost $1,000 and load .2 FTE (advanced $2,000/.1;
vendor-managed $3,000/.05), in addition to the existing one-off tier price. Including the
two inherited connections, initial recurring cost is **$78,200** and staff load **3.7**.
This supersedes any draft that treated $76,200 as the complete initial cost. No integration
may fabricate an owned entity or an undeclared receiver dependency. The missing customer-data
role for marketing_sales remains a named M4 content limitation. M1's all-strategy gate proves
executable, deterministic games and honest evidence, not perfect coverage or balance.

**M1-R12 — Action timing.** Emit clearing-action records only when an effect becomes live,
retaining the original commitment's locked round. Pending, cancelled and ineffective/no-op
choices create no clearing action. Actual historical timing and the original signal watch
still determine responsiveness; arrival does not rewrite the commitment clock.

**M1-R13 — Bounded solvency.** No invented funding beyond the final game round. Reject a new
procurement, replacement or hire whose arrival would exceed that round with
`arrival_after_game_end`. Pause/continue cannot create a back door to an unsupported late
arrival. Forecast all committed live and pending operating costs through the final round,
including the arrival-round charge. Sunk cancellation/abandonment costs remain. A forecast
is not an infinite-horizon solvency claim. Empty and liability-reducing choices remain
resolvable after unavoidable deficits. A later-horizon model belongs to M4.

**M1-R14 — Money, debt and TCO.** Approve the proposed explicit one-off capital versus
recurring operating categories, with integer dollars and Decimal HALF_UP rounding. Technical
debt records one frozen positive cheapest-fix estimate per signal episode, settles when the
actual cause stops raising, and never creates a second cash expense/refund. Fired episode
history stays immutable even when its monetary estimate settles. Debt ratios use outstanding
debt and cumulative real attributed capital. Approve the concrete provisional TCO category
estimators in the master contract: forecast frozen at commitment, actuals from unique real
asset-attributed cost entries, overhead shown separately, and partial observations clearly
labeled. Selected decoys can distort a forecast but never fabricate expenditure. Full
valuation, ROI and Financial scoring remain M4.

**M1-R15 — Preference scope.** The ten explicitly enumerated stakeholder rows in the master
contract are NEW provisional interpretations of source interests. Every original preference
leaf needs a validated live-rule or explicit context/M4 disposition. Unsupported raw metrics
and ambiguous item overrides are not silently neutral votes or guessed numeric conversions.
Existing policy preference scoring remains separate. No builder may select weights, caring
sets, inferred metrics or fallback mappings.

These rulings settle author choices; independent review still must verify complete field
shapes, source references, null/error paths, formulas, examples and acceptance coverage.
