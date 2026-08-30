# Catálogo de fuentes de datos

> **Códice** — *Cómo funciona México.* by Gorilla Labs
>
> Toda afirmación de Códice apunta a una de estas fuentes oficiales, con URL, fecha de
> captura y hash del documento crudo (R1). Este catálogo es la versión pública y
> autocontenida de la tabla de fuentes del proyecto; la columna **Key** es el
> identificador estable de cada fuente en la base de datos y el API (`/fuentes`).

---

## Fuentes

| Key | Fuente | Qué da | Formato | Dificultad |
|---|---|---|---|---|
| `sil` | **SIL (Gobernación)** | Integración del Congreso, perfiles de legisladores, iniciativas, seguimiento de sesiones | HTML | Scraping. Sin API. |
| `leyfed` | **Cámara de Diputados — LEYFED** | Compilación completa de leyes federales vigentes | ZIP descargable | Media. Texto estructurado por artículos. |
| `ojn` | **Orden Jurídico Nacional** | Normativa federal, estatal y municipal | HTML | Scraping. Clave para nivel local. |
| `dof` | **DOF** | Publicación oficial, acuerdos del INE, reformas | HTML/PDF | Scraping. |
| `contrataciones_abiertas` | **Contrataciones Abiertas (SHCP)** | Licitaciones y adjudicaciones, estándar **OCDS**, desde 2017 | **JSON** ✅ | Baja. La mejor fuente de dinero. |
| `obra_publica_abierta` | **Obra Pública Abierta (SHCP)** | Proyectos de inversión federal **geolocalizados**, clave de cartera, presupuesto | Mapa + BD abiertas | Media. |
| `compranet_historico` | **CompraNet histórico (datos.gob.mx)** | Contratos y expedientes 2010–2022 | Descargable | Baja. |
| `pdn` | **PDN / SNA** ⭐ | **Sistema 1**: declaraciones patrimoniales y de intereses. **Sistema 2**: servidores públicos en contrataciones. **Sistema 3**: sancionados (personas y empresas) | **API real documentada** ✅ | Baja. Repos en GitHub org `PDNMX`. |
| `ine_padron` | **INE — Datos Abiertos** | Padrón de afiliados a partidos nacionales | Descargable ✅ | Baja. |
| `ine_sif` | **INE — Portal SIF** | Fiscalización: origen y destino de recursos de partidos y candidatos | Reportes descargables | Media. |
| `ine_acuerdos_cg` | **INE — Acuerdos CG (vía DOF)** | Distribución exacta de financiamiento por partido | PDF/HTML | Media. |
| `asf` | **ASF** ⚠️ | Auditorías, observaciones, pliegos, recuperaciones | **PDFs por auditoría** | **Alta.** Sin datos abiertos reales. Entrada: *Matriz de Datos Básicos consolidada* (índice tabular). Fundar publicó crítica pidiéndoles formatos abiertos. |
| `sat_69b` | **SAT — Lista 69-B** | Empresas que facturan operaciones simuladas (EFOS). **Trae RFC** | Descargable ✅ | Baja. Llave dura para matching. |
| `sfp_sancionados` | **Función Pública — Directorio de Sancionados** | Proveedores y contratistas inhabilitados | App web | Media. Scraping. |
| `pnt_sipot` | **PNT / SIPOT** | Directorio obligatorio de todos los sujetos obligados: nombre, cargo, remuneración, contacto institucional | Formato estandarizado ✅ | Media. **Ahorra 32 scrapers distintos.** |
| `inegi_censo` | **INEGI** (Censo y conteos) | Censo 2020, conteos por localidad | Descargable ✅ | Baja. Versionar por año (viene Censo 2030). |
| `inegi_marco_geo` | **INEGI** (Marco Geoestadístico) | Fronteras y claves oficiales de entidades, municipios y localidades | Descargable ✅ | Baja. Versionar por edición. |

> Nota: la fuente INEGI de la tabla original del proyecto se divide aquí en dos keys
> (`inegi_censo`, `inegi_marco_geo`) porque son productos con versionado y ciclo de
> actualización distintos; el contenido es el mismo de la tabla original.

Convención de keys: minúsculas, `snake_case`, prefijo del organismo cuando este publica
varias fuentes (`ine_*`, `inegi_*`). Las keys son permanentes: identifican la fuente en
la tabla de procedencia y en el endpoint `/fuentes` del API, y nunca se reutilizan.

---

## Huecos conocidos

Decir qué no sabemos es parte del producto (R6). **"No hay fuente oficial para esto" es
una respuesta válida y valiosa.** Estos son los huecos que conocemos y documentamos
públicamente:

- **Propiedad corporativa / beneficiario final.** El Registro Público de Comercio y el
  SIGER no son abiertos. Esto rompe la cadena de parentesco y empresas fantasma.
  *Parches parciales*: la lista 69-B (`sat_69b`) y el Directorio de Sancionados
  (`sfp_sancionados`).
- **Teléfono personal de legisladores.** No es obligación de transparencia. Solo se
  publica el contacto institucional.
- **Promesas cumplidas.** No existe como dato oficial en ninguna fuente. Se construye
  como dato propio del proyecto (Fase 6), cruzando plataformas electorales registradas
  ante el INE contra iniciativas presentadas (SIL), siempre con validación humana.

Si conoces una fuente oficial que cubra alguno de estos huecos, repórtala como Issue:
es la contribución más valiosa que este proyecto puede recibir.
