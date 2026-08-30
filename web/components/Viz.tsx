"use client";
/**
 * Dual-mode container: MapLibre basemap behind a transparent R3F canvas.
 *
 * ponytail: the basemap lives in its own WebGL context and is only roughly
 * aligned with the scene at the initial framing — zooming the canvas does not
 * move the map. Upgrade path: render the R3F scene as a MapLibre custom layer
 * sharing ONE WebGL context so both cameras stay in sync (ADR-004).
 */
import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import { Canvas } from "@react-three/fiber";
import Scene from "./Scene";
import { CAMERA_ZOOM, EDGE_COLORS, LEVEL_COLORS, MAP_CENTER, MAP_ZOOM } from "../lib/data";
import { useVizStore } from "../lib/store";
import type { VizMode } from "../lib/store";

const panelStyle: React.CSSProperties = {
  background: "rgba(11, 15, 20, 0.85)",
  border: "1px solid #1f2937",
  borderRadius: 8,
  padding: "10px 14px",
  fontSize: 13,
  lineHeight: 1.7,
};

function Dot({ color }: { color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 10,
        height: 10,
        borderRadius: "50%",
        background: color,
        marginRight: 6,
      }}
    />
  );
}

function Line({ color }: { color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 16,
        height: 3,
        background: color,
        marginRight: 6,
        verticalAlign: "middle",
      }}
    />
  );
}

export default function Viz() {
  const mode = useVizStore((s) => s.mode);
  const setMode = useVizStore((s) => s.setMode);
  const mapDiv = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapDiv.current!,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: MAP_CENTER,
      zoom: MAP_ZOOM,
      interactive: false,
    });
    return () => map.remove();
  }, []);

  const modeButton = (m: VizMode, label: string) => (
    <button
      onClick={() => setMode(m)}
      style={{
        padding: "6px 16px",
        borderRadius: 6,
        border: "1px solid " + (mode === m ? "#fbbf24" : "#374151"),
        background: mode === m ? "#fbbf24" : "transparent",
        color: mode === m ? "#0b0f14" : "#e5e7eb",
        fontWeight: 600,
        cursor: "pointer",
      }}
    >
      {label}
    </button>
  );

  return (
    <div style={{ position: "fixed", inset: 0, overflow: "hidden" }}>
      <div
        ref={mapDiv}
        style={{
          position: "absolute",
          inset: 0,
          opacity: mode === "mapa" ? 1 : 0,
          transition: "opacity 500ms",
        }}
      />
      <Canvas
        orthographic
        camera={{ zoom: CAMERA_ZOOM, position: [0, 0, 100], near: 0.1, far: 1000 }}
        gl={{ alpha: true, antialias: true }}
        style={{ position: "absolute", inset: 0 }}
        // Dev-only escape hatch: lets tooling advance frames when rAF is
        // throttled (hidden tab). Harmless in production builds.
        onCreated={(state) => {
          if (process.env.NODE_ENV !== "production") (window as unknown as Record<string, unknown>).__r3f = state;
        }}
      >
        <Scene />
      </Canvas>

      <div
        style={{
          position: "absolute",
          top: 16,
          left: 16,
          zIndex: 2,
          display: "flex",
          flexDirection: "column",
          gap: 10,
          maxWidth: 340,
        }}
      >
        <div style={panelStyle}>
          <strong>Códice</strong> — Cómo funciona México
          <div style={{ color: "#9ca3af", fontSize: 12 }}>Prototipo Fase 0 · visualización dual</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {modeButton("grafo", "Grafo")}
          {modeButton("mapa", "Mapa")}
        </div>
      </div>

      <div style={{ position: "absolute", bottom: 16, left: 16, zIndex: 2, ...panelStyle }}>
        <div style={{ fontWeight: 600, marginBottom: 2 }}>Niveles</div>
        <div>
          <Dot color={LEVEL_COLORS.federal} /> Federal
        </div>
        <div>
          <Dot color={LEVEL_COLORS.estatal} /> Estatal
        </div>
        <div>
          <Dot color={LEVEL_COLORS.ciudadano} /> Ciudadanía
        </div>
        <div style={{ fontWeight: 600, marginTop: 8, marginBottom: 2 }}>Relaciones</div>
        <div>
          <Line color={EDGE_COLORS.autoridad} /> Autoridad (baja ↓)
        </div>
        <div>
          <Line color={EDGE_COLORS.legitimidad} /> Legitimidad (sube ↑)
        </div>
        <div style={{ color: "#9ca3af", fontSize: 12, marginTop: 8 }}>
          Scroll para hacer zoom · arrastra para desplazar.
          <br />
          En modo mapa, los nodos sin geografía conservan su posición jerárquica.
        </div>
      </div>
    </div>
  );
}
