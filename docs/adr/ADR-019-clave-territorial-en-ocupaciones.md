# ADR-019 — Clave INEGI en las ocupaciones, y territorio nulo para representación proporcional

Estado: aceptada · Fecha: 2026-08-30

## Contexto

La Fase 2 trajo 627 legisladores. Las fuentes oficiales nombran la entidad que representan en prosa y con nombres cortos: la Cámara escribe `Coahuila` y `Veracruz`, el Senado `Estado de México`, mientras el catálogo del INEGI usa `Coahuila de Zaragoza`, `Veracruz de Ignacio de la Llave` y `México`. Guardar solo ese texto deja la ocupación desconectada del territorio: no se puede unir a población, geometría ni, más adelante, a gasto.

R7 ya obliga a usar la clave INEGI como identificador territorial, pero el contrato de `tenure` congelado en la Fase 0 no tenía dónde ponerla, porque en ese momento no existían ocupaciones.

Hay además un caso que no es una discrepancia de nombre sino de naturaleza: las 200 diputaciones y 32 senadurías de representación proporcional se eligen en una circunscripción nacional. La fuente escribe `Lista Nacional`, que no es una entidad federativa y no tiene clave.

## Decisión

Se agrega `territory_key` a `tenure`, con llave foránea a `territory(inegi_key)` (migración `0002_tenure_territory.sql`).

La normalización resuelve el nombre de la fuente contra el catálogo del INEGI de forma determinística: coincidencia exacta sobre el nombre normalizado, y si falla, coincidencia por prefijo contra el nombre oficial. El nombre tal como lo publica la fuente se conserva en `role` y, sin alteración alguna, en el snapshot.

**`territory_key` nulo es un valor con significado**: representa un cargo electo en la circunscripción nacional, no un dato faltante. No se inventa una entidad para rellenarlo (R6).

## Alternativas descartadas

- **Guardar solo el nombre de la fuente.** Es lo que ya hacía y es justo lo que R7 prohíbe: hay municipios homónimos y entidades con varios nombres de uso corriente. Un cruce por nombre produce afirmaciones falsas en cuanto cambia el texto de la fuente.
- **Una tabla de alias de entidades.** Treinta y dos entidades con cuatro discrepancias conocidas no justifican una tabla; la coincidencia por prefijo sobre el nombre oficial las resuelve todas y no hay que mantener nada.
- **Asignar una entidad ficticia a la representación proporcional** (por ejemplo la del domicilio del legislador). Sería inventar un dato que la elección no produce.
- **Esperar a la Fase 3.** Corregir el modelo después obliga a migrar datos ya publicados y a romper enlaces citables.

## Consecuencias

- Una ocupación se puede unir con población y geometría, lo que habilita métricas por habitante sin cruces por nombre.
- Todo consumidor debe tratar `territory_key` nulo como "electo en circunscripción nacional", no como dato ausente. Queda documentado en el catálogo de fuentes y verificado por pruebas.
- Cambiar el contrato exigió este ADR y una migración nueva; la migración `0001` permanece inmutable, según la convención del repo.
