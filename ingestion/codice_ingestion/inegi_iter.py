"""INEGI Censo 2020 ITER ingestion.

Three separate, testable steps (project convention §15):
  fetch_raw()      - download bytes, touch nothing else
  store_snapshot() - persist raw bytes + sha256 + capture date (R8: never parse here)
  parse()          - read a STORED snapshot, emit territories + population rows

Output of parse() is written as CSV artifacts for the normalization lane;
this lane never talks to Postgres.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ITER_URL = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip"
ITER_MEMBER = "iter_00_cpv2020/conjunto_de_datos/conjunto_de_datos_iter_00CSV20.csv"
CENSUS_YEAR = 2020

_DMS = re.compile(r"^(\d+)°(\d+)'([\d.]+)\"\s*([NSWEO])$")


def dms_to_decimal(value: str) -> float | None:
    """'102°17\\'45.768" W' -> -102.29604666...  Returns None for blank."""
    value = value.strip()
    if not value:
        return None
    m = _DMS.match(value)
    if not m:
        raise ValueError(f"unparseable DMS coordinate: {value!r}")
    deg, minutes, seconds, hemi = m.groups()
    dec = int(deg) + int(minutes) / 60 + float(seconds) / 3600
    # O = Oeste (some INEGI files use W, some O)
    return -dec if hemi in ("W", "S", "O") else dec


def fetch_raw(url: str = ITER_URL, timeout: int = 600) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 - official source
        return resp.read()


def store_snapshot(raw: bytes, dest: Path, url: str = ITER_URL) -> dict:
    """Write raw bytes untouched; return snapshot metadata (R1)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return {
        "source_key": "inegi_censo",
        "url": url,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "content_type": "application/zip",
        "r2_key": f"inegi_censo/{datetime.now(timezone.utc):%Y-%m-%d}/iter_00_cpv2020_csv.zip",
        "local_path": str(dest),
    }


def parse(snapshot_path: Path, out_dir: Path) -> dict:
    """Read the stored ITER zip; write territories.csv and population.csv.

    Levels emitted: estado (MUN=000) and municipio (LOC=0000 totals).
    Municipio representative point = most populated localidad (usually the
    cabecera, but not always LOC=0001 — e.g. 24056 Villa de Arista is 0002).
    ponytail: localidad level (~300k rows) is skipped until a phase needs it;
    real polygon geometries arrive with the Marco Geoestadístico later.
    """
    territories: dict[str, dict] = {}
    population: list[tuple[str, int]] = []
    best_loc: dict[str, int] = {}  # municipio key -> POBTOT of the locality providing coords

    with zipfile.ZipFile(snapshot_path) as zf, zf.open(ITER_MEMBER) as fh:
        reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
        for row in reader:
            ent, mun, loc = row["ENTIDAD"], row["MUN"], row["LOC"]
            if ent == "00":  # national total
                continue
            if mun == "000" and loc == "0000":
                territories[ent] = {
                    "inegi_key": ent,
                    "level": "estado",
                    "name": row["NOM_ENT"],
                    "parent_key": "",
                    "lon": "",
                    "lat": "",
                }
                population.append((ent, int(row["POBTOT"])))
            elif loc == "0000":
                key = ent + mun
                territories[key] = {
                    "inegi_key": key,
                    "level": "municipio",
                    "name": row["NOM_MUN"],
                    "parent_key": ent,
                    "lon": "",
                    "lat": "",
                }
                population.append((key, int(row["POBTOT"])))
            else:  # a localidad: keep coords of the most populated one seen
                key = ent + mun
                pob = int(row["POBTOT"] or 0)
                if key in territories and pob > best_loc.get(key, -1):
                    lon = dms_to_decimal(row["LONGITUD"])
                    lat = dms_to_decimal(row["LATITUD"])
                    if lon is not None and lat is not None:
                        best_loc[key] = pob
                        territories[key]["lon"] = f"{lon:.6f}"
                        territories[key]["lat"] = f"{lat:.6f}"

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "territories.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["inegi_key", "level", "name", "parent_key", "lon", "lat"])
        w.writeheader()
        w.writerows(territories.values())
    with (out_dir / "population.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["inegi_key", "census_year", "population"])
        w.writerows((k, CENSUS_YEAR, p) for k, p in population)

    estados = sum(1 for t in territories.values() if t["level"] == "estado")
    municipios = sum(1 for t in territories.values() if t["level"] == "municipio")
    with_coords = sum(1 for t in territories.values() if t["lon"])
    return {"estados": estados, "municipios": municipios, "with_coords": with_coords}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    snap = root / "ingestion" / "snapshots" / "iter_00_cpv2020_csv.zip"
    cmd = sys.argv[1] if len(sys.argv) > 1 else "parse"
    if cmd == "fetch":
        raw = fetch_raw()
        meta = store_snapshot(raw, snap)
        print(json.dumps(meta, indent=2))
    elif cmd == "parse":
        stats = parse(snap, root / "ingestion" / "parsed")
        print(json.dumps(stats))
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
