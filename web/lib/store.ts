import { create } from "zustand";

export type VizMode = "grafo" | "mapa";

type VizState = {
  mode: VizMode;
  selected: string | null;
  showExtinct: boolean;
  /** Tour step index, or null when the tour is not running. */
  tourStep: number | null;
  /** Whether the instructions panel is open. */
  helpOpen: boolean;
  setMode: (mode: VizMode) => void;
  select: (id: string | null) => void;
  toggleExtinct: () => void;
  setExtinct: (show: boolean) => void;
  startTour: () => void;
  goToStep: (i: number | null) => void;
  toggleHelp: () => void;
};

export const useVizStore = create<VizState>((set) => ({
  mode: "grafo",
  selected: null,
  showExtinct: false,
  tourStep: null,
  helpOpen: false,
  setMode: (mode) => set({ mode }),
  select: (selected) => set({ selected }),
  toggleExtinct: () => set((s) => ({ showExtinct: !s.showExtinct })),
  setExtinct: (showExtinct) => set({ showExtinct }),
  startTour: () => set({ tourStep: 0, helpOpen: false }),
  goToStep: (tourStep) => set({ tourStep }),
  toggleHelp: () => set((s) => ({ helpOpen: !s.helpOpen })),
}));
