-- One batch of linked insurees back into the history table; ids in %(ids)s.
INSERT INTO "tblInsuree_history"
SELECT * FROM "tblInsuree" WHERE "InsureeID" = ANY(%(ids)s);

SELECT set_config('insuree.via_view', 'on', true);

WITH links AS (
    DELETE FROM "insuree_InsureeIndividual"
    WHERE "InsureeID" = ANY(%(ids)s)
    RETURNING individual_id
), history AS (
    DELETE FROM individual_historicalindividual
    WHERE "UUID" IN (SELECT individual_id FROM links)
)
DELETE FROM individual_individual
WHERE "UUID" IN (SELECT individual_id FROM links);

SELECT set_config('insuree.via_view', 'off', true);
