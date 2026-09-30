DROP TRIGGER IF EXISTS insuree_family_location_moved ON "tblFamilies";
DROP TRIGGER IF EXISTS insuree_guard_linked_individual ON individual_individual;
DROP TRIGGER IF EXISTS insuree_references ON individual_individual;
DROP VIEW "tblInsuree";
DROP FUNCTION insuree_int(text);
DROP FUNCTION IF EXISTS insuree_family_location_moved();
DROP FUNCTION IF EXISTS insuree_guard_linked_individual();
DROP FUNCTION IF EXISTS insuree_owned_json(jsonb);
DROP FUNCTION IF EXISTS insuree_check_references();
DROP FUNCTION IF EXISTS insuree_view_write();
DROP FUNCTION IF EXISTS insuree_write_history(uuid, char, uuid, text);
DROP FUNCTION IF EXISTS insuree_fields_json(jsonb);

ALTER SEQUENCE "tblInsuree_InsureeID_seq" OWNED BY NONE;
DROP TABLE "insuree_InsureeIndividual";
DROP INDEX "tblInsuree_history_LegacyID";
ALTER TABLE "tblInsuree_history" RENAME TO "tblInsuree";
ALTER SEQUENCE "tblInsuree_InsureeID_seq" OWNED BY "tblInsuree"."InsureeID";

-- NOT VALID: adding them validated would scan every referencing table under lock.
ALTER TABLE "tblClaim" ADD CONSTRAINT "tblClaim_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblClaimDedRem" ADD CONSTRAINT "tblClaimDedRem_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblFamilies" ADD CONSTRAINT "tblFamilies_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblHealthStatus" ADD CONSTRAINT "tblHealthStatus_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblInsureePolicy" ADD CONSTRAINT "tblInsureePolicy_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblPolicyRenewalDetails" ADD CONSTRAINT "tblPolicyRenewalDetails_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblPolicyRenewals" ADD CONSTRAINT "tblPolicyRenewals_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "insuree_InsureeMutation" ADD CONSTRAINT "insuree_InsureeMutation_insuree_id_fk_tblInsuree" FOREIGN KEY (insuree_id) REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblPolicyHolderInsuree" ADD CONSTRAINT "tblPolicyHolderInsuree_InsureeId_fk_tblInsuree" FOREIGN KEY ("InsureeId") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblContractDetails" ADD CONSTRAINT "tblContractDetails_InsureeID_fk_tblInsuree" FOREIGN KEY ("InsureeID") REFERENCES "tblInsuree" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
