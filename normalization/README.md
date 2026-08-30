# /normalization — L2 Normalización

Parsers, IDs canónicos, resolución de entidades y procedencia. Aquí está el trabajo real.

- Entrada: snapshots crudos de R2 (nunca se re-descarga de la fuente).
- Salida: Postgres canónico, siempre con fila en `provenance`.
- Resolución de entidades en tres etapas (ver ADR-006): normalización determinística → RFC como llave dura → trigram. **Jamás fusión automática** (R3): solo `entity_match_candidates`.
