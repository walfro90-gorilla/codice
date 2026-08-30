# Esquema de enlaces permanentes

> **Códice** — *Cómo funciona México.* by Gorilla Labs
>
> Regla R10: **cada nodo tiene enlace permanente citable con su descarga de datos.**
> Si un periodista no lo puede citar, no sirve. Este documento define el contrato de URLs.

---

## 1. Formas de URL

| Recurso | Forma | Identificador |
|---|---|---|
| Nodo institucional | `https://codice.mx/nodo/{id}` | Slug permanente (ej. `secretaria-de-hacienda`) |
| Territorio | `https://codice.mx/territorio/{clave-inegi}` | Clave INEGI, nunca el nombre (R7). Ej. `09` (CDMX), `09015` (Cuauhtémoc) |
| Persona | `https://codice.mx/persona/{uuid}` | UUID |
| Señal | `https://codice.mx/senal/{uuid}` | UUID |

- Los **nodos** usan slugs legibles porque son la unidad de cita más frecuente.
- Los **territorios** usan la clave INEGI porque hay municipios homónimos: el nombre no
  identifica, la clave sí.
- Las **personas y señales** usan UUID: los nombres de personas no son únicos y las
  señales no tienen nombre natural.

## 2. Descarga de datos citable

Cada página de enlace permanente ofrece la descarga de sus datos completos en JSON,
servida por el API público:

```
GET https://api.codice.mx/v1/nodos/{id}/datos
```

La descarga incluye el nodo, sus relaciones, sus ocupantes, la licencia (ODbL 1.0),
la fecha de generación y `sources[]` con `{url, captured_at, hash}` para cada dato (R1).
Lo que se ve en la página y lo que se descarga es el mismo dato: la cita es verificable
por máquina.

## 3. Cita temporal (*as-of*)

Todo dato en Códice es temporal (R9). Cualquier enlace permanente acepta el parámetro
`?en=YYYY-MM-DD` y devuelve el estado del recurso **tal como era en esa fecha**:

```
https://codice.mx/nodo/secretaria-de-hacienda?en=2024-06-01
```

- Sin el parámetro, se muestra el estado presente (el presente es un caso particular).
- Las correcciones no reescriben el pasado: `?en=` siempre devuelve lo que Códice
  publicaba en esa fecha, incluidas las versiones luego corregidas (ver
  `docs/politica-de-correcciones.md` §3).
- Para una cita estable en el tiempo, **incluye siempre `?en=` con la fecha de consulta.**

## 4. Los enlaces permanentes nunca se rompen

Compromiso público:

- Los identificadores son **permanentes**. Un `id` de nodo, una clave INEGI, un UUID de
  persona o señal jamás se reutilizan ni se eliminan.
- Si una institución cambia de nombre, el slug viejo **redirige** (HTTP 301) al nuevo.
  El slug viejo sigue funcionando para siempre.
- Si una institución se extingue, su nodo no desaparece: queda con `valid_to` cerrado y
  su página lo indica. Extinguirse es un dato, no un motivo para romper la URL.
- Cambios a este esquema de URLs requieren un ADR y conservan compatibilidad: toda URL
  publicada alguna vez sigue resolviendo.

## 5. Formato de cita recomendado para periodistas

```
Códice (Gorilla Labs), "{título de la página}",
https://codice.mx/nodo/{id}?en=YYYY-MM-DD, consultado el {fecha}.
Datos: https://api.codice.mx/v1/nodos/{id}/datos
```

Ejemplo:

> Códice (Gorilla Labs), "Secretaría de Hacienda y Crédito Público",
> https://codice.mx/nodo/secretaria-de-hacienda?en=2026-08-29, consultado el 29 de
> agosto de 2026. Datos: https://api.codice.mx/v1/nodos/secretaria-de-hacienda/datos

Recomendaciones:

1. **Cita con `?en=`.** Es la única forma de que tu cita apunte exactamente a lo que
   viste, aunque el dato cambie después.
2. **Enlaza la descarga de datos**, no solo la página: permite a cualquiera verificar
   fuente, fecha de captura y hash de cada dato citado.
3. Códice publica **señales por verificar y datos oficiales con fuente, nunca
   veredictos** (R2). Al citar una señal, cítala como lo que es: una señal con su
   fundamento y evidencia, con estado `por_verificar`.
4. Los datos son ODbL 1.0: úsalos libremente con atribución y compartiendo igual.
