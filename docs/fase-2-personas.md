# Fase 2 — Personas

Estado: **Congreso federal completo** (30 de agosto de 2026). 627 legisladores en funciones, cada uno con partido, periodo y contacto institucional, trazables a un snapshot con hash.

## Qué contiene

| Nodo | Ocupantes | Fuente |
|---|---|---|
| `camara-diputados` | 500 (300 mayoría relativa + 200 representación proporcional, Art. 52) | SITL, Cámara de Diputados |
| `senado` | 127 (63 MR + 32 primera minoría + 32 RP) | Directorio del Senado |

Por partido, sumando ambas cámaras: MORENA 319, PAN 90, PVEM 76, PT 55, PRI 49, MC 35, y 3 escaños sin grupo parlamentario.

## El versionado temporal ya es transversal (R9)

Cada ocupación es un registro con `start_date` y `end_date`, así que "quién ocupaba este cargo" es una consulta con fecha, no un hecho del presente:

```sql
SELECT p.full_name, t.party
FROM tenure t JOIN person p ON p.id = t.person_id
WHERE t.node_id = 'senado'
  AND t.start_date <= '2025-01-15'
  AND (t.end_date IS NULL OR t.end_date >= '2025-01-15');
-- 127 filas; la misma consulta con fecha 2020-01-15 devuelve 0
```

## Decisiones de datos

**Solo contacto institucional.** Las fichas oficiales publican fecha de nacimiento, domicilio de oficina y el correo del secretario particular. El registro guarda únicamente el correo institucional de la persona titular: los datos de terceros y los personales no aportan al objetivo del proyecto y sí aumentan el daño posible de un error. Hay una prueba automatizada que falla si alguno se cuela.

**Claves de partido normalizadas.** La Cámara escribe `VERDE` y el Senado `PVEM` para el mismo partido. La capa de normalización unifica a una clave canónica — sin eso, ningún cruce entre cámaras funciona. El valor crudo se conserva en el snapshot.

**"Sin grupo" no es un partido.** Los 3 escaños sin grupo parlamentario quedan con partido nulo, no con una etiqueta inventada (R6).

**Nunca fusión automática de personas.** La coincidencia por nombre normalizado detecta colisiones dentro de una misma ingesta y las reporta; unir a una persona entre fuentes distintas requiere revisión humana registrada (R3). La `ñ` se colapsa a `n` a propósito: las fuentes oficiales la sirven con encoding roto y un normalizador estricto no cruzaría un origen limpio contra uno dañado.

## Infraestructura de scrapers

Ambos scrapers implementan `fetch_raw()` → `store_snapshot()` → `parse()` como pasos separados. Detalles que costaron y quedan documentados:

- **Cadena TLS incompleta.** `sitl.diputados.gob.mx` sirve un certificado válido pero omite el intermedio. Se versiona el intermedio de la CA en `ingestion/codice_ingestion/certs/` y se completa la cadena; **nunca se desactiva la verificación**. Un snapshot que no verificó TLS es un snapshot en el que no se puede confiar (ADR-018).
- **Transporte curl.** Los WAF de estos hosts responden 403 o un ciclo infinito de redirecciones a `urllib`, y aceptan la misma petición vía `curl`. La verificación de certificado sigue activa con un bundle explícito.
- **Cortesía.** Intervalo mínimo de 1.5 s por host y User-Agent identificable con URL de contacto, en el mismo formato que usan los crawlers públicos.

## Huecos conocidos (R6)

- **Congresos locales y ayuntamientos**: los 32 congresos y los municipios aún no tienen ocupantes. La vía es SIPOT/PNT, que ahorra escribir 32 scrapers distintos.
- **Titulares del Ejecutivo**: las 22 dependencias federales no tienen persona asignada todavía.
- **Una senaduría vacante**: la fuente oficial reporta 63 de mayoría relativa, no 64. Se registra lo que dice la fuente.
- **14 senadurías sin correo publicado**: la fuente no lo trae; el campo queda nulo en vez de inventarse.
- **Sin historial anterior a 2024**: solo la legislatura en funciones. Las anteriores requieren otras vistas del SITL.
