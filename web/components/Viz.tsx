"use client";
/**
 * Dual-mode container: MapLibre basemap behind a transparent R3F canvas.
 *
 * ponytail: the basemap lives in its own WebGL context and is only aligned at
 * the initial framing — canvas zoom does not move the map. Upgrade path: render
 * the R3F scene as a MapLibre custom layer sharing ONE WebGL context (ADR-004).
 */
import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { Canvas } from "@react-three/fiber";
import Scene from "./Scene";
import { CAMERA_ZOOM, EDGE_COLORS, LEVEL_COLORS, MAP_CENTER, MAP_ZOOM, formatMXN, loadDataset } from "../lib/data";
import type { Dataset } from "../lib/data";
import { useVizStore } from "../lib/store";
import type { VizMode } from "../lib/store";

const panel: React.CSSProperties = {
  background: "rgba(11, 15, 20, 0.9)",
  border: "1px solid #1f2937",
  borderRadius: 8,
  padding: "10px 14px",
  fontSize: 13,
  lineHeight: 1.6,
};

function Dot({ color }: { color: string }) {
  return <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: color, marginRight: 6 }} />;
}
function Line({ color }: { color: string }) {
  return <span style={{ display: "inline-block", width: 16, height: 3, background: color, marginRight: 6, verticalAlign: "middle" }} />;
}

