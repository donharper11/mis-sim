"""Format the calibration report -- the curves a human reads (spec section 5.2 / 5.3).

Instructor-readable (invariant I3): every displayed name resolves to a business label -- capability
and strategy names through the pack's ``labels.yaml``, archetype names through the archetype's own
``label``, and the scorecard / term names through the fixed maps below. No raw engine key appears in
the default output; the exact pack sub-keys and per-capability detail live behind ``--debug``.

The report is descriptive only. It prints diagnostics (spread, ratio, rank order) as INFORMATIONAL
lines; it makes no ruling and produces no exit code (spec decision 5 / O3 / I6). The judgment is the
calibration authority's (spec section 5.4).
"""

from __future__ import annotations

from app.casepack.models import Casepack

from app.calibrate import inventory

#: Balanced-Scorecard perspective labels (design/03). No raw engine key in the report (I3).
_BSC_LABELS: dict[str, str] = {
    "financial": "Financial",
    "customer": "Customer",
    "internal_process": "Internal Process",
    "learning_growth": "Learning & Growth",
}
_BSC_ORDER = ("financial", "customer", "internal_process", "learning_growth")

#: Term labels (spec 5.6). realised value = Technology x Organisation x Management.
_TERM_LABELS: dict[str, str] = {"tech": "Technology", "org": "Organisation", "mgmt": "Management"}
_TERM_ORDER = ("tech", "org", "mgmt")

_ROWLABEL_W = 18


def _cap_label(pack: Casepack, key: str) -> str:
    return pack.labels.capabilities.get(key, key)


def _strategy_label(pack: Casepack, key: str) -> str:
    return pack.labels.strategies.get(key, key)


def _focus_capability(pack: Casepack) -> str:
    """The capability to decompose in the comparison table -- the highest-weighted capability of
    the pack's first strategy (its central capability). Pack-agnostic: no capability is named in
    code (I1)."""
    weights = dict(pack.strategies[0].capability_weights)
    return max(weights, key=lambda k: weights[k]) if weights else pack.capabilities[0].key


def _fmt_row(label: str, cells: list[str]) -> str:
    return f"  {label:<{_ROWLABEL_W}}" + "".join(f"{c:>10}" for c in cells)


def _header(pack: Casepack, archetypes, rounds: int) -> list[str]:
    return [
        "",
        f"  {pack.metadata.pack_key} {pack.metadata.pack_version} "
        f"· {rounds} rounds · {len(archetypes)} archetypes",
    ]


def _inventory_section(pack_dir, debug: bool) -> list[str]:
    markers = inventory.scan(pack_dir)
    total = inventory.total_sites(markers)
    lines = [
        "",
        f"  CALIBRATION CHECKLIST -- {total} TODO:calibrate marker sites live in the pack",
        "  (calibrate against these knowingly; a curve read while one is a placeholder is nonsense)",
        "",
    ]
    for fm in markers:
        lines.append(f"    {fm.rel_path:<28} {fm.count:>2} sites  -- {fm.affects}")
        if debug:
            for lineno, text in fm.sites:
                lines.append(f"        L{lineno}: {text}")
    lines.append("")
    lines.append("  plus 5 register-owned calibration items (not pack-YAML markers):")
    for code, what, affects in inventory.REGISTER_ITEMS:
        lines.append(f"    {code:<12} {what}")
        if debug:
            lines.append(f"                 affects: {affects}")
    lines.append(f"  = {total} marker sites + 5 register items = the 1.7 calibration checklist")
    return lines


def _realised_section(pack, archetypes, results, rounds: int) -> list[str]:
    lines = ["", "  REALISED VALUE (firm, strategy-weighted)      [from RoundResult.firm_score]"]
    lines.append(_fmt_row("", [f"R{r}" for r in range(1, rounds + 1)]))
    for a in archetypes:
        cells = [f"{p['firm_score']:.4f}" for p in results[a.key]]
        lines.append(_fmt_row(a.label, cells))
    return lines


