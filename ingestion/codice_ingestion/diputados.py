"""Cámara de Diputados (SITL) — who holds each seat.

Source: sitl.diputados.gob.mx, the Chamber's own legislative information system.
Two stages, both snapshotted before any parsing (R8):

  1. The roster page: 500 deputies with their SITL id, entity and district.
  2. One profile page per deputy: parliamentary group, institutional email,
     election principle, substitute.

We keep only what the project needs (CLAUDE.md Fase 2): name, party, term and
INSTITUTIONAL contact. Birth dates and other personal data present on the page
are deliberately not extracted.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from .http import fetch_raw, store_snapshot

LEGISLATURE = "LXVI"
BASE = f"https://sitl.diputados.gob.mx/{LEGISLATURE}_leg"
ROSTER_URL = f"{BASE}/listado_diputados_gpnp.php?tipot=TOTAL"
PROFILE_URL = BASE + "/curricula.php?dipt={sitl_id}"
SOURCE_KEY = "sitl_diputados"

# LXVI Legislature: 1 September 2024 - 31 August 2027 (CPEUM Art. 51, 65).
TERM_START = "2024-09-01"
TERM_END = "2027-08-31"

_ROW = re.compile(
    r'<a href="curricula\.php\?dipt=(\d+)"[^>]*>\s*\d+\s+(.*?)</a>.*?'
    r'<td[^>]*>\s*(.*?)\s*</td>.*?<td[^>]*>\s*(.*?)\s*</td>',
    re.S,
)


def _text(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_roster(raw: bytes) -> list[dict]:
    """Roster page -> one row per deputy. Never touches the network."""
    doc = raw.decode("utf-8", errors="replace")
    out = []
    for sitl_id, name, entity, district in _ROW.findall(doc):
        d = _text(district)
        m = re.search(r"(\d+)", d)
        out.append({
            "sitl_id": int(sitl_id),
            "name_listed": _text(name),  # "Apellido Apellido Nombre" order
            "entity": _text(entity),
            # The roster shows a bare number whose meaning depends on the
            # election principle; the profile page labels it, so that wins.
            "listed_number": int(m.group(1)) if m else None,
        })
    return out


def parse_profile(raw: bytes) -> dict:
    """Profile page -> party, institutional email, election principle."""
    doc = raw.decode("utf-8", errors="replace")

    party = None
    m = re.search(r'<img[^>]+src="images/([a-z0-9_]+)\.webp"[^>]*class="header-gp"', doc, re.I)
    if m:
        party = m.group(1).upper()

    full_name = None
    m = re.search(r"Dip\.\s*([^<\n]{4,120})", _text_blocks(doc))
    if m:
        full_name = m.group(1).strip()

    email = None
    m = re.search(r"[\w.\-]+@diputados\.gob\.mx", doc)
    if m:
        email = m.group(0).lower()

    text = _text_blocks(doc)

    principle = None
    m = re.search(r"Principio de elecci[óo]n:\s*([^\n]{3,40})", text)
    if m:
        principle = m.group(1).strip()

    # The profile labels the number itself: majority seats have a "Distrito",
    # proportional ones a "Circunscripción" (1-5, the plurinominal regions).
    # They are different things and must not be conflated — a proportional
    # deputy is not elected by an entity (CPEUM Art. 53).
    district = constituency = None
    m = re.search(r"Distrito:\s*(\d+)", text)
    if m:
        district = int(m.group(1))
    m = re.search(r"Circunscripci[óo]n:\s*(\d+)", text)
    if m:
        constituency = int(m.group(1))

    substitute = None
    m = re.search(r"Suplente:\s*([^\n]{4,120})", _text_blocks(doc))
    if m:
        substitute = m.group(1).strip()

    return {
        "full_name": full_name,
        "party": party,
        "contact_email": email,
        "election_principle": principle,
        "district": district,
        "constituency": constituency,
        "substitute": substitute,
    }


def _text_blocks(doc: str) -> str:
    t = re.sub(r"<(script|style).*?</\1>", " ", doc, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "\n", t))


def run(snapshots_dir: Path, out_dir: Path, limit: int | None = None) -> dict:
    """Fetch + snapshot + parse the whole chamber. Prints progress; slow by design."""
    snaps: list[dict] = []

    raw = fetch_raw(ROSTER_URL)
    snaps.append(store_snapshot(raw, snapshots_dir / "sitl_roster.html", ROSTER_URL, SOURCE_KEY, "text/html"))
    roster = parse_roster(raw)
    print(f"roster: {len(roster)} diputados", file=sys.stderr)

    people = []
    todo = roster[:limit] if limit else roster
    prof_dir = snapshots_dir / "sitl_profiles"
    for i, row in enumerate(todo, 1):
        url = PROFILE_URL.format(sitl_id=row["sitl_id"])
        praw = fetch_raw(url)
        snaps.append(store_snapshot(praw, prof_dir / f"dip_{row['sitl_id']}.html", url, SOURCE_KEY, "text/html"))
        people.append({**row, **parse_profile(praw), "term_start": TERM_START, "term_end": TERM_END})
        if i % 25 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diputados.json").write_text(json.dumps(people, ensure_ascii=False, indent=1))
    # Snapshot metadata is the provenance record; the roster snapshot goes first.
    (out_dir / "diputados_snapshots.json").write_text(json.dumps(snaps, ensure_ascii=False, indent=1))

    return {
        "deputies": len(people),
        "with_party": sum(1 for p in people if p["party"]),
        "with_email": sum(1 for p in people if p["contact_email"]),
        "snapshots": len(snaps),
    }
