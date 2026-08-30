# ADR-014 — Apache 2.0 para código, ODbL para datos

Estado: aceptada · Fecha: 2026-08-29

## Contexto

Códice es infraestructura cívica abierta con autoría institucional (Gorilla Labs) y contribuciones externas esperadas, incluida gente no programadora que agrega nodos con fundamento legal. El código y los datos son activos de naturaleza distinta: el código necesita protección frente a reclamos de patentes; la base de datos — el cruce curado de fuentes oficiales, que en casos como Fase 6 es dato propietario que no existe en ningún lado — necesita que las derivaciones sigan siendo abiertas y que la atribución sea obligatoria, porque la citabilidad es la razón de ser del proyecto (R10).

## Decisión

Código bajo **Apache 2.0**: licencia permisiva con concesión explícita de patentes, que protege a contribuyentes y usuarios de reclamos y es estándar en infraestructura abierta. Datos bajo **ODbL**: cualquier uso exige atribución y cualquier base de datos derivada debe compartirse bajo la misma licencia, lo que impide que un tercero cierre el trabajo de curaduría. CC-BY-SA queda como opción equivalente aceptada para contenidos donde ODbL no aplique bien.

## Alternativas descartadas

- **MIT para el código**: más corta, pero sin cláusula de patentes; en un proyecto que raspa y republica datos de gobierno, la cobertura explícita de Apache 2.0 vale las líneas extra.
- **GPL/AGPL para el código**: el copyleft fuerte desincentivaría reuso del cliente MCP y de los parsers en otros proyectos cívicos, que es justo lo que queremos que pase.
- **CC0 / dominio público para los datos**: maximiza reuso pero elimina la atribución obligatoria y permite silos cerrados derivados; para un proyecto cuyo valor es ser fuente citable, la atribución no es negociable.
- **Una sola licencia para todo**: las licencias de software aplican mal a bases de datos (el derecho sui generis de bases de datos no queda cubierto); separar por tipo de activo es la práctica establecida (OpenStreetMap usa exactamente este esquema).

## Consecuencias

Los archivos `LICENSE` (Apache 2.0) y `LICENSE-DATA` (ODbL) viven en la raíz del repo desde la Fase 0, y `CONTRIBUTING.md` declara que toda contribución se acepta bajo estas licencias. Cualquier medio o investigador puede reusar los datos citando a Códice, y los derivados permanecen abiertos. El costo es que ODbL es incompatible con algunos agregadores comerciales de datos que exigen relicenciamiento — incompatibilidad deliberada y asumida.
