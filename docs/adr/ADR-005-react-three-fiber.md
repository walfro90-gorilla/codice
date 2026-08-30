# ADR-005 — react-three-fiber sobre Three.js imperativo

Estado: aceptada · Fecha: 2026-08-29

## Contexto

La capa de visualización (L4) renderiza un grafo institucional con ~400–500 nodos en Fase 1, que crecerá hacia 2,500+ municipios en fases posteriores. El mismo nodo tiene dos posiciones —jerárquica en modo grafo y geográfica (lat/lng) en modo mapa— y al cambiar de modo se interpola, sin duplicar datos. Además, la escena Three convive con MapLibre GL en el mismo contexto WebGL, y el frontend es Next.js con estado en Zustand. Mantener sincronizado un árbol de escena imperativo con el estado de React (nodos que aparecen, filtros, transiciones de modo, agrupación por nivel de zoom) exige código de pegamento manual que crece con cada feature.

## Decisión

Usar **react-three-fiber (R3F)** como capa declarativa sobre Three.js para toda la escena 3D. La escena se expresa como componentes React: los nodos, aristas y capas se derivan del estado (Zustand) y R3F reconcilia los cambios contra el árbol de Three. Las optimizaciones necesarias —instancing para los 2,500+ municipios (que no pueden ser 2,500 draw calls), agrupación por zoom— se implementan dentro del modelo R3F, que expone las mismas primitivas de Three sin renunciar al render declarativo.

## Alternativas descartadas

- **Three.js imperativo puro**: gestionar a mano el ciclo de vida de cientos de objetos de escena sincronizados con el estado de la aplicación es, en palabras del propio CLAUDE.md, "un infierno de mantener" a 500 nodos; cada cambio de estado requiere código explícito de creación/actualización/destrucción y es fuente constante de fugas y desincronización.
- **Librerías de grafos 2D (D3, Sigma, etc.)**: no cubren el requisito de modo dual grafo/mapa interpolado sobre el mismo contexto WebGL que MapLibre, ni el rendering 3D con instancing.

## Consecuencias

- El estado de la escena vive en un solo lugar (Zustand) y el render se deriva de él; la interpolación grafo↔mapa se modela como cambio de datos, no como coreografía imperativa de objetos.
- Se acepta una dependencia adicional y su curva de aprendizaje (hooks de R3F, `useFrame`, reconciliación), a cambio de que el equipo trabaje con el mismo modelo mental de React en toda la capa L4.
- El rendimiento sigue siendo responsabilidad nuestra: R3F no exime del instancing ni de la agrupación por nivel de zoom; solo cambia dónde se escribe esa optimización.
- La integración con MapLibre GL (capa custom de Three en el mismo contexto) debe resolverse dentro del ecosistema R3F; cualquier limitación encontrada ahí se documentará como ADR nuevo antes de romper esta decisión.