/** Detail panel: what makes a node citable (R1, R10). */
function Detalle({ data }: { data: Dataset }) {
  const selected = useVizStore((s) => s.selected);
  const select = useVizStore((s) => s.select);
  const node = useMemo(() => data.nodes.find((n) => n.id === selected), [data, selected]);
  if (!node) return null;

  const rel = data.edges.filter((e) => e.from === node.id || e.to === node.id);
  // Per-capita spending applies to territorial nodes, and only with its caveats.
  const latestYear = Math.max(...data.perCapita.map((p) => p.fiscal_year), 0);
  const perCapita = node.territory_key
    ? data.perCapita.find((p) => p.territory_key === node.territory_key && p.fiscal_year === latestYear)
    : undefined;
  const name = (id: string) => data.nodes[data.index.get(id)!]?.name ?? id;

  return (
    <div style={{ position: "absolute", top: 16, right: 16, zIndex: 3, width: 380, maxHeight: "calc(100vh - 32px)", overflowY: "auto", ...panel }}>
      <button onClick={() => select(null)} style={{ float: "right", background: "none", border: "none", color: "#9ca3af", cursor: "pointer", fontSize: 18 }}>×</button>
      <div style={{ fontWeight: 700, fontSize: 15, paddingRight: 20 }}>{node.name}</div>
      <div style={{ color: "#9ca3af", fontSize: 12 }}>
        {node.node_type_name} · {node.level}
        {node.territory_name ? ` · ${node.territory_name} (clave INEGI ${node.territory_key})` : ""}
      </div>
      {node.valid_to && (
        <div style={{ marginTop: 6, color: "#fca5a5", fontSize: 12 }}>
          Órgano extinto el {node.valid_to}. Se conserva en el registro histórico.
        </div>
      )}
      {node.summary && <p style={{ marginTop: 8, color: "#d1d5db" }}>{node.summary}</p>}
      {node.population !== null && (
        <div style={{ marginTop: 6, fontSize: 12, color: "#9ca3af" }}>
          Población {node.population.toLocaleString("es-MX")} — Censo 2020, INEGI.
        </div>
      )}

      <div style={{ fontWeight: 600, marginTop: 12 }}>Fundamento legal</div>
      {node.legal_basis.map((b, i) => (
        <div key={i} style={{ marginTop: 6, fontSize: 12, borderLeft: "2px solid #374151", paddingLeft: 8 }}>
          <a href={b.url} target="_blank" rel="noreferrer" style={{ color: "#93c5fd" }}>
            {b.document} — {b.article}
          </a>
          {b.hash && (
            <div style={{ color: "#6b7280", fontFamily: "monospace", fontSize: 10, wordBreak: "break-all" }}>
              sha256 {b.hash.slice(0, 24)}… · capturado {b.captured_at?.slice(0, 10)}
            </div>
          )}
        </div>
      ))}

      {node.budget.length > 0 && (
        <>
          <div style={{ fontWeight: 600, marginTop: 12 }}>Presupuesto aprobado</div>
          {node.budget.map((b, i) => {
            const prev = node.budget[i - 1];
            const delta = prev ? ((b.amount_mxn - prev.amount_mxn) / prev.amount_mxn) * 100 : null;
            return (
              <div key={b.fiscal_year} style={{ fontSize: 12, marginTop: 4 }}>
                <span style={{ color: "#9ca3af" }}>{b.fiscal_year}</span>{" "}
                <strong style={{ color: "#e5e7eb" }}>{formatMXN(b.amount_mxn)}</strong>
                {delta !== null && (
                  <span style={{ color: "#9ca3af" }}>
                    {" "}({delta >= 0 ? "+" : ""}{delta.toFixed(1)}% nominal)
                  </span>
                )}
                <div style={{ color: "#6b7280", fontFamily: "monospace", fontSize: 10 }}>
                  sha256 {b.hash.slice(0, 24)}… · capturado {b.captured_at.slice(0, 10)}
                </div>
              </div>
            );
          })}
          {(data.caveats["presupuesto_por_nodo"] ?? []).map((c, i) => (
            <div key={i} style={{ fontSize: 11, color: "#9ca3af", marginTop: 6, borderLeft: "2px solid #78350f", paddingLeft: 8 }}>
              {c}
            </div>
          ))}
        </>
      )}

      {perCapita && (
        <>
          <div style={{ fontWeight: 600, marginTop: 12 }}>Gasto federal por habitante</div>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            <strong style={{ color: "#e5e7eb" }}>
              {perCapita.mxn_per_inhabitant?.toLocaleString("es-MX", { maximumFractionDigits: 0 })} pesos
            </strong>{" "}
            <span style={{ color: "#9ca3af" }}>
              por habitante en {perCapita.fiscal_year}
            </span>
            <div style={{ color: "#6b7280", fontSize: 11 }}>
              {formatMXN(perCapita.amount_mxn)} entre{" "}
              {perCapita.population.toLocaleString("es-MX")} habitantes (Censo {perCapita.census_year}, INEGI)
            </div>
          </div>
          {(data.caveats["gasto_por_habitante"] ?? []).map((c, i) => (
            <div key={i} style={{ fontSize: 11, color: "#9ca3af", marginTop: 6, borderLeft: "2px solid #78350f", paddingLeft: 8 }}>
              {c}
            </div>
          ))}
        </>
      )}

      {node.occupants.length > 0 && (
        <>
          <div style={{ fontWeight: 600, marginTop: 12 }}>
            Quién lo ocupa ({node.occupants.length})
          </div>
          <div style={{ maxHeight: 260, overflowY: "auto", marginTop: 4 }}>
            {node.occupants.map((o, i) => (
              <div key={i} style={{ fontSize: 12, padding: "4px 0", borderBottom: "1px solid #1f2937" }}>
                <div style={{ color: "#e5e7eb" }}>
                  {o.name}
                  {o.party && (
                    <span style={{ color: "#9ca3af" }}> · {o.party}</span>
                  )}
                </div>
                <div style={{ color: "#6b7280", fontSize: 11 }}>
                  {o.role} · {o.start_date}
                  {o.end_date ? ` a ${o.end_date}` : " en funciones"}
                </div>
                {o.contact_email && (
                  <a href={`mailto:${o.contact_email}`} style={{ color: "#93c5fd", fontSize: 11 }}>
                    {o.contact_email}
                  </a>
                )}
              </div>
            ))}
          </div>
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
            Solo contacto institucional. Partido: el de su elección.
          </div>
        </>
      )}

      {rel.length > 0 && (
        <>
          <div style={{ fontWeight: 600, marginTop: 12 }}>Relaciones</div>
          {rel.slice(0, 12).map((e, i) => (
            <div key={i} style={{ fontSize: 12, color: "#d1d5db" }}>
              <Line color={EDGE_COLORS[e.type]} />
              {e.from === node.id ? `${e.type} sobre ${name(e.to)}` : `${e.type} de ${name(e.from)}`}
            </div>
          ))}
          {rel.length > 12 && <div style={{ fontSize: 11, color: "#6b7280" }}>+{rel.length - 12} más</div>}
        </>
      )}
      <div style={{ marginTop: 12, fontSize: 11, color: "#6b7280" }}>
        Enlace citable: <code>/nodo/{node.id}</code>
      </div>
    </div>
  );
}

