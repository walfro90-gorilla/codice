"use client";
/**
 * Hover card: the middle rung of the reading ladder.
 *
 * Labels answer "what am I looking at"; the full panel answers "what can I
 * cite". This answers "and this one?" without opening anything — browsing ten
 * organs stops costing ten clicks and ten panel dismissals.
 *
 * It follows the pointer but never sits under it, and flips before it would
 * leave the viewport.
 */
import { useMemo } from "react";
import { formatMXN } from "../lib/data";
import type { Dataset } from "../lib/data";
import { composition } from "../lib/parties";
import { useVizStore } from "../lib/store";

const CARD_W = 290;
const OFFSET = 18;

export default function HoverCard({ data }: { data: Dataset }) {
  const hovered = useVizStore((s) => s.hovered);
  const pointer = useVizStore((s) => s.pointer);
  const selected = useVizStore((s) => s.selected);

  const node = useMemo(
    () => (hovered ? data.nodes.find((n) => n.id === hovered) : undefined),
    [data, hovered],
  );

  // The full panel already says everything; two cards at once is noise.
  if (!node || node.id === selected) return null;

  const bars = composition(node.occupants);
  const latest = node.budget[node.budget.length - 1];
  const spent = [...node.budget].reverse().find((b) => b.stages?.ejercido !== undefined);

  const flipX = typeof window !== "undefined" && pointer.x + OFFSET + CARD_W > window.innerWidth;
  const flipY = typeof window !== "undefined" && pointer.y + 240 > window.innerHeight;

  return (
    <div
      style={{
        position: "fixed",
        left: flipX ? pointer.x - OFFSET - CARD_W : pointer.x + OFFSET,
        top: flipY ? undefined : pointer.y + OFFSET,
        bottom: flipY ? window.innerHeight - pointer.y + OFFSET : undefined,
        width: CARD_W,
        zIndex: 5,
        pointerEvents: "none",
        background: "rgba(11, 15, 20, 0.96)",
        border: "1px solid #334155",
        borderRadius: 8,
        padding: "11px 13px",
        boxShadow: "0 10px 34px rgba(0,0,0,0.55)",
        display: "flex",
        flexDirection: "column",
        gap: 7,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 700, lineHeight: 1.3, color: "#f3f4f6" }}>
        {node.name}
      </div>
      <div style={{ fontSize: 11, color: "#9ca3af" }}>
        {node.node_type_name} · {node.level}
        {node.territory_name ? ` · ${node.territory_name}` : ""}
      </div>

      {node.extinct && (
        <div style={{ fontSize: 11, color: "#fca5a5" }}>
          Extinto el {node.valid_to}
        </div>
      )}

      {/* Who holds it, as a composition — the "flag" of the body */}
      {bars.length > 0 && (
        <>
          <div style={{ height: 1, background: "#1f2937" }} />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span style={{ fontSize: 11, color: "#9ca3af" }}>Integración</span>
            <span style={{ fontSize: 12, fontWeight: 600 }}>{node.occupants.length} escaños</span>
          </div>
          <span style={{ display: "flex", height: 7, borderRadius: 4, overflow: "hidden" }}>
            {bars.map((b) => (
              <span key={b.label} style={{ width: `${b.share * 100}%`, background: b.color }} />
            ))}
          </span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "3px 10px" }}>
            {bars.slice(0, 6).map((b) => (
              <span key={b.label} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10.5 }}>
                <span style={{ width: 7, height: 7, borderRadius: 2, background: b.color }} />
                <span style={{ color: "#d1d5db" }}>{b.label}</span>
                <span style={{ color: "#6b7280" }}>{b.seats}</span>
              </span>
            ))}
          </div>
        </>
      )}

      {/* Money, if this organ has a ramo of its own */}
      {latest && (
        <>
          <div style={{ height: 1, background: "#1f2937" }} />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span style={{ fontSize: 11, color: "#9ca3af" }}>Aprobado {latest.fiscal_year}</span>
            <span style={{ fontSize: 12, fontWeight: 600 }}>{formatMXN(latest.amount_mxn)}</span>
          </div>
          {spent?.stages?.ejercido !== undefined && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>Ejercido {spent.fiscal_year}</span>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{formatMXN(spent.stages.ejercido)}</span>
            </div>
          )}
        </>
      )}

      {/* Saying what we do not have is part of the record (R6) */}
      {bars.length === 0 && !latest && (
        <div style={{ fontSize: 11, color: "#6b7280", lineHeight: 1.5 }}>
          Sin titular ni presupuesto propio cargados todavía.
        </div>
      )}

      <div style={{ fontSize: 10, color: "#6b7280", marginTop: 1 }}>
        Clic para el fundamento legal y su procedencia
      </div>
    </div>
  );
}
