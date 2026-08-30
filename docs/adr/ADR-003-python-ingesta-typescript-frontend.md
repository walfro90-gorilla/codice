# ADR-003 — Python para ingesta, TypeScript para frontend, servicios separados

Estado: aceptada · Fecha: 2026-08-29

## Contexto

La regla del stack es "la mejor tecnología para cada función, no la que ya dominamos" (§9). La ingesta pelea contra HTML sin API, ZIPs de leyes y sobre todo los PDFs de la ASF — el ecosistema de scraping y extracción de PDFs vive en Python. El frontend es Next.js con react-three-fiber y MapLibre, terreno TypeScript. Unificar el lenguaje obligaría a sacrificar uno de los dos lados, y el plan multiagente (§14) exige carriles paralelos que no se pisen.

## Decisión

**Python para toda la ingesta y normalización** (scrapers, Dagster, extracción de PDFs, FastAPI en L3). **TypeScript para el frontend y el MCP** (Next.js, R3F, MapLibre, Worker de Cloudflare). Son servicios separados con directorios propios (`/ingestion`, `/normalization`, `/api` vs. `/web`, `/mcp`), cada uno con sus tests y capaz de correr aislado. La frontera entre mundos se protege con contratos de datos validados en ambos lados: **Pydantic en Python ↔ Zod en TypeScript**, congelados antes de paralelizar.

## Alternativas descartadas

- **Scraping en TypeScript**: prohibido explícitamente (§16). El tooling de scraping y de PDFs en JS es inferior al de Python, y la ASF es puro PDF.
- **Todo en Python (frontend incluido)**: no hay equivalente serio a react-three-fiber + MapLibre para la visualización dual grafo/mapa; el frontend Python quedaría de segunda clase.
- **Monolito de un solo servicio/lenguaje**: rompe el plan de carriles paralelos y acopla el ciclo de vida del pipeline de datos al del frontend.

## Consecuencias

Dos toolchains que mantener (deps, CI, linters) — costo aceptado a cambio de usar el mejor ecosistema en cada capa. Los esquemas compartidos existen dos veces (Pydantic y Zod) y deben mantenerse en sincronía; por eso son contratos congelados y cualquier cambio requiere PR separado, ADR y aviso a todos los carriles (§14). La separación por servicios permite que agentes distintos trabajen en paralelo sin solaparse.
