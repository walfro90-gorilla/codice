/** Validates the Fase 0 fixture against the frozen contracts (node --test). */
import test from "node:test";
import assert from "node:assert/strict";
import { Graph, GraphNode } from "@codice/contracts";
import { edges, graph, nodes } from "../lib/data.ts";

test("every fixture row conforms to the GraphNode contract", () => {
  for (const node of nodes) {
    const result = GraphNode.safeParse(node);
    assert.ok(result.success, `node ${node.id}: ${result.success ? "" : result.error.message}`);
  }
});

test("the whole fixture conforms to the Graph contract", () => {
  const result = Graph.safeParse(graph);
  assert.ok(result.success, result.success ? "" : result.error.message);
});

test("one dataset, two positions: estados are geographic, the rest are not", () => {
  assert.equal(nodes.length, 41);
  const estados = nodes.filter((n) => n.id.startsWith("estado-"));
  assert.equal(estados.length, 32);
  for (const e of estados) {
    assert.ok(e.pos_geo, `${e.id} must carry real geography`);
    assert.ok(e.pos_geo!.lon > -118 && e.pos_geo!.lon < -86, `${e.id} lon out of Mexico`);
    assert.ok(e.pos_geo!.lat > 14 && e.pos_geo!.lat < 33, `${e.id} lat out of Mexico`);
  }
  for (const n of nodes.filter((x) => !x.id.startsWith("estado-"))) {
    assert.equal(n.pos_geo, null, `${n.id} is non-territorial, pos_geo must be null`);
  }
});

test("node ids are unique and edges reference existing nodes", () => {
  const ids = new Set(nodes.map((n) => n.id));
  assert.equal(ids.size, nodes.length);
  for (const e of edges) {
    assert.ok(ids.has(e.from), `unknown edge source ${e.from}`);
    assert.ok(ids.has(e.to), `unknown edge target ${e.to}`);
  }
  assert.ok(edges.some((e) => e.type === "autoridad"));
  assert.ok(edges.some((e) => e.type === "legitimidad"));
});
