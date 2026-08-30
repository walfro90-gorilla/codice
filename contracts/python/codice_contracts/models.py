"""Códice shared data contracts (Python side).

Frozen contract: changes require a new ADR and must be mirrored in
contracts/typescript/src/index.ts. Layer boundaries validate with these
models — if a scraper or parser emits garbage, it stops here.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GovLevel(str, Enum):
    federal = "federal"
    estatal = "estatal"
    municipal = "municipal"
    ciudadano = "ciudadano"


class TerritoryLevel(str, Enum):
    estado = "estado"
    municipio = "municipio"
    localidad = "localidad"


class EdgeType(str, Enum):
    autoridad = "autoridad"
    legitimidad = "legitimidad"


class ReviewStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"


class SignalStatus(str, Enum):
    por_verificar = "por_verificar"
    verificada = "verificada"
    descartada = "descartada"


class MatchMethod(str, Enum):
    deterministic = "deterministic"
    rfc = "rfc"
    trigram = "trigram"


class EntityKind(str, Enum):
    person = "person"
    company = "company"


class PromiseState(str, Enum):
    sin_evidencia = "sin_evidencia"
    iniciativa_presentada = "iniciativa_presentada"
    dictaminada_en_comision = "dictaminada_en_comision"
    aprobada = "aprobada"
    publicada_dof = "publicada_dof"
    presupuesto_asignado = "presupuesto_asignado"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceRef(_Strict):
    """Provenance of a datum (R1). Every published object carries these."""

    url: HttpUrl
    captured_at: datetime
    hash: str = Field(pattern=r"^[0-9a-f]{64}$", description="sha256 of raw snapshot")


class SnapshotMeta(_Strict):
    """Output of the L1 ingestion boundary (R8: raw, never parsed)."""

    source_key: str
    url: HttpUrl
    captured_at: datetime
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    r2_key: str
    content_type: str


class LegalBasis(_Strict):
    document: str
    article: str
    url: HttpUrl


class Node(_Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$", description="permanent citable slug (R10)")
    node_type: str
    name: str
    level: GovLevel
    territory_key: str | None = Field(default=None, description="INEGI key, never a name (R7)")
    summary: str | None = None
    legal_basis: list[LegalBasis]
    valid_from: date
    valid_to: date | None = None


class Edge(_Strict):
    from_node: str
    to_node: str
    type: EdgeType
    legal_basis: str | None = None
    valid_from: date
    valid_to: date | None = None


class Territory(_Strict):
    inegi_key: str = Field(pattern=r"^\d{2}(\d{3})?(\d{4})?$")
    level: TerritoryLevel
    name: str
    parent_key: str | None = None


class Population(_Strict):
    inegi_key: str
    census_year: int
    population: int = Field(ge=0)


class Person(_Strict):
    id: UUID
    full_name: str
    normalized_name: str
    rfc: str | None = Field(default=None, pattern=r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")


class Tenure(_Strict):
    person_id: UUID
    node_id: str
    role: str
    party: str | None = None
    start_date: date
    end_date: date | None = None
    contact_email: str | None = Field(default=None, description="institutional only")
    contact_phone: str | None = Field(default=None, description="institutional only")


class Company(_Strict):
    id: UUID
    legal_name: str
    normalized_name: str = Field(description="lowercase, unaccented, corporate suffixes stripped")
    rfc: str | None = Field(default=None, pattern=r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")


class EntityMatchCandidate(_Strict):
    """R3/R4: candidates only. Merging requires a recorded human review."""

    kind: EntityKind
    entity_a: UUID
    entity_b: UUID
    score: float = Field(ge=0, le=1)
    method: MatchMethod
    status: ReviewStatus = ReviewStatus.pending
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None


class Signal(_Strict):
    """A signal to verify — never a conclusion (R2)."""

    signal_type: str
    score: float = Field(ge=0, le=1)
    legal_basis: str
    status: SignalStatus = SignalStatus.por_verificar
    entities: list[tuple[EntityKind, UUID]]
    evidence_snapshots: list[UUID]


class Promise(_Strict):
    text: str
    actor_party: str | None = None
    actor_person: UUID | None = None
    election_year: int


class PromiseEvidence(_Strict):
    """One rung of the evidence ladder; a document with folio is mandatory (R5)."""

    promise_id: UUID
    state: PromiseState
    folio: str
    event_date: date
    snapshot_id: UUID


class PromiseLink(_Strict):
    """LLM proposes with a score; a human confirms and is recorded (R4)."""

    promise_id: UUID
    target_kind: str
    target_ref: str
    score: float = Field(ge=0, le=1)
    proposed_by: str
    status: ReviewStatus = ReviewStatus.pending
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
