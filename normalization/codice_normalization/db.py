"""Load parsed + curated data into canonical Postgres (L2).

Idempotent upserts keyed on natural ids so re-running is safe.
Connection via DATABASE_URL (default: local dev container).
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import psycopg

from .curated import CuratedGraph

DEFAULT_DSN = "postgresql://postgres:codice_dev@localhost:54320/postgres"

SOURCES = [
    ("leyfed", "Cámara de Diputados — Leyes Federales", "https://www.diputados.gob.mx/LeyesBiblio/", "pdf"),
    ("inegi_censo", "INEGI — Censo de Población y Vivienda", "https://www.inegi.org.mx/programas/ccpv/2020/", "zip"),
    ("curated", "Curaduría Códice (fundamento legal citado por nodo)", "https://github.com/gorilla-labs/codice", "yaml"),
]


def connect() -> psycopg.Connection:
    return psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_DSN))


def load_sources_and_snapshots(conn: psycopg.Connection, snapshots_json: Path) -> int:
    with conn.cursor() as cur:
        for key, name, base_url, fmt in SOURCES:
            cur.execute(
                """INSERT INTO source (key, name, base_url, format) VALUES (%s,%s,%s,%s)
                   ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name, base_url=EXCLUDED.base_url""",
                (key, name, base_url, fmt),
            )
        n = 0
        for s in json.loads(snapshots_json.read_text())["snapshots"]:
            cur.execute(
                """INSERT INTO snapshot (source_key, url, captured_at, content_hash, r2_key, content_type)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (content_hash, url) DO NOTHING""",
                (s["source_key"], s["url"], s["captured_at"], s["sha256"], s["r2_key"], s["content_type"]),
            )
            n += cur.rowcount
    conn.commit()
    return n


def load_territories(conn: psycopg.Connection, parsed_dir: Path) -> dict:
    with conn.cursor() as cur:
        rows = list(csv.DictReader((parsed_dir / "territories.csv").open()))
        # parents (estados) first so the FK holds
        for row in sorted(rows, key=lambda r: len(r["inegi_key"])):
            centroid = (
                f"SRID=4326;POINT({row['lon']} {row['lat']})" if row["lon"] else None
            )
            cur.execute(
                """INSERT INTO territory (inegi_key, level, name, parent_key, centroid)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (inegi_key) DO UPDATE
                     SET name=EXCLUDED.name, centroid=EXCLUDED.centroid""",
                (row["inegi_key"], row["level"], row["name"], row["parent_key"] or None, centroid),
            )
        # Estados carry no coordinates in the ITER; derive a representative point
        # from their municipios so state-level nodes can be placed on the map.
        # ponytail: geometric centroid of municipio points — real polygons and
        # their true centroids arrive with the Marco Geoestadístico.
        cur.execute(
            """UPDATE territory e SET centroid = sub.c FROM (
                 SELECT parent_key, ST_Centroid(ST_Collect(centroid)) AS c
                 FROM territory WHERE level='municipio' AND centroid IS NOT NULL
                 GROUP BY parent_key) sub
               WHERE e.inegi_key = sub.parent_key AND e.level='estado'"""
        )
        pop = list(csv.reader((parsed_dir / "population.csv").open()))[1:]
        for key, year, value in pop:
            cur.execute(
                """INSERT INTO population (inegi_key, census_year, population) VALUES (%s,%s,%s)
                   ON CONFLICT (inegi_key, census_year) DO UPDATE SET population=EXCLUDED.population""",
                (key, int(year), int(value)),
            )
    conn.commit()
    return {"territories": len(rows), "population_rows": len(pop)}


def load_curated(conn: psycopg.Connection, g: CuratedGraph, data_dir: Path) -> dict:
    if not g.ok:
        raise ValueError(f"refusing to load: {len(g.errors)} validation errors")
    types = yaml_types(data_dir)
    with conn.cursor() as cur:
        for t in types:
            cur.execute(
                """INSERT INTO node_type (key, name, description) VALUES (%s,%s,%s)
                   ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description""",
                (t["key"], t["name"], t.get("description")),
            )
        for node in g.nodes.values():
            cur.execute(
                """INSERT INTO node (id, node_type_key, name, level, territory_key, summary, valid_from, valid_to)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET
                     node_type_key=EXCLUDED.node_type_key, name=EXCLUDED.name, level=EXCLUDED.level,
                     territory_key=EXCLUDED.territory_key, summary=EXCLUDED.summary,
                     valid_from=EXCLUDED.valid_from, valid_to=EXCLUDED.valid_to""",
                (node.id, g.node_types[node.id], node.name, node.level.value,
                 node.territory_key, node.summary, node.valid_from, node.valid_to),
            )
            # legal basis: replace wholesale per node (curated source of truth)
            cur.execute("DELETE FROM node_legal_basis WHERE node_id = %s", (node.id,))
            for b in node.legal_basis:
                cur.execute(
                    """INSERT INTO node_legal_basis (node_id, document, article, url, snapshot_id)
                       VALUES (%s,%s,%s,%s,
                         (SELECT id FROM snapshot WHERE url = %s ORDER BY captured_at DESC LIMIT 1))""",
                    (node.id, b.document, b.article, str(b.url), str(b.url)),
                )
        cur.execute("DELETE FROM edge")  # curated edges are the full truth for Fase 1
        for e in g.edges:
            cur.execute(
                """INSERT INTO edge (from_node, to_node, type, legal_basis, valid_from, valid_to)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (e.from_node, e.to_node, e.type.value, e.legal_basis, e.valid_from, e.valid_to),
            )
    conn.commit()
    return {"node_types": len(types), "nodes": len(g.nodes), "edges": len(g.edges)}


def yaml_types(data_dir: Path) -> list[dict]:
    import yaml

    return yaml.safe_load((data_dir / "node-types.yaml").read_text())["node_types"]


def known_territories(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT inegi_key FROM territory")
        return {r[0] for r in cur.fetchall()}
