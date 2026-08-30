/**
 * Guided tour: the steps are data, the component that plays them is dumb.
 *
 * The tour DRIVES the app — it selects nodes, switches modes, reveals extinct
 * organs — so the reader watches the real interface do the thing being
 * explained instead of reading a description of it.
 *
 * What it teaches is the method, not the buttons: where a claim comes from,
 * why a figure carries a warning, and why the present is just one date.
 */
import type { VizMode } from "./store";

export type TourStep = {
  title: string;
  body: string;
  /** Node the step selects, so the detail panel shows what the text describes. */
  select?: string | null;
  mode?: VizMode;
  showExtinct?: boolean;
  /** Where to put the tour card so it never covers what it points at. */
  place?: "center" | "left" | "bottom-left";
};

export const TOUR: TourStep[] = [
  {
    title: "Cómo funciona México",
    body:
      "Este es un mapa del Estado mexicano: 201 órganos, quiénes los ocupan y cuánto dinero manejan. " +
      "Cada dato apunta a un documento oficial con su fecha y su huella digital. " +
      "El recorrido toma un minuto y te enseña cómo leerlo.",
    select: null,
    mode: "grafo",
    showExtinct: false,
    place: "center",
  },
  {
    title: "La doble flecha",
    body:
      "Las líneas naranjas son autoridad y bajan: del Ejecutivo a sus secretarías, de la Cámara a la Auditoría. " +
      "Las líneas azules son legitimidad y suben: de la ciudadanía a cada cargo que se elige por voto. " +
      "Esa doble dirección explica el país mejor que cualquier organigrama, y por eso está en el modelo, no en el dibujo.",
    select: "ciudadania",
    place: "left",
  },
  {
    title: "Lo que no existe también informa",
    body:
      "No verás una flecha de autoridad del gobierno federal a los estados, ni de un gobernador a sus municipios. " +
      "No es un olvido: el pacto federal (artículo 40) y el municipio libre (artículo 115) establecen que esa autoridad no existe. " +
      "Un organigrama que la dibujara estaría mintiendo.",
    select: null,
    place: "left",
  },
  {
    title: "De dónde sale cada afirmación",
    body:
      "Haz clic en cualquier órgano y verás su fundamento legal: el artículo exacto, un enlace al documento y la huella sha256 " +
      "del archivo que descargamos, con la fecha en que lo hicimos. " +
      "Si mañana la fuente cambia o desaparece, ese archivo sigue existiendo de nuestro lado.",
    select: "suprema-corte",
    place: "left",
  },
  {
    title: "Quién ocupa cada cargo",
    body:
      "Las 500 diputaciones y las 127 senadurías en funciones, con su partido, el periodo y su correo institucional. " +
      "Solo contacto institucional: las fichas oficiales publican más datos personales y aquí no se guardan.",
    select: "senado",
    place: "left",
  },
  {
    title: "El dinero, y lo que el dinero no dice",
    body:
      "Presupuesto aprobado frente a gasto ejercido, año por año. " +
      "Fíjate en las notas al pie de la cifra: aparecen siempre, pegadas al número. " +
      "Gastar más o menos de lo aprobado no es por sí mismo irregularidad ni ahorro, y el sistema no califica a nadie: " +
      "publica las dos cifras y su diferencia.",
    select: "imss",
    place: "left",
  },
  {
    title: "El mismo nodo, en el territorio",
    body:
      "Cambia a modo mapa y cada entidad viaja a su ubicación real. Es el mismo dato con otra posición, no una copia. " +
      "Aquí aparece el gasto federal por habitante — junto con la advertencia de que el presupuesto se registra donde está " +
      "la oficina, no donde se gasta. Sin esa nota, comparar entidades induce a una conclusión falsa.",
    select: "ejecutivo-estatal-09",
    mode: "mapa",
    place: "left",
  },
  {
    title: "El presente es solo una fecha",
    body:
      "Activa «mostrar órganos extintos» y reaparecen el INAI, la COFECE, el IFT y los demás que desaparecieron entre 2024 y 2025, " +
      "con su fecha de extinción y su presupuesto de los años en que existieron. " +
      "Nada se borra: se le pone fecha de cierre.",
    select: "inai",
    mode: "grafo",
    showExtinct: true,
    place: "left",
  },
  {
    title: "Para citarlo",
    body:
      "Cada órgano tiene un enlace permanente, y los datos completos están abiertos en /data/grafo.json para descargar y reusar. " +
      "Si un periodista no lo puede citar, no sirve. Ya puedes explorar por tu cuenta: arrastra para moverte, rueda para acercar.",
    select: null,
    showExtinct: false,
    place: "center",
  },
];

export const TOUR_SEEN_KEY = "codice.tour.v1";

/** Whether this visitor has already been through the tour. */
export function tourAlreadySeen(): boolean {
  try {
    return localStorage.getItem(TOUR_SEEN_KEY) === "1";
  } catch {
    return false; // private windows and blocked storage: just show it
  }
}

export function markTourSeen(): void {
  try {
    localStorage.setItem(TOUR_SEEN_KEY, "1");
  } catch {
    // Not being able to remember is not a reason to fail
  }
}
