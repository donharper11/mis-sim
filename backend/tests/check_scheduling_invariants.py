"""Static guard for the M2.3 scheduler boundary."""

from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
SERVICE = (ROOT / "app/scheduling/service.py").read_text()
ENTRYPOINT = (ROOT / "app/scheduling/entrypoint.py").read_text()
assert "datetime.now" not in SERVICE
assert "datetime.utcnow" not in SERVICE
assert "SimulationService" in SERVICE
assert "claim_token" in SERVICE and "claim_until" in SERVICE
assert "datetime.now" in ENTRYPOINT
assert not (ROOT / "BECSR/async-round-deadlines.md").exists()
tree = ast.parse(SERVICE)
assert not any(isinstance(node, ast.Import) and any(alias.name.startswith("app.round") for alias in node.names) for node in ast.walk(tree))
print("scheduling invariants: PASS (BECSR source unavailable; amendment is binding)")
