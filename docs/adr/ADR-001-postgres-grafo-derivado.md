# ADR-001 — Postgres canónico con grafo como vista derivada

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El producto presenta un grafo (jerarquía de poderes, flujos de dinero, vínculos entre entidades), lo que invita a pensar en una base de datos de grafos como almacenamiento primario. Pero el trabajo real del sistema está en la capa de normalización: resolución de identidades, IDs canónicos, procedencia y versionado temporal (R1, R9) — todo terreno relacional. Además el proyecto vive en free tiers (Supabase 500 MB) y necesita extensiones concretas: PostGIS para geometrías, `pg_trgm` para matching difuso de empresas y `pgvector` para indexado semántico de leyes.

## Decisión

**PostgreSQL (Supabase) es la verdad canónica.** El grafo que sirve el API (L3) es una **vista derivada** construida sobre el modelo relacional; las travesías jerárquicas se resuelven con recursive CTEs, que aguantan perfectamente los ~400–500 nodos de la Fase 1 y órdenes de magnitud más. Las extensiones obligatorias son PostGIS, `pg_trgm` y `pgvector`. DuckDB y Parquet estático cubren la carga analítica sin tocar la base canónica.

## Alternativas descartadas

- **Neo4j como base primaria**: descartado al inicio. "Es un grafo" no es razón suficiente (§16); añade un segundo sistema de almacenamiento que duplicaría la verdad canónica, complica procedencia y versionado temporal, no ofrece equivalentes a PostGIS/pg_trgm/pgvector y no cabe en el presupuesto de free tier.
- **Base de grafos como réplica sincronizada**: sincronizar dos verdades es exactamente la clase de complejidad que un proyecto de este tamaño no puede pagar; la vista derivada dentro de Postgres da lo mismo sin sincronización.

## Consecuencias

Una sola base que respaldar, migrar y auditar; la procedencia y la temporalidad viven junto a los datos que describen. Las consultas de grafo se escriben en SQL (recursive CTEs), lo cual es más verboso que Cypher pero elimina un servicio completo. Si en el futuro el volumen o la profundidad de travesías rebasa a Postgres, migrar es posible porque el grafo ya está modelado como vista derivada — la decisión es reversible y requerirá un ADR nuevo.
