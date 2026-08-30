# ADR-016 — El LLM propone, el humano decide. Siempre con score y auditoría

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El proyecto usa LLMs en tres trabajos (§10): extracción estructurada de PDFs de la ASF, resumen ciudadano de artículos de ley y vínculo promesa↔iniciativa. Los LLMs alucinan, y Códice habla de dinero público, empresas y funcionarios: fusionar mal dos empresas o afirmar un vínculo inexistente cuesta la credibilidad del proyecto entero (§5). La regla R4 ya fija el principio; esta decisión lo vuelve arquitectura.

## Decisión

Ningún output de LLM entra al dato canónico sin validación humana registrada. El LLM genera *candidatos* con `score` de confianza y método; el registro nace en estado `pending_review` y solo un humano lo mueve a `confirmed` o `rejected`, guardando `reviewed_by` y `reviewed_at` (tabla `entity_match_candidates` y equivalentes). Aplica igual al matching de entidades (R3), al vínculo promesa↔iniciativa (§7) y a cualquier cruce futuro. Los trabajos de bajo riesgo (resúmenes cacheados, extracción de PDFs) se guardan como dato versionado y revisable, nunca se generan en vivo frente al usuario.

## Alternativas descartadas

- **Auto-fusión sobre umbral de score alto.** Un umbral no elimina falsos positivos, solo los esconde; y un solo falso positivo publicado sobre dinero público es fatal. Rechazado por R3.
- **LLM en vivo respondiendo consultas de usuario.** Costo por consulta e imposibilidad de auditar cada respuesta. En el Contrastador (Fase 7) el LLM solo extrae entidades y cifras de la afirmación; los datos que se devuelven son propios, con fuente y fecha.
- **Validación humana sin registro.** Sin `reviewed_by`/`reviewed_at` no hay trazabilidad de quién decidió, y la procedencia (R1) aplica también a las decisiones editoriales.

## Consecuencias

El pipeline gana una cola de revisión humana como componente permanente: el throughput de fusiones y vínculos lo limita la capacidad de revisión, no el modelo. Cada validación queda auditada, lo que permite responder públicamente por qué existe cualquier vínculo publicado. El costo de LLM se mantiene acotado porque todo se procesa una vez y se versiona (§10), y el sistema puede citar al revisor humano como parte de la cadena de evidencia.
