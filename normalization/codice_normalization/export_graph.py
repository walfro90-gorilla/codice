"""Export the curated graph as static JSON for the web prototype.

Derived view (ADR-001): depth comes from BFS over currently-valid authority
edges; pos_geo comes from the node's territory centroid. The web computes its
own layout from level/depth — positions are never duplicated in the data.

Every node ships its legal basis WITH the snapshot hash and capture date that
backs it (R1), so a citation can be traced from the UI to a raw document.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import psycopg


def export(conn: psycopg.Connection, out_path: Path) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT n.id, n.name, n.level, n.node_type_key, nt.name, n.summary,
                      n.valid_from, n.valid_to, n.territory_key,
                      ST_X(t.centroid), ST_Y(t.centroid), t.name, p.population
               FROM node n
               LEFT JOIN node_type nt ON nt.key = n.node_type_key
               LEFT JOIN territory t ON t.inegi_key = n.territory_key
               LEFT JOIN population p ON p.inegi_key = n.territory_key AND p.census_year = 2020"""
        )
        nodes = {}
        for r in cur.fetchall():
            nodes[r[0]] = {
                "id": r[0], "name": r[1], "level": r[2],
                "node_type": r[3], "node_type_name": r[4],
                "summary": r[5],
                "valid_from": r[6].isoformat(), "valid_to": r[7].isoformat() if r[7] else None,
                "territory_key": r[8],
                "territory_name": r[11], "population": r[12],
                "pos_geo": {"lon": r[9], "lat": r[10]} if r[9] is not None else None,
                "legal_basis": [],
                "occupants": [],
            }

        # Legal basis with the provenance of the document it cites (R1).
        cur.execute(
            """SELECT lb.node_id, lb.document, lb.article, lb.url,
                      s.content_hash, s.captured_at
               FROM node_legal_basis lb LEFT JOIN snapshot s ON s.id = lb.snapshot_id
               ORDER BY lb.node_id, lb.document, lb.article"""
        )
        for nid, doc, art, url, h, cap in cur.fetchall():
            if nid in nodes:
                nodes[nid]["legal_basis"].append({
                    "document": doc, "article": art, "url": url,
                    "hash": h, "captured_at": cap.isoformat() if cap else None,
                })

        # Occupants (Fase 2): who holds each seat, with the party they were
        # elected under and their institutional contact. Aggregated per node so
        # the UI can show a summary without shipping 627 rows to every client.
        cur.execute(
            """SELECT t.node_id, p.full_name, t.role, t.party, t.contact_email,
                      t.start_date, t.end_date
               FROM tenure t JOIN person p ON p.id = t.person_id
               ORDER BY t.node_id, p.full_name"""
        )
        for nid, name, role, party, email, start, end in cur.fetchall():
            if nid in nodes:
                nodes[nid].setdefault("occupants", []).append({
                    "name": name, "role": role, "party": party,
                    "contact_email": email,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat() if end else None,
                })

        cur.execute("SELECT from_node, to_node, type, legal_basis FROM edge WHERE valid_to IS NULL")
        edges = [{"from": r[0], "to": r[1], "type": r[2], "legal_basis": r[3]} for r in cur.fetchall()]

        cur.execute(
            """SELECT DISTINCT s.url, s.captured_at, s.content_hash, src.name
               FROM snapshot s JOIN source src ON src.key = s.source_key"""
        )
        sources = [
            {"url": r[0], "captured_at": r[1].isoformat(), "hash": r[2], "source": r[3]}
            for r in cur.fetchall()
        ]

    children: dict[str, list[str]] = {}
    has_parent: set[str] = set()
    for e in edges:
        if e["type"] == "autoridad":
            children.setdefault(e["from"], []).append(e["to"])
            has_parent.add(e["to"])

    depth = {nid: 0 for nid in nodes if nid not in has_parent}
    q = deque(depth)
    while q:
        u = q.popleft()
        for v in children.get(u, []):
            if v not in depth or depth[u] + 1 < depth[v]:
                depth[v] = depth[u] + 1
                q.append(v)
    for nid, n in nodes.items():
        n["depth"] = depth.get(nid, 0)

    out = {
        "generated_from": "Códice — datos curados con fundamento legal citado",
        "license": "ODbL 1.0",
        "nodes": sorted(nodes.values(), key=lambda n: (n["depth"], n["id"])),
        "edges": edges,
        "sources": sources,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return {
        "nodes": len(nodes), "edges": len(edges), "sources": len(sources),
        "legal_basis_rows": sum(len(n["legal_basis"]) for n in nodes.values()),
        "occupants": sum(len(n["occupants"]) for n in nodes.values()),
        "with_geo": sum(1 for n in nodes.values() if n["pos_geo"]),
    }
