-- NOT VALID: enforced for every new row at once; `insuree_individual_check --finalize`
-- validates the existing rows later without blocking reads.
ALTER TABLE "tblClaim" ADD CONSTRAINT "tblClaim_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblClaimDedRem" ADD CONSTRAINT "tblClaimDedRem_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblFamilies" ADD CONSTRAINT "tblFamilies_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblHealthStatus" ADD CONSTRAINT "tblHealthStatus_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblInsureePolicy" ADD CONSTRAINT "tblInsureePolicy_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblPolicyRenewalDetails" ADD CONSTRAINT "tblPolicyRenewalDetails_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblPolicyRenewals" ADD CONSTRAINT "tblPolicyRenewals_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "insuree_InsureeMutation" ADD CONSTRAINT "insuree_InsureeMutation_insuree_id_fk_insuree_individual" FOREIGN KEY ("insuree_id") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblPolicyHolderInsuree" ADD CONSTRAINT "tblPolicyHolderInsuree_InsureeId_fk_insuree_individual" FOREIGN KEY ("InsureeId") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;
ALTER TABLE "tblContractDetails" ADD CONSTRAINT "tblContractDetails_InsureeID_fk_insuree_individual" FOREIGN KEY ("InsureeID") REFERENCES "insuree_InsureeIndividual" ("InsureeID") DEFERRABLE INITIALLY DEFERRED NOT VALID;

-- Every chain head now lives in the individual table; only copies stay here.
ALTER TABLE "tblInsuree_history" ADD CONSTRAINT "tblInsuree_history_copies_only" CHECK ("LegacyID" IS NOT NULL) NOT VALID;

-- The exact expressions the view exposes: an index on a different cast is not used.
CREATE INDEX insuree_chf_id ON individual_individual ((("Json_ext" ->> 'chf_id')::varchar(50)));
CREATE INDEX insuree_family_id ON individual_individual ((("Json_ext" ->> 'family_id')::integer));
CREATE INDEX insuree_current_village_id ON individual_individual ((("Json_ext" ->> 'current_village_id')::integer));
CREATE INDEX insuree_health_facility_id ON individual_individual ((("Json_ext" ->> 'health_facility_id')::integer));
CREATE INDEX insuree_uuid ON individual_individual ((COALESCE("Json_ext" ->> 'insuree_uuid', "UUID"::text)::varchar(36)));
