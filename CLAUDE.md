# CLAUDE.md — Códice

> **Códice** — *Cómo funciona México.*
> Infraestructura cívica abierta para entender el Estado mexicano.
> **by Gorilla Labs 🦍** — Open source, autoría institucional.
>
> *Los códices explicaban cómo funcionaba el mundo. Este explica cómo funciona México.*
>
> **Convención de escritura:** `Códice` con acento en prosa, UI y documentación.
> `codice` sin acento en identificadores técnicos: repo, paquete npm, dominio, nombres de tablas.

---

## 0. Misión

Construir un sistema de información **de grado institucional** que explique, con trazabilidad completa, cómo funciona el Estado mexicano: quién manda, de dónde viene su legitimidad, cuál es su fundamento legal, a dónde va el dinero y quién lo vigila.

El producto tiene dos caras:

1. **Didáctica**: un mapa navegable (jerárquico y geográfico) que va desde el Ejecutivo Federal hasta el ciudadano que vota.
2. **Investigativa**: un motor de cruces entre obra pública, contratos, empresas, funcionarios, sanciones y fiscalización.

**No somos un medio. No emitimos veredictos. Somos infraestructura de datos citable.**

---

## 1. Reglas no negociables

Estas reglas aplican a todo el código, todos los datos y todas las respuestas del sistema. Si una tarea entra en conflicto con alguna, **detente y pregunta**.

| # | Regla |
|---|---|
| R1 | **Procedencia siempre.** Todo dato publicado apunta a un documento crudo con URL, fecha de captura y hash. Sin procedencia, no se publica. |
| R2 | **Nunca veredictos.** No existe "verdadero/falso", no existe la palabra "corrupción" en outputs. Solo "señal por verificar" con fundamento y evidencia. |
| R3 | **Nunca auto-fusionar entidades.** El matching de empresas/personas genera *candidatos* con score y estado `pending_review`. La fusión requiere validación humana registrada. |
| R4 | **El LLM nunca decide.** Propone vínculos con score de confianza. Un humano confirma. Se guarda quién validó y cuándo. |
| R5 | **Nunca porcentajes de cumplimiento.** Las promesas se modelan como escalera de evidencia con estados verificables, no como métricas agregadas. |
| R6 | **Decir qué no sabemos.** "No hay fuente oficial para esto" es una respuesta válida y valiosa. Los huecos conocidos se documentan explícitamente. |
| R7 | **Clave INEGI como ID territorial.** Nunca el nombre. Hay municipios homónimos. |
| R8 | **Ingesta cruda inmutable.** Los scrapers guardan el archivo tal cual antes de parsear. Nunca se parsea en la capa de ingesta. |
| R9 | **Todo dato es temporal.** Cada registro lleva vigencia (`valid_from`, `valid_to`) y fecha de observación. El presente es un caso particular. |
| R10 | **Cada nodo tiene enlace permanente citable** con su descarga de datos. Si un periodista no lo puede citar, no sirve. |

---

## 2. Contexto político-institucional relevante

- **El INAI se extinguió el 20 de marzo de 2025.** Sus funciones pasaron a **Transparencia para el Pueblo**, órgano desconcentrado de la Secretaría Anticorrupción y Buen Gobierno. La PNT y el SIPOT siguen operando.
- **Implicación de diseño:** el órgano garante ya no es autónomo, es parte del Ejecutivo. Por eso la capa de *snapshots con hash y fecha* no es buena práctica: **es el activo central del proyecto**. Si una fuente cambia o desaparece, nosotros somos el archivo histórico.

---

## 3. Fases

El orden es por **dependencia técnica**, no por emoción. No saltar fases.

### Fase 0 — Fundación y diseño visual
- Monorepo, licencias, CI, ADRs, política de correcciones, esquema de enlaces permanentes.
- **Congelar contratos**: esquema de datos + forma del API. *Esto lo hace un solo agente antes de paralelizar.*
- Prototipo de visualización dual:
  - **Modo grafo**: jerárquico, posiciones calculadas por nivel.
  - **Modo mapa**: geográfico real (lat/lng).
  - Un solo nodo con **dos posiciones**; al cambiar de modo se interpola. Cero duplicación de datos.
