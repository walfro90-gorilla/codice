# ADR-008 — Escalera de evidencia para promesas; prohibido el porcentaje de cumplimiento

Estado: aceptada · Fecha: 2026-08-29

## Contexto

La Fase 6 cruza plataformas electorales registradas ante el INE contra iniciativas presentadas en el SIL — un dato que no existe oficialmente en ningún lado y que es propietario del proyecto. La tentación obvia es resumirlo en un "% de promesas cumplidas", pero ese número esconde juicios arbitrarios: qué cuenta como cumplida, cómo se pondera una promesa vaga contra una concreta, y qué pasa con etapas intermedias. Un porcentaje agregado es un veredicto político disfrazado de métrica, y el proyecto no emite veredictos (R2, R5).

## Decisión

Cada promesa se modela como un nodo cuya relación con la realidad es una **escalera de estados verificables**, donde cada peldaño exige un documento con folio y fecha:

```
sin_evidencia → iniciativa_presentada → dictaminada_en_comision
             → aprobada → publicada_dof → presupuesto_asignado
```

El vínculo promesa↔iniciativa lo propone un LLM con score de confianza y lo confirma un humano (R4, ADR-016). El usuario ve la cadena completa de evidencia y saca su propia conclusión. **Nunca se publica un porcentaje de cumplimiento** ni ninguna métrica agregada que lo sustituya (R5).

## Alternativas descartadas

- **Porcentaje de cumplimiento por actor o partido**: exige decidir arbitrariamente qué es "cumplir" y cómo ponderar promesas heterogéneas; el número resultante es indefendible metodológicamente y funciona como semáforo político, prohibido por §16.
- **Clasificación binaria cumplida/incumplida**: pierde toda la información intermedia (una iniciativa presentada pero congelada en comisión es un hecho relevante) y hereda el mismo problema de veredicto.
- **Vincular promesas a iniciativas de forma automática por el LLM**: viola R4; el matching semántico entre lenguaje de campaña y lenguaje legislativo es exactamente el terreno donde el LLM alucina con confianza.

## Consecuencias

- Cada estado de la escalera es auditable: hay un documento oficial con folio y fecha detrás de cada transición, lo que hace la cadena citable (R10) y trazable (R1).
- El estado `sin_evidencia` es un dato en sí mismo (R6): documenta explícitamente qué promesas no tienen rastro oficial, sin afirmarlas incumplidas.
- La carga interpretativa se transfiere al lector con la evidencia completa a la vista; el sistema renuncia deliberadamente al titular fácil a cambio de credibilidad.
- El modelo de datos debe soportar promesas con múltiples iniciativas asociadas y vigencia temporal (R9); la escalera es por vínculo verificado, no un campo suelto en la promesa.
