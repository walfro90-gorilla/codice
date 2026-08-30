# ADR-004 — MapLibre GL sobre Google Maps y Leaflet

Estado: aceptada · Fecha: 2026-08-29

## Contexto

La visualización es dual: modo grafo (jerárquico, posiciones calculadas por nivel) y modo mapa (geográfico real, lat/lng), con un solo nodo que tiene dos posiciones e interpola al cambiar de modo (§3, Fase 0). Eso exige que la capa de nodos Three.js y el mapa base compartan **el mismo contexto WebGL** — con scroll = zoom, agrupación por nivel de zoom e instancing para que 2,500+ municipios no sean 2,500 draw calls. El proyecto además vive en free tiers y es open source, así que la licencia y el costo del mapa importan.

## Decisión

**MapLibre GL** como mapa base, con una capa custom de Three (vía react-three-fiber) renderizando en el mismo contexto WebGL. MapLibre es open source (fork de Mapbox GL bajo licencia libre), renderiza vectorial por WebGL, soporta custom layers que exponen el contexto GL, y no impone costos por carga ni términos de uso que comprometan un proyecto cívico.

## Alternativas descartadas

- **Google Maps**: descartado por licencia y costo. El pricing por carga de mapa es incompatible con un proyecto gratuito de tráfico impredecible, y sus términos restringen cómo se superponen y reutilizan los datos.
- **Leaflet**: descartado por ser 2D con render DOM/Canvas en contexto separado del de Three. Imposibilita la interpolación grafo↔mapa en un solo contexto WebGL y no escala a miles de nodos con instancing.

## Consecuencias

La interpolación entre modo grafo y modo mapa se implementa sin duplicar datos ni sincronizar dos renderers: un solo canvas, una sola escena. Hay que mantener la integración MapLibre↔Three (matrices de proyección de la custom layer), que es el punto técnico más delicado del frontend. Los tiles vectoriales deben venir de un proveedor compatible con MapLibre (p. ej. tiles propios u OpenStreetMap vía proveedor libre), lo cual queda como decisión operativa posterior.
