-- The json_ext keys that belong to the insuree: the ones the view reads.
CREATE FUNCTION insuree_owned_json(j jsonb) RETURNS jsonb LANGUAGE sql IMMUTABLE AS $$
    SELECT COALESCE(jsonb_object_agg(e.key, e.value), '{}'::jsonb)
    FROM jsonb_each(j) e
    WHERE e.key = 'insuree_uuid'
       OR e.key IN (SELECT jsonb_object_keys(insuree_fields_json('{}'::jsonb)))
$$;

-- Individual-side writes skip every insuree rule (number validation, policy
-- expiry on delete, versioning), so what the insuree owns changes only through
-- the view. The rest of the row (location, other labels, other json_ext keys)
-- stays the individual module's: groups and benefit plans write it.
CREATE FUNCTION insuree_guard_linked_individual() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('insuree.via_view', true) IS DISTINCT FROM 'on'
       AND EXISTS (SELECT 1 FROM "insuree_InsureeIndividual" WHERE individual_id = OLD."UUID")
       AND (TG_OP = 'DELETE'
            OR NEW."UUID" IS DISTINCT FROM OLD."UUID"
            OR NEW.first_name IS DISTINCT FROM OLD.first_name
            OR NEW.last_name IS DISTINCT FROM OLD.last_name
            OR NEW.dob IS DISTINCT FROM OLD.dob
            OR NEW."isDeleted" IS DISTINCT FROM OLD."isDeleted"
            OR NOT 'INSUREE' = ANY (NEW.labels)
            OR insuree_owned_json(NEW."Json_ext") IS DISTINCT FROM insuree_owned_json(OLD."Json_ext")) THEN
        RAISE EXCEPTION USING ERRCODE = 'IS003',
            MESSAGE = 'insuree_view: this individual is an insuree, change it through the insuree module';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER insuree_guard_linked_individual BEFORE UPDATE OR DELETE ON individual_individual
    FOR EACH ROW EXECUTE FUNCTION insuree_guard_linked_individual();

-- Individual row security reads location_id; an insuree without a village of its
-- own follows its family, which moves without touching its members.
CREATE FUNCTION insuree_family_location_moved() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW."LocationId" IS DISTINCT FROM OLD."LocationId" THEN
        PERFORM set_config('insuree.via_view', 'on', true);
        UPDATE individual_individual i SET location_id = NEW."LocationId"
        FROM "insuree_InsureeIndividual" l
        WHERE l.individual_id = i."UUID"
          AND (i."Json_ext" ->> 'family_id')::integer = NEW."FamilyID"
          AND i."Json_ext" ->> 'current_village_id' IS NULL;
        PERFORM set_config('insuree.via_view', 'off', true);
    END IF;
    RETURN NULL;
END $$;

CREATE TRIGGER insuree_family_location_moved AFTER UPDATE OF "LocationId" ON "tblFamilies"
    FOR EACH ROW EXECUTE FUNCTION insuree_family_location_moved();
