"""Snapshot the appointment documents that back curated office-holders.

The curated file carries a URL per holder; this downloads each one and stores
it with its hash and capture date, so a tenure's provenance is a real archived
document and not just a link that may rot (ADR-018).

It reads the same YAML the normalization lane validates, but only takes the
URLs from it: what a name means is that lane's problem, not this one (R8).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from .http import fetch_raw, store_snapshot

SOURCE_KEY = "nombramientos"


def urls_from(data_dir: Path) -> list[tuple[str, str]]:
    """[(url, holder name)] — the name is only used for progress output."""
    f = data_dir / "titulares.yaml"
    if not f.exists():
        return []
    doc = yaml.safe_load(f.read_text()) or {}
    out = []
    for e in doc.get("titulares") or []:
        nom = (e or {}).get("nombramiento") or {}
        url = (nom.get("url") or "").strip()
        if url:
            out.append((url, (e.get("nombre") or "?").strip()))
    return out


def _filename(url: str) -> str:
    """A stable, readable filename per document; the hash guarantees identity."""
    m = re.search(r"codigo=(\d+)", url)
    if m:
        return f"dof_{m.group(1)}.html"
    return "nombramiento_" + hashlib.sha256(url.encode()).hexdigest()[:16] + ".html"


def run(data_dir: Path, snapshots_dir: Path, out_dir: Path) -> dict:
    pairs = urls_from(data_dir)
    if not pairs:
        print("no hay nombramientos curados todavía", file=sys.stderr)
        return {"documents": 0, "snapshots": 0, "failed": []}

    snaps, failed = [], []
    dest_dir = snapshots_dir / "nombramientos"
    for i, (url, who) in enumerate(pairs, 1):
        try:
            raw = fetch_raw(url, timeout=90)
            snaps.append(store_snapshot(raw, dest_dir / _filename(url), url, SOURCE_KEY, "text/html"))
            print(f"  {i}/{len(pairs)} {who}", file=sys.stderr)
        except Exception as e:  # a dead link is data too: report it, do not hide it
            failed.append({"url": url, "holder": who, "error": str(e)[:160]})
            print(f"  {i}/{len(pairs)} {who} — FALLÓ: {str(e)[:90]}", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "nombramientos_snapshots.json").write_text(json.dumps(snaps, ensure_ascii=False, indent=1))
    if failed:
        (out_dir / "nombramientos_fallidos.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1))
    return {"documents": len(pairs), "snapshots": len(snaps), "failed": failed}