- Scroll = zoom. Agrupación por nivel de zoom + instancing (2,500+ municipios no pueden ser 2,500 draw calls).

### Fase 1 — Estructura constitucional (PRIMORDIAL)
- ~400–500 nodos **curados a mano**. Casi cero scrapers.
- Tres poderes federales + órganos autónomos + esqueleto estatal y municipal (estructura sin datos aún).
- Cada nodo con su **artículo de fundamento**.
- **Doble flecha**: la *autoridad* baja del Ejecutivo al ciudadano; la *legitimidad* sube del ciudadano al Ejecutivo. Esto explica México mejor que cualquier organigrama.
- Capa de población por entidad/municipio/localidad (INEGI, versionada por año de censo).

### Fase 2 — Personas
- Quién ocupa cada nodo hoy: nombre, partido, periodo (inicio/fin), contacto institucional.
- Fuentes: SIL (federal), SIPOT/PNT (32 congresos locales y municipios).
- **Aquí nace la infraestructura real de scrapers, snapshots y versionado histórico.**
- El versionado temporal es **transversal desde aquí en adelante** (ver R9).

### Fase 3 — Dinero
- Presupuesto (Transparencia Presupuestaria), Contrataciones Abiertas (OCDS), Obra Pública Abierta (geolocalizada).
- Métrica visible: **gasto por habitante**, siempre con año, fuente y población de referencia. Nunca el número solo.

### Fase 4 — Poder electoral
- Partidos, financiamiento público, padrón de afiliados, resultados electorales.
- **Modelar la fórmula del Art. 41 constitucional**, no solo el resultado. Si modelas la fórmula (padrón × UMA), el sistema puede *explicar* y *proyectar*.

### Fase 5 — Contrapesos y señales
- ASF (auditorías, observaciones, recuperaciones), PDN Sistemas 1/2/3, lista 69-B del SAT, Directorio de Sancionados de Función Pública.
- **Motor de señales** (ver §6). Incluye tipo de señal **"puerta giratoria"**: funcionario que autoriza contrato y aparece después en la empresa adjudicada.
- **Cruce estrella del proyecto**: obra pública geolocalizada → contrato → empresa adjudicada → pliego de observaciones de la ASF → sanciones. Nadie tiene esto junto.

### Fase 6 — Promesas vs. evidencia
- Cruce de plataformas electorales registradas ante el INE contra iniciativas presentadas (SIL).
- **Dato propietario del proyecto.** No existe oficialmente en ningún lado.
- Escalera de evidencia (ver §7).

### Fase 7 — Contrastador (NO verificador)
- El usuario pega una afirmación política. El sistema devuelve **los datos oficiales relevantes con fuente y fecha**, sin veredicto.
- El LLM solo extrae entidades, años y cifras mencionadas. Luego consulta datos propios.
- Salida obligatoria: advertencias metodológicas (nominal vs. real, per cápita vs. total, año base).
- Cero adjetivos. Cero semáforo. Que el dato hable.

---

## 4. Arquitectura — 4 capas, ninguna depende de la de arriba

```
┌─ L4  VISUALIZACIÓN ── Next.js + R3F + MapLibre ──── solo lee del API
├─ L3  API / GRAFO ──── FastAPI (read-only) + vista de grafo derivada
├─ L2  NORMALIZACIÓN ── Postgres canónico + IDs canónicos + procedencia
└─ L1  INGESTA CRUDA ── scrapers Python → R2 (archivo tal cual + hash + fecha)
```

**L1 nunca parsea.** Baja el HTML/ZIP/PDF y lo guarda. Cuando el parser falle (y va a fallar), no perdiste el dato y puedes reprocesar histórico.

**L2 es donde está el trabajo real.** Resolución de identidades, IDs canónicos, tabla de procedencia.

**L3: el grafo es vista derivada, no base primaria.** Postgres con recursive CTEs aguanta perfecto. No meter Neo4j (ver ADR-001).

**Contratos de datos con validación (Pydantic / Zod) en la frontera de cada capa.** Si un scraper devuelve basura, se detiene ahí y no contamina.

---

## 5. Resolución de identidades (empresas y personas)

Tres etapas, en este orden:

