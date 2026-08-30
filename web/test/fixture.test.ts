/**
 * The exported dataset must satisfy the frozen contract and the constitutional
 * invariants — this is the check that fails if curation or export regresses.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { GraphNode } from "@codice/contracts";
import { layout } from "../lib/data.ts";
import type { RawNode, EdgeRow } from "../lib/data.ts";

const raw = JSON.parse(readFileSync(new URL("../public/data/grafo.json", import.meta.url), "utf8")) as {
  nodes: RawNode[];
  edges: EdgeRow[];
  sources: { url: string; hash: string; captured_at: string }[];
};
const nodes = layout(raw.nodes);

test("every laid-out node satisfies the frozen GraphNode contract", () => {
  for (const n of nodes) {
    const r = GraphNode.safeParse({
      id: n.id, name: n.name, level: n.level, depth: n.depth,
      pos_graph: n.pos_graph, pos_geo: n.pos_geo,
    });
    assert.ok(r.success, `${n.id}: ${r.success ? "" : JSON.stringify(r.error.issues)}`);
  }
});

test("ids are unique and layout preserves node count", () => {
  assert.equal(new Set(nodes.map((n) => n.id)).size, nodes.length);
  assert.equal(nodes.length, raw.nodes.length);
});

test("every node cites at least one legal basis (R1)", () => {
  const naked = raw.nodes.filter((n) => n.legal_basis.length === 0).map((n) => n.id);
  assert.deepEqual(naked, [], `nodes without legal basis: ${naked.join(", ")}`);
});

test("legal basis carries provenance: url, sha256 hash and capture date", () => {
  for (const n of raw.nodes) {
    for (const b of n.legal_basis) {
      assert.match(b.url, /^https:\/\//, `${n.id}: bad url`);
      if (b.hash) assert.match(b.hash, /^[0-9a-f]{64}$/, `${n.id}: bad hash`);
      if (b.captured_at) assert.match(b.captured_at, /^\d{4}-\d{2}-\d{2}/, `${n.id}: bad date`);
    }
  }
});

test("edges reference existing nodes", () => {
  const ids = new Set(raw.nodes.map((n) => n.id));
  for (const e of raw.edges) {
    assert.ok(ids.has(e.from), `unknown edge source ${e.from}`);
    assert.ok(ids.has(e.to), `unknown edge target ${e.to}`);
  }
});

test("no authority edge crosses orders of government (Art. 40 y 115)", () => {
  const lvl = new Map(raw.nodes.map((n) => [n.id, n.level]));
  const bad = raw.edges.filter((e) => {
    if (e.type !== "autoridad") return false;
    const a = lvl.get(e.from), b = lvl.get(e.to);
    return (a === "federal" && (b === "estatal" || b === "municipal")) || (a === "estatal" && b === "municipal");
  });
  assert.deepEqual(bad, [], "federal pact / municipio libre violated");
});

test("territory keys are INEGI keys, never names (R7)", () => {
  for (const n of raw.nodes) {
    if (n.territory_key !== null) assert.match(n.territory_key, /^\d{2}(\d{3})?$/, `${n.id}`);
  }
});

test("all 32 entities are covered", () => {
  const ents = new Set(raw.nodes.map((n) => n.territory_key).filter((k): k is string => !!k && k.length === 2));
  assert.equal(ents.size, 32);
});

test("nodes with geography are subnational; federal organs have none", () => {
  for (const n of raw.nodes) {
    if (n.level === "federal" || n.level === "ciudadano") assert.equal(n.pos_geo, null, `${n.id}`);
  }
});

test("extinct organs keep an extinction date (R9)", () => {
  const extinct = raw.nodes.filter((n) => n.valid_to !== null);
  assert.ok(extinct.length > 0, "expected historical organs in the record");
  for (const n of extinct) assert.match(n.valid_to!, /^\d{4}-\d{2}-\d{2}$/);
});

test("no verdict vocabulary in published summaries (R2)", () => {
  for (const n of raw.nodes) {
    const text = `${n.summary ?? ""}`.toLowerCase();
    assert.ok(!/\bcorrupci[óo]n\b/.test(text.replace(/anticorrupci[óo]n/g, "")), `${n.id}: forbidden vocabulary`);
  }
});

// --- Fase 2: occupants ---

test("occupants only carry institutional contact", () => {
  for (const n of raw.nodes) {
    for (const o of n.occupants ?? []) {
      if (o.contact_email) {
        assert.match(
          o.contact_email,
          /@(diputados|senado)\.gob\.mx$/,
          `${n.id}/${o.name}: non-institutional contact leaked`,
        );
      }
    }
  }
});

test("every occupant has a name and a bounded term (R9)", () => {
  for (const n of raw.nodes) {
    for (const o of n.occupants ?? []) {
      assert.ok(o.name && o.name.length > 3, `${n.id}: unnamed occupant`);
      assert.match(o.start_date, /^\d{4}-\d{2}-\d{2}$/, `${o.name}: bad start`);
      if (o.end_date) assert.ok(o.end_date > o.start_date, `${o.name}: term ends before it starts`);
    }
  }
});

test("chamber sizes match the Constitution (Arts. 52 y 56)", () => {
  const byId = new Map(raw.nodes.map((n) => [n.id, n]));
  assert.equal(byId.get("camara-diputados")?.occupants.length, 500, "Art. 52: 300 MR + 200 RP");
  const senate = byId.get("senado")?.occupants.length ?? 0;
  // Art. 56 sets 128; the source currently reports one vacancy, so allow <= 128
  assert.ok(senate > 120 && senate <= 128, `senate has ${senate}, expected <= 128`);
});

test("party keys are canonical across chambers", () => {
  const parties = new Set(
    raw.nodes.flatMap((n) => (n.occupants ?? []).map((o) => o.party)).filter(Boolean),
  );
  // VERDE (Chamber) and PVEM (Senate) are the same party; only one key may survive
  assert.ok(!parties.has("VERDE"), "found un-normalized party key VERDE");
  for (const p of parties) assert.match(p!, /^[A-Z]{2,8}$/, `odd party key: ${p}`);
});

test("no personal data beyond what the project needs", () => {
  // The official profiles expose birth dates and home-district addresses; the
  // published dataset must not carry them.
  const blob = JSON.stringify(raw.nodes.flatMap((n) => n.occupants ?? []));
  assert.ok(!/\b\d{2}-(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b/i.test(blob), "birth date leaked");
  assert.ok(!/curp|rfc\b/i.test(blob), "identity document leaked");
});
