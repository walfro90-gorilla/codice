-- Methodological caveats travel WITH the metric, not in a footnote.
--
-- The PEF's territorial breakdown records spending against the entity where the
-- executing unit is domiciled, not where the money lands. Half of all entity-
-- assigned spending falls on Ciudad de México for that reason alone. Publishing
-- "CDMX: 531,699 pesos per inhabitant" as a ranking, without saying so, would be
-- exactly the misleading number CLAUDE.md forbids: "nunca el número solo".
--
-- Making this a table rather than prose in a README means the API and the UI
-- cannot serve the metric without also carrying its warning: any consumer that
-- reads the metric reads the caveat in the same query.

BEGIN;

CREATE TABLE metric_caveat (
  metric      text NOT NULL,          -- e.g. 'gasto_por_habitante'
  seq         int  NOT NULL,          -- display order
  caveat      text NOT NULL,
  PRIMARY KEY (metric, seq)
);

INSERT INTO metric_caveat (metric, seq, caveat) VALUES
  ('gasto_por_habitante', 1,
   'El PEF asigna el gasto a la entidad donde está domiciliada la unidad responsable, no donde se ejerce. Cerca de la mitad del gasto con entidad asignada se registra en la Ciudad de México por el domicilio de las oficinas centrales.'),
  ('gasto_por_habitante', 2,
   'La población de referencia es la del Censo 2020 del INEGI; el gasto es del ejercicio fiscal indicado. Comparar años distintos sin ajustar por inflación compara pesos nominales, no poder de compra.'),
  ('gasto_por_habitante', 3,
   'No incluye el gasto sin entidad asignada (erogaciones en el extranjero y gasto no distribuible geográficamente), que se publica por separado.'),
  ('presupuesto_por_nodo', 1,
   'La correspondencia entre ramo presupuestario y órgano es una atribución de Códice, no de la fuente. Varios ramos —deuda, participaciones, aportaciones— no corresponden a ningún órgano y quedan sin vincular.'),
  ('presupuesto_por_nodo', 2,
   'Es presupuesto aprobado, no gasto ejercido. La Cuenta Pública reporta lo efectivamente gastado y puede diferir.');

-- Replace the plain view with one that reports what is NOT included, so the
-- omission is visible in the same row as the figure.
DROP VIEW IF EXISTS v_spending_per_capita;
CREATE VIEW v_spending_per_capita AS
WITH unassigned AS (
  SELECT fiscal_year, sum(amount_mxn) AS amount_mxn
  FROM budget_allocation WHERE territory_key IS NULL GROUP BY fiscal_year
)
SELECT
  b.fiscal_year,
  b.territory_key,
  t.name AS territory_name,
  p.census_year,
  p.population,
  sum(b.amount_mxn) AS amount_mxn,
  round(sum(b.amount_mxn) / nullif(p.population, 0), 2) AS mxn_per_inhabitant,
  u.amount_mxn AS excluded_unassigned_mxn,
  'gasto_por_habitante'::text AS metric
FROM budget_allocation b
JOIN territory t ON t.inegi_key = b.territory_key
JOIN population p ON p.inegi_key = b.territory_key
LEFT JOIN unassigned u ON u.fiscal_year = b.fiscal_year
WHERE b.territory_key IS NOT NULL
GROUP BY b.fiscal_year, b.territory_key, t.name, p.census_year, p.population, u.amount_mxn;

COMMIT;
