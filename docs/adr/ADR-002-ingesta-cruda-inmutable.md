# ADR-002 — Ingesta cruda inmutable antes de cualquier parseo (raw-first)

Estado: aceptada · Fecha: 2026-08-29

## Contexto

Las fuentes oficiales mexicanas son frágiles: HTML sin API (SIL, DOF, Orden Jurídico Nacional), PDFs por auditoría (ASF), portales que cambian sin aviso. El contexto institucional agrava el riesgo: el INAI se extinguió el 20 de marzo de 2025 y el órgano garante ya no es autónomo, así que una fuente puede cambiar o desaparecer. Si el scraper parsea al vuelo y el parser falla —y va a fallar—, el dato se pierde para siempre. La regla R1 exige además que todo dato publicado apunte a un documento crudo con URL, fecha de captura y hash.

## Decisión

**L1 nunca parsea.** Todo scraper descarga el archivo tal cual (HTML/ZIP/PDF/JSON) y lo guarda inmutable en Cloudflare R2 con su hash y fecha de captura, antes de cualquier procesamiento. El parseo ocurre después, en L2, leyendo del snapshot. Cada scraper implementa `fetch_raw()` → `store_snapshot()` → `parse()` como pasos separados y testeables (§15). Los snapshots con hash y fecha no son buena práctica: son **el activo central del proyecto** — somos el archivo histórico (ADR-018).

## Alternativas descartadas

- **Parsear en la capa de ingesta**: pierde el dato cuando el parser falla y hace imposible reprocesar histórico cuando el parser mejora o la fuente muere.
- **Guardar blobs crudos en Postgres**: prohibido (§16); revienta el free tier de 500 MB y mezcla archivo con dato canónico. R2 da 10 GB gratis con cero egress.
- **Guardar solo el dato extraído con la URL de origen**: la URL no es evidencia — la fuente puede cambiar o desaparecer; sin el snapshot con hash, la cadena de procedencia de R1 se rompe.

## Consecuencias

Cuando un parser falle, el dato crudo sigue ahí y se reprocesa el histórico completo sin volver a la fuente. Toda cita del sistema puede resolverse hasta un documento con hash y fecha, lo que blinda la trazabilidad frente a fuentes que se modifican retroactivamente. El costo es almacenamiento (acotado por R2) y una capa más en el pipeline, que Dagster modela naturalmente como assets con linaje.
