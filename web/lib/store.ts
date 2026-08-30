import { create } from "zustand";

export type VizMode = "grafo" | "mapa";

/** How much of the graph is legible at the current camera zoom. */
export type LabelTier = "anchors" | "federal" | "all";

type VizState = {
  mode: VizMode;
  selected: string | null;
  /** Node under the pointer, and where the pointer is, for the hover card. */
  hovered: string | null;
  pointer: { x: number; y: number };
  labelTier: LabelTier;
  showExtinct: boolean;
  /** Tour step index, or null when the tour is not running. */
  tourStep: number | null;
  /** Whether the instructions panel is open. */
  helpOpen: boolean;
  setMode: (mode: VizMode) => void;
  select: (id: string | null) => void;
  hover: (id: string | null, x?: number, y?: number) => void;
  setLabelTier: (tier: LabelTier) => void;
  toggleExtinct: () => void;
  setExtinct: (show: boolean) => void;
  startTour: () => void;
  goToStep: (i: number | null) => void;
  toggleHelp: () => void;
};

export const useVizStore = create<VizState>((set) => ({
  mode: "grafo",
  selected: null,
  hovered: null,
  pointer: { x: 0, y: 0 },
  labelTier: "anchors",
  showExtinct: false,
  tourStep: null,
  helpOpen: false,
  setMode: (mode) => set({ mode }),
  select: (selected) => set({ selected }),
  hover: (hovered, x, y) =>
    set((s) => ({ hovered, pointer: x === undefined ? s.pointer : { x, y: y ?? 0 } })),
  // Only ever set from a frame loop when the tier actually changes, so the
  // camera moving does not re-render React sixty times a second.
  setLabelTier: (labelTier) => set((s) => (s.labelTier === labelTier ? s : { labelTier })),
  toggleExtinct: () => set((s) => ({ showExtinct: !s.showExtinct })),
  setExtinct: (showExtinct) => set({ showExtinct }),
  startTour: () => set({ tourStep: 0, helpOpen: false }),
  goToStep: (tourStep) => set({ tourStep }),
  toggleHelp: () => set((s) => ({ helpOpen: !s.helpOpen })),
}));
