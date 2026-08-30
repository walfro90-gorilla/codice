# ADR-018 — Snapshots con hash como activo central (contexto post-extinción del INAI)

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El INAI se extinguió el 20 de marzo de 2025 y sus funciones pasaron a Transparencia para el Pueblo, órgano desconcentrado de la Secretaría Anticorrupción y Buen Gobierno: el órgano garante de transparencia ya no es autónomo, es parte del Ejecutivo. Eso significa que las fuentes oficiales pueden cambiar, reescribirse o desaparecer sin contrapeso institucional. En ese escenario, guardar copias fechadas y verificables de cada documento deja de ser buena práctica de ingeniería y se convierte en la función histórica del proyecto.

## Decisión

La capa de snapshots crudos —archivo tal cual, con URL de origen, fecha de captura y hash— es el activo central de Códice, no un detalle de infraestructura. Todo scraper implementa `fetch_raw()` → `store_snapshot()` → `parse()` como pasos separados (§15), y L1 nunca parsea (R8): primero se preserva el documento intacto en Cloudflare R2, después se procesa. Toda afirmación publicada apunta a su snapshot (R1), y todo endpoint del API devuelve `sources[]` con `{url, captured_at, hash}`. Si una fuente cambia o desaparece, Códice es el archivo histórico.

## Alternativas descartadas

- **Guardar solo el dato parseado.** Cuando el parser falle —y va a fallar— el documento original ya no existe y el histórico es irreproducible; además la afirmación queda sin procedencia verificable, violando R1.
- **Blobs crudos en Postgres.** Revienta el free tier y mezcla archivo con base transaccional; R2 da 10 GB gratis con cero egress y está prohibido guardar PDFs o HTML crudo en Postgres (§16).
- **Confiar en archivos de terceros (Wayback Machine, caches).** Útiles como corroboración, pero no cubren descargas ZIP/JSON ni portales dinámicos, y el proyecto no puede delegar su activo central a un servicio que no controla ni garantiza el hash.

## Consecuencias

El costo de almacenamiento crece de forma permanente, pero R2 lo hace marginal y el egress cero permite servir los crudos públicamente. Cualquier dato puede reprocesarse desde su snapshot cuando mejoren los parsers, sin volver a depender de que la fuente siga en línea. El hash permite a cualquier tercero verificar que el documento citado no fue alterado, lo que blinda al proyecto frente a disputas sobre qué decía una fuente en una fecha dada. El pipeline de scrapers corre en GitHub Actions sobre repos públicos, de modo que la captura misma es auditable.
