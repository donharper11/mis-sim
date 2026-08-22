"""Guard for event display titles (finding J1 / open item R1).

Every label family maps a key to a short name, except `events`, which maps an event's
`body_key` to the persona's message (prose). So a finding about an event -- `E21`, an event
whose preconditions can never all be true -- had nowhere to read a title and led with the
machine key, while the other seven codes of `1.2-024` no longer did. `labels.event_names`
is the title map events gained; `E21` routes its subject through it.

The guard plants an impossible precondition in Riverside (which authors `event_names`) and
asserts the E21 finding leads with the authored title, not the key. Non-vacuous: it checks
the title and the key genuinely differ.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.casepack.validate import validate_pack_dir

RIVERSIDE = Path(__file__).resolve().parents[1] / "packs/riverside_grocery"


def test_e21_leads_with_the_authored_event_title(tmp_path):
    pack = tmp_path / "pack"
    shutil.copytree(RIVERSIDE, pack)

    # inventory_audit_question waits on wh_rollout_01 at critical; demand it also at warning
    # so its preconditions can never all be true -> E21.
    events = pack / "events.yaml"
    text = events.read_text()
    one = "    - {type: signal_open, signal: wh_rollout_01, severity: critical}\n"
    assert one in text
    text = text.replace(one, one + "    - {type: signal_open, signal: wh_rollout_01, severity: warning}\n", 1)
    events.write_text(text)

    e21 = [f for f in validate_pack_dir(pack).findings if f.code == "E21"]
    assert e21, "planted conflict must raise E21"
    finding = e21[0]

    assert "Inventory Accuracy Challenged" in finding.subject, (
        f"E21 must lead with the authored title, got {finding.subject!r} -- event_names routing lost"
    )
    # Non-vacuous: the machine key is not what leads the line, and it differs from the title.
    assert "inventory_audit_question" not in finding.subject
    assert finding.field.startswith("inventory_audit_question")  # the field path still cites the key
