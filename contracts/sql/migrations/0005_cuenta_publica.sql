-- Cuenta Pública: what was actually spent, next to what was approved.
--
-- The PEF is a plan; the Cuenta Pública is the outcome. Keeping them in the
-- same table with an explicit stage lets a reader compare them without us
-- computing a judgement: we publish both figures and the difference is theirs
-- to read (R2 — we never score anyone's execution).
--
-- Stages, as the source publishes them:
--   aprobado   what the Chamber approved (this is what the PEF carries)
--   modificado the budget after in-year adjustments
--   devengado  obligations incurred
--   pagado     cash actually disbursed
--   ejercido   the headline "spent" figure

BEGIN;

CREATE TYPE budget_stage AS ENUM
  ('aprobado', 'modificado', 'devengado', 'pagado', 'ejercido');

ALTER TABLE budget_allocation
  ADD COLUMN stage budget_stage NOT NULL DEFAULT 'aprobado';

-- The old uniqueness rule did not know about stages.
ALTER TABLE budget_allocation
  DROP CONSTRAINT budget_allocation_fiscal_year_ramo_id_territory_key_scope_key;
ALTER TABLE budget_allocation
  ADD CONSTRAINT budget_allocation_unique
  UNIQUE (fiscal_year, ramo_id, territory_key, scope, stage);

CREATE INDEX idx_budget_stage ON budget_allocation (stage);

-- Approved vs spent, per organ and year. No ratio, no score, no colour: two
-- numbers and their difference, which is a fact, not a verdict.
CREATE VIEW v_budget_execution AS
SELECT
  b.fiscal_year,
  r.node_id,
  n.name AS node_name,
  sum(b.amount_mxn) FILTER (WHERE b.stage = 'aprobado')  AS aprobado_mxn,
  sum(b.amount_mxn) FILTER (WHERE b.stage = 'modificado') AS modificado_mxn,
  sum(b.amount_mxn) FILTER (WHERE b.stage = 'ejercido')  AS ejercido_mxn,
  sum(b.amount_mxn) FILTER (WHERE b.stage = 'ejercido')
    - sum(b.amount_mxn) FILTER (WHERE b.stage = 'aprobado') AS diferencia_mxn
FROM budget_allocation b
JOIN ramo r ON r.id = b.ramo_id
JOIN node n ON n.id = r.node_id
GROUP BY b.fiscal_year, r.node_id, n.name;

INSERT INTO metric_caveat (metric, seq, caveat) VALUES
  ('ejecucion_presupuestal', 1,
   'Aprobado y ejercido no son comparables sin contexto: el presupuesto puede modificarse legalmente durante el año por ampliaciones, reducciones y transferencias autorizadas. La columna modificado es la referencia intermedia.'),
  ('ejecucion_presupuestal', 2,
   'Gastar menos de lo aprobado no significa por sí mismo subejercicio ni ahorro, y gastar más no significa irregularidad. Códice publica las cifras y su fuente; la interpretación corresponde a quien consulta.'),
  ('ejecucion_presupuestal', 3,
   'La Cuenta Pública se publica al cierre del ejercicio, así que el año en curso no tiene cifra ejercida.');

COMMIT;
