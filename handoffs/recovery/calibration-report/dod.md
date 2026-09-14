# Recovery calibration report — builder evidence

Date: 2026-09-14. Builder: reporting builder. Status: **ready for independent audit**.
Worktree: `/tmp/mis-sim-recovery-report`; branch: `build/recovery-calibration-report`.
Base: `d4652c1e34e712303d101177ba1c5949941bae0a`.
Implementation commit: `0ebba6b7ec2f6ea72b8f317dc9d10324b0b8ba14`.
This evidence is committed separately after the implementation; its enclosing commit is
identified by `git log -1 --format=%H -- handoffs/recovery/calibration-report/dod.md`.

The supervisor's author amendment from `0a3f967` was copied verbatim into the recovery spec
and committed separately as `8bd8c1c`. It assigns a fresh build reviewer in addition to the
supervisor's integration audit; it changes no build requirement. The supervisor expressly
allowed that spec file for this amendment only. The four original allowed files are the
only other changes. No root-checkout edits, engine/runner/archetype changes, pack writes,
dependency changes, shared-document edits, push, deployment, or main merge were performed.

## Read set and contracts

Read in full: `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md`, `CONTRACTS.md`,
`design/08-implementation-north-star.md`, both the recovery and original 1.7 specs,
`backend/app/calibrate/{inventory,report,harness}.py`,
`backend/tests/check_calibration_harness.py`, and the pack's `strategies.yaml` and
`watch_rules.yaml`. Also inspected the CLI, DB helper, RoundResult model, Makefile,
test DB call sites, and archetype run/readback path.

Relevant `CONTRACTS.md` rule: "every query that reads or writes game state filters on it"
(`instance_id`). The report adds no query; verification readback filters on both instance
and team. The 1.7 spec decision 8 defines the existing source as
`payload["scorecard"].{financial,customer,internal_process,learning_growth}`. This change
reads those values directly and changes no field, formula, score unit, or persisted payload.

## Preflight — completed and reported before editing

