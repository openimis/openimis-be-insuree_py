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

-- json_ext is shared with every individual, and a filter on a view column is
-- applied while scanning all of them, before the join to the link table: a key
-- the view reads as a number, boolean or date may hold anything for individuals
-- that are not insurees. These read such a value as NULL instead of failing.
-- They are IMMUTABLE because they only cast unambiguous forms (0028 indexes some).
CREATE FUNCTION insuree_int(value text) RETURNS integer LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN value ~ '^-?[0-9]{1,9}$' THEN value::integer END
$$;

CREATE FUNCTION insuree_smallint(value text) RETURNS smallint LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN value ~ '^-?[0-9]{1,4}$' THEN value::smallint END
$$;

CREATE FUNCTION insuree_bool(value text) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN value IN ('true', 'false') THEN value::boolean END
$$;

-- Days 29-31 can be impossible for the month; only those take the slow path.
CREATE FUNCTION insuree_checked_date(value text) RETURNS date LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN value::date;
EXCEPTION WHEN others THEN
    RETURN NULL;
END $$;

CREATE FUNCTION insuree_date(value text) RETURNS date LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN value ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-8])$' THEN value::date
        WHEN value ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(29|30|31)$' THEN insuree_checked_date(value)
    END
$$;

-- Only with an explicit offset, as to_jsonb() writes a timestamptz: the result
-- then does not depend on the session time zone.
CREATE FUNCTION insuree_checked_timestamptz(value text) RETURNS timestamptz LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN value::timestamptz;
EXCEPTION WHEN others THEN
    RETURN NULL;
END $$;

CREATE FUNCTION insuree_timestamptz(value text) RETURNS timestamptz LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN value ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-8])[T ]([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?([+-][0-9]{2}(:?[0-9]{2})?|Z)$'
            THEN value::timestamptz
        WHEN value ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(29|30|31)[T ]([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?([+-][0-9]{2}(:?[0-9]{2})?|Z)$'
            THEN insuree_checked_timestamptz(value)
    END
$$;

-- Same columns, order and types as the table it replaces: the PL/pgSQL reports
-- and the uvw* views read it by position (SELECT *) as well as by name.
CREATE VIEW "tblInsuree" AS
SELECT
    l."InsureeID",
    -- Who last changed the insuree through this view: individual-side saves (a group
    -- join, a benefit plan sync) change the individual, not the insuree.
    COALESCE((SELECT u.i_user_id FROM "core_User" u WHERE u.id = CASE
        WHEN i."Json_ext" ->> 'updated_by' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            THEN (i."Json_ext" ->> 'updated_by')::uuid
        ELSE i."UserUpdatedUUID" END), -1)::integer AS "AuditUserID",
    (i."Json_ext" ->> 'chf_id')::varchar(50) AS "CHFID",
    insuree_bool(i."Json_ext" ->> 'card_issued') AS "CardIssued",
    (i."Json_ext" ->> 'current_address')::varchar(200) AS "CurrentAddress",
    insuree_int(i."Json_ext" ->> 'current_village_id') AS "CurrentVillage",
    CASE WHEN COALESCE(insuree_bool(i."Json_ext" ->> 'dob_unknown'), false) THEN NULL::date ELSE i.dob END AS "DOB",
    insuree_smallint(i."Json_ext" ->> 'education_id') AS "Education",
    (i."Json_ext" ->> 'email')::varchar(100) AS "Email",
    insuree_int(i."Json_ext" ->> 'family_id') AS "FamilyID",
    (i."Json_ext" ->> 'gender_code')::varchar(1) AS "Gender",
    (i."Json_ext" ->> 'geolocation')::varchar(250) AS "GeoLocation",
    insuree_int(i."Json_ext" ->> 'health_facility_id') AS "HFID",
    COALESCE(i."Json_ext" ->> 'insuree_uuid', i."UUID"::text)::varchar(36) AS "InsureeUUID",
    COALESCE(insuree_bool(i."Json_ext" ->> 'head'), false) AS "IsHead",
    i.last_name::varchar(100) AS "LastName",
    NULL::integer AS "LegacyID",
    (i."Json_ext" ->> 'marital')::varchar(1) AS "Marital",
    i.first_name::varchar(100) AS "OtherNames",
    (i."Json_ext" ->> 'phone')::varchar(50) AS "Phone",
    insuree_date(i."Json_ext" ->> 'photo_date') AS "PhotoDate",
    insuree_int(i."Json_ext" ->> 'photo_id') AS "PhotoID",
    insuree_smallint(i."Json_ext" ->> 'profession_id') AS "Profession",
    insuree_smallint(i."Json_ext" ->> 'relationship_id') AS "Relationship",
    NULL::bytea AS "RowID",
    (i."Json_ext" ->> 'type_of_id_code')::varchar(1) AS "TypeOfId",
    COALESCE(insuree_timestamptz(i."Json_ext" ->> 'validity_from'), i."DateUpdated", i."DateCreated") AS "ValidityFrom",
    CASE WHEN i."isDeleted" THEN COALESCE(
        insuree_timestamptz(i."Json_ext" ->> 'validity_to'), insuree_timestamptz(i."Json_ext" ->> 'validity_from'),
        i."DateUpdated", i."DateCreated") END AS "ValidityTo",
    insuree_bool(i."Json_ext" ->> 'vulnerability') AS "Vulnerability",
    insuree_bool(i."Json_ext" ->> 'offline') AS "isOffline",
    (i."Json_ext" ->> 'passport')::varchar(25) AS "passport",
    (i."Json_ext" ->> 'source')::varchar(50) AS "Source",
    (i."Json_ext" ->> 'source_version')::varchar(15) AS "SourceVersion",
    NULLIF(i."Json_ext" -> 'legacy_json_ext', 'null'::jsonb) AS "JsonExt",
    (i."Json_ext" ->> 'status')::varchar(2) AS "status",
    insuree_date(i."Json_ext" ->> 'status_date') AS "status_date",
    insuree_smallint(i."Json_ext" ->> 'status_reason_id') AS "StatusReason"
FROM "insuree_InsureeIndividual" l
JOIN individual_individual i ON i."UUID" = l.individual_id;
