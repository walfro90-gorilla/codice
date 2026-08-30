# ADR-009 — Contrastador, no verificador de verdad/mentira

Estado: aceptada · Fecha: 2026-08-29

## Contexto

La Fase 7 ofrece una herramienta donde el usuario pega una afirmación política y el sistema responde con datos. Un "verificador" al estilo fact-checking emite veredictos (verdadero/falso/engañoso), lo cual viola R2 y convierte al proyecto en árbitro editorial en lugar de infraestructura de datos citable. Además, muchas afirmaciones políticas no son binarias: dependen de si la cifra es nominal o real, per cápita o total, y del año base elegido — matices que un veredicto aplasta.

## Decisión

Construir un **contrastador**: el usuario pega la afirmación y el sistema devuelve **los datos oficiales relevantes con fuente y fecha**, sin veredicto. El LLM tiene un rol estrictamente acotado: extraer entidades, años y cifras mencionadas en la afirmación; después el sistema consulta exclusivamente datos propios, nunca el conocimiento del modelo. La salida incluye obligatoriamente advertencias metodológicas (nominal vs. real, per cápita vs. total, año base). Cero adjetivos, cero semáforo: que el dato hable.

## Alternativas descartadas

- **Verificador con veredicto (verdadero/falso/engañoso)**: emite juicios editoriales, viola R2, y expone al proyecto a disputas sobre el veredicto en vez de sobre los datos; el valor diferencial del proyecto es la procedencia, no la opinión.
- **Semáforo o score de veracidad**: es el mismo veredicto comprimido en un color o número, prohibido por §16 como resumen de juicio político.
- **Dejar que el LLM responda con su propio conocimiento**: el modelo alucinaría cifras y fuentes; su única tarea es la extracción estructurada de la afirmación, y toda cifra mostrada proviene de la base propia con `sources[]` (§15).

## Consecuencias

- Cada respuesta es citable y auditable: los datos devueltos llevan fuente, fecha de captura y enlace al documento, cumpliendo R1 y R10; si no hay fuente oficial para la afirmación, decirlo es la respuesta correcta (R6).
- Las advertencias metodológicas son parte del contrato de salida, no un footer opcional: comparar cifras sin fijar nominal/real o año base induce a error aunque los números sean correctos.
- El sistema renuncia al atractivo mediático del veredicto; a cambio, ningún actor puede acusarlo de sesgo editorial: solo exhibe datos oficiales junto a la afirmación.
- El alcance del LLM queda técnicamente delimitado a extracción; cualquier ampliación de ese rol (por ejemplo, redactar conclusiones) requiere revisar este ADR y las reglas R2/R4 antes de escribir código.
