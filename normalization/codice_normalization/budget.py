"""Load the federal budget into canonical Postgres (Fase 3).

Two things this layer is responsible for:

1. **Not losing money.** The aggregate loaded must equal the published total to
   the cent. A budget figure that silently drops rows is worse than no figure.
2. **Not inventing attribution.** Which node a ramo belongs to is our assertion,
   curated in data/ramos.yaml and nullable — several ramos are transfers, debt
   or provisions that no single organ executes.
"""

from __future__ import annotations

import json
from pathlib import Path

import psycopg
import yaml


def load_ramos(conn: psycopg.Connection, data_dir: Path, parsed: list[dict]) -> dict:
    """Ramo catalogue: names from the source, node mapping from our curation."""
    mapping = {r["id"]: r for r in yaml.safe_load((data_dir / "ramos.yaml").read_text())["ramos"]}

    names: dict[int, str] = {}
    for year in parsed:  # later years win; the source renames ramos over time
        for r in year["ramos"]:
            names[r["id"]] = r["name"]

    unmapped, missing_nodes = [], []
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM node")
        known_nodes = {r[0] for r in cur.fetchall()}
        for rid, name in sorted(names.items()):
            entry = mapping.get(rid)
            if entry is None:
                unmapped.append(rid)
                node = None
                note = "sin curar: el ramo apareció después de la última revisión"
            else:
                node = entry.get("node")
                note = entry.get("note")
                if node and node not in known_nodes:
                    missing_nodes.append((rid, node))
                    note = f"nodo '{node}' no existe en la estructura curada; se deja sin vincular"
                    node = None
            cur.execute(
                """INSERT INTO ramo (id, name, node_id, note) VALUES (%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE
                     SET name=EXCLUDED.name, node_id=EXCLUDED.node_id, note=EXCLUDED.note""",
                (rid, name, node, note),
            )
    conn.commit()
    return {"ramos": len(names), "unmapped": unmapped, "missing_nodes": missing_nodes}


def load_allocations(conn: psycopg.Connection, parsed: list[dict], snapshots: list[dict],
                     stage: str = "aprobado") -> dict:
    """One row per (year, ramo, territory, stage). Verifies the total to the cent.

    PEF rows carry only the approved figure; Cuenta Pública rows carry a stage
    each, so the caller passes `stage=None` to read it from the row itself.
    """
    by_hash = {s["sha256"]: s for s in snapshots}
    stats = {"years": [], "rows": 0, "mismatches": []}

    with conn.cursor() as cur:
        for year in parsed:
            fy = year["fiscal_year"]
            snap = by_hash.get(year.get("snapshot_sha256"))
            if not snap:
                raise ValueError(f"{fy}: no snapshot metadata; refusing to load money without provenance (R1)")
            cur.execute(
                "SELECT id FROM snapshot WHERE content_hash = %s AND url = %s",
                (snap["sha256"], snap["url"]),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"{fy}: snapshot {snap['sha256'][:12]} not registered")
            snapshot_id = row[0]

            stages = {a.get("stage", stage) for a in year["allocations"]}
            cur.execute(
                "DELETE FROM budget_allocation WHERE fiscal_year = %s AND stage = ANY(%s)",
                (fy, list(stages)),
            )
            for a in year["allocations"]:
                cur.execute(
                    """INSERT INTO budget_allocation
                         (fiscal_year, ramo_id, territory_key, scope, amount_mxn, snapshot_id, stage)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (fy, a["ramo_id"], a["territory_key"], a["scope"], a["amount_mxn"],
                     snapshot_id, a.get("stage", stage)),
                )
                stats["rows"] += 1

            # The loaded total must equal what the parser read from the file,
            # stage by stage: a budget that loses money while loading is worse
            # than no budget at all.
            expected = year.get("totals_by_stage") or {stage: year["total_mxn"]}
            for st, exp in expected.items():
                cur.execute(
                    "SELECT sum(amount_mxn) FROM budget_allocation WHERE fiscal_year=%s AND stage=%s",
                    (fy, st),
                )
                loaded = float(cur.fetchone()[0] or 0)
                if abs(loaded - exp) > 0.01:
                    stats["mismatches"].append({"year": fy, "stage": st, "loaded": loaded, "expected": exp})
            stats["years"].append({"year": fy, "stages": expected, "allocations": len(year["allocations"])})
    conn.commit()
    if stats["mismatches"]:
        raise ValueError(f"budget totals do not match: {stats['mismatches']}")
    return stats


def load_snapshots(conn: psycopg.Connection, snapshots_json: Path) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO source (key, name, base_url, format) VALUES (%s,%s,%s,%s)
               ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name""",
            ("transparencia_presupuestaria", "SHCP — Transparencia Presupuestaria",
             "https://www.transparenciapresupuestaria.gob.mx/", "csv"),
        )
        n = 0
        for s in json.loads(snapshots_json.read_text()):
            cur.execute(
                """INSERT INTO snapshot (source_key, url, captured_at, content_hash, r2_key, content_type)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (content_hash, url) DO NOTHING""",
                (s["source_key"], s["url"], s["captured_at"], s["sha256"], s["r2_key"], s["content_type"]),
            )
            n += cur.rowcount
    conn.commit()
    return n
