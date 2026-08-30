# ADR-000 — Nombre del proyecto: Códice

Estado: aceptada · Fecha: 2026-08-29

## Contexto

El proyecto necesita un nombre desde el commit 1: define el repo, el paquete npm, el dominio y la identidad pública de una infraestructura cívica que aspira a ser citada por periodistas e investigadores. El nombre debe comunicar el *qué* del producto —un sistema que explica cómo funciona el Estado mexicano— sin sesgarlo hacia una sola de sus caras (didáctica e investigativa). También debe funcionar en prosa en español y como identificador técnico sin fricción.

## Decisión

El proyecto se llama **Códice**, con el tagline *"Cómo funciona México"*. Los códices mesoamericanos explicaban cómo funcionaba el mundo; este explica cómo funciona México — la metáfora es directa y describe el producto, no el proceso. Convención de escritura: `Códice` con acento en prosa, UI y documentación; `codice` sin acento en identificadores técnicos (repo, paquete npm, dominio, nombres de tablas). La autoría es institucional: *by Gorilla Labs*.

## Alternativas descartadas

- **Tequio**: describe el *cómo* (trabajo comunitario, contribución colectiva) pero no el *qué* del producto.
- **Tlacuilo**: fricción ortográfica alta; difícil de escribir, pronunciar y buscar para el público general.
- **Atlas-MX**: sesga la percepción hacia lo geográfico, cuando el mapa es solo uno de los dos modos de visualización (grafo jerárquico y mapa).

## Consecuencias

El nombre queda congelado en repo, dominio y paquete npm; cambiarlo después tendría costo alto en enlaces permanentes citables (R10), así que esta decisión se toma antes de publicar nada. La convención acento/sin-acento evita inconsistencias entre prosa e identificadores y debe respetarse en todo el código y la documentación. El tagline fija la promesa del producto: explicar, no juzgar, en línea con la regla de nunca emitir veredictos (R2).
