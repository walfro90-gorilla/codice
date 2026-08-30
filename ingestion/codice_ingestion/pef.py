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
CUENTA_PUBLICA_MANIFEST = f"{BASE}/work/models/PTP/NPTP/PTP_Datos_Abiertos/data/cuenta_publica/cuenta_publica.json"

# The Cuenta Pública publishes the whole spending cycle in one row, so one file
# yields several stages. Column names are NOT stable across years: 2024 writes
# MONTO_EJERCIDO, 2025 writes " Ejercido_Bruto " (with surrounding spaces), and
# 2022-2023 publish no spent column at all. Each stage therefore lists the
# spellings seen, and a stage simply does not exist for a year that omits it —
# inventing one would be worse than reporting its absence (R6).
STAGE_COLUMN_ALIASES = {
    "aprobado":   ("MONTO_APROBADO", "ORIGINAL_BRUTO", "APROBADO"),
    "modificado": ("MONTO_MODIFICADO", "MODIFICADO_BRUTO", "MODIFICADO"),
    "devengado":  ("MONTO_DEVENGADO", "DEVENGADO"),
    "pagado":     ("MONTO_PAGADO", "PAGADO"),
    "ejercido":   ("MONTO_EJERCIDO", "EJERCIDO_BRUTO", "EJERCIDO"),
}

# Ramo and entity keys move too: 2025 uses short names (R, EF).
RAMO_ID_ALIASES = ("ID_RAMO", "R")
ENTITY_ID_ALIASES = ("ID_ENTIDAD_FEDERATIVA", "EF")
RAMO_DESC_ALIASES = ("DESC_RAMO", "RAMO_DESC")


def _resolve_columns(fieldnames: list[str]) -> dict:
    """Map this file's actual headers onto our stable names.

    Headers are normalised (trimmed, upper-cased) before matching because at
    least one published year pads them with spaces.
    """
    norm = {(c or "").strip().upper(): c for c in fieldnames}

    def pick(aliases):
        for a in aliases:
            if a in norm:
                return norm[a]
        return None

    return {
        "ramo_id": pick(RAMO_ID_ALIASES),
        "ramo_desc": pick(RAMO_DESC_ALIASES),
        "entity": pick(ENTITY_ID_ALIASES),
        "stages": {st: pick(al) for st, al in STAGE_COLUMN_ALIASES.items() if pick(al)},
    }
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


def parse_cuenta_publica(raw: bytes, fiscal_year: int) -> dict:
    """Aggregate the Cuenta Pública to (ramo, territory) totals PER STAGE.

    Same keys as the PEF (ID_RAMO, ID_ENTIDAD_FEDERATIVA), so approved and
    spent land in the same table and can be read side by side.
    """
    txt = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(txt))
    cols = _resolve_columns(reader.fieldnames or [])
    if not cols["ramo_id"]:
        raise ValueError(f"{fiscal_year}: no ramo column found in {reader.fieldnames}")
    if not cols["stages"]:
        raise ValueError(f"{fiscal_year}: no amount columns found in {reader.fieldnames}")

    ramos: dict[int, str] = {}
    totals: dict[tuple[str, int, str | None, str], float] = defaultdict(float)
    unreadable: list[str] = []
    rows = 0
    blank_rows = 0
    for row in reader:
        rows += 1
        # Some published files are Excel exports padded to the sheet's row limit
        # (1,048,576). Those trailing rows are entirely empty — skipped, but
        # COUNTED, so "we ignored 828,067 rows" is never a silent claim.
        if not (row.get(cols["ramo_id"]) or "").strip():
            if not any((v or "").strip() for v in row.values()):
                blank_rows += 1
                continue
            unreadable.append("fila sin ramo con datos")
            continue
        ramo_id = int(row[cols["ramo_id"]])
        ramos.setdefault(ramo_id, (row.get(cols["ramo_desc"]) or "").strip())

        ent = (row.get(cols["entity"]) or "").strip() if cols["entity"] else ""
        if ent in NON_TERRITORIAL:
            key, scope = None, NON_TERRITORIAL[ent]
        elif ent.isdigit() and 1 <= int(ent) <= 32:
            key, scope = f"{int(ent):02d}", "entidad"
        else:
            key, scope = None, "no_distribuible"

        for stage, col in cols["stages"].items():
            value = _amount(row.get(col))
            if value is None:
                unreadable.append(row[col])
                continue
            totals[(stage, ramo_id, key, scope)] += value

    allocations = [
        {"stage": st, "ramo_id": r, "territory_key": k, "scope": sc, "amount_mxn": round(v, 2)}
        for (st, r, k, sc), v in sorted(totals.items(), key=lambda t: (t[0][0], t[0][1], t[0][2] or ""))
    ]
    per_stage = defaultdict(float)
    for a in allocations:
        per_stage[a["stage"]] += a["amount_mxn"]
    return {
        "fiscal_year": fiscal_year,
        "rows_read": rows,
        "blank_rows_skipped": blank_rows,
        "data_rows": rows - blank_rows,
        "ramos": [{"id": k, "name": v} for k, v in sorted(ramos.items())],
        "allocations": allocations,
        "unreadable_cells": len(unreadable),
        "unreadable_samples": sorted(set(unreadable))[:5],
        "totals_by_stage": {k: round(v, 2) for k, v in sorted(per_stage.items())},
        # Which stages this year actually publishes; absent is not zero.
        "stages_published": sorted(cols["stages"]),
    }


def run_cuenta_publica(snapshots_dir: Path, out_dir: Path, years: list[int] | None = None) -> dict:
    manifest_raw = fetch_raw(CUENTA_PUBLICA_MANIFEST, timeout=60)
    snaps = [store_snapshot(manifest_raw, snapshots_dir / "cp_manifest.json",
                            CUENTA_PUBLICA_MANIFEST, SOURCE_KEY, "application/json")]
    urls = available_years(manifest_raw)
    print(f"años publicados: {sorted(urls)}", file=sys.stderr)

    wanted = years or [max(urls)]
    parsed = []
    for year in wanted:
        if year not in urls:
            print(f"  {year}: no publicado, se omite", file=sys.stderr)
            continue
        raw = fetch_raw(urls[year], timeout=900)
        snap = store_snapshot(raw, snapshots_dir / f"cuenta_publica_{year}.csv", urls[year], SOURCE_KEY, "text/csv")
        snaps.append(snap)
        result = parse_cuenta_publica(raw, year)
        result["snapshot_sha256"] = snap["sha256"]
        parsed.append(result)
        t = result["totals_by_stage"]
        print(f"  {year}: {result['data_rows']:,} filas con datos "
              f"({result['blank_rows_skipped']:,} vacías) | aprobado {t.get('aprobado',0):,.0f} "
              f"| ejercido {t.get('ejercido',0):,.0f}", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cuenta_publica.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=1))
    (out_dir / "cuenta_publica_snapshots.json").write_text(json.dumps(snaps, ensure_ascii=False, indent=1))
    return {"years": [p["fiscal_year"] for p in parsed], "snapshots": len(snaps)}


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
