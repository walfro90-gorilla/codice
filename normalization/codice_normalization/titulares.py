"""Curated office-holders: who occupies each node, with the document that says so.

This closes the gap the scrapers cannot reach — executive secretaries, state
governors, the Supreme Court, autonomous organs — using the same method that
worked for the constitutional structure: hand curation where every claim cites
a document.

The rule this module exists to enforce: **a person's name without a document
backing it does not get published** (R1). Naming a real person as the holder of
a public office is exactly the kind of claim that must be citable, and "everyone
knows it" is not a source. Validation refuses the whole file rather than loading
a nameless-sourced entry, because a partially-sourced dataset is worse than an
empty one: it looks complete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import psycopg
import yaml

# Contact kept only where it is institutional; a personal address is not ours
# to publish (same rule the legislator scrapers follow).
INSTITUTIONAL_DOMAIN = re.compile(r"@[\w.\-]*gob\.mx$", re.I)


@dataclass
class Holder:
    node_id: str
    name: str
    role: str
    start_date: date
    end_date: date | None
    contact: str | None
    doc_title: str
    doc_url: str
    doc_date: date | None


@dataclass
class HolderSet:
    holders: list[Holder] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _as_date(value, where: str, errors: list[str], required: bool) -> date | None:
    if value is None:
        if required:
            errors.append(f"{where}: falta la fecha")
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{where}: fecha inválida {value!r}")
        return None


def load_file(path: Path, known_nodes: dict[str, tuple[date, date | None]] | None = None) -> HolderSet:
    """Parse and validate data/titulares.yaml. Collects every error, not the first."""
    out = HolderSet()
    if not path.exists():
        return out

    doc = yaml.safe_load(path.read_text()) or {}
    entries = doc.get("titulares") or []
    if not isinstance(entries, list):
        out.errors.append("titulares: debe ser una lista")
        return out

    for i, e in enumerate(entries):
        where = f"titulares[{i}]"
        if not isinstance(e, dict):
            out.errors.append(f"{where}: debe ser un mapa")
            continue
        name = (e.get("nombre") or "").strip()
        node_id = (e.get("node") or "").strip()
        if not name:
            out.errors.append(f"{where}: falta el nombre")
        else:
            where = f"titulares[{i}] ({name})"
        if not node_id:
            out.errors.append(f"{where}: falta el nodo que ocupa")

        # The point of the whole module: no document, no entry.
        nom = e.get("nombramiento")
        if not isinstance(nom, dict) or not (nom.get("url") or "").strip():
            out.errors.append(
                f"{where}: sin documento de nombramiento. Un nombre sin fuente no se publica (R1)"
            )
            continue
        url = nom["url"].strip()
        if not url.startswith("https://"):
            out.errors.append(f"{where}: la URL del nombramiento debe ser https")
        doc_title = (nom.get("documento") or "").strip()
        if not doc_title:
            out.errors.append(f"{where}: el nombramiento necesita un título de documento")

        start = _as_date(e.get("desde"), where, out.errors, required=True)
        end = _as_date(e.get("hasta"), where, out.errors, required=False)
        doc_date = _as_date(nom.get("fecha"), where, out.errors, required=False)
        if start and end and end <= start:
            out.errors.append(f"{where}: 'hasta' debe ser posterior a 'desde'")

        contact = (e.get("contacto") or None)
        if contact and not INSTITUTIONAL_DOMAIN.search(contact):
            out.errors.append(f"{where}: solo se guarda contacto institucional (dominio gob.mx)")
            contact = None

        role = (e.get("cargo") or "").strip()
        if not role:
            out.errors.append(f"{where}: falta el cargo")

        if not (name and node_id and start):
            continue

        if known_nodes is not None:
            if node_id not in known_nodes:
                out.errors.append(f"{where}: el nodo {node_id!r} no existe en la estructura curada")
            else:
                n_from, n_to = known_nodes[node_id]
                # Nobody can hold an office that had already been abolished.
                if n_to and start > n_to:
                    out.errors.append(
                        f"{where}: toma posesión el {start} de un órgano extinto el {n_to}"
                    )

        out.holders.append(
            Holder(node_id, name, role, start, end, contact, doc_title, url, doc_date)
        )

    _check_single_holder(out)
    return out


def _check_single_holder(s: HolderSet) -> None:
    """An office has one holder at a time; overlapping terms are a data error."""
    by_node: dict[str, list[Holder]] = {}
    for h in s.holders:
        by_node.setdefault(h.node_id, []).append(h)
    for node_id, hs in by_node.items():
        ordered = sorted(hs, key=lambda h: h.start_date)
        for a, b in zip(ordered, ordered[1:]):
            if a.end_date is None or a.end_date > b.start_date:
                s.errors.append(
                    f"{node_id}: {a.name} y {b.name} aparecen como titulares al mismo tiempo; "
                    f"ponle 'hasta' al anterior"
                )


def known_nodes(conn: psycopg.Connection) -> dict[str, tuple[date, date | None]]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, valid_from, valid_to FROM node")
        return {r[0]: (r[1], r[2]) for r in cur.fetchall()}


def load(conn: psycopg.Connection, data_dir: Path) -> dict:
    """Load curated holders as person + tenure rows, refusing an invalid file."""
    from .people import normalize_name

    s = load_file(data_dir / "titulares.yaml", known_nodes(conn))
    if not s.ok:
        raise ValueError("titulares.yaml no válido:\n  " + "\n  ".join(s.errors))

    stats = {"holders": 0, "people_created": 0, "nodes": set()}
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO source (key, name, base_url, format) VALUES (%s,%s,%s,%s)
               ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name""",
            ("nombramientos", "Nombramientos curados (documento por titular)",
             "https://www.dof.gob.mx/", "html"),
        )
        # Curated holders own these rows: replacing them wholesale keeps the file
        # the single source of truth and makes a removal actually remove.
        cur.execute(
            "DELETE FROM tenure WHERE node_id NOT IN ('camara-diputados','senado')"
        )
        for h in s.holders:
            norm = normalize_name(h.name)
            cur.execute("SELECT id FROM person WHERE normalized_name = %s", (norm,))
            row = cur.fetchone()
            if row:
                pid = row[0]
            else:
                cur.execute(
                    "INSERT INTO person (full_name, normalized_name) VALUES (%s,%s) RETURNING id",
                    (h.name, norm),
                )
                pid = cur.fetchone()[0]
                stats["people_created"] += 1

            cur.execute(
                """INSERT INTO tenure
                     (person_id, node_id, role, start_date, end_date, contact_email)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                (pid, h.node_id, h.role, h.start_date, h.end_date, h.contact),
            )
            tenure_id = cur.fetchone()[0]
            stats["holders"] += 1
            stats["nodes"].add(h.node_id)

            # Provenance points at the appointment document. Where the ingestion
            # lane has already snapshotted that URL, the tenure gets its hash.
            cur.execute(
                """INSERT INTO provenance (record_table, record_id, snapshot_id)
                   SELECT 'tenure', %s, id FROM snapshot
                   WHERE url = %s ORDER BY captured_at DESC LIMIT 1""",
                (str(tenure_id), h.doc_url),
            )
        # A person exists in this record because they hold or held an office.
        # Remove one whose last tenure just disappeared — otherwise editing the
        # curated file leaves orphans behind that no query will ever surface.
        # Anyone still referenced elsewhere (a promise, say) is left alone, and
        # a former holder keeps their row because their closed tenure remains.
        cur.execute(
            """DELETE FROM person p
               WHERE NOT EXISTS (SELECT 1 FROM tenure t WHERE t.person_id = p.id)
                 AND NOT EXISTS (SELECT 1 FROM promise pr WHERE pr.actor_person = p.id)"""
        )
        stats["orphans_removed"] = cur.rowcount
    conn.commit()
    stats["nodes"] = len(stats["nodes"])
    return stats
