# Contratos congelados

Frontera entre carriles. **Cambiar cualquier archivo de este directorio requiere: PR separado + ADR nuevo en `/docs/adr/` + aviso a todos los carriles afectados.**

| Archivo | Qué congela |
|---|---|
| `sql/migrations/` | Esquema canónico de Postgres (L2). Numeradas, inmutables una vez mergeadas: corregir = nueva migración. |
| `openapi.yaml` | Forma del API read-only (L3). |
| `python/codice_contracts/` | Modelos Pydantic — frontera de validación en ingesta y normalización. |
| `typescript/src/` | Esquemas Zod — frontera de validación en web y MCP. |

Los lados Pydantic y Zod **se mantienen espejados a mano**; todo PR que toque uno debe tocar el otro.

## Validado contra lo real (2026-08-29)

- Migración aplicada limpia en Postgres 17 (imagen `supabase/postgres`), con PostGIS + pg_trgm + pgvector.
- Vista recursiva `v_hierarchy`, similitud trigram y constraint de revisión humana (R3) probados con datos.
- OpenAPI lint en verde (`redocly lint`).
- Pydantic y Zod ejercitados con payloads válidos e inválidos.
