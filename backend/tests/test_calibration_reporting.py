"""Read-only reporting regressions; synthetic values are independent of the scorer."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.calibrate import inventory, report


@pytest.mark.parametrize("spacing", ["", " ", "   ", "\t", " \t  "])
def test_marker_horizontal_whitespace_counts_lines(tmp_path, spacing):
    (tmp_path / "values.yaml").write_text(
        f"# TODO:{spacing}calibrate two numbers: 12, 24\n"
        f"amount: 7  # TODO:{spacing}calibrate; TODO:{spacing}calibrate\n"
        "# An ordinary comment\n",
        encoding="utf-8",
    )

    markers = inventory.scan(tmp_path)

    assert inventory.total_sites(markers) == 2
    assert markers[0].rel_path == "values.yaml"
    assert [line for line, _ in markers[0].sites] == [1, 2]


@pytest.mark.parametrize("header_line", [1, 7, 12])
def test_moved_convention_header_preserves_legitimate_comment_markers(tmp_path, header_line):
    lines = ["# context"] * 13
    lines[header_line - 1] = (
        "# Thresholds carry TODO: calibrate wherever the number is authored judgement rather than a"
    )
    marker_line = 7 if header_line != 7 else 8
    lines[marker_line - 1] = "# TODO: calibrate -- a legitimate threshold: 0.8"
    lines[12] = "# Thresholds carry TODO: calibrate -- this specific threshold needs review"
    (tmp_path / "watch_rules.yaml").write_text("\n".join(lines), encoding="utf-8")

    markers = inventory.scan(tmp_path)

    assert inventory.total_sites(markers) == 2
    assert [line for line, _ in markers[0].sites] == [marker_line, 13]


@pytest.fixture
def two_round_report():
    pack = SimpleNamespace(
        metadata=SimpleNamespace(pack_key="example", pack_version="1.0.0", rounds=2),
        labels=SimpleNamespace(
            capabilities={"fulfilment": "Order Fulfilment"},
            strategies={"low_cost": "Cost Leadership", "distinctive": "Differentiation"},
        ),
        strategies=[SimpleNamespace(capability_weights={"fulfilment": 1.0})],
    )
    archetypes = [
        SimpleNamespace(key="alpha", label="Alpha Team", strategy="low_cost"),
        SimpleNamespace(key="beta", label="Beta Team", strategy="distinctive"),
    ]
    results = {
        "alpha": [
            {"round": 1, "firm_score": 0.21, "capabilities": [], "scorecard": {
                "financial": 0.111, "customer": 0.222,
                "internal_process": 0.333, "learning_growth": 0.444,
            }},
            {"round": 2, "firm_score": 0.91, "capabilities": [], "scorecard": {
                "financial": 0.555, "customer": 0.666,
                "internal_process": 0.777, "learning_growth": 0.888,
            }},
        ],
        "beta": [
            {"round": 1, "firm_score": 0.32, "capabilities": [], "scorecard": {
                "financial": 0.123, "customer": 0.234,
                "internal_process": 0.345, "learning_growth": 0.456,
            }},
            {"round": 2, "firm_score": 0.43, "capabilities": [], "scorecard": {
                "financial": 0.567, "customer": 0.678,
                "internal_process": 0.789, "learning_growth": 0.891,
            }},
        ],
    }
    return pack, archetypes, results


def _table_rows(text, heading):
    assert heading in text
    table = text.split(heading, 1)[1].split("\n\n", 1)[0]
    return {
        label: line.strip().removeprefix(label).split()
        for label in ("Alpha Team", "Beta Team")
        for line in table.splitlines()
        if line.strip().startswith(label)
    }


@pytest.mark.parametrize("count", [0, 2, 6])
def test_registered_item_totals_follow_live_register(tmp_path, monkeypatch, two_round_report, count):
    monkeypatch.setattr(inventory, "REGISTER_ITEMS", tuple(
        (f"Review {n}", f"Calibration item {n}", "Cost curve") for n in range(count)
    ))
    pack, archetypes, results = two_round_report

    text = report.render(pack, tmp_path, archetypes, results)

    assert f"plus {count} register-owned calibration items" in text
    assert f"0 marker sites + {count} register items" in text


def test_all_round_perspective_tables_show_distinct_source_values(tmp_path, two_round_report):
    pack, archetypes, results = two_round_report
    before = deepcopy(results)

    text = report.render(pack, tmp_path, archetypes, results)

    expected = {
        "Financial": {"Alpha Team": ["0.111", "0.555"], "Beta Team": ["0.123", "0.567"]},
        "Customer": {"Alpha Team": ["0.222", "0.666"], "Beta Team": ["0.234", "0.678"]},
        "Internal Process": {"Alpha Team": ["0.333", "0.777"], "Beta Team": ["0.345", "0.789"]},
        "Learning & Growth": {"Alpha Team": ["0.444", "0.888"], "Beta Team": ["0.456", "0.891"]},
    }
    for perspective, rows in expected.items():
        heading = f"BALANCED SCORECARD -- {perspective} by round"
        assert _table_rows(text, heading) == rows
        section = text.split(heading, 1)[1].split("\n\n", 1)[0]
        assert section.splitlines()[1].split() == ["R1", "R2"]
    assert _table_rows(text, "REALISED VALUE (firm, strategy-weighted)") == {
        "Alpha Team": ["0.2100", "0.9100"], "Beta Team": ["0.3200", "0.4300"],
    }
    assert _table_rows(text, "BALANCED SCORECARD at R2") == {
        "Alpha Team": ["0.555", "0.666", "0.777", "0.888"],
        "Beta Team": ["0.567", "0.678", "0.789", "0.891"],
    }
    assert results == before


@pytest.mark.parametrize("perspective,label", [
    ("financial", "Financial"), ("customer", "Customer"),
    ("internal_process", "Internal Process"), ("learning_growth", "Learning & Growth"),
])
@pytest.mark.parametrize("value,raw,cell", [
    (-0.125, "-0.125", "-0.125"), (1.125, "1.125", "1.125"),
    (float("nan"), "nan", "nan"), (float("inf"), "inf", "inf"),
    (float("-inf"), "-inf", "-inf"),
    (-0.000001, "-1e-06", "-0.000"), (1.000001, "1.000001", "1.000"),
])
def test_early_round_scale_diagnostics_preserve_raw_values(
    tmp_path, two_round_report, perspective, label, value, raw, cell,
):
    pack, archetypes, results = two_round_report
    results["alpha"][0]["scorecard"][perspective] = value

    text = report.render(pack, tmp_path, archetypes, results)

    assert "SCORE-SCALE DIAGNOSTICS REQUIRING REVIEW" in text
    assert "not a balance verdict" in text
    assert f"Alpha Team | R1 | {label} | raw value {raw}" in text
    assert _table_rows(text, f"BALANCED SCORECARD -- {label} by round")["Alpha Team"][0] == cell
    assert results["alpha"][0]["scorecard"][perspective] is value


def test_scale_boundaries_do_not_raise_diagnostics(tmp_path, two_round_report):
    pack, archetypes, results = two_round_report
    results["alpha"][0]["scorecard"]["financial"] = 0.0
    results["beta"][1]["scorecard"]["customer"] = 1.0

    text = report.render(pack, tmp_path, archetypes, results)

    assert "All reported perspective values are finite and within 0–1." in text
    assert " | raw value " not in text


@pytest.mark.parametrize("alpha,beta,ranking", [
    (0.91, 0.43, "Alpha Team > Beta Team"),
    (0.43, 0.91, "Beta Team > Alpha Team"),
    (0.43, 0.43, "Alpha Team = Beta Team"),
    (0.430001, 0.43, "Alpha Team > Beta Team"),
])
def test_final_ranking_uses_actual_scores_and_honest_ties(
    tmp_path, two_round_report, alpha, beta, ranking,
):
    pack, archetypes, results = two_round_report
    results["alpha"][-1]["firm_score"] = alpha
    results["beta"][-1]["firm_score"] = beta

    text = report.render(pack, tmp_path, archetypes, results)

    rank_lines = [line.strip() for line in text.splitlines() if "rank order" in line]
    assert rank_lines == [f"rank order at R2: {ranking}"]


def test_declared_strategy_scope_keeps_historical_gate_unchanged(tmp_path, two_round_report):
    pack, archetypes, results = two_round_report

    text = report.render(pack, tmp_path, archetypes, results)

    assert "curves cover only their listed declared strategies" in text
    assert "No claim is made that all strategies were exercised" in text
    assert "The historical human calibration gate remains unchanged." in text
    assert "No exit-code judgment." in text
    assert "Cost Leadership" in text
    assert "Differentiation" in text
    assert "low_cost" not in text
    assert "distinctive" not in text
