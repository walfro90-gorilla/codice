"""CLI: validate / load / export.

  python -m codice_normalization validate ../data
  python -m codice_normalization load ../data ../ingestion
  python -m codice_normalization people ../ingestion
  python -m codice_normalization titulares ../data ../ingestion
  python -m codice_normalization budget ../data ../ingestion
  python -m codice_normalization cuenta-publica ../data ../ingestion
  python -m codice_normalization export ../web/public/data/grafo.json
"""

from __future__ import annotations

import sys
from pathlib import Path

import json

from . import budget, curated, db, export_graph, people, titulares


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

        # Curated office-holders live beside the structure and validate with it,
        # so a contributor gets one answer instead of two commands.
        nodes_for_check = None
        try:
            with db.connect() as conn:
                nodes_for_check = titulares.known_nodes(conn)
        except Exception:
            pass
        h = titulares.load_file(data_dir / "titulares.yaml", nodes_for_check)
        for err in h.errors:
            print(f"ERROR {err}")

        print(f"{len(g.nodes)} nodes, {len(g.edges)} edges, "
              f"{len(h.holders)} titulares, {len(g.errors) + len(h.errors)} errors")
        sys.exit(0 if (g.ok and h.ok) else 1)

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

    if cmd == "budget":
        data_dir, ingestion_dir = Path(sys.argv[2]), Path(sys.argv[3])
        parsed = json.loads((ingestion_dir / "parsed" / "pef.json").read_text())
        snaps = json.loads((ingestion_dir / "parsed" / "pef_snapshots.json").read_text())
        with db.connect() as conn:
            print(f"snapshots: {budget.load_snapshots(conn, ingestion_dir / 'parsed' / 'pef_snapshots.json')} new")
            print(budget.load_ramos(conn, data_dir, parsed))
            print(budget.load_allocations(conn, parsed, snaps))
        return

    if cmd == "cuenta-publica":
        data_dir, ingestion_dir = Path(sys.argv[2]), Path(sys.argv[3])
        parsed = json.loads((ingestion_dir / "parsed" / "cuenta_publica.json").read_text())
        snaps = json.loads((ingestion_dir / "parsed" / "cuenta_publica_snapshots.json").read_text())
        with db.connect() as conn:
            print(f"snapshots: {budget.load_snapshots(conn, ingestion_dir / 'parsed' / 'cuenta_publica_snapshots.json')} new")
            print(budget.load_ramos(conn, data_dir, parsed))
            print(budget.load_allocations(conn, parsed, snaps, stage=None))
        return

    if cmd == "titulares":
        data_dir = Path(sys.argv[2])
        ingestion_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        with db.connect() as conn:
            if ingestion_dir:
                snaps = ingestion_dir / "parsed" / "nombramientos_snapshots.json"
                if snaps.exists():
                    print(f"snapshots: {budget.load_snapshots(conn, snaps)} new")
            print(titulares.load(conn, data_dir))
        return

    if cmd == "export":
        out = Path(sys.argv[2])
        with db.connect() as conn:
            print(export_graph.export(conn, out))
        return

    sys.exit(f"unknown command: {cmd}")


main()
