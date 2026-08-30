"""Load legislators into canonical Postgres as person + tenure rows (Fase 2).

Name normalization here is the deterministic first stage of entity resolution
(ADR-006): lowercase, unaccented, punctuation stripped. It is used to detect
same-person collisions WITHIN one intake, never to merge across sources —
cross-source merging goes through entity_match_candidate with a human review.

Seats come from the curated structure: a deputy holds a seat in
`camara-diputados`, a senator in `senado`. The tenure carries the term dates
of the legislature, so asking "who held this seat on date X" is a plain
temporal query (R9).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import psycopg

DEPUTY_NODE = "camara-diputados"
SENATE_NODE = "senado"

# Institutional email domains we accept; anything else is dropped rather than
# stored, since only institutional contact belongs in the record.
INSTITUTIONAL_DOMAINS = ("@diputados.gob.mx", "@senado.gob.mx")


def normalize_name(name: str) -> str:
    """'Álvarez Lima, José Antonio' -> 'alvarez lima jose antonio'.

    ñ collapses to n on purpose: official sources mangle it often (the SITL
    profile pages themselves serve 'Secretarí­a' with broken encoding), so a
    normalizer that preserved ñ would fail to match a clean source against a
    mojibake one. Collapsing favours recall, which is safe here because a
    match is only ever a candidate for human review, never an automatic
    merge (R3).
    """
    s = unicodedata.normalize("NFD", name.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace(",", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Each chamber names the same party differently (the Chamber writes VERDE, the
# Senate PVEM). Normalizing to one key is what makes a cross-chamber query
# possible at all; the raw value stays in the snapshot.
PARTY_ALIASES = {
    "VERDE": "PVEM",
    "PVEM": "PVEM",
    "MORENA": "MORENA",
    "PAN": "PAN",
    "PRI": "PRI",
    "PT": "PT",
    "MC": "MC",
    "SG": None,  # "Sin Grupo" is the absence of a party, not a party
}


def canonical_party(raw: str | None) -> str | None:
    if not raw:
        return None
    return PARTY_ALIASES.get(raw.strip().upper(), raw.strip().upper())


# Sources name the entity in prose and with short names ("Coahuila"), while the
# INEGI catalogue uses the official one ("Coahuila de Zaragoza"). Resolution is
# deterministic: exact normalized match, then prefix against the official name.
NATIONAL_CONSTITUENCY = "lista nacional"


def _norm_place(name: str) -> str:
    s = unicodedata.normalize("NFD", name.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()


def resolve_territory(name: str | None, catalogue: dict[str, str]) -> str | None:
    """Entity name -> INEGI key (R7). None means the national constituency.

    `catalogue` maps normalized official names to keys. A None result for a
    proportional-representation seat is MEANINGFUL, not missing data: those
    seats are elected nationwide and represent no entity (ADR-019).
    """
    if not name:
        return None
    n = _norm_place(name)
    if not n or n == NATIONAL_CONSTITUENCY:
        return None
    if n in catalogue:
        return catalogue[n]
    # "Estado de México" -> "México"; "Coahuila" -> "Coahuila de Zaragoza"
    n2 = re.sub(r"^estado de ", "", n)
    if n2 in catalogue:
        return catalogue[n2]
    hits = [k for official, k in catalogue.items() if official.startswith(n2 + " ") or official == n2]
    return hits[0] if len(hits) == 1 else None


def territory_catalogue(conn: psycopg.Connection) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute("SELECT inegi_key, name FROM territory WHERE level = 'estado'")
        return {_norm_place(name): key for key, name in cur.fetchall()}


def _institutional(email: str | None) -> str | None:
    if email and email.lower().endswith(INSTITUTIONAL_DOMAINS):
        return email.lower()
    return None


def load_snapshots(conn: psycopg.Connection, snapshot_files: list[Path]) -> int:
    """Register the scraper's snapshots so tenures can cite them (R1)."""
    n = 0
    with conn.cursor() as cur:
        for key, name, url, fmt in (
            ("sitl_diputados", "Cámara de Diputados — SITL", "https://sitl.diputados.gob.mx/", "html"),
            ("senado_directorio", "Senado de la República — Directorio", "https://www.senado.gob.mx/", "html"),
        ):
            cur.execute(
                """INSERT INTO source (key, name, base_url, format) VALUES (%s,%s,%s,%s)
                   ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name""",
                (key, name, url, fmt),
            )
        for f in snapshot_files:
            if not f.exists():
                continue
            for s in json.loads(f.read_text()):
                cur.execute(
                    """INSERT INTO snapshot (source_key, url, captured_at, content_hash, r2_key, content_type)
                       VALUES (%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (content_hash, url) DO NOTHING""",
                    (s["source_key"], s["url"], s["captured_at"], s["sha256"], s["r2_key"], s["content_type"]),
                )
                n += cur.rowcount
    conn.commit()
    return n


