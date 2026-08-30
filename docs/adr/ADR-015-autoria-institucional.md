# ADR-015 — Open source con autoría institucional Gorilla Labs, no anónimo

Estado: aceptada · Fecha: 2026-08-29

## Contexto

Códice publica datos sobre dinero público, funcionarios y sanciones en un contexto donde el órgano garante de transparencia dejó de ser autónomo. Un proyecto así necesita ser creíble para periodistas y citable en trabajos serios (R10), y la credibilidad exige saber quién responde por el sistema. Al mismo tiempo, el proyecto quiere contribuciones abiertas de gente no programadora, lo que requiere una identidad pública estable que reciba y gobierne esas contribuciones.

## Decisión

El proyecto es open source con autoría institucional: *by Gorilla Labs*. El código se publica bajo Apache 2.0 y los datos bajo ODbL (ver ADR-014), con contribuciones abiertas guiadas por un `CONTRIBUTING.md` obligatorio que explica cómo agregar un nodo con su fundamento legal. Gorilla Labs firma el trabajo, mantiene la política de correcciones pública y el derecho de réplica documentado desde Fase 0 como contrato público, no como añadido posterior.

## Alternativas descartadas

- **Publicación anónima o seudónima.** Protegería a los autores, pero un sistema que emite señales sobre contratistas y funcionarios sin nadie que responda por él es imposible de citar con seriedad y vulnerable a la acusación de campaña encubierta. Sin autoría no hay derecho de réplica creíble.
- **Autoría personal individual.** Concentra el riesgo jurídico y reputacional en una persona y no escala a contribuciones abiertas; la institución sobrevive a los individuos.
- **Proyecto cerrado propietario.** Contradice la misión de infraestructura cívica abierta y elimina la auditoría pública del pipeline, que es parte de la defensa metodológica del proyecto.

## Consecuencias

Gorilla Labs asume la cara pública: responde correcciones, réplicas y cuestionamientos metodológicos. La marca institucional obliga a mantener la disciplina de las reglas R1–R10 en todo output, porque cada error se cobra contra la credibilidad de la institución completa. Las contribuciones externas pasan por revisión bajo la guía de `CONTRIBUTING.md`, y la infraestructura de Códice se despliega con credenciales separadas de otros proyectos de Gorilla Labs (§16).
