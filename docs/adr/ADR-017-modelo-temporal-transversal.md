# ADR-017 — Modelo temporal transversal: todo registro es versionado

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El Estado mexicano cambia constantemente: funcionarios entran y salen de cargos, leyes se reforman, presupuestos se ejercen por año, municipios cambian de partido cada trienio. Un sistema que solo modela "el presente" no puede responder quién ocupaba un cargo cuando se adjudicó un contrato, que es exactamente el tipo de cruce que da valor al proyecto (ej. la señal `puerta_giratoria`, §6). Además, las fuentes oficiales cambian o desaparecen, y datos como la población del INEGI se versionan por año de censo (viene el Censo 2030).

## Decisión

Todo registro del modelo canónico lleva vigencia (`valid_from`, `valid_to`) y fecha de observación, conforme a R9. El presente no es un estado especial: es el caso particular donde `valid_to` es nulo. El versionado temporal es transversal desde la Fase 2 en adelante, cuando nace la infraestructura real de scrapers, snapshots y versionado histórico; toda tabla nueva lo incorpora desde su diseño, no como migración posterior. Las capas poblacionales y toda métrica derivada (ej. gasto por habitante, §3 Fase 3) citan siempre el año y la versión de referencia.

## Alternativas descartadas

- **Modelo solo-presente con sobrescritura.** Pierde el histórico en cada actualización; imposibilita los cruces temporales que son la razón de ser de las Fases 5 y 6 y contradice el rol de archivo histórico del proyecto (§2).
- **Tablas de histórico separadas (snapshot tables por entidad).** Duplica esquema y consultas, y convierte el pasado en ciudadano de segunda clase; la vigencia en el propio registro mantiene una sola forma de consultar cualquier fecha.
- **Versionado solo en la capa de ingesta (snapshots crudos).** Los snapshots (ADR-018) preservan el documento, pero sin vigencia en L2 no se puede consultar el estado del mundo a una fecha dada sin reprocesar todo.

## Consecuencias

Toda consulta canónica se vuelve una consulta a una fecha, con el presente como default. Los joins llevan condición temporal, lo que añade complejidad a L2 y L3 pero habilita respuestas del tipo "quién firmaba cuando se adjudicó". La base crece porque nada se borra, empujando el límite del free tier de Supabase (§11). Los contratos congelados de la Fase 0 incluyen los campos temporales desde el inicio, de modo que ningún carril paralelo (§14) diseñe tablas sin vigencia.
