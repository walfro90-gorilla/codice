# /normalization — L2 Normalización

Parsers, IDs canónicos, resolución de entidades y procedencia. Aquí está el trabajo real.

- Entrada: snapshots crudos de R2 (nunca se re-descarga de la fuente).
- Salida: Postgres canónico, siempre con fila en `provenance`.
- Resolución de entidades en tres etapas (ver ADR-006): normalización determinística → RFC como llave dura → trigram. **Jamás fusión automática** (R3): solo `entity_match_candidates`.

## CLI

```bash
python -m codice_normalization validate ../data                       # valida los YAML curados
python -m codice_normalization load ../data ../ingestion              # carga a Postgres canónico
python -m codice_normalization export ../web/public/data/grafo.json   # exporta el grafo derivado
python test_curated.py                                                # reglas del validador
```

El validador exige fundamento legal en cada nodo, verifica que las aristas de autoridad formen un DAG, que las claves territoriales existan y que los órganos extintos tengan fechas coherentes. Se niega a cargar si hay un solo error.

## Base local

```bash
docker run -d --name codice-db -e POSTGRES_PASSWORD=codice_dev -p 54320:5432 \
  -v codice-pgdata:/var/lib/postgresql/data public.ecr.aws/supabase/postgres:17.6.1.143
docker exec -i codice-db psql -U postgres -f - < ../contracts/sql/migrations/0001_initial.sql
```
