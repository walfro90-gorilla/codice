# Política de correcciones

> **Códice** — *Cómo funciona México.* by Gorilla Labs
>
> Este documento es un **contrato público**. Aplica desde la Fase 0 del proyecto y obliga
> a quienes mantenemos Códice frente a cualquier persona que use, cite o aparezca en
> nuestros datos. Los cambios a esta política se registran con la misma trazabilidad que
> cualquier otro dato del sistema.

Códice no emite veredictos: publica datos oficiales con procedencia completa (fuente,
fecha de captura y hash del documento crudo). Aun así, los datos pueden estar mal — por
error de la fuente, error de nuestro procesamiento o cambio posterior de la realidad.
Esta política define qué hacemos cuando eso pasa.

---

## 1. Cómo reportar un error en los datos

Cualquier persona puede reportar un error. No hace falta ser periodista, funcionario ni
afectado directo.

**Canal:** abrir un *Issue* en el repositorio público del proyecto con la etiqueta
**`corrección`**.

El reporte debe incluir:

1. **El enlace permanente** del dato cuestionado (ej. `https://codice.mx/nodo/{id}` o
   `https://codice.mx/senal/{uuid}`). Todo dato publicado en Códice tiene uno; si no
   puedes encontrarlo, descríbelo y nosotros lo localizamos.
2. **La fuente oficial que lo contradice**: URL del documento oficial (DOF, gaceta,
   portal de transparencia, resolución, etc.) y, de ser posible, la fecha y el fragmento
   relevante.
3. Opcionalmente, la fecha de consulta (`?en=YYYY-MM-DD`) si el error es sobre un estado
   histórico y no sobre el presente.

Un reporte sin fuente oficial que lo respalde no se descarta: se responde igual, pero la
corrección solo procede cuando existe un documento oficial verificable que la sustente.
"No hay fuente oficial para esto" es una respuesta válida del sistema (regla R6), y
también puede ser el resultado de una corrección.

---

## 2. Compromiso de tiempos de respuesta

| Etapa | Plazo máximo |
|---|---|
| Acuse de recibo del reporte | **3 días naturales** |
| Evaluación inicial (procede / no procede / falta información) | **10 días naturales** |
| Resolución y publicación de la corrección, si procede | **30 días naturales** |
| Derecho de réplica (ver §4): publicación de la réplica recibida | **5 días naturales** desde su recepción |

Si un caso requiere más tiempo (por ejemplo, esperar respuesta de una solicitud de
información pública), se documenta en el mismo Issue el motivo y el nuevo plazo estimado.
El Issue permanece abierto y visible mientras el caso no esté resuelto.

---

## 3. Cómo se registran las correcciones

**El valor equivocado nunca se borra en silencio.** Todo dato en Códice es temporal y
versionado (regla R9): corregir significa **agregar una nueva versión**, con su propia
vigencia y su propia procedencia, y cerrar la vigencia de la versión anterior.

Concretamente, una corrección produce:

- Un **nuevo registro** con el valor corregido, su `valid_from`, su fuente oficial (URL,
  fecha de captura, hash) y la referencia al Issue de corrección que lo originó.
- El **registro anterior conservado** con su `valid_to` cerrado. Sigue siendo consultable
  vía cita temporal (`?en=YYYY-MM-DD`) para cualquier fecha en la que estuvo vigente.
- Una **anotación de corrección** que enlaza ambas versiones y el Issue público donde se
  discutió.

Esto garantiza dos cosas: quien citó el dato antes de la corrección puede demostrar
exactamente qué decía Códice en esa fecha, y quien lo consulta después ve el dato
corregido junto con el historial completo. La transparencia sobre nuestros propios
errores es parte del producto, no una vergüenza a ocultar.

---

## 4. Derecho de réplica

Toda persona física o moral **nombrada por una señal** del motor de señales (o por
cualquier otro dato publicado en Códice) tiene derecho de réplica documentado.

- La réplica se solicita por el mismo canal (Issue con etiqueta `corrección`,
  indicando que se ejerce derecho de réplica) o por el correo de contacto publicado en
  el sitio, si la persona prefiere no usar un canal público para el primer contacto.
- La réplica se publica **junto al dato o señal que la motivó**, en la misma página del
  enlace permanente, con fecha de recepción, sin edición de fondo por nuestra parte
  (solo límites razonables de extensión y la exclusión de contenido ilegal o de datos
  personales de terceros).
- Publicar la réplica **no implica** que Códice valide o rechace su contenido. Códice no
  emite veredictos (regla R2): las señales son siempre "señal por verificar" y la réplica
  es parte del expediente que el lector evalúa por sí mismo.
- Si la réplica aporta una fuente oficial que contradice el dato, se procesa además como
  reporte de corrección conforme a §1–§3.

---

## 5. Cómo se muestran las correcciones en las páginas afectadas

En la página del enlace permanente de todo dato corregido:

- Un **aviso de corrección visible** en la parte superior del dato afectado, con la fecha
  de la corrección y un enlace al Issue público donde se documentó.
- El **historial de versiones** accesible desde la misma página: qué decía antes, qué
  dice ahora, con qué fuente cambió cada versión.
- Las **réplicas recibidas** (§4), publicadas junto al dato con su fecha de recepción.
- La **descarga de datos citable** de la página (`/nodos/{id}/datos` en el API) incluye
  las versiones y sus vigencias, de modo que la corrección también es legible por máquina.

Las correcciones nunca se aplican reescribiendo el pasado: la cita temporal
`?en=YYYY-MM-DD` siempre devuelve lo que Códice publicaba en esa fecha.

---

## 6. Qué no cubre esta política

- **Desacuerdos de interpretación.** Códice publica datos oficiales con fuente; no emite
  juicios que se puedan disputar como opinión. Si el desacuerdo es con la fuente oficial,
  la vía es la propia fuente; nosotros registramos lo que la fuente dice y cuándo lo dijo.
- **Solicitudes de eliminación de datos públicos.** Los datos de servidores públicos en
  ejercicio de funciones son públicos por ley. Las solicitudes que aleguen datos
  personales fuera de ese supuesto se evalúan caso por caso y se responden en los mismos
  plazos de §2.

---

*Este documento forma parte de la gobernanza pública de Códice (ver `CLAUDE.md` §12 y la
política de enlaces permanentes en `docs/enlaces-permanentes.md`).*
