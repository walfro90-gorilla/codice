import { create } from "zustand";

export type VizMode = "grafo" | "mapa";

type VizState = {
  mode: VizMode;
  setMode: (mode: VizMode) => void;
};

export const useVizStore = create<VizState>((set) => ({
  mode: "grafo",
  setMode: (mode) => set({ mode }),
}));
