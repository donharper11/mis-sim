"""Focused regression guard for the PolicyOption.options ordinal contract.

design/07 §3.5b (ruled 2026-08-18) settled that ``PolicyOption.options`` is an
ordered, ORDINAL list -- index 0 is the least constrained / most permissive state,
each higher index progressively more restrictive -- reversing the earlier
"order carries no meaning" note.

This test pins the DOCUMENTATION / CONTRACT correction (F1 + F2 in
``findings/OPEN-REGISTER.md``; audit findings 1.1-RA-001 / 1.1-RA-002). It FAILS at
``main 174e980``, where ``models.py`` still said *"carries no meaning: do not infer
strictness from position"* and ``CONTRACTS.md`` had no ``PolicyOption.options``
entry, and PASSES once both are corrected to the ordinal contract.

It asserts on documentation because the correction *is* documentation: ``options``
remains a plain ``list[str]`` with no ordinal flag in the type, and nothing
consumes the ordering yet (1.4's policy-switch dimension is deferred and raises
``NotImplementedError``). The corrected prose is therefore the only artifact to
guard until that dimension is built.

Contributed by the 1.4 coordinator session (2026-08-21) and verified independently
on this branch before landing. Companion to ``check_policy_options.py`` (the
standalone loader/behaviour suite + static-surface checks); this is the pytest form
that will run alongside 1.4's ``test_engine_scoring.py`` once the branches merge.
"""
from __future__ import annotations

import inspect
from pathlib import Path

from app.casepack.models import PolicyOption

# backend/tests/<this file>  ->  repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "CONTRACTS.md"

# Phrases that must be GONE once the contract is corrected (present at 174e980).
SUPERSEDED = ("carries no meaning", "do not infer strictness")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def test_models_policyoption_declares_ordinal_not_meaningless():
    src = _norm(inspect.getsource(PolicyOption))
    for phrase in SUPERSEDED:
        assert phrase not in src, (
            f"models.py PolicyOption still carries the superseded phrase {phrase!r}; "
            "design/07 §3.5b rules options ORDINAL (index 0 = most permissive). "
            "This is the state at 174e980 -- apply the F1 correction."
        )
    assert "ordinal" in src, (
        "PolicyOption.options docstring must declare options ORDINAL (design/07 §3.5b)."
    )
    assert "least constrained" in src or "index 0" in src, (
        "PolicyOption.options docstring must state index 0 is the least constrained / "
        "most permissive state."
    )


def test_contracts_has_policyoption_options_ordinal_entry():
    assert CONTRACTS.exists(), f"CONTRACTS.md not found at {CONTRACTS}"
    text = _norm(CONTRACTS.read_text(encoding="utf-8"))
    assert "policyoption.options" in text, (
        "CONTRACTS.md has no PolicyOption.options entry -- the state at 174e980 (F2). "
        "Add the canonical ordinal contract entry."
    )
    assert "ordered, ordinal" in text or ("ordinal" in text and "index 0" in text), (
        "CONTRACTS.md PolicyOption.options entry must declare the list ordered and "
        "ordinal, index 0 the least constrained / most permissive."
    )
