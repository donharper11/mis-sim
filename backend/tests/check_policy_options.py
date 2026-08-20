#!/usr/bin/env python3
"""Focused checks for the `PolicyOption.options` ordinal-ordering contract.

    python3 backend/tests/check_policy_options.py

Exits 0 when everything holds, 1 otherwise. No test framework, matching this repo's
convention (`check_fixture_matrix.py`), so no new dependency.

Added by the 1.1 policy-order rework closing findings `1.1-RA-001` / `1.1-RA-002`. The
settled contract (design/07 section 3.5b, CONTRACTS.md `PolicyOption.options`):

  * `options` is ORDERED and ORDINAL -- index 0 is least constrained / most permissive,
    each higher index progressively more restrictive.
  * list order must survive YAML load and model round-trip UNCHANGED, or ordinal distance
    is measured on the wrong axis.
  * `default` is a separate concept from an obligation's `permissive_value`; a pack may
    start compliant (they differ) or permissive (they coincide).
  * a policy declaring neither field is the legacy shape and loads exactly as before the
    fields existed.

These are the four things the rework packet requires proven.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # put backend/ on sys.path

from app.casepack.loader import load_casepack  # noqa: E402
from app.casepack.models import PolicyOption, Provenance  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RIVERSIDE = REPO / "backend" / "packs" / "riverside_grocery"
LEGACY_FIXTURE = REPO / "backend" / "tests" / "fixtures" / "packs" / "ok_obligations_empty"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((ok, name))
    tail = f"  {detail}" if detail else ""
    print(f"{'PASS' if ok else 'FAIL'}  {name}{tail}")


# --- 1. YAML list order survives loading unchanged --------------------------------------
# Load Riverside through the real loader, then independently re-parse the raw YAML and
# compare element-by-element. Equal lists prove the loader preserves author order rather
# than, say, sorting or de-duplicating.
pack = load_casepack(RIVERSIDE)
loaded = {p.key: p for p in pack.policies}

raw_docs = yaml.safe_load((RIVERSIDE / "policies.yaml").read_text())
raw = {d["key"]: d for d in raw_docs if isinstance(d, dict) and "key" in d}

declaring = [k for k, d in raw.items() if "options" in d]
check(
    "riverside declares options on its switches (fixture for the order check)",
    len(declaring) == 6,
    f"{len(declaring)} switches carry options: {declaring}",
)

order_preserved = True
for key in declaring:
    authored = list(raw[key]["options"])
    got = list(loaded[key].options)
    if authored != got:
        order_preserved = False
        check(f"order preserved through load: {key}", False, f"authored={authored} loaded={got}")
check(
    "YAML list order survives loading unchanged (all six switches)",
    order_preserved,
    "loaded options list is element-for-element identical to the authored YAML",
)

# --- 2. First and last option retain their intended positions ---------------------------
# Explicitly assert the endpoints, and that the permissive end (index 0) is the value the
# pack starts on and that every obligation names as permissive -- i.e. index 0 really is
# the permissive end the contract claims.
obligations = {o.policy: o for o in pack.obligation_rules}
endpoints_ok = True
for key in declaring:
    opts = loaded[key].options
    authored = raw[key]["options"]
    if opts[0] != authored[0] or opts[-1] != authored[-1]:
        endpoints_ok = False
        check(f"endpoints retained: {key}", False, f"first/last drifted: {opts}")
check(
    "first and last option retain their positions (all six switches)",
    endpoints_ok,
    "options[0] and options[-1] match the authored first/last",
)

permissive_at_zero = True
detail_lines = []
for key in declaring:
    opts = loaded[key].options
    dflt = loaded[key].default
    obl = obligations.get(key)
    # Riverside starts every switch on its permissive end, so default == options[0]
    # and the obligation's permissive_value names that same index-0 state.
    if dflt != opts[0]:
        permissive_at_zero = False
    if obl is not None and obl.permissive_value != opts[0]:
        permissive_at_zero = False
    detail_lines.append(f"{key}: index0={opts[0]!r} default={dflt!r} permissive={getattr(obl,'permissive_value',None)!r}")
check(
    "index 0 is the permissive end (default and permissive_value both name it)",
    permissive_at_zero,
    "; ".join(detail_lines),
)

# --- 3. default remains distinct from permissive_value ----------------------------------
# They are separate fields on separate models. Prove default does not derive from
# permissive_value by constructing a COMPLIANT-START policy: default one step in from the
# permissive end, while an obligation would still name the permissive (index-0) state.
compliant = PolicyOption(
    key="data_retention",
    category="data_governance",
    cost=9000,
    effects={"privacy_risk": -0.25},
    options=["indefinite", "standard_period", "minimal"],
    default="standard_period",  # NOT the permissive value 'indefinite'
    provenance=Provenance(source="AUTHORED", note="compliant-start check"),
)
permissive_value_from_obligation = "indefinite"  # what obligation_rules would name
check(
    "default is distinct from permissive_value (compliant-start pack is valid)",
    compliant.default == "standard_period"
    and compliant.default != permissive_value_from_obligation
    and compliant.default in compliant.options,
    f"default={compliant.default!r} permissive_value={permissive_value_from_obligation!r}",
)

# And on the real pack the two live on different objects entirely.
distinct_objects = all(
    isinstance(getattr(loaded[k], "default", None), str)
    and hasattr(obligations.get(k), "permissive_value")
    for k in declaring
)
check(
    "on Riverside, default (PolicyOption) and permissive_value (ObligationRule) are "
    "separate attributes on separate models",
    distinct_objects,
)

# --- 4. Legacy policies without options/default retain documented compatibility ---------
# (a) In-memory: a PolicyOption with neither field loads, options==[] default==None.
legacy = PolicyOption(
    key="encrypt_customer_data",
    category="data_governance",
    cost=1500,
    effects={"privacy_risk": -0.2},
    provenance=Provenance(source="AUTHORED", note="legacy shape"),
)
check(
    "legacy PolicyOption (no options/default) loads with options==[] default==None",
    legacy.options == [] and legacy.default is None,
    f"options={legacy.options} default={legacy.default}",
)

# (b) A real legacy-shape pack still loads, every policy on the legacy shape.
legacy_pack = load_casepack(LEGACY_FIXTURE)
all_legacy = all(p.options == [] and p.default is None for p in legacy_pack.policies)
check(
    f"legacy-shape pack {LEGACY_FIXTURE.name} loads; every policy is options==[] default==None",
    all_legacy and len(legacy_pack.policies) > 0,
    f"{len(legacy_pack.policies)} policies, all legacy shape",
)

# --- 5. Round-trip: dumping and reloading preserves order (guards I8 for this field) -----
redumped = [
    PolicyOption.model_validate(loaded[k].model_dump()).options for k in declaring
]
roundtrip_ok = all(redumped[i] == list(loaded[declaring[i]].options) for i in range(len(declaring)))
check(
    "options order survives model_dump -> model_validate round-trip",
    roundtrip_ok,
)

# --- 6. STATIC contract-surface checks (the regression guards) --------------------------
# The nine behavioral checks above pass on the PRE-rework base too, because the pack order
# and loader were already correct there -- they cannot regress the two things this packet
# repairs (finding `1.1-PR-002`). These checks read the authoritative documentation surfaces
# as text and assert they DECLARE the ordinal rule and do NOT declare order meaningless.
# They are RED on `174e980` (models.py said "carries no meaning"; CONTRACTS.md had no entry;
# docs said "authoring convention, not semantics") and GREEN at the corrected tip.

MODELS_SRC = (REPO / "backend" / "app" / "casepack" / "models.py").read_text()
CONTRACTS_SRC = (REPO / "CONTRACTS.md").read_text()
DOCS_SRC = (REPO / "docs" / "casepack-schema.md").read_text()

# Phrases that assert order is meaningless -- none may survive on any authoritative surface.
MEANINGLESS = [
    "carries no meaning",
    "authoring convention, not semantics",
    "authoring convention and",       # models.py's "Ordering is an authoring convention and\ncarries no meaning"
    "do not infer strictness",
    "nothing reads position",
]

# models.py: the PolicyOption.options docstring must affirm ordinal and forbid meaningless.
models_forbidden = [p for p in MEANINGLESS if p.lower() in MODELS_SRC.lower()]
check(
    "models.py declares options ORDINAL and carries no 'order is meaningless' statement",
    ("ordinal" in MODELS_SRC.lower())
    and ("least constrained" in MODELS_SRC.lower())
    and not models_forbidden,
    f"surviving meaningless phrase(s): {models_forbidden}" if models_forbidden else "ordinal affirmed, no meaningless phrase",
)

# CONTRACTS.md: the cross-cutting entry must exist and declare the ordinal rule.
check(
    "CONTRACTS.md has a PolicyOption.options entry declaring the ordinal ordering",
    ("PolicyOption.options" in CONTRACTS_SRC)
    and ("ordinal" in CONTRACTS_SRC.lower())
    and ("least constrained / most permissive" in CONTRACTS_SRC.lower())
    and not any(p in CONTRACTS_SRC.lower() for p in ("carries no meaning", "authoring convention, not semantics")),
    "entry present, ordinal, index-0-permissive",
)

# docs/casepack-schema.md: authoring guide must affirm ordinal and drop the old convention line.
docs_forbidden = [p for p in MEANINGLESS if p.lower() in DOCS_SRC.lower()]
check(
    "docs/casepack-schema.md declares options ordinal and carries no 'order is meaningless' statement",
    ("ordinal" in DOCS_SRC.lower())
    and not docs_forbidden,
    f"surviving meaningless phrase(s): {docs_forbidden}" if docs_forbidden else "ordinal affirmed, no meaningless phrase",
)

# The contract must NOT overstate 1.4: it may not claim the scorer READS policy distance
# today (finding `1.1-PR-001`). The deferred hook raises rather than read.
present_tense_overclaim = (
    "reads ordinal\ndistance" in CONTRACTS_SRC.lower()
    or "reads ordinal distance" in CONTRACTS_SRC.lower()
    or "alignment scoring reads that distance" in MODELS_SRC.lower()
    or "alignment scoring measures the\ndistance" in CONTRACTS_SRC.lower()
)
check(
    "model/contract describe the 1.4 policy-distance consumer as PROSPECTIVE, not current",
    not present_tense_overclaim
    and ("notimplementederror" in CONTRACTS_SRC.lower() or "deferred" in CONTRACTS_SRC.lower()),
    "no present-tense 'reads distance' overclaim; deferral stated",
)

# --- summary ----------------------------------------------------------------------------
failed = [name for ok, name in results if not ok]
print()
if failed:
    print(f"{len(failed)} FAILED: {failed}")
    sys.exit(1)
print(f"all {len(results)} policy-option contract checks pass")
sys.exit(0)
