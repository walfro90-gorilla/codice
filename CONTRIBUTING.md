# Contribuir a Códice

Gracias por querer explicar cómo funciona México. Hay dos formas de contribuir y **las dos valen igual**: agregar conocimiento (no requiere programar) y agregar código.

## Reglas que nadie puede saltarse

1. **Procedencia siempre.** Todo dato apunta a un documento oficial con URL y fecha de consulta. Sin fuente, no entra.
2. **Cero veredictos.** No usamos "corrupción", "verdadero/falso", porcentajes de cumplimiento ni semáforos. Solo hechos con fuente y "señales por verificar".
3. **Clave INEGI como ID territorial.** Nunca el nombre del municipio (hay homónimos).
4. **Idiomas**: código y comentarios en inglés; contenido, docs y UI en español.
5. **Commits**: [Conventional Commits](https://www.conventionalcommits.org/es/) (`feat:`, `fix:`, `docs:`, `data:`...).
6. **Nada de secretos en el repo.** Todo por variables de entorno.

## Contribuir conocimiento: agregar un nodo

Un **nodo** es cualquier pieza del Estado: un poder, una secretaría, un órgano autónomo, un congreso, un municipio, un cargo. Para proponer uno abre un Pull Request (o un Issue si no manejas git) con esta plantilla:

```yaml
# nodo propuesto
id: sre                        # slug corto, minúsculas, sin acentos
nombre: Secretaría de Relaciones Exteriores
tipo: secretaria_de_estado     # ver contracts/ para tipos válidos
nivel: federal                 # federal | estatal | municipal | ciudadano
territorio: null               # clave INEGI si aplica (ej. "09" CDMX, "09015" Cuauhtémoc)
depende_de: ejecutivo-federal  # id del nodo del que recibe autoridad
fundamento_legal:
  - documento: Ley Orgánica de la Administración Pública Federal
    articulo: "Art. 26 y 28"
    url: https://www.diputados.gob.mx/LeyesBiblio/pdf/LOAPF.pdf
    consultado: 2026-08-29
```

Checklist antes de mandar:

- [ ] El `fundamento_legal` cita artículo específico, no solo la ley.
- [ ] La URL es de fuente oficial (diputados.gob.mx, dof.gob.mx, orden jurídico estatal...).
- [ ] El `territorio` usa clave INEGI, no nombre.
- [ ] Si el nodo tiene vigencia (se creó o extinguió), incluye fechas y fuente.

Un mantenedor valida contra la fuente y hace merge. Tu nombre queda en el historial.

## Contribuir código

### Estructura de carriles

Cada directorio es un carril independiente con sus propios tests:

| Carril | Stack | Regla |
|---|---|---|
| `/ingestion` | Python | Todo scraper implementa `fetch_raw()` → `store_snapshot()` → `parse()` como pasos separados y testeables. L1 **nunca** parsea. |
| `/normalization` | Python | Resolución de entidades genera candidatos, jamás fusiona solo. |
| `/api` | Python (FastAPI) | Read-only. Todo endpoint devuelve `sources[]` con `{url, captured_at, hash}`. |
| `/web` | TypeScript (Next.js) | Solo lee del API. |
| `/mcp` | TypeScript | Cliente delgado del API público. Nunca habla directo a la base. |

### Contratos congelados

`/contracts` (DDL, OpenAPI, esquemas Pydantic/Zod) es la frontera entre carriles. **Cambiarlos requiere: PR separado + ADR nuevo en `/docs/adr/` + aviso en el PR a todos los carriles afectados.**

### Flujo

1. Fork + rama desde `main` (`feat/nombre-corto`).
2. Tests del carril en verde localmente.
3. PR con descripción de qué y por qué. CI debe pasar.
4. Nunca push directo a `main`.

## Correcciones de datos

¿Encontraste un dato incorrecto? Abre un Issue con la etiqueta `corrección` citando el permalink del dato y la fuente que lo contradice. Ver [política de correcciones](docs/politica-de-correcciones.md) — incluye derecho de réplica.