def _upsert_person(cur, full_name: str) -> str:
    """Return the id of the person, creating them if this intake hasn't seen them.

    Matching is by normalized name WITHIN this source only. Two different people
    who share a normalized name would collide, so the caller reports collisions
    and a human resolves them (R3) — we never silently merge.
    """
    norm = normalize_name(full_name)
    cur.execute("SELECT id FROM person WHERE normalized_name = %s", (norm,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO person (full_name, normalized_name) VALUES (%s,%s) RETURNING id",
        (full_name, norm),
    )
    return cur.fetchone()[0]


def load_legislators(conn: psycopg.Connection, parsed_dir: Path) -> dict:
    stats = {"deputies": 0, "senators": 0, "people": 0, "name_collisions": [],
             "unresolved_entities": [], "national_constituency": 0}
    seen_norm: dict[str, str] = {}
    places = territory_catalogue(conn)

    with conn.cursor() as cur:
        # Curated structure must exist first — a tenure without its seat is meaningless.
        cur.execute("SELECT id FROM node WHERE id IN (%s,%s)", (DEPUTY_NODE, SENATE_NODE))
        found = {r[0] for r in cur.fetchall()}
        missing = {DEPUTY_NODE, SENATE_NODE} - found
        if missing:
            raise ValueError(f"missing curated nodes: {missing}; load Fase 1 data first")

        # Re-running replaces this intake's tenures rather than duplicating them.
        cur.execute("DELETE FROM tenure WHERE node_id IN (%s,%s)", (DEPUTY_NODE, SENATE_NODE))

        dip_file = parsed_dir / "diputados.json"
        if dip_file.exists():
            for d in json.loads(dip_file.read_text()):
                name = d.get("full_name") or d["name_listed"]
                norm = normalize_name(name)
                if norm in seen_norm:
                    stats["name_collisions"].append(name)
                pid = _upsert_person(cur, name)
                seen_norm[norm] = pid
                # A majority seat represents an entity's district; a proportional
                # seat is elected in one of the five plurinominal constituencies
                # and represents no entity (CPEUM Art. 53, ADR-019).
                role = f"diputación federal · {d.get('election_principle') or 'sin dato'}"
                if d.get("district") and d.get("entity"):
                    role += f" · {d['entity']} distrito {d['district']}"
                elif d.get("constituency"):
                    role += f" · circunscripción {d['constituency']}"
                # Only majority seats carry a territory: a proportional deputy is
                # elected nationwide-by-region, not by an entity (ADR-019).
                tkey = resolve_territory(d.get("entity"), places) if d.get("district") else None
                if d.get("district") and d.get("entity") and not tkey:
                    stats["unresolved_entities"].append(d["entity"])
                if not tkey:
                    stats["national_constituency"] += 1
                cur.execute(
                    """INSERT INTO tenure (person_id, node_id, role, party, start_date, end_date,
                                           contact_email, territory_key)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (pid, DEPUTY_NODE, role, canonical_party(d.get("party")), d["term_start"], d["term_end"],
                     _institutional(d.get("contact_email")), tkey),
                )
                stats["deputies"] += 1

        sen_file = parsed_dir / "senadores.json"
        if sen_file.exists():
            for s in json.loads(sen_file.read_text()):
                name = s["full_name"]
                norm = normalize_name(name)
                if norm in seen_norm:
                    stats["name_collisions"].append(name)
                pid = _upsert_person(cur, name)
                seen_norm[norm] = pid
                role = f"senaduría · {s.get('election_principle') or 'sin dato'}"
                if s.get("entity"):
                    role += f" · {s['entity']}"
                tkey = resolve_territory(s.get("entity"), places)
                if s.get("entity") and not tkey:
                    if _norm_place(s["entity"]) == NATIONAL_CONSTITUENCY:
                        stats["national_constituency"] += 1
                    else:
                        stats["unresolved_entities"].append(s["entity"])
                cur.execute(
                    """INSERT INTO tenure (person_id, node_id, role, party, start_date, end_date,
                                           contact_email, territory_key)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (pid, SENATE_NODE, role, canonical_party(s.get("party")), s["term_start"], s["term_end"],
                     _institutional(s.get("contact_email")), tkey),
                )
                stats["senators"] += 1

        cur.execute("SELECT count(*) FROM person")
        stats["people"] = cur.fetchone()[0]
    conn.commit()
    return stats


def link_tenure_provenance(conn: psycopg.Connection) -> int:
    """Point every tenure at the snapshot of the page it came from (R1)."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM provenance WHERE record_table = 'tenure'")
        cur.execute(
            """INSERT INTO provenance (record_table, record_id, snapshot_id)
               SELECT 'tenure', t.id::text, s.id
               FROM tenure t
               JOIN LATERAL (
                 SELECT id FROM snapshot
                 WHERE source_key = CASE WHEN t.node_id = %s THEN 'sitl_diputados' ELSE 'senado_directorio' END
                 ORDER BY captured_at DESC LIMIT 1
               ) s ON true
               WHERE t.node_id IN (%s, %s)""",
            (DEPUTY_NODE, DEPUTY_NODE, SENATE_NODE),
        )
        n = cur.rowcount
    conn.commit()
    return n
