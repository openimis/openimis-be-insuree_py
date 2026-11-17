-- Foreign keys from other tables to individuals, but for the link table.
SELECT conrelid::regclass::text, a.attname
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
WHERE c.confrelid = 'individual_individual'::regclass AND c.contype = 'f'
  AND c.conrelid <> '"insuree_InsureeIndividual"'::regclass
ORDER BY 1
