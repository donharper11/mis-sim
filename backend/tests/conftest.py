"""Explicit non-production auth secret for isolated test processes."""

from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "mis-sim-test-only-secret")
