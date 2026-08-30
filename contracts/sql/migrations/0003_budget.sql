-- Fase 3: money. Federal budget (PEF) by administrative branch and territory.
--
-- Volume decision: the raw PEF is ~130k rows PER YEAR at line-item detail.
-- Postgres stores the aggregate that answers the project's question — how much
-- per branch, per entity, per year — while the line-item detail belongs in
-- static Parquet for analytical queries (ADR-012). Keeping 130k rows/year of
-- accounting detail in the canonical database buys nothing and breaks the
-- free tier by Fase 3, exactly as CLAUDE.md §11 warns.

BEGIN;

-- Administrative classification of the federal budget. The "ramo" is the unit
-- the PEF itself is organized by, so it is the natural bridge between money and
-- structure. Which node a ramo corresponds to is OUR assertion, not the source's,
-- so it is curated, nullable, and reviewable.
CREATE TABLE ramo (
  id          int PRIMARY KEY,          -- ID_RAMO as published in the PEF
  name        text NOT NULL,
  node_id     text REFERENCES node(id), -- NULL = no single organ owns this ramo
  note        text,                     -- why it maps there, or why it cannot
  valid_from  date NOT NULL DEFAULT '1900-01-01',
  valid_to    date
);

-- One row per (year, ramo, territory). Territory NULL is meaningful: the PEF
-- publishes "En el Extranjero" (33) and "No Distribuible Geográficamente" (34),
-- which are not entities and have no INEGI key (same rule as ADR-019).
CREATE TABLE budget_allocation (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fiscal_year   int NOT NULL,
  ramo_id       int NOT NULL REFERENCES ramo(id),
  territory_key text REFERENCES territory(inegi_key),
  -- Non-INEGI buckets the source publishes, kept verbatim rather than dropped (R6)
  scope         text NOT NULL DEFAULT 'entidad'
                CHECK (scope IN ('entidad', 'extranjero', 'no_distribuible')),
  amount_mxn    numeric(20,2) NOT NULL,
  snapshot_id   uuid NOT NULL REFERENCES snapshot(id),
  UNIQUE (fiscal_year, ramo_id, territory_key, scope)
);
CREATE INDEX idx_budget_year ON budget_allocation (fiscal_year);
CREATE INDEX idx_budget_territory ON budget_allocation (territory_key);
CREATE INDEX idx_budget_ramo ON budget_allocation (ramo_id);

-- Spending per inhabitant, never the raw number alone (CLAUDE.md Fase 3).
-- The view forces year, source and reference population to travel with the
-- metric: a peso figure without them is not citable.
CREATE VIEW v_spending_per_capita AS
SELECT
  b.fiscal_year,
  b.territory_key,
  t.name AS territory_name,
  p.census_year,
  p.population,
  sum(b.amount_mxn) AS amount_mxn,
  round(sum(b.amount_mxn) / nullif(p.population, 0), 2) AS mxn_per_inhabitant
FROM budget_allocation b
JOIN territory t ON t.inegi_key = b.territory_key
JOIN population p ON p.inegi_key = b.territory_key
WHERE b.territory_key IS NOT NULL
GROUP BY b.fiscal_year, b.territory_key, t.name, p.census_year, p.population;

COMMIT;