| Item | Result | Evidence |
|---|---|---|
| Isolated branch and exact base | PASS | `git status --short --branch`, `git rev-parse HEAD`: clean `build/recovery-calibration-report`, base above. No AGENTS.md found in the worktree or its ancestor directories. |
| Reproduce marker omission | PASS | Baseline `inventory.total_sites(inventory.scan(pack_dir))` returned **37**. Independent `TODO:[\t ]*calibrate` search found **39** lines, one convention header, hence **38** sites. Missing site: `strategies.yaml:40`, `# TODO:calibrate (owner 1.7) ...`. |
| Inspect excluded header | PASS | `watch_rules.yaml:7`: `# Thresholds carry TODO: calibrate wherever the number is authored judgement rather than a`. It describes the convention; legitimate calibration comments remain countable. |
| Hidden R1/R2 perspectives | PASS | Scoped SQLite readback found all perspectives for both rounds. Do Nothing R1 Financial = `-26.999000000000002`, R2 Internal Process = `-5.0`. Baseline report's only BSC heading was `BALANCED SCORECARD at R6`; its R1/R2 columns belonged solely to realised value. |
| Baseline digest and bytes | PASS | Six rounds × four archetypes on explicit temporary SQLite; digest below. SHA256 captured for **all 19 pack files**, including provenance, before edits. |
| Frozen scoring pins | PASS | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q`: **10 passed**. |
| Pack validation | PASS | `cd backend && PYTHONPATH=. python3 -m app.casepack.validate packs/riverside_grocery`: **0 errors, 0 warnings**, exit 0. |

The initial direct equality check between runner-returned dictionaries and JSON-persisted
payloads failed on tuple/list serialization within capability details. Inspection showed
JSON-normalized payload equality for every archetype and identical score digests. Subsequent
figure checks read the persisted JSON directly; no production behavior was changed.

## Definition of done

| Requirement | Status | Evidence |
|---|---|---|
| No-space, space, multiple-space and tab markers; count lines rather than numbers/occurrences | PASS | Five whitespace cases, including two marker occurrences on one line, in `test_marker_horizontal_whitespace_counts_lines`. Real pack count **37 → 38**. |
| Header exclusion follows its comment text | PASS | `test_moved_convention_header_preserves_legitimate_comment_markers` moves it to lines 1, 7 and 12, checks exact retained line numbers, and preserves both another comment marker and a similar-looking legitimate comment. |
| Register totals derive from REGISTER_ITEMS | PASS | `test_registered_item_totals_follow_live_register` substitutes 0, 2 and 6 items and checks both totals. Real inventory still has five registered items. |
| Preserve realised curves and final comparison; add four all-round BSC tables | PASS | Synthetic two-team/two-round fixture has 16 distinct perspective values and independent expected cells. Real CLI's **96 BSC cells** and **24 realised cells** independently compared to scoped persisted RoundResults. |
| Direct values; no clipping, rescaling, recomputation or mutation | PASS | Synthetic expected values and input-preservation checks; persisted results and score digest equal baseline. Tables retain the existing three-decimal BSC presentation; diagnostics print the full raw representation. |
| Early-round negative, above-range and nonfinite diagnostics | PASS | Tests exercise all four perspectives with negative, above-one, NaN, positive/negative infinity, and tiny boundary violations. Every anomaly includes label, round, perspective and raw value. Exact 0 and 1 are accepted. Real run prints **25** source-matched diagnostic lines. |
| Honest ranking and scope | PASS | Tests cover exact ties, reversed order, and unequal values that round alike. Real rank: `Balanced > Overspender > Do Nothing = All Tech, No Org`. Declared-strategy limitation and unchanged historical human gate are explicit. |
| Business labels and CLI report-only behavior | PASS | Existing I3/I6 guards pass. Actual CLI exits **0**, stderr empty, despite 25 scale diagnostics. Default output has no triple-snake-case engine keys. |
| Regression proof against baseline | PASS | New tests run before production edits: **41 failed, 5 passed**. Repeated on a fresh archive of the exact base with only the new test file copied in: same result. Includes marker, moved-header and early-round table failures. Reproduction below. |
| Focused tests and complete verification | PASS | `PYTHONPATH=. python3 -m pytest tests/test_calibration_reporting.py -q`: **46 passed**. `make check`: **128 passed**, every check script green, **44 fixtures** behave as named. |
| Digest, pack bytes and 1.4 pins unchanged | PASS | Baseline/after digest below; all 19 file SHA256 values equal. `make check` includes the unchanged scoring tests. No seed, scorer, pack, dependency or runner diff. |
| Isolation | PASS | Existing instance-isolation canary reports zero cross-instance reads. Harness guards confirm three deterministic runs, idempotent per-archetype wipes, and no results for an unrun instance. All runtime checks use explicit temporary SQLite URLs. |
| Scope and whitespace | PASS | `git diff --check`; changed paths are the four-file allowlist plus the separately authorized spec amendment. |
| Browser, auth, responsive UI and screenshots | N-A | Headless CLI reporting only; no browser surface or auth behavior changes. |
| Migration and schema checks | N-A | No schema, model or migration changes. Existing persistence path exercised by real SQLite harness and isolation tests. |
| Independent audit and integration | PENDING | Fresh reviewer then supervisor integration audit; this is builder verification, not an acceptance ruling. |
| Shared-register/spec reconciliation | SUPERVISOR OWNED | Ripple search found old 37-count/fixed-line claims in original 1.7 `spec.md` (e.g. lines 291, 411) and historical `dod.md` (19, 25). Reported to supervisor, who owns reconciliation under this handoff; these files were not edited. |

The unchanged score digest, both returned and persisted:

```text
e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129
```

## Actual display excerpt

Produced by the real CLI against a new SQLite file, then checked against that file's
RoundResults. Values below are computed outputs, not synthetic demonstration values.

```text
  BALANCED SCORECARD -- Financial by round   [from RoundResult.scorecard]
                            R1        R2        R3        R4        R5        R6
  Do Nothing           -26.999    -2.999    -2.999     0.001     0.001     0.001
  All Tech, No Org     -11.971     0.029     0.029     0.029     0.029     0.029
  Balanced             -26.033     0.967    -2.557     0.878     0.864     0.864
  Overspender          -26.607     0.393    -2.452     0.456     0.479     0.479

  SCORE-SCALE DIAGNOSTICS REQUIRING REVIEW (informational -- not a balance verdict)
    Do Nothing | R1 | Financial | raw value -26.999000000000002
    Do Nothing | R2 | Internal Process | raw value -5.0
```

Customer, Internal Process and Learning & Growth have their own equivalent R1–R6 tables.
The diagnostic excerpt selects two of the 25 lines; the full output is in the local evidence.

## Reproduction commands

From the worktree root, `make check` runs the focused tests as part of the complete suite.
For a clean real demo, run this from `backend/`; `--db-url` is always supplied:

```bash
PYTHONPATH=. python3 - <<'PY'
import subprocess, sys, tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="calibration-report-") as td:
    subprocess.run([
        sys.executable, "-m", "app.calibrate", "packs/riverside_grocery",
        "--db-url", f"sqlite:///{Path(td) / 'report.db'}",
    ], check=True)
