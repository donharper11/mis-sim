# Independent SQLite archive contract review

2026-10-07 · Reviewer `/root/contract_review`, not author or implementation builder.
Reviewed `sqlite-archive-contract.md`, SHA-256
`5672c83ee00aa1f85e23990ecf4711578e21cfd6675b91b923f16ee1f74a619c`.
Basis:the independently inspected actual0013 schemas in `sqlite-archive-preflight-review.md`,
current migration0010/0012/0013 and Alembic environment,model,lifecycle service/API and existing
create_all-backed archive tests. No implementation or database changes in this review.

## Verdict

**ACCEPT for the bounded archive repair, after instructor-start's final gate completes.**
No contract amendment is required. This is dispatch acceptance,not proof the future migration
works or permission to claim the entire release ready.

The author explicitly chose retained-correction no-op downgrade,closing the only policy
choice identified in preflight. This is coherent across engines:PostgreSQL0013 already permits
archived; SQLite0014 corrects its schema to the current model/API and keeps that correction on
downgrade. No status row needs reinterpretation or destructive reversal. The contract expressly
does not claim that downgrading through older PostgreSQL0010 is safe with archived rows.

## Consistency and feasibility

- A new successor0014 repairs the historical omission without rewriting shipped migrations.
  Four-value and already-correct five-value SQLite constraints have explicit treatment;
  missing/unexpected constraints and unknown statuses refuse before destructive DDL.
- Reflected Alembic batch replacement is a feasible route that preserves existing columns,
  defaults,keys and indexes. PostgreSQL is verification-only and must not rewrite its table.
  No model-table inventory change,new runtime vocabulary or API payload is implied.
- Alembic's current online environment creates a NullPool migration connection and exposes
  it through run_sync. FK-state changes outside transactions can therefore be bounded to
  that connection. The dedicated-connection/original-state restoration and inspection rules
  avoid claiming SQLite DDL atomicity that the environment does not provide.
- Full32-table snapshots,populated0013 fixtures,actual CHECK rejection on predecessor,
  omitted-replacement falsification and migrated API/browser tests directly target the
  defect class the previous create_all test missed. Existing FK/unique/round constraints,
  identity allocation and foreign-scope preservation are explicitly retained.
- No-op downgrade/re-upgrade with archived rows,preflight refusal and same-connection failure
  restoration are required evidence rather than unverified assurances. The planned file
  homes and closing gates are bounded to migration/tests/docs; production lifecycle/scoring
  semantics remain unchanged.

## Implementation/audit attention points within the accepted contract

These are consequences of the frozen requirements,not additional product decisions:

1. Capture FK enforcement before changing it and verify restoration for **both initial ON
   and OFF states**,including injected failures. Migration0012 always restores ON; copying
   that helper unchanged would violate this packet's original-state requirement. Tests must
   inspect the exact migration connection,not a newly opened connection's default PRAGMA.
2. Constraint verification must check the actual known expression/domain,not merely find
   the five status words. A widened `OR TRUE`,extra value or absent/narrower second status
   constraint must not masquerade as the canonical condition. PostgreSQL introspection's
   cast/ANY representation differs textually from SQLite's IN expression; handle the known
   dialect forms without broadening the accepted domain.
3. FK-off rebuilding must not delete or detach child teams,enrollments,hosts,schedules,
   checkpoints or results. Compare actual persisted rows and reflected constraints after
   successful migration,including pack_digest and both instance identity unique constraints.
   The inspected SQLite table has no explicit AUTOINCREMENT clause; test allocation without
   inventing a sqlite_sequence requirement.
4. Perform preflight before entering any SQLite autocommit/rebuild work,and fail on an
   incomplete rebuild before stamping0014. The contract does not promise arbitrary DDL
   failure rollback; the failure report must show the actual remaining schema/revision.
5. Keep historical0010 comments as historical evidence; current docs/report should explain
   that migrated SQLite now receives its correction in0014. Do not hide the predecessor
   failure by replacing migration-backed tests with fresh model-created schemas.

SPEC_PROTOCOL §11 dispatch consistency passes:acceptance maps to migration/API/browser
checks; explicit falsification is specified; canonical field vocabulary matches the current
model/API and PostgreSQL; a feasible reflected-rebuild route exists; migration verifier,
fixture,documentation and audit consumers are enumerated. Observed failing/restored tests,
full checks,candidate hashes and fresh backend/browser verdicts remain implementation gates.