export default function Viz() {
  const mode = useVizStore((s) => s.mode);
  const setMode = useVizStore((s) => s.setMode);
  const showExtinct = useVizStore((s) => s.showExtinct);
  const toggleExtinct = useVizStore((s) => s.toggleExtinct);
  const mapDiv = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDataset().then(setData).catch((e) => setError(String(e)));
  }, []);

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
        padding: "6px 16px", borderRadius: 6,
        border: "1px solid " + (mode === m ? "#fbbf24" : "#374151"),
        background: mode === m ? "#fbbf24" : "transparent",
        color: mode === m ? "#0b0f14" : "#e5e7eb",
        fontWeight: 600, cursor: "pointer",
      }}
    >
      {label}
    </button>
  );

  const extinctCount = data?.nodes.filter((n) => n.extinct).length ?? 0;

  return (
    <div style={{ position: "fixed", inset: 0, overflow: "hidden" }}>
      <div ref={mapDiv} style={{ position: "absolute", inset: 0, opacity: mode === "mapa" ? 1 : 0, transition: "opacity 500ms" }} />
      {data && (
        <Canvas
          orthographic
          camera={{ zoom: CAMERA_ZOOM, position: [0, 0, 100], near: 0.1, far: 1000 }}
          gl={{ alpha: true, antialias: true }}
          style={{ position: "absolute", inset: 0 }}
          // Dev-only escape hatch: lets tooling advance frames when rAF is
          // throttled (hidden tab). Harmless in production builds.
          onCreated={(state) => {
            if (process.env.NODE_ENV !== "production") {
              const w = window as unknown as Record<string, unknown>;
              w.__r3f = state;
              w.__ids = data.nodes.map((n) => n.id); // instance order, for automated checks
            }
          }}
        >
          <Scene data={data} />
        </Canvas>
      )}

      <div style={{ position: "absolute", top: 16, left: 16, zIndex: 2, display: "flex", flexDirection: "column", gap: 10, maxWidth: 360 }}>
        <div style={panel}>
          <strong>Códice</strong> — Cómo funciona México
          <div style={{ color: "#9ca3af", fontSize: 12 }}>
            {data ? `${data.nodes.length} nodos · ${data.edges.length} relaciones · fundamento legal citado` : error ? `Error: ${error}` : "Cargando…"}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {modeButton("grafo", "Grafo")}
          {modeButton("mapa", "Mapa")}
        </div>
      </div>

      <div style={{ position: "absolute", bottom: 16, left: 16, zIndex: 2, maxWidth: 330, ...panel }}>
        <div style={{ fontWeight: 600, marginBottom: 2 }}>Niveles</div>
        <div><Dot color={LEVEL_COLORS.federal} /> Federal</div>
        <div><Dot color={LEVEL_COLORS.estatal} /> Estatal</div>
        <div><Dot color={LEVEL_COLORS.municipal} /> Municipal</div>
        <div><Dot color={LEVEL_COLORS.ciudadano} /> Ciudadanía</div>
        <div style={{ fontWeight: 600, marginTop: 8, marginBottom: 2 }}>Relaciones</div>
        <div><Line color={EDGE_COLORS.autoridad} /> Autoridad (baja ↓)</div>
        <div><Line color={EDGE_COLORS.legitimidad} /> Legitimidad (sube ↑)</div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 10, fontSize: 12, cursor: "pointer" }}>
          <input type="checkbox" checked={showExtinct} onChange={toggleExtinct} />
          Mostrar órganos extintos ({extinctCount})
        </label>
        <div style={{ color: "#9ca3af", fontSize: 12, marginTop: 8 }}>
          Clic en un nodo para ver su fundamento legal y procedencia. Scroll para zoom.
          <br />
          En modo mapa, los nodos sin territorio conservan su posición jerárquica.
        </div>
      </div>

      {data && <Detalle data={data} />}
    </div>
  );
}
