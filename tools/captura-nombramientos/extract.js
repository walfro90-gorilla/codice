/**
 * Runs INSIDE the page the user is looking at, once, when they click the icon.
 *
 * It reads only what is already on screen and returns it — no navigation, no
 * requests, no storage. Everything it finds is a PROPOSAL the popup shows for
 * confirmation (R4): the person's name in particular is never guessed from the
 * text, because an appointment decree names several people (who appoints, who
 * is appointed, sometimes who is replaced) and picking the wrong one publishes
 * a false claim about a real person.
 */
(() => {
  const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();

  // Canonical URL, minus the noise search widgets leave behind: a citation has
  // to survive being pasted, and "#gsc.tab=0" is not part of the document.
  const raw =
    document.querySelector('link[rel="canonical"]')?.href ||
    document.querySelector('meta[property="og:url"]')?.content ||
    location.href;
  const canonical = (() => {
    try {
      const u = new URL(raw);
      u.hash = "";
      for (const k of [...u.searchParams.keys()]) {
        if (/^(utm_|gsc|gclid|fbclid)/i.test(k)) u.searchParams.delete(k);
      }
      return u.toString();
    } catch {
      return raw.split("#")[0];
    }
  })();

  // The DOF puts the decree's real title in the note container's first heading.
  // Reaching for the h2 instead — as this did at first — picks up the seal line
  // ("Al margen un sello con el Escudo Nacional...") that opens every decree,
  // which is the same string for thousands of unrelated documents.
  const heading =
    text(document.querySelector("#DivDetalleNota h1")) ||
    text(document.querySelector("#DivDetalleNota")).slice(0, 300) ||
    text(document.querySelector("h1")) ||
    text(document.querySelector('meta[property="og:title"]')) ||
    document.title.trim();

  // Publication date — NOT the date someone takes office. The popup keeps them
  // apart on purpose.
  //
  // Where it comes from decides how much it can be trusted. The DOF puts the
  // publication date in the URL, which is unambiguous. A date found in the body
  // is NOT: a decree quotes other dates ("el acuerdo publicado el 14 de marzo
  // de 2025..."), and taking the first one produced a plausible, wrong date —
  // worse than none, because nothing about it looks wrong. So a body date is
  // returned flagged, for the popup to mark as needing a second look.
  const body = document.body.innerText || "";
  const MONTHS = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre";
  let published = null;
  let publishedIsCertain = false;

  const urlSlash = canonical.match(/[?&]fecha=(\d{2})[/-](\d{2})[/-](\d{4})/);
  const urlIso = canonical.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (urlSlash) {
    published = `${urlSlash[3]}-${urlSlash[2]}-${urlSlash[1]}`;
    publishedIsCertain = true;
  } else if (urlIso) {
    published = `${urlIso[1]}-${urlIso[2]}-${urlIso[3]}`;
    publishedIsCertain = true;
  } else {
    const long = body.match(new RegExp(`(\\d{1,2})\\s+de\\s+(${MONTHS})\\s+de\\s+(\\d{4})`, "i"));
    const slash = body.match(/\b(\d{2})\/(\d{2})\/(\d{4})\b/);
    if (long) {
      const m = MONTHS.split("|").indexOf(long[2].toLowerCase()) + 1;
      published = `${long[3]}-${String(m).padStart(2, "0")}-${String(long[1]).padStart(2, "0")}`;
    } else if (slash) {
      published = `${slash[3]}-${slash[2]}-${slash[1]}`;
    }
  }

  // Whatever the user highlighted — that is their choice, not our inference.
  const selection = (window.getSelection()?.toString() || "").replace(/\s+/g, " ").trim();

  // A hint, shown as a hint: does this read like an appointment at all?
  const looksLikeAppointment =
    /\b(se nombra|nombramiento|designa|designación|toma de protesta|declaratoria de validez)\b/i.test(
      heading + " " + body.slice(0, 4000),
    );

  return {
    url: canonical,
    heading: heading.slice(0, 300),
    published,
    publishedIsCertain,
    selection: selection.length <= 120 ? selection : "",
    looksLikeAppointment,
    host: location.hostname,
  };
})();