def _scorecard_section(pack, archetypes, results, rounds: int) -> list[str]:
    lines = ["", f"  BALANCED SCORECARD at R{rounds}                       [from RoundResult.scorecard]"]
    lines.append(_fmt_row("", [_BSC_LABELS[d] for d in _BSC_ORDER]))
    for a in archetypes:
        sc = results[a.key][-1]["scorecard"]
        cells = [f"{sc[d]:.3f}" for d in _BSC_ORDER]
        lines.append(_fmt_row(a.label, cells))
    return lines


def _decomposition_section(pack, archetypes, results, rounds: int) -> list[str]:
    focus = _focus_capability(pack)
    lines = [
        "",
        f"  TERM DECOMPOSITION at R{rounds} -- {_cap_label(pack, focus)}   "
        f"[from RoundResult.capabilities]",
    ]
    lines.append(_fmt_row("", [_TERM_LABELS[t] for t in _TERM_ORDER] + ["Realised"]))
    for a in archetypes:
        cap = next((c for c in results[a.key][-1]["capabilities"] if c["capability"] == focus), None)
        if cap is None:
            continue
        cells = [f"{cap['terms'][t]:.3f}" for t in _TERM_ORDER] + [f"{cap['realised']:.4f}"]
        lines.append(_fmt_row(a.label, cells))
    return lines


def _diagnostics_section(pack, archetypes, results, rounds: int) -> list[str]:
    finals = {a.key: results[a.key][-1]["firm_score"] for a in archetypes}
    label = {a.key: a.label for a in archetypes}
    lines = ["", "  DIAGNOSTICS (informational -- not a gate)"]

    hi = max(finals.values())
    lo = min(finals.values())
    lines.append(f"    realised spread at R{rounds}: max {hi:.4f} - min {lo:.4f} = {hi - lo:.4f}")

    # complementary-asset ratio -- the Org throttle, the sim's thesis (spec 5.3).
    at = finals.get("all_tech_no_org")
    bal = finals.get("balanced")
    if at is not None and bal is not None:
        ratio = f"{at / bal:.3f}" if bal else "n/a (balanced final is 0)"
        lines.append(
            f"    {label['all_tech_no_org']} / {label['balanced']} final: "
            f"{at:.4f} / {bal:.4f} = {ratio}"
        )

    ranked = sorted(archetypes, key=lambda a: finals[a.key], reverse=True)
    lines.append(f"    rank order at R{rounds}: " + " > ".join(a.label for a in ranked))
    return lines


def render(pack: Casepack, pack_dir, archetypes, results, *, debug: bool = False) -> str:
    """The full report string (spec section 5.2). ``debug`` reveals the raw pack sub-keys and the
    per-capability decomposition detail -- the only place raw engine keys may appear (I3)."""
    rounds = pack.metadata.rounds
    lines: list[str] = []
    lines += _header(pack, archetypes, rounds)
    lines += _inventory_section(pack_dir, debug)
    lines += _realised_section(pack, archetypes, results, rounds)
    lines += _scorecard_section(pack, archetypes, results, rounds)
    lines += _decomposition_section(pack, archetypes, results, rounds)
    lines += _diagnostics_section(pack, archetypes, results, rounds)
    lines += [
        "",
        "  Declared strategy per archetype:",
    ]
    for a in archetypes:
        lines.append(f"    {a.label:<18} {_strategy_label(pack, a.strategy)}")
    lines += [
        "",
        "  -> reviewed by the calibration authority (spec section 5.4). No exit-code judgment.",
        "",
    ]
    if debug:
        lines += _debug_section(pack, archetypes, results)
    return "\n".join(lines)


def _debug_section(pack, archetypes, results) -> list[str]:
    """--debug: full per-capability term decomposition, every round. Raw engine keys allowed here
    (I3 scopes the no-raw-keys rule to the default report)."""
    lines = ["  == DEBUG: per-capability decomposition (raw keys) =="]
    for a in archetypes:
        lines.append(f"  [{a.key}]")
        for p in results[a.key]:
            lines.append(f"    round {p['round']} firm_score={p['firm_score']:.6f}")
            for c in p["capabilities"]:
                t = c["terms"]
                lines.append(
                    f"      {c['capability']:<20} tech={t['tech']:.4f} org={t['org']:.4f} "
                    f"mgmt={t['mgmt']:.4f} realised={c['realised']:.6f} throttle={c['throttle']}"
                )
    return lines
