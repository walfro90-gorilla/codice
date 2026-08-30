-- Códice — canonical schema (L2). Frozen contract: changes require a new ADR.
-- Postgres 15+. Extensions required by ADR: PostGIS, pg_trgm, pgvector.

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Closed vocabularies (true enums). Open vocabularies use lookup tables below.
-- ---------------------------------------------------------------------------

CREATE TYPE gov_level AS ENUM ('federal', 'estatal', 'municipal', 'ciudadano');
CREATE TYPE territory_level AS ENUM ('estado', 'municipio', 'localidad');
-- Dual arrow (ADR: authority flows down, legitimacy flows up)
CREATE TYPE edge_type AS ENUM ('autoridad', 'legitimidad');
CREATE TYPE review_status AS ENUM ('pending', 'confirmed', 'rejected');
CREATE TYPE signal_status AS ENUM ('por_verificar', 'verificada', 'descartada');
CREATE TYPE match_method AS ENUM ('deterministic', 'rfc', 'trigram');
CREATE TYPE entity_kind AS ENUM ('person', 'company');
-- Evidence ladder for promises (R5: states, never percentages)
CREATE TYPE promise_state AS ENUM (
  'sin_evidencia', 'iniciativa_presentada', 'dictaminada_en_comision',
  'aprobada', 'publicada_dof', 'presupuesto_asignado'
);

-- ---------------------------------------------------------------------------
-- L1 metadata: sources & raw snapshots (R1, R8). Blobs live in R2, never here.
-- ---------------------------------------------------------------------------

CREATE TABLE source (
  key         text PRIMARY KEY,          -- e.g. 'sil', 'dof', 'sat_69b', 'inegi_censo'
  name        text NOT NULL,
  base_url    text NOT NULL,
  format      text NOT NULL,             -- 'html', 'json', 'zip', 'pdf', ...
  notes       text
);

CREATE TABLE snapshot (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_key    text NOT NULL REFERENCES source(key),
  url           text NOT NULL,           -- exact URL fetched
  captured_at   timestamptz NOT NULL,
  content_hash  text NOT NULL,           -- sha256 hex of the raw bytes
  r2_key        text NOT NULL,           -- object key in Cloudflare R2
  content_type  text NOT NULL,
  UNIQUE (content_hash, url)
);