1. **Normalización determinística** — minúsculas, sin acentos, y sobre todo **eliminar sufijos societarios**: `S.A. de C.V.`, `S. de R.L.`, `S.A.P.I. de C.V.`, `S.C.`, y ~20 variantes de puntuación. Esto resuelve ~60%.
2. **RFC como llave dura** — Contrataciones Abiertas y la lista 69-B lo traen. **Si hay RFC, nunca hacer match difuso.**
3. **Similitud difusa** — `pg_trgm` con índice GIN sobre trigramas para lo que quede.

**Salida:** tabla `entity_match_candidates` con `score`, `method`, `status ∈ {pending, confirmed, rejected}`, `reviewed_by`, `reviewed_at`. **Jamás fusión automática** (R3).

> Fusionar mal dos empresas en un sistema que habla de dinero público cuesta la credibilidad del proyecto entero.

---

## 6. Motor de señales — *Machiyotl*

> `machiyotl` = "señal" en náhuatl. Nombre interno del submódulo.

Tabla de **señales, no de conclusiones**. Cada regla que se dispara genera un registro:

- `signal_type` (ej. `adjudicacion_a_empresa_69b`, `puerta_giratoria`, `contratista_sancionado_vigente`)
- `entities[]` — entidades involucradas
- `score` — confianza de la regla
- `legal_basis` — artículo/ley que da contexto
- `evidence[]` — documentos crudos con hash y fecha
- `status` — siempre inicia en `por_verificar`

**Nunca la palabra "corrupción".** Siempre "señal por verificar". Esto blinda jurídicamente y es lo que hace que un periodista pueda citar el sistema.

---

## 7. Escalera de evidencia (promesas)

Cada promesa es un nodo. Su relación con la realidad tiene estados **verificables**, cada uno exigiendo un documento con folio y fecha:

```
sin_evidencia → iniciativa_presentada → dictaminada_en_comision
              → aprobada → publicada_dof → presupuesto_asignado
```

El LLM propone el vínculo promesa↔iniciativa con score. Un humano confirma. El usuario ve la cadena completa y saca su propia conclusión. **Sin porcentajes** (R5).

---

## 8. Fuentes de datos

| Fuente | Qué da | Formato | Dificultad |
|---|---|---|---|
| **SIL (Gobernación)** | Integración del Congreso, perfiles de legisladores, iniciativas, seguimiento de sesiones | HTML | Scraping. Sin API. |
| **Cámara de Diputados — LEYFED** | Compilación completa de leyes federales vigentes | ZIP descargable | Media. Texto estructurado por artículos. |
| **Orden Jurídico Nacional** | Normativa federal, estatal y municipal | HTML | Scraping. Clave para nivel local. |
| **DOF** | Publicación oficial, acuerdos del INE, reformas | HTML/PDF | Scraping. |
| **Contrataciones Abiertas (SHCP)** | Licitaciones y adjudicaciones, estándar **OCDS**, desde 2017 | **JSON** ✅ | Baja. La mejor fuente de dinero. |
| **Obra Pública Abierta (SHCP)** | Proyectos de inversión federal **geolocalizados**, clave de cartera, presupuesto | Mapa + BD abiertas | Media. |
| **CompraNet histórico (datos.gob.mx)** | Contratos y expedientes 2010–2022 | Descargable | Baja. |
| **PDN / SNA** ⭐ | **Sistema 1**: declaraciones patrimoniales y de intereses. **Sistema 2**: servidores públicos en contrataciones. **Sistema 3**: sancionados (personas y empresas) | **API real documentada** ✅ | Baja. Repos en GitHub org `PDNMX`. |
| **INE — Datos Abiertos** | Padrón de afiliados a partidos nacionales | Descargable ✅ | Baja. |
| **INE — Portal SIF** | Fiscalización: origen y destino de recursos de partidos y candidatos | Reportes descargables | Media. |
| **INE — Acuerdos CG (vía DOF)** | Distribución exacta de financiamiento por partido | PDF/HTML | Media. |
| **ASF** ⚠️ | Auditorías, observaciones, pliegos, recuperaciones | **PDFs por auditoría** | **Alta.** Sin datos abiertos reales. Entrada: *Matriz de Datos Básicos consolidada* (índice tabular). Fundar publicó crítica pidiéndoles formatos abiertos. |
| **SAT — Lista 69-B** | Empresas que facturan operaciones simuladas (EFOS). **Trae RFC** | Descargable ✅ | Baja. Llave dura para matching. |
| **Función Pública — Directorio de Sancionados** | Proveedores y contratistas inhabilitados | App web | Media. Scraping. |
| **PNT / SIPOT** | Directorio obligatorio de todos los sujetos obligados: nombre, cargo, remuneración, contacto institucional | Formato estandarizado ✅ | Media. **Ahorra 32 scrapers distintos.** |
| **INEGI** | Censo 2020, conteos por localidad, Marco Geoestadístico (fronteras + claves oficiales) | Descargable ✅ | Baja. Versionar por año (viene Censo 2030). |

