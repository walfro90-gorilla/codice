"""CLI: validate / load / export.

  python -m codice_normalization validate ../data
  python -m codice_normalization load ../data ../ingestion
  python -m codice_normalization people ../ingestion
  python -m codice_normalization export ../web/public/data/grafo.json
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import curated, db, export_graph, people


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        data_dir = Path(sys.argv[2])
        terr: set[str] | None = None
        try:
            with db.connect() as conn:
                terr = db.known_territories(conn)
        except Exception:
            print("warning: no database, skipping territory checks", file=sys.stderr)
        g = curated.load_dir(data_dir, terr)
        for err in g.errors:
            print(f"ERROR {err}")
        print(f"{len(g.nodes)} nodes, {len(g.edges)} edges, {len(g.errors)} errors")
        sys.exit(0 if g.ok else 1)

    if cmd == "load":
        data_dir, ingestion_dir = Path(sys.argv[2]), Path(sys.argv[3])
        with db.connect() as conn:
            print(f"snapshots: {db.load_sources_and_snapshots(conn, ingestion_dir / 'snapshots.json')} new")
            print(db.load_territories(conn, ingestion_dir / "parsed"))
            g = curated.load_dir(data_dir, db.known_territories(conn))
            if not g.ok:
                for err in g.errors:
                    print(f"ERROR {err}")
                sys.exit(1)
            print(db.load_curated(conn, g, data_dir))
        return

    if cmd == "people":
        ingestion_dir = Path(sys.argv[2])
        with db.connect() as conn:
            snaps = [ingestion_dir / "parsed" / f for f in
                     ("diputados_snapshots.json", "senadores_snapshots.json")]
            print(f"snapshots: {people.load_snapshots(conn, snaps)} new")
            stats = people.load_legislators(conn, ingestion_dir / "parsed")
            print(stats)
            print(f"provenance rows: {people.link_tenure_provenance(conn)}")
        return

    if cmd == "export":
        out = Path(sys.argv[2])
        with db.connect() as conn:
            print(export_graph.export(conn, out))
        return

    sys.exit(f"unknown command: {cmd}")


main()
