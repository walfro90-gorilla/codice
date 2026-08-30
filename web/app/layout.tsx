import type { Metadata } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Códice — Cómo funciona México",
  description:
    "Prototipo Fase 0: visualización dual (grafo jerárquico / mapa geográfico) del Estado mexicano.",
};

// Dev-only: browsers freeze requestAnimationFrame in hidden tabs, which stops
// the R3F loop and blocks headless/automated visual checks. Fall back to a
// timer ONLY while hidden; native rAF takes over as soon as the tab is shown.
const devRafShim = `(function () {
  var native = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) {
    if (!document.hidden) return native(cb);
    return setTimeout(function () { cb(performance.now()); }, 33);
  };
})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        {process.env.NODE_ENV === "development" && (
          <script dangerouslySetInnerHTML={{ __html: devRafShim }} />
        )}
        {children}
      </body>
    </html>
  );
}