### Huecos conocidos (documentar públicamente)

- **Propiedad corporativa / beneficiario final.** El Registro Público de Comercio y el SIGER no son abiertos. Rompe la cadena de parentesco y empresas fantasma. *Parches parciales*: 69-B y Directorio de Sancionados.
- **Teléfono personal de legisladores.** No es obligación de transparencia. Solo institucional.
- **Promesas cumplidas.** No existe como dato oficial. Se construye (Fase 6).

---

## 9. Stack

> Regla: **la mejor tecnología para cada función**, no la que ya dominamos.

### Frontend
- **Next.js** (App Router)
- **react-three-fiber** — NO Three.js imperativo. 500 nodos en imperativo es un infierno de mantener.
- **MapLibre GL** — capa custom de Three en el mismo contexto WebGL. NO Google Maps (licencia/costo), NO Leaflet (2D, contexto separado).
- **Zustand** para estado.
- **DuckDB WASM** para consultas analíticas en el navegador sobre Parquet estático.

### Datos e ingesta
- **Python** para toda la ingesta. El ecosistema de scraping y extracción de PDFs vive en Python, y la ASF es puro PDF.
- **Dagster** para orquestación. Piensa en *assets* con linaje — es exactamente el requisito de trazabilidad. (Prefect como alternativa.)
- **Cloudflare R2** para snapshots crudos. Nunca blobs en la base.
- **GitHub Actions** para correr scrapers → pipeline público y auditable. Gratis e ilimitado en repos públicos.

### Base de datos
- **PostgreSQL** (Supabase) con tres extensiones obligatorias:
  - `PostGIS` — geometrías
  - `pg_trgm` — matching difuso de empresas
  - `pgvector` — indexado semántico de leyes
- **DuckDB** para consultas analíticas pesadas. Postgres queda como verdad canónica.
- **Parquet estático** publicado en el repo/R2 como capa de servido.

### API
- **FastAPI**, read-only.

### MCP
- **Cloudflare Workers**, transporte HTTP con streaming (remoto).
- Publicado en **npm**; el mismo paquete corre local o apunta al remoto según variable de entorno.
- **Cliente delgado del API público.** Nunca habla directo a la base.
- **4 herramientas**, no 20:
  1. `buscar_entidad`
  2. `explicar_estructura`
  3. `rastrear_dinero`
  4. `consultar_fundamento_legal`
- Cada herramienta **devuelve siempre la cita**: fuente, fecha de captura, enlace al documento. Así ningún chat puede alucinar nuestros datos.
- **Rate limit desde el día uno.** Un agente en bucle tumba el free tier.
- Sin autenticación: son datos públicos.

---

## 10. Uso de LLMs

Tres trabajos distintos, modelos distintos:

| Trabajo | Modelo | Notas |
|---|---|---|
| Extracción estructurada de PDFs de la ASF | Modelo con visión, capa gratuita generosa (ej. Gemini Flash) | **Único costo real.** Miles de documentos. Procesar **una vez**, guardar resultado como dato versionado en el repo, no volver a pagar. |
| Resumen ciudadano de artículos de ley | Modelo barato | Una sola vez, cacheado. **Nunca en vivo.** |
| Vínculo promesa ↔ iniciativa | Modelo fuerte | Bajo volumen. **Siempre con humano validando** (R4). |

---

## 11. Costos / free tier

