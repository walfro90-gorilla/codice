"use client";
/**
 * Guided tour and instructions.
 *
 * The tour applies each step's state to the visualization, so the reader
 * watches the real interface do what the text describes. It never blocks the
 * canvas: the card sits to one side and the app stays interactive underneath.
 */
import { useEffect } from "react";
import { TOUR, markTourSeen, tourAlreadySeen } from "../lib/tour";
import { useVizStore } from "../lib/store";

const card: React.CSSProperties = {
  position: "absolute",
  zIndex: 10,
  background: "rgba(11, 15, 20, 0.96)",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: "16px 18px",
  fontSize: 13,
  lineHeight: 1.65,
  boxShadow: "0 10px 40px rgba(0,0,0,0.55)",
};

const button = (primary = false): React.CSSProperties => ({
  padding: "6px 14px",
  borderRadius: 6,
  border: "1px solid " + (primary ? "#fbbf24" : "#374151"),
  background: primary ? "#fbbf24" : "transparent",
  color: primary ? "#0b0f14" : "#e5e7eb",
  fontWeight: 600,
  fontSize: 12,
  cursor: "pointer",
});

export function TourOverlay() {
  const step = useVizStore((s) => s.tourStep);
  const goToStep = useVizStore((s) => s.goToStep);
  const select = useVizStore((s) => s.select);
  const setMode = useVizStore((s) => s.setMode);
  const setExtinct = useVizStore((s) => s.setExtinct);

  // Offer the tour on a first visit, without forcing it on returning readers.
  useEffect(() => {
    if (!tourAlreadySeen()) goToStep(0);
  }, [goToStep]);

  // Apply the step: this is what makes the tour a demonstration, not a text.
  useEffect(() => {
    if (step === null) return;
    const s = TOUR[step];
    if (!s) return;
    if (s.select !== undefined) select(s.select);
    if (s.mode) setMode(s.mode);
    if (s.showExtinct !== undefined) setExtinct(s.showExtinct);
  }, [step, select, setMode, setExtinct]);

  // Arrow keys and Escape, because a tour you cannot leave is a trap.
  useEffect(() => {
    if (step === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") finish();
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (step === null) return null;
  const s = TOUR[step];
  if (!s) return null;

  const last = step === TOUR.length - 1;

  function finish() {
    markTourSeen();
    goToStep(null);
  }
  function next() {
    if (last) finish();
    else goToStep(step! + 1);
  }
  function prev() {
    if (step! > 0) goToStep(step! - 1);
  }

  const position: React.CSSProperties =
    s.place === "center"
      ? { top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: 460 }
      : s.place === "bottom-left"
        ? { bottom: 24, left: 24, width: 400 }
        // Clears the header (title card plus the control row) so the tour never
        // covers the buttons it is telling the reader about.
        : { top: 152, left: 16, width: 400 };

  return (
    <div style={{ ...card, ...position }} role="dialog" aria-label="Recorrido guiado">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
        <strong style={{ fontSize: 15, color: "#fbbf24" }}>{s.title}</strong>
        <span style={{ color: "#6b7280", fontSize: 11, whiteSpace: "nowrap" }}>
          {step + 1} de {TOUR.length}
        </span>
      </div>

      <p style={{ margin: "10px 0 0", color: "#d1d5db" }}>{s.body}</p>

      {/* Progress: thin, unobtrusive, and clickable to jump around. */}
      <div style={{ display: "flex", gap: 4, marginTop: 14 }}>
        {TOUR.map((_, i) => (
          <button
            key={i}
            onClick={() => goToStep(i)}
            aria-label={`Ir al paso ${i + 1}`}
            style={{
              flex: 1,
              height: 3,
              border: "none",
              padding: 0,
              cursor: "pointer",
              background: i <= step ? "#fbbf24" : "#374151",
            }}
          />
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 14, alignItems: "center" }}>
        <button onClick={next} style={button(true)}>{last ? "Explorar" : "Siguiente"}</button>
        {step > 0 && <button onClick={prev} style={button()}>Atrás</button>}
        <button
          onClick={finish}
          style={{ ...button(), border: "none", color: "#6b7280", marginLeft: "auto" }}
        >
          Saltar
        </button>
      </div>
    </div>
  );
}

/** Instructions panel: the controls, plus how to read what is on screen. */
export function HelpPanel() {
  const open = useVizStore((s) => s.helpOpen);
  const toggleHelp = useVizStore((s) => s.toggleHelp);
  const startTour = useVizStore((s) => s.startTour);
  if (!open) return null;

  return (
    <div style={{ ...card, top: 96, right: 16, width: 380, maxHeight: "calc(100vh - 120px)", overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <strong style={{ fontSize: 15, color: "#fbbf24" }}>Cómo usar este mapa</strong>
        <button onClick={toggleHelp} style={{ background: "none", border: "none", color: "#9ca3af", cursor: "pointer", fontSize: 18 }}>
          ×
        </button>
      </div>

      <div style={{ fontWeight: 600, marginTop: 12, color: "#e5e7eb" }}>Moverte</div>
      <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: "#d1d5db" }}>
        <li>Rueda del ratón o gesto de pellizco: acercar y alejar</li>
        <li>Arrastrar: desplazarte por el mapa</li>
        <li>Clic en un órgano: abrir su ficha</li>
        <li>Clic fuera o la tecla Esc: cerrar la ficha</li>
      </ul>

      <div style={{ fontWeight: 600, marginTop: 12, color: "#e5e7eb" }}>Los dos modos</div>
      <p style={{ margin: "6px 0 0", color: "#d1d5db" }}>
        <strong>Grafo</strong> ordena los órganos por jerarquía. <strong>Mapa</strong> los coloca en su territorio real.
        Es el mismo dato con dos posiciones: los órganos federales no tienen territorio, así que conservan su lugar en la jerarquía.
      </p>

      <div style={{ fontWeight: 600, marginTop: 12, color: "#e5e7eb" }}>Los nombres y la minitarjeta</div>
      <p style={{ margin: "6px 0 0", color: "#d1d5db" }}>
        Los nombres aparecen conforme te acercas: de lejos solo los poderes, luego las secretarías, después todo.
        Al pasar el cursor por un órgano sale una tarjeta con lo esencial —su integración por partido o su
        presupuesto— sin abrir la ficha completa.
      </p>

      <div style={{ fontWeight: 600, marginTop: 12, color: "#e5e7eb" }}>Qué significan los colores</div>
      <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: "#d1d5db" }}>
        <li>El color del círculo es el orden de gobierno: federal, estatal, municipal o la ciudadanía</li>
        <li>Las líneas naranjas son autoridad y van hacia abajo</li>
        <li>Las líneas azules son legitimidad y van hacia arriba, desde quien vota</li>
        <li>Los órganos en gris están extintos; aparecen si activas la casilla</li>
        <li>La barra bajo una cámara es su reparto de escaños por grupo parlamentario</li>
      </ul>

      <div style={{ fontWeight: 600, marginTop: 12, color: "#e5e7eb" }}>Cómo leer una ficha</div>
      <p style={{ margin: "6px 0 0", color: "#d1d5db" }}>
        Cada afirmación trae su fundamento legal, un enlace al documento oficial y la huella sha256 del archivo con su fecha
        de captura. Las cifras de dinero traen siempre sus advertencias metodológicas: no se publica un número sin decir
        cómo debe leerse.
      </p>

      <div style={{ fontWeight: 600, marginTop: 12, color: "#e5e7eb" }}>Qué no vas a encontrar</div>
      <p style={{ margin: "6px 0 0", color: "#d1d5db" }}>
        Ni calificaciones, ni porcentajes de cumplimiento, ni semáforos. Códice publica datos con su fuente para que saques
        tus propias conclusiones; no emite veredictos sobre nadie.
      </p>

      <button onClick={startTour} style={{ ...button(true), marginTop: 16 }}>
        Ver el recorrido guiado
      </button>
    </div>
  );
}
