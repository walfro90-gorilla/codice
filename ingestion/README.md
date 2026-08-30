# /ingestion — L1 Ingesta cruda

Scrapers Python + assets de Dagster. **Esta capa nunca parsea** (R8): baja el archivo tal cual, calcula sha256 y lo sube a R2 con fecha de captura.

Todo scraper implementa tres pasos separados y testeables:

```
fetch_raw() → store_snapshot() → parse()
```

(`parse()` vive aquí como paso invocable pero corre en el carril de normalización; la salida de este carril son snapshots inmutables.)

La salida se valida con `SnapshotMeta` de `codice-contracts` antes de cruzar la frontera.

## Ingesta implementada

| Módulo | Fuente | Salida |
|---|---|---|
| `codice_ingestion/inegi_iter.py` | INEGI Censo 2020 (ITER) | `parsed/territories.csv`, `parsed/population.csv` — 32 entidades, 2,469 municipios con punto representativo y población |

```bash
python3 codice_ingestion/inegi_iter.py fetch   # descarga + snapshot con hash
python3 codice_ingestion/inegi_iter.py parse   # lee el snapshot guardado, nunca la red
python3 test_inegi_iter.py                     # conversión de coordenadas DMS
```

Los snapshots crudos viven en `snapshots/` (fuera de git) y su metadata —URL, fecha, sha256, clave R2 prevista— en `snapshots.json`, que sí se versiona.
