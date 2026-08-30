# ADR-010 — Clave INEGI como ID territorial canónico

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El sistema modela entidades, municipios y localidades como nodos con datos poblacionales, presupuestales y geográficos. México tiene municipios homónimos (varios "Benito Juárez", "Hidalgo", "Guadalupe"), y los nombres además cambian de grafía entre fuentes: con o sin acentos, con abreviaturas, con el estado pegado. Cualquier cruce entre fuentes que use el nombre como llave produce colisiones o huecos silenciosos. El INEGI publica el Marco Geoestadístico con claves oficiales estables por entidad (2 dígitos), municipio (3) y localidad (4), versionadas por año.

## Decisión

La clave INEGI es el identificador territorial canónico en todas las capas: tablas de Postgres, respuestas del API, archivos Parquet y enlaces permanentes. El nombre es un atributo descriptivo, nunca una llave de cruce ni de deduplicación (regla R7). Las claves se versionan por año del Marco Geoestadístico, consistente con el modelo temporal del proyecto (R9), porque los municipios se crean y se fusionan.

## Alternativas descartadas

- **Nombre normalizado como llave**: los homónimos lo rompen de raíz; ninguna normalización distingue dos municipios que se llaman igual.
- **IDs propios autoincrementales**: agregan una capa de mapeo que cada fuente externa tendría que traducir, y rompen la citabilidad — un periodista no puede verificar un ID inventado contra una fuente oficial.
- **Códigos postales o claves electorales (secciones INE)**: no son jerárquicos entidad→municipio→localidad y no cubren el mismo universo territorial.

## Consecuencias

Todo cruce territorial entre fuentes (censo, obra pública geolocalizada, presupuesto) se hace por clave, lo que elimina una clase entera de errores de matching. Los scrapers deben resolver la clave INEGI en la capa de normalización (L2) antes de publicar; una fila sin clave resoluble se marca como pendiente, no se adivina. El Marco Geoestadístico se ingiere versionado por año, con lo que el Censo 2030 entra como nueva versión sin migración destructiva.
