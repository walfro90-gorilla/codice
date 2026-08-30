/**
 * Códice shared data contracts (TypeScript side).
 *
 * Frozen contract: changes require a new ADR and must be mirrored in
 * contracts/python/codice_contracts/models.py. The web and MCP lanes
 * validate API responses with these schemas.
 */

import { z } from "zod";

export const GovLevel = z.enum(["federal", "estatal", "municipal", "ciudadano"]);
export const TerritoryLevel = z.enum(["estado", "municipio", "localidad"]);
export const EdgeType = z.enum(["autoridad", "legitimidad"]);
export const ReviewStatus = z.enum(["pending", "confirmed", "rejected"]);
export const SignalStatus = z.enum(["por_verificar", "verificada", "descartada"]);
export const MatchMethod = z.enum(["deterministic", "rfc", "trigram"]);
export const EntityKind = z.enum(["person", "company"]);
export const PromiseState = z.enum([
  "sin_evidencia",
  "iniciativa_presentada",
  "dictaminada_en_comision",
  "aprobada",
  "publicada_dof",
  "presupuesto_asignado",
]);

const sha256 = z.string().regex(/^[0-9a-f]{64}$/);
const isoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const rfc = z.string().regex(/^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/);

/** Provenance of a datum (R1). Every published object carries these. */
export const SourceRef = z
  .object({
    url: z.string().url(),
    captured_at: z.string().datetime({ offset: true }),
    hash: sha256,
  })
  .strict();

export const LegalBasis = z
  .object({
    document: z.string(),
    article: z.string(),
    url: z.string().url(),
  })
  .strict();

export const Node = z
  .object({
    id: z.string().regex(/^[a-z0-9][a-z0-9-]*$/), // permanent citable slug (R10)
    node_type: z.string(),
    name: z.string(),
    level: GovLevel,
    territory_key: z.string().nullable(), // INEGI key, never a name (R7)
    summary: z.string().nullable(),
    legal_basis: z.array(LegalBasis),
    valid_from: isoDate,
    valid_to: isoDate.nullable(),
    permalink: z.string().url(),
    sources: z.array(SourceRef),
  })
  .strict();

export const Edge = z
  .object({
    from_node: z.string(),
    to_node: z.string(),
    type: EdgeType,
    legal_basis: z.string().nullable(),
    valid_from: isoDate,
    valid_to: isoDate.nullable(),
  })
  .strict();

/** Node as served by GET /grafo: one node, TWO positions, zero duplication. */
export const GraphNode = z
  .object({
    id: z.string(),
    name: z.string(),
    level: GovLevel,
    depth: z.number().int(),
    pos_graph: z.object({ x: z.number(), y: z.number() }).strict(),
    pos_geo: z.object({ lon: z.number(), lat: z.number() }).strict().nullable(),
  })
  .strict();

export const GraphEdge = z
  .object({
    from: z.string(),
    to: z.string(),
    type: EdgeType,
  })
  .strict();

export const Graph = z
  .object({
    nodes: z.array(GraphNode),
    edges: z.array(GraphEdge),
    sources: z.array(SourceRef),
  })
  .strict();

export const Territory = z
  .object({
    inegi_key: z.string().regex(/^\d{2}(\d{3})?(\d{4})?$/),
    level: TerritoryLevel,
    name: z.string(),
    parent_key: z.string().nullable(),
    centroid: z.object({ lon: z.number(), lat: z.number() }).strict().nullable(),
    population: z.array(
      z.object({ census_year: z.number().int(), population: z.number().int().nonnegative() }).strict(),
    ),
    sources: z.array(SourceRef),
  })
  .strict();

export const Tenure = z
  .object({
    person_id: z.string().uuid(),
    person_name: z.string(),
    node_id: z.string(),
    role: z.string(),
    party: z.string().nullable(),
    start_date: isoDate,
    end_date: isoDate.nullable(),
    contact_email: z.string().nullable(), // institutional only
    contact_phone: z.string().nullable(), // institutional only
    sources: z.array(SourceRef),
  })
  .strict();

export const Person = z
  .object({
    id: z.string().uuid(),
    full_name: z.string(),
    tenures: z.array(Tenure),
    sources: z.array(SourceRef),
  })
  .strict();

export const Company = z
  .object({
    id: z.string().uuid(),
    legal_name: z.string(),
    normalized_name: z.string(),
    rfc: rfc.nullable(),
  })
  .strict();

/** R3/R4: candidates only. Merging requires a recorded human review. */
export const EntityMatchCandidate = z
  .object({
    kind: EntityKind,
    entity_a: z.string().uuid(),
    entity_b: z.string().uuid(),
    score: z.number().min(0).max(1),
    method: MatchMethod,
    status: ReviewStatus,
    reviewed_by: z.string().nullable(),
    reviewed_at: z.string().datetime({ offset: true }).nullable(),
  })
  .strict();

/** A signal to verify — never a conclusion (R2). */
export const Signal = z
  .object({
    id: z.string().uuid(),
    signal_type: z.string(),
    score: z.number().min(0).max(1),
    legal_basis: z.string(),
    status: SignalStatus,
    entities: z.array(
      z.object({ kind: EntityKind, entity_id: z.string().uuid(), name: z.string() }).strict(),
    ),
    evidence: z.array(SourceRef),
    created_at: z.string().datetime({ offset: true }),
  })
  .strict();

export const Promise_ = z
  .object({
    text: z.string(),
    actor_party: z.string().nullable(),
    actor_person: z.string().uuid().nullable(),
    election_year: z.number().int(),
  })
  .strict();

/** One rung of the evidence ladder; a document with folio is mandatory (R5). */
export const PromiseEvidence = z
  .object({
    promise_id: z.string().uuid(),
    state: PromiseState,
    folio: z.string(),
    event_date: isoDate,
    snapshot_id: z.string().uuid(),
  })
  .strict();

export type GovLevelT = z.infer<typeof GovLevel>;
export type SourceRefT = z.infer<typeof SourceRef>;
export type NodeT = z.infer<typeof Node>;
export type EdgeT = z.infer<typeof Edge>;
export type GraphT = z.infer<typeof Graph>;
export type GraphNodeT = z.infer<typeof GraphNode>;
export type TerritoryT = z.infer<typeof Territory>;
export type PersonT = z.infer<typeof Person>;
export type TenureT = z.infer<typeof Tenure>;
export type SignalT = z.infer<typeof Signal>;
