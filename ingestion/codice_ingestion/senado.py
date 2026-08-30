"""Senado de la República — who holds each seat.

Source: senado.gob.mx directory listings. Two pages carry everything we need,
so this scraper makes two requests, not 128:

  - por_grupo_parlamentario: name, party, entity, institutional contact
  - por_principio_de_eleccion: how each senator got the seat (MR / PM / RP)

As with the Chamber, only institutional contact is extracted.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from .http import fetch_raw, store_snapshot

LEGISLATURE = "66"
BASE = f"https://www.senado.gob.mx/{LEGISLATURE}/senadores"
GROUP_URL = f"{BASE}/por_grupo_parlamentario"
PRINCIPLE_URL = f"{BASE}/por_principio_de_eleccion"
SOURCE_KEY = "senado_directorio"

# LXVI Legislature: senators serve 2024-2030 (CPEUM Art. 56, 58).
TERM_START = "2024-09-01"
TERM_END = "2030-08-31"

_CARD = re.compile(r'senado\.gob\.mx/66/senador/(\d+)', re.I)


def _blocks(doc: str) -> str:
    t = re.sub(r"<(script|style).*?</\1>", " ", doc, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "\n", t))


def _cards(doc: str) -> list[tuple[int, str]]:
    """Split the page into (senator_id, html_block) using the detail links.

    A card links the same senator several times (portrait, name, detail), and
    all of its content follows the FIRST of those links. So a block runs from
    one id's first link to the next id's first link — no look-behind: reaching
    backwards lands inside the previous card and steals its name, which silently
    produced one senator under two ids.
    """
    hits = [(int(m.group(1)), m.start()) for m in _CARD.finditer(doc)]
    firsts: list[tuple[int, int]] = []
    seen = set()
    for sid, pos in hits:
        if sid not in seen:
            seen.add(sid)
            firsts.append((sid, pos))
    out = []
    for i, (sid, pos) in enumerate(firsts):
        end = firsts[i + 1][1] if i + 1 < len(firsts) else min(pos + 6000, len(doc))
        out.append((sid, doc[pos:end]))
    return out


def _section_map(doc: str, pattern: str, label: callable) -> dict[int, str]:
    """Assign each senator the value of the section heading they appear under.

    The listing pages are grouped documents: a heading opens a section and every
    card after it belongs to that section until the next heading. That grouping
    is the page's own semantics, so it is more reliable than per-card markup —
    the last card on the page has no trailing party graphic at all.
    """
    marks = [
        (m.start(), html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip())
        for m in re.finditer(r"<h[1-4][^>]*>(.*?)</h[1-4]>", doc, re.S)
    ]
    keep = [(pos, t) for pos, t in marks if re.search(pattern, t, re.I)]
    out: dict[int, str] = {}
    for m in _CARD.finditer(doc):
        sid = int(m.group(1))
        if sid in out:
            continue
        current = None
        for pos, title in keep:
            if pos < m.start():
                current = title
        if current:
            out[sid] = label(current)
    return out


_PARTY_BY_GROUP = (
    (r"\bmorena\b", "MORENA"),
    (r"acci[óo]n nacional", "PAN"),
    (r"revolucionario institucional", "PRI"),
    (r"verde ecologista", "PVEM"),
    (r"del trabajo", "PT"),
    (r"movimiento ciudadano", "MC"),
    (r"sin grupo", "SG"),
)


def _party_from_group(heading: str) -> str:
    for pat, key in _PARTY_BY_GROUP:
        if re.search(pat, heading, re.I):
            return key
    return heading.strip()


# A card may also list the senator's private secretary with THEIR email. That
# belongs to a third party, so it is filtered out rather than recorded: the
# senator's own address stands alone in its element, the secretary's follows a
# "Secretari…: … E-mail:" label.
_STAFF_LABEL = re.compile(r"(secretari[oa][^<]{0,120}|e-?mail\s*:)\s*$", re.I)


def _own_email(block: str) -> str | None:
    """The legislator's institutional address, never their staff's."""
    for m in re.finditer(r"[\w.\-]+@senado\.gob\.mx", block):
        preceding = html.unescape(re.sub(r"<[^>]+>", " ", block[max(0, m.start() - 160) : m.start()]))
        if _STAFF_LABEL.search(preceding.rstrip()):
            continue
        return m.group(0).lower()
    return None


def parse_group_page(raw: bytes) -> dict[int, dict]:
    """Party page -> {senator_id: {name, party, entity, contact_email}}."""
    doc = raw.decode("utf-8", errors="replace")
    by_group = _section_map(doc, r"grupo parlamentario", _party_from_group)
    people: dict[int, dict] = {}
    for sid, block in _cards(doc):
        text = _blocks(block)
        name = None
        m = re.search(r"Sen\.\s*([^\n]{4,120})", text)
        if m:
            name = m.group(1).strip()
        email = _own_email(block)
        # Section first (the page IS grouped by party); per-card graphic as fallback.
        party = by_group.get(sid)
        if not party:
            m = re.search(r'class="fill([A-Za-zÁÉÍÓÚÑ]{2,12})"', block)
            if m:
                party = m.group(1).upper()
        # The entity is the short line right before the "Sen. X" heading.
        entity = None
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for j, l in enumerate(lines):
            if l.startswith("Sen.") and j > 0:
                cand = lines[j - 1]
                if 3 < len(cand) < 40 and not cand.startswith(("Av.", "Ext.", "55 ")) and "@" not in cand:
                    entity = cand
                break
        if name:
            people[sid] = {
                "senado_id": sid, "full_name": name, "party": party,
                "entity": entity, "contact_email": email,
            }
    return people


def parse_principle_page(raw: bytes) -> dict[int, str]:
    """Election-principle page -> {senator_id: 'Mayoría Relativa' | ...}."""
    doc = raw.decode("utf-8", errors="replace")
    return _section_map(
        doc,
        r"(mayor[íi]a relativa|primera minor[íi]a|representaci[óo]n proporcional)",
        _principle_label,
    )


def _principle_label(heading: str) -> str:
    """'...electos por el principio de mayoría relativa (63)' -> 'Mayoría Relativa'."""
    for pat, label in (
        (r"mayor[íi]a relativa", "Mayoría Relativa"),
        (r"primera minor[íi]a", "Primera Minoría"),
        (r"representaci[óo]n proporcional", "Representación Proporcional"),
    ):
        if re.search(pat, heading, re.I):
            return label
    return heading.strip()


def run(snapshots_dir: Path, out_dir: Path) -> dict:
    snaps = []
    raw_group = fetch_raw(GROUP_URL)
    snaps.append(store_snapshot(raw_group, snapshots_dir / "senado_grupos.html", GROUP_URL, SOURCE_KEY, "text/html"))
    raw_prin = fetch_raw(PRINCIPLE_URL)
    snaps.append(store_snapshot(raw_prin, snapshots_dir / "senado_principio.html", PRINCIPLE_URL, SOURCE_KEY, "text/html"))

    people = parse_group_page(raw_group)
    principles = parse_principle_page(raw_prin)
    for sid, p in people.items():
        p["election_principle"] = principles.get(sid)
        p["term_start"] = TERM_START
        p["term_end"] = TERM_END

    rows = sorted(people.values(), key=lambda p: p["full_name"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "senadores.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    (out_dir / "senadores_snapshots.json").write_text(json.dumps(snaps, ensure_ascii=False, indent=1))
    print(f"senadores: {len(rows)}", file=sys.stderr)
    return {
        "senators": len(rows),
        "with_party": sum(1 for p in rows if p["party"]),
        "with_entity": sum(1 for p in rows if p["entity"]),
        "with_email": sum(1 for p in rows if p["contact_email"]),
        "with_principle": sum(1 for p in rows if p["election_principle"]),
    }
