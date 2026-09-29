-- Individual-side writes skip every insuree rule (number validation, policy
-- expiry on delete, versioning), so linked rows change only through the view.
CREATE FUNCTION insuree_guard_linked_individual() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('insuree.via_view', true) IS DISTINCT FROM 'on'
       AND EXISTS (SELECT 1 FROM "insuree_InsureeIndividual" WHERE individual_id = OLD."UUID") THEN
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
