# Captura de nombramientos

Extensión de Chrome que arma la entrada de [`data/titulares.yaml`](../../data/titulares.yaml) a partir del documento oficial que tengas abierto, para no teclear sesenta veces la misma estructura.

## Qué hace y qué no

**Hace:** cuando tú abres un acuerdo de nombramiento y haces clic en el ícono, lee **esa** página, extrae su título, fecha y URL canónica, y te deja llenar el nodo, el nombre y el cargo. Copias el YAML y lo pegas en el repo.

**No hace:** navegar sola, recorrer listados, ni recolectar en segundo plano. No puede: el único permiso de lectura es `activeTab`, que Chrome concede exclusivamente a la pestaña activa **en el momento en que haces clic** y se revoca al salir. Sin ese clic la extensión no ve nada.

Eso no es un detalle de implementación, es el punto. Varias fuentes de datos públicos de México rechazan clientes automatizados —ComprasMX firma cada petición, CompraNet pide reCAPTCHA, gob.mx corre Akamai— y Códice no reconstruye esos mecanismos ([por qué](../../docs/hueco-contrataciones.md)). Esta herramienta no automatiza el acceso: automatiza la transcripción de lo que una persona ya está viendo, que es donde de verdad se va el tiempo. Hay un humano decidiendo cada página, y es quien responde por lo que se registra.

## Instalar

1. `chrome://extensions` → activa **Modo de desarrollador**
2. **Cargar descomprimida** → elige esta carpeta
3. Fija el ícono en la barra para tenerlo a mano

## Usar

1. Abre el acuerdo de nombramiento —el DOF, la declaratoria de un congreso local, lo que acredite el cargo.
2. Si el nombre de la persona está en el texto, **selecciónalo** con el cursor: la extensión lo toma.
3. Clic en el ícono. Verás el título, la fecha y la URL ya extraídos.
4. Elige el nodo del catálogo, revisa nombre y cargo, ajusta la fecha de **toma de posesión** (que casi nunca es la de publicación).
5. **Copiar YAML** y pégalo en `data/titulares.yaml`.
6. Valida antes del PR:

   ```bash
   cd normalization && .venv/bin/python -m codice_normalization validate ../data
   ```

## Lo que la extensión no decide

Propone; tú confirmas (R4). En particular **no adivina el nombre de la persona** a partir del texto del acuerdo: los acuerdos mencionan a varias personas —quien nombra, quien es nombrada, a veces a quien sustituye— y equivocarse ahí es publicar que alguien ocupa un cargo que no ocupa. Si seleccionas texto, lo usa; si no, lo escribes tú.

La fecha que extrae es la de **publicación** del documento. El campo `desde` es la **toma de posesión**, y son distintas: la extensión las separa y te pide la segunda.

## Catálogo de nodos

Se descarga de `https://codice-tan.vercel.app/data/grafo.json`, el mismo conjunto publicado. Si no hay red, puedes escribir el id del nodo a mano.
