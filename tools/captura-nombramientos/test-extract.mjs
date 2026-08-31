/**
 * The extractor's failure modes are silent and specific, so they are pinned:
 * grabbing the seal line instead of the decree title, and letting search-widget
 * noise into a URL meant to be cited.
 *
 * Run: node test-extract.mjs
 */
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import { test } from "node:test";

// The file is an IIFE ending in a semicolon; wrapping it in parentheses (see
// below) needs that trailing semicolon gone.
const SRC = readFileSync(new URL("./extract.js", import.meta.url), "utf8")
  .trim()
  .replace(/;$/, "");

/** Minimal DOM stand-in — enough for the extractor's actual queries. */
function runWith({ html, url, selection = "" }) {
  const nodes = new Map(Object.entries(html));
  const el = (t) => (t === undefined ? null : { textContent: t, href: t, content: t });
  const doc = {
    title: html.title ?? "",
    body: { innerText: html.body ?? "" },
    querySelector: (sel) => el(nodes.get(sel)),
  };
  const win = { getSelection: () => ({ toString: () => selection }) };
  // The parenthesis matters: `return` followed by a newline triggers automatic
  // semicolon insertion, which silently returns undefined and made every
  // assertion here fail against an extractor that actually works.
  const fn = new Function("document", "location", "window", "URL", `return (${SRC});`);
  return fn(doc, new URL(url), win, URL);
}

const DECREE_BODY =
  "Al margen un sello con el Escudo Nacional. ACUERDO ... publicado el 28 de agosto de 2026 ...";

test("takes the decree's title, not the seal line every decree opens with", () => {
  const r = runWith({
    url: "https://dof.gob.mx/nota_detalle.php?codigo=5797384&fecha=28/08/2026",
    html: {
      "#DivDetalleNota h1": "ACUERDO Delegatorio de facultades de la Secretaría de Medio Ambiente",
      h2: "Al margen un sello con el Escudo Nacional, que dice: Estados Unidos Mexicanos.",
      title: "DOF - Diario Oficial de la Federación",
      body: DECREE_BODY,
    },
  });
  assert.match(r.heading, /^ACUERDO Delegatorio/);
  assert.ok(!r.heading.includes("sello"), "picked up the seal line");
});

test("a citable URL carries no search-widget or tracking noise", () => {
  const r = runWith({
    url: "https://dof.gob.mx/nota_detalle.php?codigo=5797384&fecha=28/08/2026#gsc.tab=0",
    html: { title: "DOF", body: DECREE_BODY },
  });
  assert.ok(!r.url.includes("#"), `hash survived: ${r.url}`);
  assert.ok(r.url.includes("codigo=5797384"), "dropped a parameter that identifies the document");
});

test("reads the publication date from the decree's own wording", () => {
  const r = runWith({
    url: "https://example.gob.mx/doc",
    html: { title: "x", body: "Publicado el 28 de agosto de 2026 en el Diario Oficial." },
  });
  assert.equal(r.published, "2026-08-28");
});

test("flags a page that does not read like an appointment", () => {
  const notAppointment = runWith({
    url: "https://dof.gob.mx/x",
    html: { title: "Aviso de tarifas", body: "Aviso por el que se dan a conocer las tarifas." },
  });
  assert.equal(notAppointment.looksLikeAppointment, false);

  const appointment = runWith({
    url: "https://dof.gob.mx/y",
    html: { "#DivDetalleNota h1": "ACUERDO por el que se nombra a la Titular", body: "se nombra" },
  });
  assert.equal(appointment.looksLikeAppointment, true);
});

test("uses the user's selection as the name, and never invents one", () => {
  const withSel = runWith({
    url: "https://dof.gob.mx/z",
    html: { title: "x", body: "se nombra a Fulana de Tal como Titular" },
    selection: "Fulana de Tal",
  });
  assert.equal(withSel.selection, "Fulana de Tal");

  const withoutSel = runWith({
    url: "https://dof.gob.mx/z",
    html: { title: "x", body: "se nombra a Fulana de Tal como Titular" },
  });
  // The decree names several people; guessing one would publish a false claim.
  assert.equal(withoutSel.selection, "");
});

test("a date taken from the body is flagged; one from the URL is not", () => {
  // A decree quotes other decrees' dates. Trusting the first date in the body
  // produced a plausible, wrong publication date on a real DOF page.
  const fromUrl = runWith({
    url: "https://dof.gob.mx/nota_detalle.php?codigo=5797384&fecha=28/08/2026",
    html: { title: "x", body: "publicado el 14 de marzo de 2025 se reforma..." },
  });
  assert.equal(fromUrl.published, "2026-08-28", "the URL date must win");
  assert.equal(fromUrl.publishedIsCertain, true);

  const fromBody = runWith({
    url: "https://example.gob.mx/doc",
    html: { title: "x", body: "Publicado el 28 de agosto de 2026." },
  });
  assert.equal(fromBody.published, "2026-08-28");
  assert.equal(fromBody.publishedIsCertain, false, "a body date must be flagged");
});
