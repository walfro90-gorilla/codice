"use client";
/**
 * Persistent node labels.
 *
 * The graph's core problem was that 201 identical circles tell a visitor
 * nothing until they click. Labels answer "what am I looking at" before any
 * interaction — and because they are real DOM text they are selectable,
 * findable with Ctrl+F, and readable by a screen reader, which a WebGL-only
 * scene is not.
 *
 * They are rendered per VISIBLE node, not per node: the tier rises with the
 * camera zoom, so the reader gets anchors when far out and detail when close.
 * That is what keeps this affordable when the 2,469 municipios arrive — nobody
 * reads 2,469 labels at once.
 */
import { Html } from "@react-three/drei";
import { useMemo } from "react";
import { LEVEL_COLORS, geoOffset, nodeRadius, projectGeo } from "../lib/data";
import type { Dataset, VizNode } from "../lib/data";
import { composition } from "../lib/parties";
import { useVizStore } from "../lib/store";
import type { LabelTier } from "../lib/store";

/**
 * Which nodes earn a label at each zoom tier.
 *
 * The opening tier is deliberately tiny — four labels. Thirteen long federal
 * names in one row overlap into an unreadable smear, which is worse than no
 * label at all: the reader gets the three branches and where power comes from,
 * and everything else arrives as they zoom in.
 */
function visibleAt(tier: LabelTier, n: VizNode): boolean {
  if (n.level === "ciudadano") return true;
  if (n.node_type === "poder") return true;
  if (tier === "anchors") return false;
  if (tier === "federal") return n.level === "federal";
  return true;
}

/**
 * A label has to read at a glance, so prefer the acronym the official name
 * already carries: "Comisión Federal de Competencia Económica (COFECE)" is
 * COFECE on the canvas and keeps its full name in the card. Stripping the
 * parenthesis instead — which this did at first — produced exactly the
 * overlapping smear the labels were meant to fix.
 */
function shortName(n: VizNode): string {
  const acronym = n.name.match(/\(([A-ZÁÉÍÓÚÑ0-9.\-]{2,12})\)\s*$/);
  if (acronym) return acronym[1];

  // Subnational names repeat their entity in every one of the four organs, so
  // the entity is the noise there and the organ is the signal. Federal names
  // are the opposite. Applying one set of rules to both is how "Congreso de la
  // Unión" briefly became "la Unión".
  if (n.level !== "federal" && n.level !== "ciudadano") {
    return n.name
      .replace(/^Gobernador\/a del? (Estado de )?/i, "")
      .replace(/^Jefatura de Gobierno de la /i, "")
      .replace(/^Congreso del? (Estado de |la )?/i, "")
      .replace(/^Poder Judicial del? (Estado de )?/i, "")
      .replace(/^Ayuntamientos del? (Estado de )?/i, "")
      .replace(/^Alcaldías de la /i, "")
      .trim();
  }

  return n.name
    .replace(/^Secretaría de (la |las |el )?/i, "")
    .replace(/^Instituto Nacional de /i, "")
    .replace(/^Comisión Nacional de /i, "")
    .replace(/^Comisión Federal de /i, "")
    .replace(/^Instituto Mexicano del /i, "")
    .replace(/^Tribunal Federal de /i, "")
    .replace(/^Consejo Nacional de /i, "")
    .replace(/^Servicios de Salud del /i, "")
    .replace(/ de la Federación$/i, "")
    .replace(/ de la Nación$/i, "")
    .replace(/\s*\([^)]*\)\s*$/, "")
    .trim();
}

/**
 * Labels in one row are staggered so neighbours never collide: even indices
 * ride above the node, odd ones below. It doubles the horizontal room a label
 * has without moving a single node.
 */
function stagger(indexInRow: number): number {
  return indexInRow % 2 === 0 ? -1 : 1;
}

