-- The '+' history row of each individual the batch created.
INSERT INTO individual_historicalindividual (
    "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version, first_name, last_name,
    dob, history_date, history_change_reason, history_type, history_user_id,
    "UserCreatedUUID", "UserUpdatedUUID", location_id, labels)
SELECT i."UUID", i."isDeleted", i."Json_ext", i."DateCreated", i."DateUpdated", i.version,
       i.first_name, i.last_name, i.dob, now(),
       'moved from tblInsuree' || CASE WHEN NOT EXISTS (
           SELECT 1 FROM "core_User" WHERE i_user_id = h."AuditUserID")
           THEN ', AuditUserID=' || h."AuditUserID" ELSE '' END,
       '+', i."UserCreatedUUID", i."UserCreatedUUID", i."UserUpdatedUUID", i.location_id, i.labels
FROM "tblInsuree_history" h
JOIN "insuree_InsureeIndividual" l ON l."InsureeID" = h."InsureeID"
JOIN individual_individual i ON i."UUID" = l.individual_id
WHERE h."InsureeID" = ANY(%(ids)s)
