"""Presupuesto de Egresos de la Federación (Transparencia Presupuestaria).

The published CSV is line-item detail: ~130k rows a year, down to the specific
budget line of a specific programme. We snapshot it whole (R8) and aggregate to
the question the project asks — how much per branch, per entity, per year.

Discovering the download URL is not guesswork: the site's open-data section is
a JavaScript app that fetches a manifest per dataset, and the manifest carries
the real file URLs plus every year available. We read the manifest.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

from .http import fetch_raw, store_snapshot

BASE = "https://www.transparenciapresupuestaria.gob.mx"
MANIFEST = f"{BASE}/work/models/PTP/NPTP/PTP_Datos_Abiertos/data/PEF/PEF.json"
DICTIONARY = f"{BASE}/work/models/PTP/DatosAbiertos/Diccionarios/Diccionario_PEF.csv"
SOURCE_KEY = "transparencia_presupuestaria"

# The PEF publishes two buckets that are not federal entities and have no
# INEGI key. Dropping them would silently lose money; inventing a territory
# would be worse. They are kept with an explicit scope (R6).
NON_TERRITORIAL = {"33": "extranjero", "34": "no_distribuible"}


def available_years(manifest_raw: bytes) -> dict[int, str]:
    """{year: csv_url} straight from the site's own manifest."""
    out: dict[int, str] = {}
    for entry in json.loads(manifest_raw).get("datos", []):
        year = int(entry["anio"])
        for d in entry.get("descarga", []):
            if d.get("formato") == "csv":
                out[year] = BASE + d["url"]
    return out


# Accounting zero, written as a dash in several published years.
_ZERO_TOKENS = {"", "-", "--", "0", "n/a", "na", "nd", "n.d."}


def _amount(raw_value: str | None) -> float | None:
    """Parse an amount, or return None if the cell is not a number.

    Amounts are not written the same way every year: recent files publish a
    bare number, older ones use thousands separators ("259,000,000.00"), and
    some write an accounting dash for zero. Returning None instead of guessing
    lets the caller COUNT what it could not read — silently coercing an
    unreadable cell to zero is how a budget loses money without anyone noticing.
    """
    if raw_value is None:
        return 0.0
    v = raw_value.strip().replace(" ", "").replace("$", "")
    if v.lower() in _ZERO_TOKENS:
        return 0.0
    if "," in v and "." in v:
        v = v.replace(",", "")           # 1,234.56
    elif "," in v:
        _, _, tail = v.rpartition(",")
        v = v.replace(",", "") if len(tail) == 3 else v.replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def parse(raw: bytes, fiscal_year: int) -> dict:
    """Aggregate the line-item CSV to (ramo, territory) totals.

    Returns ramos, allocations and the grand total, so the caller can check the
    aggregate against the published headline figure before trusting it.
    """
    txt = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(txt))
    amount_col = f"MONTO_PEF_{fiscal_year}"

    ramos: dict[int, str] = {}
    totals: dict[tuple[int, str | None, str], float] = defaultdict(float)
    unreadable: list[str] = []
    rows = 0
    for row in reader:
        rows += 1
        if amount_col not in row:  # older files name the column differently
            amount_col = next(c for c in row if c and c.startswith("MONTO"))
        ramo_id = int(row["ID_RAMO"])
        ramos.setdefault(ramo_id, row["DESC_RAMO"].strip())

        ent = (row.get("ID_ENTIDAD_FEDERATIVA") or "").strip()
        if ent in NON_TERRITORIAL:
            key, scope = None, NON_TERRITORIAL[ent]
        elif ent.isdigit() and 1 <= int(ent) <= 32:
            key, scope = f"{int(ent):02d}", "entidad"  # INEGI key, zero-padded (R7)
        else:
            key, scope = None, "no_distribuible"

        value = _amount(row[amount_col])
        if value is None:
            unreadable.append(row[amount_col])
            continue
        totals[(ramo_id, key, scope)] += value

    allocations = [
        {"ramo_id": r, "territory_key": k, "scope": s, "amount_mxn": round(v, 2)}
        for (r, k, s), v in sorted(totals.items(), key=lambda t: (t[0][0], t[0][1] or ""))
    ]
    return {
        "fiscal_year": fiscal_year,
        "rows_read": rows,
        # Never silently zero a cell we could not read (R6)
        "unreadable_cells": len(unreadable),
        "unreadable_samples": sorted(set(unreadable))[:5],
        "ramos": [{"id": k, "name": v} for k, v in sorted(ramos.items())],
        "allocations": allocations,
        "total_mxn": round(sum(a["amount_mxn"] for a in allocations), 2),
    }


def run(snapshots_dir: Path, out_dir: Path, years: list[int] | None = None) -> dict:
    manifest_raw = fetch_raw(MANIFEST, timeout=60)
    snaps = [store_snapshot(manifest_raw, snapshots_dir / "pef_manifest.json", MANIFEST, SOURCE_KEY, "application/json")]
    urls = available_years(manifest_raw)
    print(f"años publicados: {sorted(urls)}", file=sys.stderr)

    wanted = years or [max(urls)]
    parsed = []
    for year in wanted:
        if year not in urls:
            print(f"  {year}: no publicado, se omite", file=sys.stderr)
            continue
        raw = fetch_raw(urls[year], timeout=600)
        snap = store_snapshot(raw, snapshots_dir / f"PEF_{year}.csv", urls[year], SOURCE_KEY, "text/csv")
        snaps.append(snap)
        result = parse(raw, year)
        result["snapshot_sha256"] = snap["sha256"]
        parsed.append(result)
        print(f"  {year}: {result['rows_read']:,} filas -> {len(result['allocations'])} agregados, "
              f"{result['total_mxn']:,.0f} MXN", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pef.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=1))
    (out_dir / "pef_snapshots.json").write_text(json.dumps(snaps, ensure_ascii=False, indent=1))
    return {"years": [p["fiscal_year"] for p in parsed], "snapshots": len(snaps)}