/**
 * How wide a label may get before it truncates.
 *
 * Thirty-eight secretarías in one row leave roughly 46 px of screen each at the
 * tier where they appear — far less than their names need. Truncating keeps the
 * row readable and costs nothing, because the hover card carries the full name
 * a few pixels away. Letting them run instead produces the unreadable smear
 * this whole feature exists to remove.
 */
function maxLabelWidth(tier: LabelTier, n: VizNode): number {
  if (n.node_type === "poder" || n.level === "ciudadano") return 200;
  return tier === "all" ? 122 : 86;
}

export default function Labels({ data }: { data: Dataset }) {
  const tier = useVizStore((s) => s.labelTier);
  const mode = useVizStore((s) => s.mode);
  const selected = useVizStore((s) => s.selected);
  const showExtinct = useVizStore((s) => s.showExtinct);
  const select = useVizStore((s) => s.select);

  // Rows are the layout's own bands, so grouping by y is enough to know who a
  // label's neighbours are.
  const shown = useMemo(() => {
    const visible = data.nodes.filter((n) => (showExtinct || !n.extinct) && visibleAt(tier, n));
    const perRow = new Map<number, number>();
    return visible
      .slice()
      .sort((a, b) => b.pos_graph.y - a.pos_graph.y || a.pos_graph.x - b.pos_graph.x)
      .map((n) => {
        const row = Math.round(n.pos_graph.y);
        const i = perRow.get(row) ?? 0;
        perRow.set(row, i + 1);
        return { node: n, side: stagger(i) };
      });
  }, [data, tier, showExtinct]);

  return (
    <>
      {shown.map(({ node: n, side }) => {
        // Labels sit at the node's CURRENT target, matching the scene's own
        // interpolation target rather than fighting it mid-transition.
        let x = n.pos_graph.x;
        let y = n.pos_graph.y;
        if (mode === "mapa" && n.pos_geo) {
          [x, y] = projectGeo(n.pos_geo.lon, n.pos_geo.lat);
          const [ox, oy] = geoOffset(n.node_type);
          x += ox;
          y += oy;
        }
        const isSel = n.id === selected;
        const bars = composition(n.occupants);

        return (
          <Html
            key={n.id}
            position={[x, y + side * (nodeRadius(n) + 0.9), 0]}
            center
            distanceFactor={undefined}
            style={{ pointerEvents: "none", userSelect: "text" }}
            zIndexRange={[1, 0]}
          >
            <div
              onClick={() => select(n.id)}
              style={{
                pointerEvents: "auto",
                cursor: "pointer",
                transform: "translateY(2px)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                whiteSpace: "nowrap",
              }}
            >
              <span
                title={n.name}
                style={{
                  fontSize: n.node_type === "poder" || n.level === "ciudadano" ? 12 : 10,
                  fontWeight: n.node_type === "poder" || n.level === "ciudadano" ? 600 : 500,
                  color: isSel ? "#ffffff" : n.extinct ? "#6b7280" : "#d1d5db",
                  textShadow: "0 1px 3px #0b0f14, 0 0 8px #0b0f14",
                  letterSpacing: 0.1,
                  maxWidth: maxLabelWidth(tier, n),
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {shortName(n)}
              </span>

              {/* Composition bar: the "flag" of a chamber is how its seats split. */}
              {bars.length > 0 && (
                <span
                  title={bars.map((b) => `${b.label} ${b.seats}`).join(" · ")}
                  style={{
                    display: "flex",
                    width: 92,
                    height: 5,
                    borderRadius: 3,
                    overflow: "hidden",
                    boxShadow: "0 0 0 1px rgba(11,15,20,0.9)",
                  }}
                >
                  {bars.map((b) => (
                    <span
                      key={b.label}
                      style={{ width: `${b.share * 100}%`, background: b.color }}
                    />
                  ))}
                </span>
              )}
            </div>
          </Html>
        );
      })}
    </>
  );
}

export { LEVEL_COLORS };
