# ADRs — Registro de decisiones de arquitectura

Un archivo por decisión, formato **ADR-lite**, en este directorio. Nombre: `ADR-NNN-slug-corto.md`.

## Convención de formato

Cada ADR contiene, en este orden:

1. Título: `# ADR-NNN — <decisión>`
2. Línea de estado: `Estado: aceptada · Fecha: AAAA-MM-DD`
3. `## Contexto`
4. `## Decisión`
5. `## Alternativas descartadas`
6. `## Consecuencias`

**Regla:** todo cambio a los contratos compartidos (esquema de datos, OpenAPI, esquemas Pydantic/Zod) requiere un ADR nuevo, en PR separado, con aviso a todos los carriles (§14 del CLAUDE.md).

## Índice

| ID | Decisión |
|---|---|
| ADR-000 | Nombre del proyecto: **Códice**. Tagline: *"Cómo funciona México"*. Descartados: Tequio, Tlacuilo, Atlas-MX. |
| ADR-001 | Postgres canónico + grafo como vista derivada. No Neo4j al inicio. |
| ADR-002 | Ingesta cruda inmutable antes de cualquier parseo (raw-first). |
| ADR-003 | Python para ingesta, TypeScript para frontend. Servicios separados. |
| ADR-004 | MapLibre GL sobre Google Maps y Leaflet. |
| ADR-005 | react-three-fiber sobre Three.js imperativo. |
| ADR-006 | Nunca auto-fusionar entidades; tabla de candidatos con revisión humana. |
| ADR-007 | Señales, no conclusiones. Vocabulario prohibido en outputs. |
| ADR-008 | Escalera de evidencia para promesas; prohibido el % de cumplimiento. |
| ADR-009 | Contrastador, no verificador de verdad/mentira. |
| ADR-010 | Clave INEGI como ID territorial canónico. |
| ADR-011 | Dagster para orquestación (assets con linaje). |
| ADR-012 | Parquet estático + DuckDB WASM como capa de servido analítico. |
| ADR-013 | MCP remoto como cliente delgado del API público. |
| ADR-014 | Apache 2.0 (código) + ODbL (datos). |
| ADR-015 | Open source con autoría institucional Gorilla Labs, no anónimo. |
| ADR-016 | El LLM propone, el humano decide. Siempre con score y auditoría. |
| ADR-017 | Modelo temporal transversal: todo registro es versionado. |
| ADR-018 | Snapshots con hash como activo central (contexto post-extinción del INAI). |
