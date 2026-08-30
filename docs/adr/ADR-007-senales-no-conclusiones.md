# ADR-007 — Señales, no conclusiones; vocabulario prohibido en outputs

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El motor de señales (*Machiyotl*) cruza contratos, empresas, sanciones y auditorías, y sus hallazgos tocan reputaciones y dinero público. El proyecto no es un medio y no emite veredictos (R2): su valor es ser infraestructura de datos citable. Un sistema que afirme conclusiones se expone jurídicamente y deja de ser citable por periodistas, que necesitan hechos con fuente, no juicios de un tercero. Además, el contexto institucional (órgano garante ya no autónomo tras la extinción del INAI) hace más importante que el sistema hable solo con documentos verificables.

## Decisión

Toda regla del motor genera **señales, no conclusiones**: registros con `signal_type`, `entities[]`, `score` de confianza de la regla, `legal_basis` (artículo/ley que da contexto), `evidence[]` (documentos crudos con hash y fecha) y `status` que siempre inicia en `por_verificar`. El vocabulario de los outputs está restringido: la palabra "corrupción" está **prohibida como afirmación en cualquier salida del sistema** — UI, API, exports, respuestas del MCP. La formulación canónica es "señal por verificar", siempre acompañada de fundamento legal y evidencia.

## Alternativas descartadas

- **Publicar conclusiones o etiquetas acusatorias**: convierte al proyecto en emisor de juicios, lo expone a litigio y viola la misión declarada de no ser medio ni emitir veredictos.
- **Scores agregados, semáforos o rankings de "riesgo" por entidad**: aunque no usen palabras acusatorias, un número o color que resume un juicio político es un veredicto disfrazado (ver §16); cada señal se presenta individual, con su regla y su evidencia.
- **Suavizar con sinónimos ("presunta corrupción", "irregularidad probable")**: mantiene la afirmación implícita; la salida correcta describe el hecho verificable (ej. "adjudicación a empresa en lista 69-B") y deja la conclusión al lector.

## Consecuencias

- El sistema queda blindado jurídicamente: nunca afirma un delito, solo documenta cruces de datos oficiales con su fundamento y su evidencia, y eso es exactamente lo que permite que un periodista lo cite.
- Cada señal es rastreable hasta documentos crudos con hash y fecha (R1), y su ciclo de vida (`por_verificar` → estados posteriores) requiere validación humana, no automatismos.
- Los tests de outputs deben incluir la verificación del vocabulario prohibido: ninguna respuesta del API, la UI o el MCP puede contener el término vetado como afirmación.
- El costo es de expectativas: usuarios que busquen "el ranking de corruptos" no lo encontrarán; la comunicación del producto debe explicar por qué esa ausencia es una feature.
