# /data — Datos curados a mano

Fase 1: la estructura constitucional se cura a mano, con fundamento legal por nodo. Estos YAML **son la fuente**; el loader de `/normalization` los valida contra los contratos y los carga a Postgres.

## Formato de archivo (`data/nodes/*.yaml`)

```yaml
nodes:
  - id: ejecutivo-federal          # slug permanente citable (R10)
    node_type: poder               # clave de data/node-types.yaml
    name: Poder Ejecutivo Federal
    level: federal                 # federal | estatal | municipal | ciudadano
    territory: null                # clave INEGI o null (R7)
    valid_from: 1917-05-01         # opcional; default 1900-01-01
    valid_to: null                 # fecha de extinción si aplica (R9)
    authority_from: null           # id del nodo del que recibe autoridad (genera arista)
    summary: null                  # resumen ciudadano opcional
    legal_basis:                   # ≥1 obligatorio, artículo específico
      - document: CPEUM
        article: "Art. 80"
        url: https://www.diputados.gob.mx/LeyesBiblio/pdf/CPEUM.pdf

edges:                             # aristas extra (típicamente legitimidad)
  - from: ciudadania
    to: ejecutivo-federal
    type: legitimidad
    legal_basis: "CPEUM Art. 81 — elección directa"
```

## Reglas que el validador aplica

- `id` único global; slug `[a-z0-9-]`.
- `legal_basis` no vacío, con artículo específico (no solo la ley).
- `authority_from` y `edges[].from/to` referencian nodos existentes.
- Las aristas de autoridad forman un DAG (sin ciclos).
- `territory` válida contra claves INEGI cargadas.
- Nodos extintos: `valid_to` con fecha y fundamento del decreto de extinción en `legal_basis`.
- Órganos extintos y sucesores conviven: el extinto con `valid_to`, el sucesor con `valid_from` (R9). El presente es un caso particular.

## Validar localmente

```bash
cd normalization && .venv/bin/python -m codice_normalization validate ../data
```
