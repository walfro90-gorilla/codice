# /api — L3 API read-only

FastAPI. Solo lectura, sin excepciones.

- Todo endpoint devuelve `sources[]` con `{url, captured_at, hash}` (R1).
- La forma está congelada en `/contracts/openapi.yaml`; cambios requieren ADR.
- El grafo es vista derivada de Postgres (recursive CTE), no base primaria (ADR-001).
- También exporta Parquet estático para DuckDB WASM (ADR-012).
