-- Inbound foreign keys: a view cannot be referenced. 0028 points them at the link table.
DO $$
DECLARE r record;
BEGIN
    FOR r IN SELECT conrelid::regclass AS tbl, conname FROM pg_constraint
             WHERE confrelid = '"tblInsuree"'::regclass AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tbl, r.conname);
    END LOOP;
END $$;

ALTER TABLE "tblInsuree" RENAME TO "tblInsuree_history";
-- Old versions are found from their head; the move reads it for every row.
CREATE INDEX "tblInsuree_history_LegacyID" ON "tblInsuree_history" ("LegacyID");

CREATE TABLE "insuree_InsureeIndividual" (
    "InsureeID" integer PRIMARY KEY DEFAULT nextval('"tblInsuree_InsureeID_seq"'),
    individual_id uuid NOT NULL UNIQUE REFERENCES individual_individual ("UUID")
);
ALTER SEQUENCE "tblInsuree_InsureeID_seq" OWNED BY "insuree_InsureeIndividual"."InsureeID";

-- Same columns, order and types as the table it replaces: the PL/pgSQL reports
-- and the uvw* views read it by position (SELECT *) as well as by name.
CREATE VIEW "tblInsuree" AS
SELECT
    l."InsureeID",
    COALESCE((SELECT u.i_user_id FROM "core_User" u WHERE u.id = i."UserUpdatedUUID"), -1)::integer
        AS "AuditUserID",
    (i."Json_ext" ->> 'chf_id')::varchar(50) AS "CHFID",
    (i."Json_ext" ->> 'card_issued')::boolean AS "CardIssued",
    (i."Json_ext" ->> 'current_address')::varchar(200) AS "CurrentAddress",
    (i."Json_ext" ->> 'current_village_id')::integer AS "CurrentVillage",
    CASE WHEN COALESCE((i."Json_ext" ->> 'dob_unknown')::boolean, false) THEN NULL::date ELSE i.dob END AS "DOB",
    (i."Json_ext" ->> 'education_id')::smallint AS "Education",
    (i."Json_ext" ->> 'email')::varchar(100) AS "Email",
    (i."Json_ext" ->> 'family_id')::integer AS "FamilyID",
    (i."Json_ext" ->> 'gender_code')::varchar(1) AS "Gender",
    (i."Json_ext" ->> 'geolocation')::varchar(250) AS "GeoLocation",
    (i."Json_ext" ->> 'health_facility_id')::integer AS "HFID",
    COALESCE(i."Json_ext" ->> 'insuree_uuid', i."UUID"::text)::varchar(36) AS "InsureeUUID",
    COALESCE((i."Json_ext" ->> 'head')::boolean, false) AS "IsHead",
    i.last_name::varchar(100) AS "LastName",
    NULL::integer AS "LegacyID",
    (i."Json_ext" ->> 'marital')::varchar(1) AS "Marital",
    i.first_name::varchar(100) AS "OtherNames",
    (i."Json_ext" ->> 'phone')::varchar(50) AS "Phone",
    (i."Json_ext" ->> 'photo_date')::date AS "PhotoDate",
    (i."Json_ext" ->> 'photo_id')::integer AS "PhotoID",
    (i."Json_ext" ->> 'profession_id')::smallint AS "Profession",
    (i."Json_ext" ->> 'relationship_id')::smallint AS "Relationship",
    NULL::bytea AS "RowID",
    (i."Json_ext" ->> 'type_of_id_code')::varchar(1) AS "TypeOfId",
    COALESCE(i."DateUpdated", i."DateCreated") AS "ValidityFrom",
    CASE WHEN i."isDeleted" THEN COALESCE(
        (i."Json_ext" ->> 'validity_to')::timestamptz, i."DateUpdated", i."DateCreated") END AS "ValidityTo",
    (i."Json_ext" ->> 'vulnerability')::boolean AS "Vulnerability",
    (i."Json_ext" ->> 'offline')::boolean AS "isOffline",
    (i."Json_ext" ->> 'passport')::varchar(25) AS "passport",
    (i."Json_ext" ->> 'source')::varchar(50) AS "Source",
    (i."Json_ext" ->> 'source_version')::varchar(15) AS "SourceVersion",
    NULLIF(i."Json_ext" -> 'legacy_json_ext', 'null'::jsonb) AS "JsonExt",
    (i."Json_ext" ->> 'status')::varchar(2) AS "status",
    (i."Json_ext" ->> 'status_date')::date AS "status_date",
    (i."Json_ext" ->> 'status_reason_id')::smallint AS "StatusReason"
FROM "insuree_InsureeIndividual" l
JOIN individual_individual i ON i."UUID" = l.individual_id;