| Servicio | Free tier | Cuándo duele |
|---|---|---|
| Vercel | Suficiente para frontend | Si el dato pesado pasa por ahí. No lo hagas. |
| Supabase | 500 MB | Alcanza Fases 1–2. **Fase 3 lo revienta** → ~$25/mes. |
| Cloudflare R2 | 10 GB + **cero egress** | Es lo que mata en otros proveedores. |
| Cloudflare Workers | 100k req/día | Suficiente para MCP con rate limit. |
| GitHub Actions | Gratis e ilimitado en repos públicos | — |
| Dominio | — | ~$15 USD/año. Único costo fijo garantizado. |

**Truco que ahorra todo:** publicar datos procesados como **Parquet estático** y consultarlos con **DuckDB WASM** desde el navegador. Sin servidor, sin base, escala infinito, gratis.

---

## 12. Licencias y gobernanza

- **Código**: Apache 2.0 (cobertura de patentes).
- **Datos**: ODbL o CC-BY-SA.
- **Autoría**: institucional — *by Gorilla Labs*. Open source con contribuciones abiertas.
- **`CONTRIBUTING.md` obligatorio** con guía de cómo agregar un nodo con su fundamento legal, para que gente no programadora pueda contribuir.
- **Política de correcciones pública** + derecho de réplica documentado. Desde Fase 0, es contrato público, no añadido.

---

## 13. ADRs

Formato **ADR-lite** (D1–Dn), un archivo por decisión en `/docs/adr/`. Estructura: Contexto → Decisión → Alternativas descartadas → Consecuencias.

**Escribir estas desde el commit 1:**

| ID | Decisión |
|---|---|
| ADR-000 | Nombre del proyecto: **Códice**. Tagline: *"Cómo funciona México"*. Descartados: Tequio (describe el cómo, no el qué), Tlacuilo (fricción ortográfica), Atlas-MX (sesga a lo geográfico). |
| ADR-001 | Postgres canónico + grafo como vista derivada. **No Neo4j** al inicio. |
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

---

## 14. Plan multiagente

### Precondición (secuencial, un solo agente)
**Congelar los contratos antes de paralelizar:**
1. Esquema de base de datos (DDL + migraciones).
2. Forma del API (OpenAPI spec).
3. Esquemas de validación compartidos (Pydantic ↔ Zod).

Sin esto congelado, los agentes se pisan y hay que rehacer.

### Carriles paralelos (directorios propios, sin solapamiento)

```
/ingestion      → Agente A: scrapers Python, Dagster assets, snapshots R2
/normalization  → Agente B: parsers, IDs canónicos, entity resolution, procedencia
/api            → Agente C: FastAPI read-only, vistas de grafo, export Parquet
/web            → Agente D: Next.js, R3F, MapLibre, modo dual grafo/mapa
/mcp            → Agente E: Worker + paquete npm, 4 tools con citas
/docs           → Agente F: ADRs, CONTRIBUTING, política de correcciones, catálogo de fuentes
```

**Reglas de coordinación:**
- Ningún agente modifica archivos fuera de su directorio salvo los contratos compartidos, y esos requieren un ADR.
- Cambios a contratos = PR separado + ADR + aviso a todos los carriles.
- Cada carril tiene sus propios tests y puede correr aislado con fixtures.

---

## 15. Convenciones

- Idioma del código y comentarios: **inglés**. Idioma de contenido, docs y UI: **español**.
- Commits: Conventional Commits.
- Nada de secretos en el repo. Todo por variables de entorno. (Ya nos pasó una vez.)
- Todo scraper implementa: `fetch_raw()` → `store_snapshot()` → `parse()` como pasos separados y testeables.
- Todo endpoint del API devuelve `sources[]` con `{url, captured_at, hash}`.

---

## 16. Qué NO hacer

- ❌ No empezar por el grafo 3D bonito. Es lo que da likes y lo que menos valor tiene.
- ❌ No intentar los 3 poderes + 32 estados + 2,500 municipios con datos completos en la Fase 1.
- ❌ No meter Neo4j "porque es un grafo".
- ❌ No hacer scraping en TypeScript.
- ❌ No guardar PDFs ni HTML crudo en Postgres.
- ❌ No publicar un score, porcentaje o semáforo que resuma un juicio político.
- ❌ No desplegar en infraestructura compartida con otros proyectos de Gorilla Labs sin separar credenciales.
