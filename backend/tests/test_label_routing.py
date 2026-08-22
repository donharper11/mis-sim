"""Regression guard for the label-display contract (finding B5, re-raised as CU-003).

B5 (`1.1-r2-003` · `1.1-r2-004` · `1.2-024`) was two fixes, and CU-003 proved both had
survived two rework packets with **no permanent guard**: reverting either still passed the
whole suite. The two halves:

  * ROUTING -- a finding names the business label a pack authored in `labels.yaml`, via
    `Lens.label(section, key)`, not the raw machine key. If that routing is reverted (label
    falls back to the key, or a message stops calling `lens.label`), an instructor reads
    `clinical_records` instead of `Clinical Records`.

  * NARROWING -- `check_labels` (E07) accepts a label ONLY in the section its reference
    names. `misc` used to fall back to a union of every section, so `E07`'s fix line named
    one of eight-then-twelve accepted answers and a key authored in the wrong section passed
    silently (`1.1-r2-004`). `misc` means `misc`.

Each test is a pair: the guard, and a non-vacuous check proving the guard could fail.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.casepack.validate import validate_pack_dir

PACKS = Path(__file__).resolve().parent / "fixtures/packs"


def _codes(report, code):
    return [f for f in report.findings if f.code == code]


# ---------------------------------------------------------------------------------------
# ROUTING -- findings show the authored business label, not the machine key
# ---------------------------------------------------------------------------------------


def test_e20_names_the_business_label_not_the_key():
    """broken_E20's unwatched capability is keyed `clinical_records` and labelled
    `Clinical Records`. The E20 finding must show the label. Reverting `Lens.label` to
    return the key, or dropping the `lens.label(...)` call in E20's message, fails here."""
    report = validate_pack_dir(PACKS / "broken_E20")
    e20 = _codes(report, "E20")
    assert e20, "broken_E20 must raise E20"
    finding = e20[0]

    assert finding.subject == "Clinical Records", (
        f"E20 subject should be the authored label 'Clinical Records', got {finding.subject!r} "
        "-- the label routing (Lens.label) has been reverted"
    )
    # Non-vacuous: the key and the label genuinely differ, so this test can detect a revert.
    assert finding.field.endswith("clinical_records")
    assert "clinical_records" != finding.subject


# ---------------------------------------------------------------------------------------
# NARROWING -- a `misc` reference does not fall back to other label sections
# ---------------------------------------------------------------------------------------


def test_misc_label_does_not_fall_back_to_another_section(tmp_path):
    """A stakeholder `role_key` is a `misc` reference. Author its label ONLY under another
    section and E07 must still fire. Reverting E07 to the old union-of-all-sections fallback
    would find the key elsewhere and pass silently."""
    pack = tmp_path / "pack"
    shutil.copytree(PACKS / "minimal_valid", pack)

    # baseline: minimal_valid is clean, so any E07 below is caused by the move, not noise.
    assert not _codes(validate_pack_dir(pack), "E07"), "minimal_valid must be E07-clean"

    labels = pack / "labels.yaml"
    text = labels.read_text()
    moved = "  role_practice_ownership: Practice Ownership\n"
    assert moved in text
    # remove from `misc`, re-home under `strategies` (a real section it is not referenced in)
    text = text.replace(moved, "")
    text = text.replace("strategies:\n", "strategies:\n" + moved)
    labels.write_text(text)

    e07 = _codes(validate_pack_dir(pack), "E07")
    fields = {f.field for f in e07}
    assert "practice_owner.role_key" in fields, (
        "E07 must fire for a role_key present only in another section -- the `misc` narrowing "
        "has been reverted to the union fallback"
    )
