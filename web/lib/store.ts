import { create } from "zustand";

export type VizMode = "grafo" | "mapa";

type VizState = {
  mode: VizMode;
  selected: string | null;
  showExtinct: boolean;
  setMode: (mode: VizMode) => void;
  select: (id: string | null) => void;
  toggleExtinct: () => void;
};

export const useVizStore = create<VizState>((set) => ({
  mode: "grafo",
  selected: null,
  showExtinct: false,
  setMode: (mode) => set({ mode }),
  select: (selected) => set({ selected }),
  toggleExtinct: () => set((s) => ({ showExtinct: !s.showExtinct })),
}));
