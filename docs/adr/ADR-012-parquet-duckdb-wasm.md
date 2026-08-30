# ADR-012 — Parquet estático + DuckDB WASM como capa de servido analítico

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El proyecto corre sobre free tiers: Supabase da 500 MB y la Fase 3 (presupuesto, contratos, obra pública) lo revienta; Vercel duele si el dato pesado pasa por su infraestructura. A la vez, la cara investigativa necesita consultas analíticas (agregaciones por año, entidad, empresa) que en Postgres transaccional serían caras y en un API serverless costarían por request. Cloudflare R2 ofrece 10 GB con cero costo de egress, lo que hace viable servir archivos de datos directamente al navegador.

## Decisión

Los datos procesados se publican como archivos Parquet estáticos en el repo y en R2, y el frontend los consulta con DuckDB WASM directamente en el navegador. Postgres sigue siendo la verdad canónica (ADR-001); Parquet es una capa de servido derivada, regenerada por el pipeline. Sin servidor de consultas, sin base de datos en el camino caliente: escala con el CDN y cuesta cero.

## Alternativas descartadas

- **Todo por el API de FastAPI**: cada consulta analítica pasaría por servidor y base, pagando cómputo y saturando el free tier de Supabase con la carga de lectura pesada.
- **Data warehouse gestionado (BigQuery, ClickHouse Cloud)**: potencia sobrada, pero introduce un costo variable y una dependencia operativa que el proyecto no puede garantizar a largo plazo.
- **JSON estático precalculado por vista**: gratis también, pero congela las preguntas posibles; DuckDB sobre Parquet deja al usuario (y al Contrastador) hacer cortes no previstos.

## Consecuencias

Las consultas analíticas escalan a costo cero y sobreviven aunque el API esté caído — los Parquet en R2 son autosuficientes, coherente con el rol de archivo histórico del proyecto (§2). El API queda para lecturas puntuales del grafo y las citas de procedencia. A cambio, el frontend carga el runtime de DuckDB WASM (~ MBs, se carga bajo demanda) y los Parquet deben regenerarse y versionarse en cada corrida del pipeline, con su procedencia adjunta para no romper R1.
