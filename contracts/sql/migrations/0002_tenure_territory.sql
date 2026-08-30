-- Tenures gain the INEGI key of the territory they represent (R7).
--
-- Legislators are elected FOR a place, and the sources name that place in prose
-- ("Coahuila", "Estado de México"). Without the canonical key a tenure cannot be
-- joined to population, geography or spending — the whole point of the project.
-- The display name stays in `role`; the key is what queries use.
--
-- NULL is meaningful: proportional-representation seats are elected in a single
-- national constituency, so they represent no entity (R6 — say what we don't know,
-- and do not invent a territory that does not exist).

BEGIN;

ALTER TABLE tenure ADD COLUMN territory_key text REFERENCES territory(inegi_key);
CREATE INDEX idx_tenure_territory ON tenure (territory_key);

COMMIT;
