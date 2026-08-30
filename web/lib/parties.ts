/**
 * Party identity colours.
 *
 * These are a PRESENTATION convention, not data from any source: the colours
 * each party is conventionally identified by in Mexican press and electoral
 * material. They carry no judgement and no official standing, so they never
 * decide anything — they only let a reader tell one bar segment from another.
 *
 * We deliberately do NOT reproduce party logos: those are registered marks,
 * and a proportional bar says more than an emblem anyway — it shows how a
 * chamber is actually split.
 *
 * Party colour never replaces a node's colour. Nodes stay coloured by order of
 * government (federal / estatal / municipal / ciudadanía); party colour appears
 * only inside composition bars and the hover card, so the two encodings never
 * compete for the same pixel.
 */
import type { Occupant } from "./data";

export const PARTY_COLORS: Record<string, string> = {
  MORENA: "#9e1b32",
  PAN: "#0b4ea2",
  PRI: "#0d7c3f",
  PVEM: "#6cb33f",
  PT: "#d0021b",
  MC: "#f58220",
};

/** Seats with no parliamentary group: an absence, never an invented label (R6). */
export const NO_PARTY_COLOR = "#4b5563";
export const NO_PARTY_LABEL = "Sin grupo parlamentario";

export function partyColor(party: string | null): string {
  return (party && PARTY_COLORS[party]) || NO_PARTY_COLOR;
}

export type PartyShare = {
  party: string | null;
  label: string;
  seats: number;
  share: number; // 0..1
  color: string;
};

/** Seat counts per party, largest first — the shape a composition bar needs. */
export function composition(occupants: Occupant[]): PartyShare[] {
  if (occupants.length === 0) return [];
  const counts = new Map<string | null, number>();
  for (const o of occupants) counts.set(o.party, (counts.get(o.party) ?? 0) + 1);
  return [...counts.entries()]
    .map(([party, seats]) => ({
      party,
      label: party ?? NO_PARTY_LABEL,
      seats,
      share: seats / occupants.length,
      color: partyColor(party),
    }))
    .sort((a, b) => b.seats - a.seats);
}
