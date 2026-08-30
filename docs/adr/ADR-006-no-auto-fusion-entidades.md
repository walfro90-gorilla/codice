# ADR-006 — Nunca auto-fusionar entidades; tabla de candidatos con revisión humana

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El motor de cruces del proyecto conecta empresas y personas a través de fuentes heterogéneas: Contrataciones Abiertas, lista 69-B del SAT, Directorio de Sancionados, PDN, ASF. Los nombres de una misma empresa varían por sufijos societarios (`S.A. de C.V.`, `S. de R.L.`, `S.A.P.I. de C.V.`) y puntuación, y existen razones sociales casi idénticas que corresponden a entidades distintas. Fusionar mal dos empresas en un sistema que habla de dinero público cuesta la credibilidad del proyecto entero, y ninguna mejora de recall justifica ese riesgo.

## Decisión

El pipeline de resolución de identidades (normalización determinística → RFC como llave dura → similitud difusa con `pg_trgm`) **jamás fusiona automáticamente**. Su salida es la tabla `entity_match_candidates` con `score`, `method`, `status ∈ {pending, confirmed, rejected}`, `reviewed_by` y `reviewed_at`. Todo candidato nace en `pending`; la fusión efectiva solo ocurre cuando un humano la confirma, y queda registrado quién validó y cuándo (R3, R4). Cuando hay RFC en ambos lados, es la única llave de match aceptada y nunca se hace match difuso sobre esos registros.

## Alternativas descartadas

- **Fusión automática por umbral de score**: cualquier umbral produce falsos positivos eventualmente, y un solo falso positivo visible (atribuir un contrato o una sanción a la empresa equivocada) destruye la citabilidad del sistema; el costo del error es asimétrico frente al costo de revisar.
- **Que el LLM decida las fusiones**: viola R4 directamente; el LLM puede proponer candidatos con score de confianza, pero no existe camino en el que su salida modifique el grafo canónico sin validación humana registrada.
- **No hacer matching y dejar entidades duplicadas**: rompe el cruce estrella del proyecto (obra → contrato → empresa → observaciones ASF → sanciones); el matching es necesario, lo que se rechaza es su automatización final.

## Consecuencias

- La revisión humana se vuelve un cuello de botella deliberado: el volumen de candidatos pendientes es una métrica operativa a vigilar, y la normalización determinística (que resuelve ~60%) más el RFC existen precisamente para minimizar lo que llega a revisión difusa.
- Cada fusión es auditable: se puede reconstruir quién la aprobó, cuándo y con qué método/score se generó el candidato, lo que permite deshacer errores y responder a derecho de réplica.
- El esquema y el API deben tratar los candidatos `pending` como no-vínculos: ningún cruce publicado puede apoyarse en un match sin confirmar.
- Se necesita tooling de revisión (aunque sea mínimo) para que confirmar/rechazar candidatos sea barato; sin él, la cola crece y la regla se vuelve tentación de saltarse.
