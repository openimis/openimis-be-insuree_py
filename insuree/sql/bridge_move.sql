-- One batch of chain heads into individuals and links; ids in %(ids)s.
WITH batch AS (
    SELECT h.*, u.id AS user_id,
           lower(COALESCE(h."InsureeUUID", gen_random_uuid()::text))::uuid AS individual_uuid
    FROM "tblInsuree_history" h
    LEFT JOIN LATERAL (
        SELECT id FROM "core_User" WHERE i_user_id = h."AuditUserID" ORDER BY username LIMIT 1
    ) u ON true
    WHERE h."InsureeID" = ANY(%(ids)s)
), individuals AS (
    INSERT INTO individual_individual (
        "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, first_name, last_name,
        dob, "UserCreatedUUID", "UserUpdatedUUID", location_id, labels)
    SELECT b.individual_uuid, b."ValidityTo" IS NOT NULL,
           insuree_fields_json(to_jsonb(b))
               || CASE WHEN b."InsureeUUID" <> b.individual_uuid::text
                       THEN jsonb_build_object('insuree_uuid', b."InsureeUUID") ELSE '{}'::jsonb END,
           (SELECT min(c."ValidityFrom") FROM "tblInsuree_history" c
            WHERE c."LegacyID" = b."InsureeID" OR c."InsureeID" = b."InsureeID"),
           b."ValidityFrom", 1, b."OtherNames", b."LastName", COALESCE(b."DOB", DATE '1970-01-01'),
           COALESCE(b.user_id, (SELECT id FROM "core_User" WHERE username = 'insuree_legacy')), COALESCE(b.user_id, (SELECT id FROM "core_User" WHERE username = 'insuree_legacy')),
           COALESCE(b."CurrentVillage", (SELECT "LocationId" FROM "tblFamilies" WHERE "FamilyID" = b."FamilyID")),
           ARRAY['INSUREE']::varchar(64)[]
    FROM batch b
)
INSERT INTO "insuree_InsureeIndividual" ("InsureeID", individual_id)
SELECT b."InsureeID", b.individual_uuid FROM batch b
