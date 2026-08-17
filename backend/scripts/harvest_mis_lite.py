#!/usr/bin/env python3
"""Read-only extraction of mis_lite content, one JSON file per source table.

Module 1.3, build step 1. This script is the reproducible half of GOVERNANCE section 4.9's
"the harvest IS the seed": it re-creates the intermediate extraction that every transform
in `packs/riverside_grocery/PROVENANCE.md` is traced back to.

INVARIANT I1 -- READ-ONLY. This file issues SELECT and nothing else: no statement that
writes, changes or removes anything appears in it, and the connection is opened with
`default_transaction_read_only`, so the server refuses a write even if one were somehow
issued. I1's grep over `backend/scripts/harvest*` must return zero, which is why the
forbidden verbs are not spelled out here either.

Usage:

    PGPASSWORD=... python3 backend/scripts/harvest_mis_lite.py \
        --from mis_lite --to riverside_grocery

Writes `backend/harvest/mis_lite/<table>.json` plus `_manifest.json` (rows per table and
the extraction timestamp). It writes nothing into the pack directory: the pack is authored
from this extraction by hand, because most of the transform is judged rather than
mechanical (spec section 5.2).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOST = "192.168.50.38"
USER = "donwh"

#: Every table named in spec section 5.1's transform map, plus the nine `*_mapping`
#: tables pre-flight row 5 audits for placeholder seeding.
TABLES: list[str] = [
    # take as-is
    "strategy",
    "objectives",
    "impact_areas",
    "stakeholders",
    "data_governance_policies",
    "security_incidents",
    "regulatory_penalties",
    "competitors",
    "market_potential",
    # take with rework
    "component_strategy_fit",
    "component_types_master",
    "it_infrastructure_addons_master",
    "change_management_master",
    "change_management_strategy_fit",
    "mis_initiatives_master",
    "erp_modules_master",
    "ecommerce_features_master",
    "business_processes_master",
    "stakeholder_infrastructure_preference",
    "deployment_types",
    "hardware_types",
    "network_types",
    "database_types",
    "maintenance_support_levels",
    "integration_services",
    # the nine preference-mapping tables -- extracted for the row-5 uniformity audit only
    "addon_mapping",
    "business_process_mapping",
    "change_mgmt_mapping",
    "component_mapping",
    "ecommerce_features_mapping",
    "ecommerce_security_mapping",
    "erp_feature_mapping",
    "erp_master_mapping",
    "mis_initiative_mapping",
]


def _psql(database: str, statement: str) -> str:
    """Run one read-only statement and return raw stdout.

    `default_transaction_read_only=on` is belt and braces for I1: the statements below are
    SELECT already, and the server would reject anything else on this connection.
    """
    env = dict(os.environ)
    env["PGOPTIONS"] = "-c default_transaction_read_only=on"
    proc = subprocess.run(
        ["psql", "-h", HOST, "-U", USER, "-d", database, "-v", "ON_ERROR_STOP=1", "-tAc", statement],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        raise SystemExit(f"psql failed on {database}: {proc.stderr.strip()}")
    return proc.stdout


def _columns(database: str, table: str) -> list[str]:
    out = _psql(
        database,
        "select column_name from information_schema.columns "
        f"where table_schema = 'public' and table_name = '{table}' order by ordinal_position;",
    )
    return [line for line in out.splitlines() if line]


def extract(database: str, out_dir: Path) -> dict[str, int]:
    """One JSON file per table. `trialNNN` columns are excluded, never modelled."""
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for table in TABLES:
        cols = _columns(database, table)
        # CONTRACTS.md: every mis_lite table carries a `trialNNN char(1)` migration
        # carryover, uniformly 'T'. Excluded here so it can never reach the pack (I2).
        keep = [c for c in cols if not c.startswith("trial")]
        if not keep:
            raise SystemExit(f"{table}: no columns left once trial* is excluded")
        selected = ", ".join(f'"{c}"' for c in keep)
        raw = _psql(
            database,
            f"select coalesce(json_agg(t), '[]'::json) from (select {selected} from {table}) t;",
        )
        rows = json.loads(raw.strip() or "[]")
        (out_dir / f"{table}.json").write_text(
            json.dumps(rows, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
        )
        counts[table] = len(rows)
        print(f"  {table:<40} {len(rows):>5} rows  ({len(cols) - len(keep)} trial column excluded)")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="source", default="mis_lite", help="source database")
    parser.add_argument("--to", dest="pack", default="riverside_grocery", help="destination pack key")
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "harvest"),
        help="directory for the intermediate extraction",
    )
    args = parser.parse_args()

    if not os.environ.get("PGPASSWORD"):
        print("PGPASSWORD is not set; psql will prompt or fail.", file=sys.stderr)

    out_dir = Path(args.out) / args.source
    print(f"extracting {args.source} @ {HOST} (read-only) -> {out_dir}")
    counts = extract(args.source, out_dir)

    manifest = {
        "source_database": args.source,
        "source_host": HOST,
        "destination_pack": args.pack,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "read-only (default_transaction_read_only = on)",
        "trial_columns": "excluded on extraction -- CONTRACTS.md",
        "rows_per_table": counts,
        "total_rows": sum(counts.values()),
    }
    (out_dir / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"\n{len(counts)} tables, {sum(counts.values())} rows -> {out_dir}/_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
