# ADR-011 — Dagster para orquestación de ingesta

Estado: aceptada · Fecha: 2026-08-29

## Contexto

La ingesta cubre ~17 fuentes oficiales con formatos y cadencias distintas (HTML scrapeado, ZIP, JSON OCDS, PDFs de la ASF), y cada dato publicado debe poder rastrearse hasta su snapshot crudo con URL, hash y fecha (R1). Eso convierte el linaje — qué archivo crudo produjo qué fila normalizada — en un requisito de primera clase, no en un lujo de observabilidad. Además, todo scraper implementa `fetch_raw()` → `store_snapshot()` → `parse()` como pasos separados (§15), lo que pide un orquestador que modele pasos y dependencias explícitamente.

## Decisión

Dagster orquesta toda la ingesta y normalización. Su modelo de *software-defined assets* con linaje declarado coincide exactamente con el requisito de trazabilidad: cada snapshot crudo, cada tabla normalizada y cada export Parquet es un asset cuyo grafo de dependencias queda documentado y visualizable. Los pipelines corren en GitHub Actions sobre repo público, de modo que la ejecución misma es auditable por terceros.

## Alternativas descartadas

- **Prefect**: alternativa viable y queda anotada como plan B, pero su modelo es de flujos/tareas, no de assets con linaje; la trazabilidad habría que construirla encima.
- **Airflow**: orientado a DAGs de tareas, operación pesada para un proyecto free-tier, y el linaje de datos tampoco es nativo.
- **Cron + scripts sueltos**: cero costo inicial, pero sin reintentos, sin linaje, sin visibilidad de qué corrió y con qué resultado; con miles de documentos de la ASF el reprocesamiento histórico se vuelve inmanejable.

## Consecuencias

Los scrapers de `/ingestion` se escriben como assets de Dagster desde la Fase 2, con el snapshot crudo y el parseado como assets separados — lo que refuerza estructuralmente la regla de ingesta cruda inmutable (R8, ADR-002). El linaje que exige R1 sale del orquestador en vez de mantenerse a mano. El costo es la curva de aprendizaje de Dagster y su vocabulario propio; si resultara demasiado pesado, la migración a Prefect es factible porque la lógica de cada paso vive en funciones Python planas y testeables.
