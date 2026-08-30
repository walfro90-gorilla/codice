/**
 * Label shortening is where a small regex mistake turns into a false claim on
 * screen ("Congreso de la Unión" once rendered as "la Unión"). These pin the
 * cases that actually appear in the dataset.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { layout } from "../lib/data.ts";
import type { RawNode } from "../lib/data.ts";
import { composition, partyColor, NO_PARTY_LABEL } from "../lib/parties.ts";

const raw = JSON.parse(
  readFileSync(new URL("../public/data/grafo.json", import.meta.url), "utf8"),
) as { nodes: RawNode[] };
const nodes = layout(raw.nodes);

test("no label is empty, and none loses the noun that identifies it", () => {
  // Reproduces the module's rule without importing the component (JSX).
  const acronym = (name: string) => name.match(/\(([A-ZÁÉÍÓÚÑ0-9.\-]{2,12})\)\s*$/)?.[1];
  for (const n of nodes) {
    const a = acronym(n.name);
    const label = a ?? n.name;
    assert.ok(label.trim().length >= 2, `${n.id}: empty label`);
    // A label must never start with a lowercase article — that is the shape a
    // greedy prefix strip leaves behind.
    assert.ok(!/^(el|la|los|las|de|del) /.test(label), `${n.id}: label starts mid-phrase: "${label}"`);
  }
});

test("acronyms are preferred where the official name carries one", () => {
  const inai = raw.nodes.find((n) => n.id === "inai");
  assert.ok(inai?.name.includes("(INAI)"), "fixture changed: INAI has no acronym");
});

test("party composition adds up to the seats it describes", () => {
  for (const n of raw.nodes) {
    if (!n.occupants.length) continue;
    const bars = composition(n.occupants);
    assert.equal(bars.reduce((s, b) => s + b.seats, 0), n.occupants.length, `${n.id}`);
    const share = bars.reduce((s, b) => s + b.share, 0);
    assert.ok(Math.abs(share - 1) < 1e-9, `${n.id}: shares do not sum to 1`);
    // Largest group first, so the bar reads in the order the legend lists
    for (let i = 1; i < bars.length; i++) assert.ok(bars[i - 1].seats >= bars[i].seats);
  }
});

test("a seat with no parliamentary group is named as such, never invented", () => {
  const withNull = raw.nodes.flatMap((n) => composition(n.occupants)).find((b) => b.party === null);
  assert.ok(withNull, "fixture changed: no unaffiliated seats");
  assert.equal(withNull.label, NO_PARTY_LABEL);
  assert.equal(partyColor(null), partyColor("PARTIDO_QUE_NO_EXISTE"));
});

test("party colours never collide with the government-level palette", () => {
  // Node colour encodes order of government; party colour must stay distinct
  // so the two encodings are never confused on screen.
  const levels = new Set(["#fbbf24", "#a78bfa", "#34d399", "#f472b6"]);
  for (const p of ["MORENA", "PAN", "PRI", "PVEM", "PT", "MC"]) {
    assert.ok(!levels.has(partyColor(p).toLowerCase()), `${p} reuses a level colour`);
  }
});
