/**
 * Fase 0 fixture: ONE node dataset with TWO positions each.
 *
 * - pos_graph {x,y}: computed here from the hierarchy level (row per depth).
 * - pos_geo {lon,lat}: real approximate geography; null for non-territorial nodes.
 *
 * Zero data duplication: switching modes only changes which position is the
 * interpolation target. Rows conform to the frozen GraphNode contract.
 */
import type { GovLevelT, GraphNodeT } from "@codice/contracts";

export type EdgeRow = { from: string; to: string; type: "autoridad" | "legitimidad" };

type Raw = {
  id: string;
  name: string;
  level: GovLevelT;
  depth: number;
  geo: [number, number] | null; // [lon, lat]
};

const PODERES: Raw[] = [
  { id: "ejecutivo-federal", name: "Ejecutivo Federal", level: "federal", depth: 0, geo: null },
  { id: "legislativo-federal", name: "Poder Legislativo", level: "federal", depth: 0, geo: null },
  { id: "judicial-federal", name: "Poder Judicial", level: "federal", depth: 0, geo: null },
];

// ponytail: 5 of ~20 secretarías; Fase 1 curates the full list with legal_basis.
const SECRETARIAS: Raw[] = (
  [
    ["secretaria-gobernacion", "Secretaría de Gobernación"],
    ["secretaria-hacienda", "Secretaría de Hacienda y Crédito Público"],
    ["secretaria-defensa", "Secretaría de la Defensa Nacional"],
    ["secretaria-bienestar", "Secretaría de Bienestar"],
    ["secretaria-anticorrupcion", "Secretaría Anticorrupción y Buen Gobierno"],
  ] as const
).map(([id, name]) => ({ id, name, level: "federal" as const, depth: 1, geo: null }));

// INEGI key in the id (R7); approximate capital coordinates [lon, lat].
const ESTADOS_DATA: ReadonlyArray<readonly [string, string, number, number]> = [
  ["01", "Aguascalientes", -102.296, 21.882],
  ["02", "Baja California", -115.468, 32.663],
  ["03", "Baja California Sur", -110.313, 24.142],
  ["04", "Campeche", -90.525, 19.845],
  ["05", "Coahuila", -100.999, 25.421],
  ["06", "Colima", -103.724, 19.245],
  ["07", "Chiapas", -93.113, 16.753],
  ["08", "Chihuahua", -106.089, 28.632],
  ["09", "Ciudad de México", -99.133, 19.433],
  ["10", "Durango", -104.653, 24.027],
  ["11", "Guanajuato", -101.257, 21.019],
  ["12", "Guerrero", -99.501, 17.551],
  ["13", "Hidalgo", -98.759, 20.101],
  ["14", "Jalisco", -103.349, 20.677],
  ["15", "México", -99.656, 19.293],
  ["16", "Michoacán", -101.194, 19.706],
  ["17", "Morelos", -99.234, 18.921],
  ["18", "Nayarit", -104.895, 21.505],
  ["19", "Nuevo León", -100.316, 25.686],
  ["20", "Oaxaca", -96.726, 17.073],
  ["21", "Puebla", -98.206, 19.041],
  ["22", "Querétaro", -100.393, 20.588],
  ["23", "Quintana Roo", -88.296, 18.501],
  ["24", "San Luis Potosí", -100.985, 22.156],
  ["25", "Sinaloa", -107.394, 24.809],
  ["26", "Sonora", -110.955, 29.072],
  ["27", "Tabasco", -92.947, 17.989],
  ["28", "Tamaulipas", -99.141, 23.736],
  ["29", "Tlaxcala", -98.237, 19.318],
  ["30", "Veracruz", -96.91, 19.542],
  ["31", "Yucatán", -89.617, 20.967],
  ["32", "Zacatecas", -102.583, 22.771],
];

const ESTADOS: Raw[] = ESTADOS_DATA.map(([key, name, lon, lat]) => ({
  id: `estado-${key}`,
  name,
  level: "estatal" as const,
  depth: 2,
  geo: [lon, lat],
}));

