# Códice

> **Cómo funciona México.**
> Infraestructura cívica abierta para entender el Estado mexicano.
> **by Gorilla Labs 🦍**

*Los códices explicaban cómo funcionaba el mundo. Este explica cómo funciona México.*

## Qué es

Un sistema de información de grado institucional que explica, con trazabilidad completa, cómo funciona el Estado mexicano: quién manda, de dónde viene su legitimidad, cuál es su fundamento legal, a dónde va el dinero y quién lo vigila.

Dos caras:

1. **Didáctica** — un mapa navegable (jerárquico y geográfico) del Ejecutivo Federal al ciudadano que vota.
2. **Investigativa** — un motor de cruces entre obra pública, contratos, empresas, funcionarios, sanciones y fiscalización.

**No somos un medio. No emitimos veredictos. Somos infraestructura de datos citable.**

## Cómo leerlo

La visualización abre con un **recorrido guiado** de nueve pasos que maneja la interfaz mientras explica: selecciona órganos, cambia al mapa y revela los extintos, para que se vea el mecanismo en vez de describirlo. Enseña de dónde sale cada afirmación, por qué toda cifra de dinero viaja con su advertencia y por qué el presente es solo una fecha.

El botón **?** abre las instrucciones en cualquier momento: controles, qué significan los colores, cómo leer una ficha y qué **no** se va a encontrar (ni calificaciones, ni porcentajes de cumplimiento, ni semáforos).

## Principios

- **Procedencia siempre.** Todo dato publicado apunta a un documento crudo con URL, fecha de captura y hash.
- **Señales, no conclusiones.** No existe "verdadero/falso" ni la palabra "corrupción" en los outputs. Solo "señal por verificar" con fundamento y evidencia.
- **El LLM propone, el humano decide.** Todo vínculo sugerido por modelo lleva score y validación humana registrada.
- **Decir qué no sabemos.** Los huecos de las fuentes oficiales se documentan públicamente.
- **Todo dato es temporal.** Cada registro lleva vigencia y fecha de observación.

## Arquitectura

```
┌─ L4  VISUALIZACIÓN ── Next.js + R3F + MapLibre ──── solo lee del API
├─ L3  API / GRAFO ──── FastAPI (read-only) + vista de grafo derivada
├─ L2  NORMALIZACIÓN ── Postgres canónico + IDs canónicos + procedencia
└─ L1  INGESTA CRUDA ── scrapers Python → R2 (archivo tal cual + hash + fecha)
```

## Estructura del repo

| Directorio | Qué vive ahí |
|---|---|
| `/contracts` | **Contratos congelados**: DDL, OpenAPI, esquemas Pydantic/Zod. Cambios requieren ADR. |
| `/ingestion` | Scrapers Python, assets de Dagster, snapshots a R2 |
| `/normalization` | Parsers, IDs canónicos, resolución de entidades, procedencia |
| `/api` | FastAPI read-only, vistas de grafo, export Parquet |
| `/web` | Next.js, react-three-fiber, MapLibre — modo dual grafo/mapa |
| `/mcp` | Servidor MCP (Cloudflare Worker + paquete npm) |
| `/docs` | ADRs, política de correcciones, catálogo de fuentes |

## Contribuir

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md). No necesitas programar para contribuir: agregar un nodo con su fundamento legal es una contribución de primera clase.

## Licencias

- **Código**: [Apache 2.0](LICENSE)
- **Datos**: [ODbL](LICENSE-DATA.md)

## Correcciones

Tenemos una [política de correcciones pública](docs/politica-de-correcciones.md) con derecho de réplica documentado. Es contrato público desde el día uno.
