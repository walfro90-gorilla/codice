# /ingestion — L1 Ingesta cruda

Scrapers Python + assets de Dagster. **Esta capa nunca parsea** (R8): baja el archivo tal cual, calcula sha256 y lo sube a R2 con fecha de captura.

Todo scraper implementa tres pasos separados y testeables:

```
fetch_raw() → store_snapshot() → parse()
```

(`parse()` vive aquí como paso invocable pero corre en el carril de normalización; la salida de este carril son snapshots inmutables.)

La salida se valida con `SnapshotMeta` de `codice-contracts` antes de cruzar la frontera.
