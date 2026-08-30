# Fase 1 — Estructura constitucional

Estado: **completa** (30 de agosto de 2026). 201 nodos curados a mano, cada uno con su fundamento legal citado y trazable a un documento oficial con hash.

## Qué contiene

| Ámbito | Nodos | Fuente del fundamento |
|---|---|---|
| Poder Ejecutivo federal | 48 — Presidencia, las 22 dependencias del Art. 26 LOAPF, Consejería Jurídica y organismos sectorizados (SAT, IMSS, ISSSTE, Pemex, CFE, Guardia Nacional, Transparencia para el Pueblo…) | CPEUM, LOAPF y leyes orgánicas propias |
| Poder Legislativo federal | 5 — Congreso, ambas cámaras, Comisión Permanente, ASF | CPEUM Arts. 50–79 |
| Poder Judicial federal | 8 — SCJN (9 ministras/os electos), TEPJF, Tribunal de Disciplina Judicial, Órgano de Administración Judicial, tribunales de circuito y juzgados de distrito | CPEUM Arts. 94–100, LOPJF |
| Órganos autónomos | 11 vigentes + extintos — INE, Banxico, INEGI, CNDH, FGR, TFJA | CPEUM Arts. 26, 28, 41, 102 |
| Esqueleto subnacional | 128 — las 32 entidades × (ejecutivo, congreso, poder judicial, ayuntamientos) | CPEUM Arts. 115, 116 y 122 (CDMX) |
| Ciudadanía | 1 — raíz de la legitimidad | CPEUM Art. 39 |

Además: **2,501 territorios** (32 entidades + 2,469 municipios) con clave INEGI, punto representativo y población del Censo 2020.

## La doble flecha

- **Autoridad** (60 aristas): baja por la línea orgánica que la ley establece — Presidencia → secretarías → organismos sectorizados; Cámara de Diputados → ASF.
- **Legitimidad** (136 aristas): sube de la ciudadanía a cada cargo de elección directa, citando el artículo que establece la elección.

Lo que **no** existe y es deliberado: no hay aristas de autoridad del Ejecutivo federal a los estados (Art. 40, pacto federal) ni de gobernadores a ayuntamientos (Art. 115, municipio libre). Un organigrama que las dibujara estaría mintiendo sobre cómo funciona México.

## Órganos extintos (R9)

El registro conserva 7 órganos extinguidos junto a sus sucesores, con fecha y decreto:

| Órgano | Extinción | Sucesor |
|---|---|---|
| INAI | 2025-03-20 | Transparencia para el Pueblo (Secretaría Anticorrupción y Buen Gobierno) |
| Secretaría de la Función Pública | 2024-11-28 | Secretaría Anticorrupción y Buen Gobierno |
| Consejo de la Judicatura Federal | 2025-09-01 | Tribunal de Disciplina Judicial + Órgano de Administración Judicial |
| Comisión Reguladora de Energía | 2025-03-19 | Secretaría de Energía / Comisión Nacional de Energía |
| Comisión Nacional de Hidrocarburos | 2025-03-19 | Secretaría de Energía / Comisión Nacional de Energía |
| Conahcyt | 2024-11-28 | Secretaría de Ciencia, Humanidades, Tecnología e Innovación |
| Inmujeres | 2024-11-28 | Secretaría de las Mujeres |

El presente es un caso particular: consultar el grafo a una fecha pasada devuelve la estructura vigente entonces.

## Verificación

Cada afirmación de este documento es reproducible:

```bash
# 1. Los snapshots crudos, con su hash
cat ingestion/snapshots.json

# 2. Validar los datos curados (fundamento obligatorio, DAG de autoridad, claves INEGI)
cd normalization && .venv/bin/python -m codice_normalization validate ../data

# 3. Cargar a Postgres y exportar el grafo derivado
.venv/bin/python -m codice_normalization load ../data ../ingestion
.venv/bin/python -m codice_normalization export ../web/public/data/grafo.json

# 4. Invariantes constitucionales sobre el dataset publicado
cd ../web && npm test
```

Las 234 citas a CPEUM, LOAPF y LOPJF se verificaron contra el texto extraído de los PDF descargados; los tres snapshots están registrados con sha256 y fecha de captura.

## Huecos conocidos (R6)

- **Constituciones locales**: el esqueleto estatal se fundamenta en la Constitución federal (Arts. 115, 116, 122). Las 32 constituciones locales no se han ingerido, así que los órganos propios de cada entidad todavía no existen como nodos.
- **Nivel municipal individual**: los 2,469 municipios existen como territorios con población y coordenadas, pero no como nodos de estructura — hoy se agregan en un nodo `ayuntamientos-<clave>` por entidad.
- **Geometrías reales**: el punto representativo de cada territorio es la localidad más poblada (municipios) o el centroide de sus municipios (entidades). Los polígonos llegan con el Marco Geoestadístico.
- **Fechas de creación**: sólo se registran donde el decreto es verificable en las fuentes descargadas; se omiten antes que inventarlas.
- **Órganos sin sucesor verificable**: para COFECE e IFT el texto vigente sólo permite afirmar que la regulación pasó al Ejecutivo federal; los sucesores concretos requieren las leyes secundarias de 2025, aún no ingeridas.
