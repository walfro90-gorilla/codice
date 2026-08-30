# Hueco documentado: contrataciones públicas federales

**Fecha del reconocimiento: 30 de agosto de 2026.**

El catálogo de fuentes de este proyecto clasificaba Contrataciones Abiertas como la mejor fuente de dinero: JSON en estándar OCDS, dificultad baja. **Ese diagnóstico ya no se sostiene.** Ninguna de las vías federales de contrataciones admite hoy acceso automatizado, y ese hallazgo es en sí mismo información pública relevante (R6).

## Qué se probó y qué respondió cada fuente

| Fuente | Resultado | Barrera |
|---|---|---|
| **ComprasMX** (`comprasmx.buengobierno.gob.mx`) — sistema vigente | El portal carga; el catálogo de descargas se sirve por una API interna que responde `401 Unauthorized` | La aplicación firma cada petición con encabezados `grc`, `igrc` y `xgrc` generados por el cliente. Es un mecanismo anti-automatización. |
| **CompraNet histórico** (`historico-compranet.buengobierno.gob.mx`) — contratos anteriores | El portal carga; la consulta exige resolver un desafío | **reCAPTCHA** invisible de Google en el flujo de búsqueda |
| **datos.gob.mx** — catálogo nacional de datos abiertos | `Access Denied` incluso desde un navegador real | WAF de Akamai |
| **Plataforma Digital Nacional** — API documentada del SNA | Especificación pública en GitHub (`PDNMX/api_docs`); los endpoints productivos devuelven 404 y la raíz exige `/auth` | Requiere registro y credenciales institucionales |
| **Contratos Abiertos CDMX** (`contratosabiertos.cdmx.gob.mx`) — OCDS estatal | Sin respuesta (tiempo de espera agotado) | El servicio no respondió durante el reconocimiento |

## Por qué no se rodearon esas barreras

Un `reCAPTCHA` y un encabezado de firma generado por el cliente son la forma en que un sitio declara que no quiere clientes automatizados en ese camino. Códice no reconstruye esos mecanismos: hacerlo convertiría al proyecto en algo que sus propias fuentes rechazan, y pondría en riesgo la legitimidad que sostiene todo lo demás.

La misma disciplina aplica en sentido contrario, y por eso conviene decirlo aquí: cuando un servidor omitió su certificado intermedio de TLS, la respuesta fue **completar la cadena** y seguir verificando, nunca desactivar la verificación. Se resuelven problemas técnicos; no se eluden decisiones de acceso.

## Qué sí se puede hacer

1. **Solicitar acceso a la Plataforma Digital Nacional.** Es la vía institucional y su especificación ya está publicada; el trabajo de integración es pequeño una vez que existen credenciales.
2. **Solicitud de información vía Transparencia para el Pueblo**, pidiendo las bases de contrataciones en formato abierto. La respuesta —y su demora— también son dato.
3. **Cuenta Pública**, que sí es accesible y ya está ingerida: no da contratos individuales, pero sí el gasto ejercido por ramo, que es la mitad de la pregunta.

## Consecuencia para el plan

El **cruce estrella** del proyecto —obra pública geolocalizada → contrato → empresa adjudicada → observación de la ASF → sanciones— depende de esta capa. Queda bloqueado en su primer eslabón hasta que exista acceso.

Se documenta aquí en vez de simplificarse en silencio, porque "no hay fuente accesible para esto" es una respuesta válida y, en este caso, es también un dato sobre el estado de la transparencia en contrataciones públicas.