PY
```

To reproduce the baseline failures without modifying either checkout, run from `backend/`:

```bash
PYTHONPATH=. python3 - <<'PY'
import io, os, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

base = "d4652c1e34e712303d101177ba1c5949941bae0a"
with tempfile.TemporaryDirectory(prefix="report-baseline-") as td:
    data = subprocess.check_output(["git", "archive", base, "backend"], cwd="..")
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(td, filter="data")
    backend = Path(td) / "backend"
    shutil.copyfile("tests/test_calibration_reporting.py", backend / "tests/test_calibration_reporting.py")
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests/test_calibration_reporting.py", "-q",
    ], cwd=backend, env={**os.environ, "PYTHONPATH": "."}, text=True, capture_output=True)
    print(result.stdout)
    assert result.returncode == 1 and "41 failed, 5 passed" in result.stdout
PY
```

The real-readback verification used a separate scoped SQLAlchemy query, never a second
renderer call as its oracle. Reproduce the figure/digest check from `backend/`:

```bash
PYTHONPATH=. python3 - <<'PY'
import math, subprocess, sys, tempfile
from pathlib import Path
from sqlalchemy.orm import Session
from app.calibrate.harness import load_archetypes, score_digest
from app.round.db import make_engine
from app.round.models import RoundResult

fields = {"Financial": "financial", "Customer": "customer",
          "Internal Process": "internal_process", "Learning & Growth": "learning_growth"}
with tempfile.TemporaryDirectory(prefix="report-readback-") as td:
    url = f"sqlite:///{Path(td) / 'report.db'}"
    cli = subprocess.run([sys.executable, "-m", "app.calibrate", "packs/riverside_grocery",
                          "--db-url", url], text=True, capture_output=True, check=True)
    assert not cli.stderr
    archetypes = load_archetypes()
    engine = make_engine(url)
    with Session(engine) as session:
        results = {a.key: [r.payload for r in session.query(RoundResult).filter(
            RoundResult.instance_id == a.instance_id, RoundResult.team_id == a.team_id
        ).order_by(RoundResult.round)] for a in archetypes}
    engine.dispose()
    assert score_digest(results) == "e0b5114c1e78574b8bafb272e40250ddad1663bb2c9d9bf553d63d04e83c2129"
    cells = 0
    for label, field in fields.items():
        section = cli.stdout.split(f"BALANCED SCORECARD -- {label} by round", 1)[1].split("\n\n", 1)[0]
        assert section.splitlines()[1].split() == ["R1", "R2", "R3", "R4", "R5", "R6"]
        for a in archetypes:
            row = next(line.strip() for line in section.splitlines() if line.strip().startswith(a.label))
            assert row.removeprefix(a.label).split() == [f'{p["scorecard"][field]:.3f}' for p in results[a.key]]
            cells += len(results[a.key])
    expected = []
    for a in archetypes:
        for p in results[a.key]:
            for label, field in fields.items():
                value = p["scorecard"][field]
                if not math.isfinite(value) or not 0 <= value <= 1:
                    expected.append(f'{a.label} | R{p["round"]} | {label} | raw value {value!r}')
    assert [line.strip() for line in cli.stdout.splitlines() if " | raw value " in line] == expected
    assert cells == 96 and len(expected) == 25
    print("96 BSC cells and 25 raw diagnostics match persisted source; digest unchanged")
PY
```

Local session evidence remains available at `/tmp/mis-sim-report-evidence-wfybeb6q/`:
`baseline.db`, `after.db`, `baseline-results.json`, `after-results.json`,
`baseline-report.txt`, `after-report.txt`, `pack-sha256.json`, `score-digest.txt`,
`baseline-regressions.txt`, `baseline-archive-regressions.txt`, and `make-check.txt`.
Those are disposable audit aids; the commands and expected outcomes above are committed.

## Limitations retained

All four historical archetypes declare **Cost Leadership**. Their ordering does not prove
coverage or balance across all four available strategies. The human historical gate is
unchanged; this report makes no new ruling. Archetypes still supply authored estates each
round, so this does not demonstrate live decision-to-estate evolution.

The 25 out-of-scale values remain exactly as computed. Correct score units and financial
partial-status persistence belong to the separate scorecard-contract recovery work. Pack
values and the five register items remain calibration work; inventory counts marker lines,
including comments, rather than the potentially many numbers a line covers. The header
exclusion identifies the inspected convention comment; it does not suppress comments in
general. No new semantic decision or scope expansion was required.
