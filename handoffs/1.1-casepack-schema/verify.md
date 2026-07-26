# 1.1 — Verification Commands

Run from the repository root.

```bash
git ls-files backend/app/casepack | xargs grep -niE "riverside|grocer|pack_key *==" || true
git ls-files backend/app/casepack/*.py | xargs grep -nE '"[A-Z][a-z]+ [a-z]+' | grep -v '#\|"""\|log\|raise' || true
PYTHONPATH=backend python3 - <<'PY'
from app.casepack.checks import run_all_checks
from app.casepack.loader import load_casepack

checks = run_all_checks(load_casepack("backend/packs/riverside_grocery"))
for key, errors in checks.items():
    print(f"{key}: {'PASS' if not errors else 'FAIL'} {errors}")
PY
git ls-files backend/packs/riverside_grocery | xargs grep -n "TODO" || true
PYTHONPATH=backend python3 -m app.casepack.seed riverside_grocery
PYTHONPATH=backend python3 -m compileall -q backend/app/casepack && echo compileall_ok
```
