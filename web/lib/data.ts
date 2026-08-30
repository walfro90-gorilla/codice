/**
 * Real dataset loader (Fase 1): reads public/data/grafo.json — 201 curated
 * nodes exported from canonical Postgres, each with its legal basis and the
 * snapshot hash backing it.
 *
 * ONE node, TWO positions: pos_graph is computed here from level/depth,
 * pos_geo comes from the territory centroid. Zero duplication in the data.
 */
import type { GovLevelT } from "@codice/contracts";

export type LegalBasis = {
  document: string;
  article: string;
  url: string;
  hash: string | null;
  captured_at: string | null;
};

export type RawNode = {
  id: string;
  name: string;
  level: GovLevelT;
  node_type: string;
  node_type_name: string;
  summary: string | null;
  valid_from: string;
  valid_to: string | null;
  territory_key: string | null;
  territory_name: string | null;
  population: number | null;
  pos_geo: { lon: number; lat: number } | null;
  legal_basis: LegalBasis[];
  depth: number;
};

export type EdgeRow = {
  from: string;
  to: string;
  type: "autoridad" | "legitimidad";
  legal_basis: string | null;
};

export type SourceRow = { url: string; captured_at: string; hash: string; source: string };

export type VizNode = RawNode & { pos_graph: { x: number; y: number }; extinct: boolean };

export type Dataset = {
  nodes: VizNode[];
  edges: EdgeRow[];
  sources: SourceRow[];
  index: Map<string, number>;
};

/**
 * Layout rows, top to bottom: authority descends, legitimacy ascends.
 * Federal organs split by authority depth; the subnational skeleton is laid
 * out by entity so each state reads as a column.
 */
function rowOf(n: RawNode): number {
  if (n.level === "ciudadano") return 5;
  if (n.level === "municipal") return 4;
  if (n.level === "estatal") return 3;
  return Math.min(n.depth, 2); // federal: 0 poderes/autónomos, 1 secretarías, 2 sectorizados
}

const ROW_Y = [30, 18, 8, -8, -20, -32];

export function layout(nodes: RawNode[]): VizNode[] {
  const rows = new Map<number, RawNode[]>();
  for (const n of nodes) {
    const r = rowOf(n);
    (rows.get(r) ?? rows.set(r, []).get(r)!).push(n);
  }

  const out: VizNode[] = [];
  for (const [r, list] of rows) {
    // Subnational rows: order by INEGI key so columns align across rows (R7).
    const ordered =
      r === 3 || r === 4
        ? [...list].sort((a, b) => (a.territory_key ?? "").localeCompare(b.territory_key ?? "") || a.node_type.localeCompare(b.node_type))
        : [...list].sort((a, b) => a.name.localeCompare(b.name, "es"));

    // States get 3 nodes each: keep them in one column per entity.
    if (r === 3) {
      const byEntity = new Map<string, RawNode[]>();
      for (const n of ordered) {
        const k = n.territory_key ?? "";
        (byEntity.get(k) ?? byEntity.set(k, []).get(k)!).push(n);
      }
      const keys = [...byEntity.keys()].sort();
      keys.forEach((k, ci) => {
        const col = byEntity.get(k)!;
        col.forEach((n, ri) => {
          out.push({
            ...n,
            extinct: n.valid_to !== null,
            pos_graph: { x: (ci - (keys.length - 1) / 2) * 2.6, y: ROW_Y[r] + (1 - ri) * 3.2 },
          });
        });
      });
      continue;
    }

    // Keep at least 2.5 units between centers so nodes never overlap; the
    // widest federal row (secretarías) drives the scene extent.
    const spacing = r === 4 ? 2.6 : r <= 2 ? Math.max(2.9, Math.min(90 / Math.max(list.length, 1), 6)) : 3;
    ordered.forEach((n, i) => {
      out.push({
        ...n,
        extinct: n.valid_to !== null,
        pos_graph: { x: (i - (ordered.length - 1) / 2) * spacing, y: ROW_Y[r] },
      });
    });
  }
  return out;
}

export async function loadDataset(): Promise<Dataset> {
  const res = await fetch("/data/grafo.json");
  if (!res.ok) throw new Error(`grafo.json: HTTP ${res.status}`);
  const raw = (await res.json()) as { nodes: RawNode[]; edges: EdgeRow[]; sources: SourceRow[] };
  const nodes = layout(raw.nodes);
  const index = new Map(nodes.map((n, i) => [n.id, i]));
  // Drop edges whose endpoints are missing rather than rendering a wrong line.
  const edges = raw.edges.filter((e) => index.has(e.from) && index.has(e.to));
  return { nodes, edges, sources: raw.sources, index };
}

// --- Geographic projection: web mercator scaled to match the graph extent ---
const GEO_CENTER: [number, number] = [-102, 23.5];
const GEO_SCALE = 2.2; // scene units per mercator degree

function mercY(lat: number): number {
  return (Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * 180) / Math.PI;
}

export function projectGeo(lon: number, lat: number): [number, number] {
  return [(lon - GEO_CENTER[0]) * GEO_SCALE, (mercY(lat) - mercY(GEO_CENTER[1])) * GEO_SCALE];
}

/**
 * All organs of one entity share a single centroid, so they would stack into
 * one dot on the map. Fan them around it by node type — the entity still reads
 * as one place, but its four organs stay countable and clickable.
 */
const FAN_ORDER = ["ejecutivo_estatal", "congreso_local", "poder_judicial_estatal", "ayuntamientos"];
const FAN_RADIUS = 0.55;

export function geoOffset(nodeType: string): [number, number] {
  const i = FAN_ORDER.indexOf(nodeType);
  if (i < 0) return [0, 0];
  const a = (i / FAN_ORDER.length) * Math.PI * 2 - Math.PI / 2;
  return [Math.cos(a) * FAN_RADIUS, Math.sin(a) * FAN_RADIUS];
}

// Basemap framing that matches the scene projection at the initial camera.
// 1 scene unit = CAMERA_ZOOM px; map px/deg = 512 * 2^z / 360 = GEO_SCALE * CAMERA_ZOOM.
export const CAMERA_ZOOM = 10;
export const MAP_CENTER = GEO_CENTER;
export const MAP_ZOOM = Math.log2((GEO_SCALE * CAMERA_ZOOM * 360) / 512);

export const LEVEL_COLORS: Record<GovLevelT, string> = {
  federal: "#fbbf24",
  estatal: "#a78bfa",
  municipal: "#34d399",
  ciudadano: "#f472b6",
};

export const EDGE_COLORS = { autoridad: "#f97316", legitimidad: "#22d3ee" } as const;

export function nodeRadius(n: VizNode): number {
  if (n.level === "ciudadano") return 2.6;
  if (n.node_type === "poder") return 1.8;
  if (n.level === "federal") return n.depth === 0 ? 1.4 : 1.0;
  return 0.8;
}