const CIUDADANIA: Raw = { id: "ciudadania", name: "Ciudadanía", level: "ciudadano", depth: 3, geo: null };

const RAW: Raw[] = [...PODERES, ...SECRETARIAS, ...ESTADOS, CIUDADANIA];

// --- Graph layout: one row per hierarchy depth, centered on x = 0 ---
const ROW_Y = [22, 8, -8, -24];
const ROW_SPACING = [14, 11, 2.3, 0];

const byDepth = new Map<number, Raw[]>();
for (const r of RAW) {
  const row = byDepth.get(r.depth) ?? [];
  row.push(r);
  byDepth.set(r.depth, row);
}

export const nodes: GraphNodeT[] = RAW.map((r) => {
  const row = byDepth.get(r.depth)!;
  const i = row.indexOf(r);
  return {
    id: r.id,
    name: r.name,
    level: r.level,
    depth: r.depth,
    pos_graph: { x: (i - (row.length - 1) / 2) * ROW_SPACING[r.depth], y: ROW_Y[r.depth] },
    pos_geo: r.geo ? { lon: r.geo[0], lat: r.geo[1] } : null,
  };
});

// --- Geographic projection: web mercator scaled to match the graph extent ---
const GEO_CENTER: [number, number] = [-102, 23.5];
const GEO_SCALE = 2.2; // scene units per mercator degree

function mercY(lat: number): number {
  return (Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * 180) / Math.PI;
}

export function projectGeo(lon: number, lat: number): [number, number] {
  return [(lon - GEO_CENTER[0]) * GEO_SCALE, (mercY(lat) - mercY(GEO_CENTER[1])) * GEO_SCALE];
}

// Rough basemap framing that matches the scene projection at the initial camera.
// 1 scene unit = CAMERA_ZOOM px; map px/deg = 512 * 2^z / 360 = GEO_SCALE * CAMERA_ZOOM.
export const CAMERA_ZOOM = 10;
export const MAP_CENTER = GEO_CENTER;
export const MAP_ZOOM = Math.log2((GEO_SCALE * CAMERA_ZOOM * 360) / 512);

// --- Edges: the double arrow. Autoridad flows down, legitimidad flows up. ---
// ponytail: simplified constitutional wiring for the prototype; Fase 1 replaces
// it with ~400 hand-curated edges, each with its legal_basis article.
export const edges: EdgeRow[] = [
  ...SECRETARIAS.map((s) => ({ from: "ejecutivo-federal", to: s.id, type: "autoridad" as const })),
  ...ESTADOS.map((e) => ({ from: "ejecutivo-federal", to: e.id, type: "autoridad" as const })),
  ...ESTADOS.map((e) => ({ from: e.id, to: CIUDADANIA.id, type: "autoridad" as const })),
  { from: CIUDADANIA.id, to: "ejecutivo-federal", type: "legitimidad" },
  { from: CIUDADANIA.id, to: "legislativo-federal", type: "legitimidad" },
  ...ESTADOS.map((e) => ({ from: CIUDADANIA.id, to: e.id, type: "legitimidad" as const })),
];

// ponytail: sources is empty — the fixture has no raw snapshots yet; real
// provenance (R1) arrives when this reads from the API instead of a fixture.
export const graph = { nodes, edges, sources: [] };

// --- Presentation constants shared by scene and legend ---
export const LEVEL_COLORS: Record<GovLevelT, string> = {
  federal: "#fbbf24",
  estatal: "#a78bfa",
  municipal: "#34d399", // not in the fixture yet; arrives with Fase 1
  ciudadano: "#f472b6",
};

export const EDGE_COLORS = { autoridad: "#f97316", legitimidad: "#22d3ee" } as const;

const RADIUS_BY_DEPTH = [2.4, 1.5, 1.0, 2.8];

export function nodeRadius(n: GraphNodeT): number {
  return RADIUS_BY_DEPTH[n.depth] ?? 1;
}
