"""Static auth boundary guard used by the repository gate."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "backend" / "app" / "api"


def main() -> int:
    api_text = "\n".join(path.read_text() for path in API.glob("*.py"))
    assert "501" not in api_text and "Not implemented" not in api_text
    assert not re.search(r"instance_id.*(?:Query|Path|Body)|request.*instance_id", api_text, re.I)
    assert "password_hash" in (ROOT / "backend/app/models/platform.py").read_text()
    config = (ROOT / "backend/app/config.py").read_text()
    assert 'SECRET_KEY: str = "dev-secret-key-change-in-production"' not in config
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "SECRET_KEY:?SECRET_KEY must be set" in compose
    print("auth invariants: PASS (no stub, no client instance context, required secret)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
