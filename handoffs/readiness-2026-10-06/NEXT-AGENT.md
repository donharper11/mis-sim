# Current handoff — implementation resumed 2026-10-07

The user released the prior pause and authorized implementation through READY-003, then requested a commit/push and a break. This checkpoint is being committed now. **Pause here after recording the push; do not begin the next task until the user resumes.** At pickup, inspect `git log -1` for the exact pushed checkpoint. Launch/production
readiness means a usable platform verified by our own seeded instructor/student rehearsals
before live participants. Recruitment, observed human pilot and live pedagogical sign-off
are post-readiness activities. Product feature scope remains in TODO.

Branch: `build/readiness-2026-10-06`, origin `donharper11/mis-sim`. The previous user-requested
checkpoint was committed/pushed as `da2ebf86a656d1c99e14b8cfe82952e4cecfda96` after the host
lifecycle task. This checkpoint records October 7 work; identify its exact commit from `git log -1`.
Preserve the branch history. No main merge or production deployment has been performed.

## Current task and evidence

READY-003 instructor start is CLOSED. Independent backend/browser/setup-concurrency reviews
ACCEPT; final gate: 885 passed, no skips, 290 warnings, 1587.28s, all guards green. The late SQLite
reset/start race is corrected and covered by both-order writer-contention regressions.
[Current evidence report](../../docs/instructor-start-2026-10-07.md), raw full-check log and
reviewed source hashes are retained. Frontend lint/build and fresh PostgreSQL verification pass.

The accepted [start contract](instructor-start-contract.md) is unchanged, SHA256:
`a05bda5b6c640ad7e23dc11ddf2a1f69ba0fe1b3498ced8ee446eaabf9eddc62`.
Instructor chooses each team's agreed authored strategy explicitly, with no default. Start
atomically initializes all teams and activates the instance; it rejects roster/binding/runtime
residue and repeat starts. Generation checks protect already-in-flight writes across reset/
restart, including post-service schedule metadata. New requests from stale browser tabs need
client tokens separately (READY-START-CLIENT). Scoring semantics are unchanged.

Preceding READY-001 host scope and READY-002 host activation/reset remain accepted, migrations
0012/0013. Previous full gate:834 passed, no skips, all guards green; frontend build/lint,
fresh PostgreSQL verifier and independent backend/browser audits passed. Historical reports
are `docs/host-scope-2026-10-06.md` and `docs/host-lifecycle-2026-10-06.md`.

## Continue in order

1. After the user resumes, implement the independently accepted SQLite archive CHECK repair
   (READY-AUD-BE-002): add a new migration, keep history intact, and test populated upgrades
   plus real migrated archive workflows. Read [archive preflight](sqlite-archive-preflight-review.md)
   and [accepted contract](sqlite-archive-contract.md), with [dispatch review](sqlite-archive-contract-review.md).
   Contract SHA256: `5672c83ee00aa1f85e23990ecf4711578e21cfd6675b91b923f16ee1f74a619c`.
2. Profile repair-inclusive reads/advance (READY-004) before simulated cohort performance claims.
3. Follow TODO for client generation tokens, AI teaching UI, roster import, content portability,
   substantive second vertical, operational deployment and full seeded rehearsal.

Read GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL and CONTRACTS before implementation. Heavy
changes require independent contract review; fresh review was explicitly requested by user.
Do not replace normal instructor onboarding with a preinitialized runtime seed.

## Local verification environment

Python3.12: `/tmp/mis-sim-readiness-venv`; Node22:
`/home/ubuntu/.nvm/versions/node/v22.23.2/bin`.
Disposable builder PostgreSQL16 cluster `/tmp/mis-sim-readiness-7kx7ly0q`, port44535,
local role `readiness`. Do not assume these processes survive a later session.

`make check` needs FOUR separate disposable PostgreSQL targets to avoid skips:
`M5_POSTGRES_URL`, `HOST_SCOPE_POSTGRES_URL`, `HOST_LIFECYCLE_POSTGRES_URL`, and
`INSTRUCTOR_START_POSTGRES_URL`. Fixtures destroy their target schemas; never point at
browser, application or production data. Start fixture requires loopback and database prefix
`mis_sim_verify_instructor_start_`. Exact run commands/logs belong in the current findings
folder. Never run simultaneous fixtures against the same database.

Independent reviewers used separate databases. Browser acceptance used only cohort/users
seed on a fresh database, then ordinary UI setup/start. Existing old readiness browser fixtures
are preinitialized and cannot prove instructor start. Read the browser report for exact replay.
