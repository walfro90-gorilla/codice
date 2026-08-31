/**
 * Popup: turns one page the user is looking at into one YAML entry.
 *
 * Everything here is a proposal awaiting confirmation. The two fields most
 * easily got wrong are handled explicitly rather than guessed:
 *   - the person's NAME is never inferred from the decree text (a decree names
 *     several people; the wrong pick publishes a false claim about someone real);
 *   - the DATE the document was published is kept apart from the date the person
 *     took office, which is what the record actually stores.
 */

const CATALOG_URL = "https://codice-tan.vercel.app/data/grafo.json";

const $ = (id) => document.getElementById(id);
const yamlString = (s) => `"${String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;

let captured = null;

/** Compose the entry. Missing pieces stay as visible placeholders, never invented. */
function buildYaml() {
  const node = ($("node").value || $("nodeManual").value || "").trim();
  const nombre = $("nombre").value.trim();
  const cargo = $("cargo").value.trim();
  const desde = $("desde").value;
  const publicado = $("publicado").value;
  const url = captured?.url ?? "";
  const heading = captured?.heading ?? "";

  const lines = [
    `  - node: ${node || "[ID DEL NODO]"}`,
    `    nombre: ${nombre ? yamlString(nombre) : "[NOMBRE COMO APARECE EN EL DOCUMENTO]"}`,
    `    cargo: ${cargo ? yamlString(cargo) : "[CARGO]"}`,
    `    desde: ${desde || "[FECHA DE TOMA DE POSESIÓN]"}`,
    `    hasta: null`,
    `    contacto: null`,
    `    nombramiento:`,
    `      documento: ${heading ? yamlString(heading) : "[TÍTULO DEL DOCUMENTO]"}`,
    `      url: ${url}`,
    `      fecha: ${publicado || "[FECHA DE PUBLICACIÓN]"}`,
  ];
  $("yaml").value = lines.join("\n");
}

async function loadCatalog() {
  const sel = $("node");
  try {
    const res = await fetch(CATALOG_URL, { cache: "no-store" });
    const data = await res.json();
    // The chambers are ingested automatically; offering them here would invite
    // a curated entry that fights the scraper.
    const nodes = data.nodes
      .filter((n) => !["camara-diputados", "senado"].includes(n.id))
      .sort((a, b) => a.name.localeCompare(b.name, "es"));
    sel.innerHTML =
      '<option value="">— elige el nodo —</option>' +
      nodes
        .map((n) => `<option value="${n.id}">${n.name}${n.valid_to ? " (extinto)" : ""}</option>`)
        .join("");
  } catch {
    sel.hidden = true;
    $("nodeManual").hidden = false;
    $("warn").hidden = false;
    $("warn").textContent =
      "No se pudo cargar el catálogo de nodos; escribe el id a mano.";
  }
}

async function capture() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["extract.js"],
    });
    captured = result;
  } catch {
    $("doc").textContent =
      "No se puede leer esta pestaña. Abre la página del documento y vuelve a intentar.";
    return;
  }

  $("doc").innerHTML =
    `<strong>${captured.heading || "(sin título)"}</strong><br>${captured.url}`;
  if (captured.published) {
    $("publicado").value = captured.published;
    // A date read out of the body may be one the decree merely cites; say so
    // rather than letting it pass as if it were the publication date.
    if (!captured.publishedIsCertain) {
      $("dateWarn").hidden = false;
    }
  }
  if (captured.selection) {
    $("nombre").value = captured.selection;
    $("selHint").hidden = false;
  }
  if (!captured.looksLikeAppointment) {
    $("warn").hidden = false;
    $("warn").textContent =
      "Esta página no parece un acuerdo de nombramiento. Revísalo antes de registrarla.";
  }
  buildYaml();
}

for (const id of ["node", "nodeManual", "nombre", "cargo", "desde", "publicado"]) {
  $(id).addEventListener("input", buildYaml);
  $(id).addEventListener("change", buildYaml);
}
$("regen").addEventListener("click", buildYaml);
$("copy").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("yaml").value);
  $("status").textContent = "Copiado";
  setTimeout(() => ($("status").textContent = ""), 1800);
});

loadCatalog();
capture();