-- Generic provenance link: any canonical record -> the snapshots backing it.
-- ponytail: polymorphic (record_table, record_id) instead of one link table per
-- entity; app layer guarantees the record side, promote to per-table links if
-- integrity bugs ever show up.
CREATE TABLE provenance (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  record_table  text NOT NULL,
  record_id     text NOT NULL,
  snapshot_id   uuid NOT NULL REFERENCES snapshot(id),
  observed_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_provenance_record ON provenance (record_table, record_id);

-- ---------------------------------------------------------------------------
-- Territory (R7: INEGI key is the canonical territorial ID, never the name)
-- ---------------------------------------------------------------------------

CREATE TABLE territory (
  inegi_key   text PRIMARY KEY,          -- '09' (estado), '09015' (municipio), '090150001' (localidad)
  level       territory_level NOT NULL,
  name        text NOT NULL,             -- display only, NEVER a join key
  parent_key  text REFERENCES territory(inegi_key),
  geom        geometry(MultiPolygon, 4326),
  centroid    geometry(Point, 4326),
  valid_from  date NOT NULL DEFAULT '1900-01-01',
  valid_to    date                       -- NULL = currently valid (R9)
);
CREATE INDEX idx_territory_geom ON territory USING gist (geom);

-- Population versioned by census year (Censo 2030 will arrive)
CREATE TABLE population (
  inegi_key    text NOT NULL REFERENCES territory(inegi_key),
  census_year  int  NOT NULL,
  population   bigint NOT NULL,
  PRIMARY KEY (inegi_key, census_year)
);

-- ---------------------------------------------------------------------------
-- Structure: nodes & edges (Fase 1). The graph is a DERIVED view, not a graph DB.
-- ---------------------------------------------------------------------------

-- Open vocabulary: adding a node type is a data change, not a DDL change.
CREATE TABLE node_type (
  key         text PRIMARY KEY,          -- 'poder', 'secretaria_de_estado', 'organo_autonomo', ...
  name        text NOT NULL,
  description text
);

CREATE TABLE node (
  id            text PRIMARY KEY,        -- permanent citable slug (R10), e.g. 'ejecutivo-federal'
  node_type_key text NOT NULL REFERENCES node_type(key),
  name          text NOT NULL,
  level         gov_level NOT NULL,
  territory_key text REFERENCES territory(inegi_key),
  summary       text,                    -- citizen-facing plain-language summary (cached, never live LLM)
  valid_from    date NOT NULL DEFAULT '1900-01-01',
  valid_to      date
);
CREATE INDEX idx_node_territory ON node (territory_key);

-- Each node cites the specific article that grounds it (Fase 1 requirement)
CREATE TABLE node_legal_basis (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id     text NOT NULL REFERENCES node(id),
  document    text NOT NULL,             -- 'CPEUM', 'Ley Orgánica de la APF', ...
  article     text NOT NULL,             -- 'Art. 80', 'Art. 26 y 28'
  url         text NOT NULL,
  snapshot_id uuid REFERENCES snapshot(id)
);

CREATE TABLE edge (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_node    text NOT NULL REFERENCES node(id),
  to_node      text NOT NULL REFERENCES node(id),
  type         edge_type NOT NULL,       -- autoridad: from -> to (down). legitimidad: from -> to (up).
  legal_basis  text,
  valid_from   date NOT NULL DEFAULT '1900-01-01',
  valid_to     date,
  UNIQUE (from_node, to_node, type, valid_from)
);
CREATE INDEX idx_edge_from ON edge (from_node);
CREATE INDEX idx_edge_to ON edge (to_node);

-- ---------------------------------------------------------------------------
-- People & tenures (Fase 2)
-- ---------------------------------------------------------------------------

CREATE TABLE person (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name        text NOT NULL,
  normalized_name  text NOT NULL,        -- lowercase, unaccented (see entity resolution ADR)
  rfc              text UNIQUE           -- hard key when present; NEVER fuzzy-match if set
);
CREATE INDEX idx_person_name_trgm ON person USING gin (normalized_name gin_trgm_ops);

CREATE TABLE tenure (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id     uuid NOT NULL REFERENCES person(id),
  node_id       text NOT NULL REFERENCES node(id),
  role          text NOT NULL,           -- 'titular', 'diputado', 'regidor', ...
  party         text,                    -- party key at the time of taking office
  start_date    date NOT NULL,
  end_date      date,                    -- NULL = in office (R9)
  contact_email text,                    -- institutional only, never personal
  contact_phone text                     -- institutional only
);
CREATE INDEX idx_tenure_node ON tenure (node_id);
CREATE INDEX idx_tenure_person ON tenure (person_id);

-- ---------------------------------------------------------------------------
-- Companies & entity resolution (R3, R4: candidates only, humans merge)
-- ---------------------------------------------------------------------------

CREATE TABLE company (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  legal_name       text NOT NULL,
  normalized_name  text NOT NULL,        -- lowercase, unaccented, corporate suffixes stripped
  rfc              text UNIQUE
);
CREATE INDEX idx_company_name_trgm ON company USING gin (normalized_name gin_trgm_ops);

CREATE TABLE entity_match_candidate (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind         entity_kind NOT NULL,
  entity_a     uuid NOT NULL,            -- references person(id) or company(id) per kind
  entity_b     uuid NOT NULL,
  score        numeric(4,3) NOT NULL CHECK (score >= 0 AND score <= 1),
  method       match_method NOT NULL,
  status       review_status NOT NULL DEFAULT 'pending',
  reviewed_by  text,                     -- required when status leaves 'pending'
  reviewed_at  timestamptz,
  CHECK (entity_a <> entity_b),
  CHECK (status = 'pending' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

-- ---------------------------------------------------------------------------
-- Signal engine — Machiyotl (Fase 5). Signals, never conclusions (R2).
-- ---------------------------------------------------------------------------

CREATE TABLE signal (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_type  text NOT NULL,            -- 'adjudicacion_a_empresa_69b', 'puerta_giratoria', ...
  score        numeric(4,3) NOT NULL CHECK (score >= 0 AND score <= 1),
  legal_basis  text NOT NULL,            -- article/law giving context, required
  status       signal_status NOT NULL DEFAULT 'por_verificar',
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE signal_entity (
  signal_id  uuid NOT NULL REFERENCES signal(id),
  kind       entity_kind NOT NULL,
  entity_id  uuid NOT NULL,
  PRIMARY KEY (signal_id, kind, entity_id)
);

CREATE TABLE signal_evidence (
  signal_id    uuid NOT NULL REFERENCES signal(id),
  snapshot_id  uuid NOT NULL REFERENCES snapshot(id),
  PRIMARY KEY (signal_id, snapshot_id)
);

-- ---------------------------------------------------------------------------
-- Promises & evidence ladder (Fase 6). No percentages, ever (R5).
-- ---------------------------------------------------------------------------

CREATE TABLE promise (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  text           text NOT NULL,          -- verbatim from the registered platform
  actor_party    text,
  actor_person   uuid REFERENCES person(id),
  election_year  int NOT NULL
);

-- One row per rung reached; each rung demands a document with folio and date.
CREATE TABLE promise_evidence (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  promise_id   uuid NOT NULL REFERENCES promise(id),
  state        promise_state NOT NULL,
  folio        text NOT NULL,
  event_date   date NOT NULL,
  snapshot_id  uuid NOT NULL REFERENCES snapshot(id),
  UNIQUE (promise_id, state)
);

-- LLM-proposed promise <-> initiative links. Model proposes, human decides (R4).
CREATE TABLE promise_link (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  promise_id   uuid NOT NULL REFERENCES promise(id),
  target_kind  text NOT NULL,            -- 'iniciativa_sil', ...
  target_ref   text NOT NULL,            -- external identifier at the source
  score        numeric(4,3) NOT NULL CHECK (score >= 0 AND score <= 1),
  proposed_by  text NOT NULL,            -- model id that proposed it
  status       review_status NOT NULL DEFAULT 'pending',
  reviewed_by  text,
  reviewed_at  timestamptz,
  CHECK (status = 'pending' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

-- ---------------------------------------------------------------------------
-- Derived graph view (ADR: Postgres + recursive CTE, not a graph database).
-- The API reads this; the frontend never computes hierarchy on its own.
-- ---------------------------------------------------------------------------

CREATE VIEW v_hierarchy AS
WITH RECURSIVE tree AS (
  SELECT n.id, n.name, n.level, n.territory_key, NULL::text AS parent_id, 0 AS depth
  FROM node n
  WHERE NOT EXISTS (
    SELECT 1 FROM edge e
    WHERE e.to_node = n.id AND e.type = 'autoridad' AND e.valid_to IS NULL
  ) AND n.valid_to IS NULL
  UNION ALL
  SELECT n.id, n.name, n.level, n.territory_key, e.from_node, t.depth + 1
  FROM edge e
  JOIN tree t ON e.from_node = t.id
  JOIN node n ON n.id = e.to_node AND n.valid_to IS NULL
  WHERE e.type = 'autoridad' AND e.valid_to IS NULL
)
SELECT * FROM tree;

COMMIT;
