-- The insuree columns as the individual's json_ext keys. Takes a row of the view
-- or of the history table (same column names) through to_jsonb().
CREATE FUNCTION insuree_fields_json(r jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE AS $$
    SELECT jsonb_build_object(
        'chf_id', r -> 'CHFID', 'card_issued', r -> 'CardIssued', 'current_address', r -> 'CurrentAddress',
        'current_village_id', r -> 'CurrentVillage', 'education_id', r -> 'Education', 'email', r -> 'Email',
        'family_id', r -> 'FamilyID', 'gender_code', r -> 'Gender', 'geolocation', r -> 'GeoLocation',
        'health_facility_id', r -> 'HFID', 'head', r -> 'IsHead', 'marital', r -> 'Marital',
        'phone', r -> 'Phone', 'photo_date', r -> 'PhotoDate', 'photo_id', r -> 'PhotoID',
        'profession_id', r -> 'Profession', 'relationship_id', r -> 'Relationship',
        'type_of_id_code', r -> 'TypeOfId', 'vulnerability', r -> 'Vulnerability', 'offline', r -> 'isOffline',
        'passport', r -> 'passport', 'source', r -> 'Source', 'source_version', r -> 'SourceVersion',
        'legacy_json_ext', r -> 'JsonExt', 'status', r -> 'status', 'status_date', r -> 'status_date',
        'status_reason_id', r -> 'StatusReason',
        'dob_unknown', COALESCE(r -> 'DOB', 'null'::jsonb) = 'null'::jsonb,
        -- The view derives validity_to from the update date; keep it only when they differ.
        'validity_to', CASE WHEN r -> 'ValidityTo' IS DISTINCT FROM r -> 'ValidityFrom'
                            AND r -> 'ValidityTo' <> 'null'::jsonb THEN r -> 'ValidityTo' END)
$$;

CREATE FUNCTION insuree_write_history(p_uuid uuid, p_type char, p_user uuid, p_reason text)
RETURNS void LANGUAGE sql AS $$
    INSERT INTO individual_historicalindividual (
        "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, first_name, last_name,
        dob, history_date, history_change_reason, history_type, history_user_id,
        "UserCreatedUUID", "UserUpdatedUUID", location_id, labels)
    SELECT i."UUID", i."isDeleted", i."Json_ext", i."DateCreated", i."DateUpdated", i.version,
           i.first_name, i.last_name, i.dob, now(), p_reason, p_type, p_user,
           i."UserCreatedUUID", i."UserUpdatedUUID", i.location_id, i.labels
    FROM individual_individual i WHERE i."UUID" = p_uuid;
$$;

-- Django saves an existing row with an UPDATE and falls back to an INSERT when
-- the UPDATE reports no row, so every UPDATE returns NEW. The view shows only
-- linked rows (old versions stay in tblInsuree_history), so UPDATE and DELETE
-- always find an individual.
CREATE FUNCTION insuree_view_write() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_individual uuid;
    v_previous text;
    v_user uuid;
    v_reason text;
    v_json jsonb;
    v_uuid uuid;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING ERRCODE = 'IS001',
            MESSAGE = 'insuree_view: a current insuree is not deleted, set validity_to instead';
    END IF;

    -- The copy VersionedModel.save_history() makes of the row it is about to change.
    IF TG_OP = 'INSERT' AND NEW."LegacyID" IS NOT NULL THEN
        NEW."InsureeID" := COALESCE(NEW."InsureeID", nextval('"tblInsuree_InsureeID_seq"'));
        INSERT INTO "tblInsuree_history" SELECT (NEW).*;
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        SELECT individual_id INTO v_individual FROM "insuree_InsureeIndividual" WHERE "InsureeID" = OLD."InsureeID";
    END IF;

    SELECT id INTO v_user FROM "core_User" WHERE i_user_id = NEW."AuditUserID" ORDER BY username LIMIT 1;
    IF v_user IS NULL THEN
        SELECT id INTO v_user FROM "core_User" WHERE username = 'insuree_legacy';
        v_reason := 'tblInsuree AuditUserID=' || COALESCE(NEW."AuditUserID"::text, 'NULL');
        IF v_user IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = 'IS004',
                MESSAGE = 'insuree_view: the insuree_legacy user is missing, run the insuree migrations';
        END IF;
    END IF;

    NEW."ValidityFrom" := COALESCE(NEW."ValidityFrom", now());
    v_json := insuree_fields_json(to_jsonb(NEW));

    v_previous := current_setting('insuree.via_view', true);
    PERFORM set_config('insuree.via_view', 'on', true);
    IF TG_OP = 'INSERT' THEN
        NEW."InsureeUUID" := COALESCE(NEW."InsureeUUID", gen_random_uuid()::text);
        v_uuid := lower(NEW."InsureeUUID")::uuid;
        IF NEW."InsureeUUID" <> v_uuid::text THEN
            v_json := v_json || jsonb_build_object('insuree_uuid', NEW."InsureeUUID");
        END IF;
        NEW."InsureeID" := COALESCE(NEW."InsureeID", nextval('"tblInsuree_InsureeID_seq"'));
        INSERT INTO individual_individual (
            "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, first_name, last_name,
            dob, "UserCreatedUUID", "UserUpdatedUUID", location_id, labels)
        VALUES (
            v_uuid, NEW."ValidityTo" IS NOT NULL, v_json, NEW."ValidityFrom", NEW."ValidityFrom", 1,
            NEW."OtherNames", NEW."LastName", COALESCE(NEW."DOB", DATE '1970-01-01'), v_user, v_user,
            COALESCE(NEW."CurrentVillage", (SELECT "LocationId" FROM "tblFamilies" WHERE "FamilyID" = NEW."FamilyID")),
            ARRAY['INSUREE']::varchar(64)[]);
        INSERT INTO "insuree_InsureeIndividual" ("InsureeID", individual_id) VALUES (NEW."InsureeID", v_uuid);
        PERFORM insuree_write_history(v_uuid, '+', v_user, v_reason);
    ELSE
        -- The individual keeps its id; the view shows the insuree's new uuid.
        IF NEW."InsureeUUID" IS DISTINCT FROM OLD."InsureeUUID" AND NEW."InsureeUUID" IS NOT NULL THEN
            v_json := v_json || jsonb_build_object('insuree_uuid', NEW."InsureeUUID");
        END IF;
        UPDATE individual_individual SET
            first_name = NEW."OtherNames", last_name = NEW."LastName",
            dob = COALESCE(NEW."DOB", DATE '1970-01-01'), "Json_ext" = "Json_ext" || v_json,
            location_id = COALESCE(NEW."CurrentVillage", (SELECT "LocationId" FROM "tblFamilies" WHERE "FamilyID" = NEW."FamilyID")),
            "isDeleted" = NEW."ValidityTo" IS NOT NULL, "DateUpdated" = NEW."ValidityFrom",
            "UserUpdatedUUID" = v_user, version = version + 1
        WHERE "UUID" = v_individual;
        PERFORM insuree_write_history(v_individual, '~', v_user, v_reason);
    END IF;
    PERFORM set_config('insuree.via_view', COALESCE(v_previous, ''), true);
    RETURN NEW;
END $$;

CREATE TRIGGER insuree_view_write INSTEAD OF INSERT OR UPDATE OR DELETE ON "tblInsuree"
    FOR EACH ROW EXECUTE FUNCTION insuree_view_write();

-- The references the table's own foreign keys enforced, checked at commit like
-- those keys were (DEFERRABLE INITIALLY DEFERRED).
CREATE FUNCTION insuree_check_references() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    j jsonb := NEW."Json_ext";
    missing text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM "insuree_InsureeIndividual" WHERE individual_id = NEW."UUID") THEN
        RETURN NULL;
    END IF;
    SELECT string_agg(name || '=' || value, ', ') INTO missing FROM (VALUES
        ('family_id', j ->> 'family_id', EXISTS (SELECT 1 FROM "tblFamilies" WHERE "FamilyID" = (j ->> 'family_id')::integer)),
        ('current_village_id', j ->> 'current_village_id', EXISTS (SELECT 1 FROM "tblLocations" WHERE "LocationId" = (j ->> 'current_village_id')::integer)),
        ('health_facility_id', j ->> 'health_facility_id', EXISTS (SELECT 1 FROM "tblHF" WHERE "HfID" = (j ->> 'health_facility_id')::integer)),
        ('photo_id', j ->> 'photo_id', EXISTS (SELECT 1 FROM "tblPhotos" WHERE "PhotoID" = (j ->> 'photo_id')::integer)),
        ('gender_code', j ->> 'gender_code', EXISTS (SELECT 1 FROM "tblGender" WHERE "Code" = j ->> 'gender_code')),
        ('education_id', j ->> 'education_id', EXISTS (SELECT 1 FROM "tblEducations" WHERE "EducationId" = (j ->> 'education_id')::smallint)),
        ('profession_id', j ->> 'profession_id', EXISTS (SELECT 1 FROM "tblProfessions" WHERE "ProfessionId" = (j ->> 'profession_id')::smallint)),
        ('relationship_id', j ->> 'relationship_id', EXISTS (SELECT 1 FROM "tblRelations" WHERE "RelationId" = (j ->> 'relationship_id')::smallint)),
        ('status_reason_id', j ->> 'status_reason_id', EXISTS (SELECT 1 FROM "tblInsureeStatusReason" WHERE "StatusReasonId" = (j ->> 'status_reason_id')::smallint))
    ) AS reference(name, value, present)
    WHERE value IS NOT NULL AND NOT present;
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION USING ERRCODE = 'IS002',
            MESSAGE = format('insuree_view: insuree %s references rows that do not exist: %s', NEW."UUID", missing);
    END IF;
    RETURN NULL;
END $$;

-- Only insurees carry the label; other individuals, bulk uploads included,
-- queue no check.
CREATE CONSTRAINT TRIGGER insuree_references AFTER INSERT OR UPDATE ON individual_individual
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN ('INSUREE' = ANY (NEW.labels))
    EXECUTE FUNCTION insuree_check_references();
