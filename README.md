# openIMIS Backend Insuree reference module
This repository holds the files of the openIMIS Backend Insuree reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Code climate (develop branch)

[![Maintainability](https://img.shields.io/codeclimate/maintainability/openimis/openimis-be-insuree_py.svg)](https://codeclimate.com/github/openimis/openimis-be-insuree_py/maintainability)
[![Test Coverage](https://img.shields.io/codeclimate/coverage/openimis/openimis-be-insuree_py.svg)](https://codeclimate.com/github/openimis/openimis-be-insuree_py)

## Insurees are individuals

Since migration `0026` an insuree is stored as an `individual.Individual`
labelled `INSUREE`. The insuree-only fields (insurance number, gender,
family, village, health facility, photo, status, ...) are keys of the
individual's `json_ext`, declared by the `INSUREE` label schema, which
migration `0025` also adds to the system-wide individual schema.

`tblInsuree` keeps its name, columns, order and types, but it is a view:

* current and soft-deleted insurees come from `individual_individual`,
  joined to `insuree_InsureeIndividual`, which keeps the integer
  `InsureeID` every other table references;
* old versions (the copies `save_history()` makes) live in
  `tblInsuree_history` and are **not** visible through the view or the ORM;
* `INSTEAD OF` triggers turn inserts and updates on the view into writes on
  the individual, its history table (`individual_historicalindividual`) and
  the link, so `Insuree.objects.create()`, `save()`, `save_history()` and
  `delete_history()` behave as before. Deleting a current insuree row is
  refused: set `validity_to`;
* the ten foreign keys that referenced `tblInsuree` now reference
  `insuree_InsureeIndividual`;
* the individual module may not change what an insuree owns (names, birth
  date, deletion, the `INSUREE` label, the insuree `json_ext` keys) other
  than through the view; groups and benefit plans still write the rest.

An insuree without a birth date is stored with `1970-01-01` and
`json_ext.dob_unknown = true`; the view still returns `DOB` empty. The
user behind an `AuditUserID` becomes the individual's author; an
`AuditUserID` without a user is attributed to the technical user
`insuree_legacy`, with the original id in the history row's change reason.

### Requirements

* PostgreSQL. Migrations `0001`-`0024` still run on SQL Server; `0026`
  refuses it (system check `insuree.E002`).
* The `individual` module, at a version with migration
  `0020_label_rights_and_seed` (system check `insuree.E001`).
* A new model referencing `Insuree` must declare `db_constraint=False`:
  a view cannot be the target of a foreign key (system check
  `insuree.E003`).

### Upgrading an existing database

Migration `0027` moves every insuree into the individual table in batches
of 5000, each committed on its own, and resumes where it stopped if it is
interrupted. Plan for about three times the size of `tblInsuree` in free
disk space plus the write-ahead log of the move, and for the application
being unavailable during it.

1. Back up the database.
2. Run `python manage.py insuree_individual_check` and resolve every
   `BLOCKER` line (invalid or already used uuids, references to old
   versions). `info` lines are for reading.
3. Stop the application: migrating while insurees are edited can duplicate
   rows.
4. `python manage.py migrate`. The steps wait at most 5 seconds for a lock;
   if one times out behind a long report, run `migrate` again.
5. `python manage.py insuree_individual_check --finalize` validates the
   constraints `0028` adds without blocking reads and vacuums the moved
   tables. It must report no `BLOCKER` line.
6. Start the application. Rebuild the OpenSearch `individual` index if it
   is used: insurees are indexed with their id and labels only.

The views built on `tblInsuree` (`uvw*` reports) are dropped and created
again around the change. They are recreated by the migrating database user:
grants given on them to other roles must be given again.

### Rolling back

`python manage.py migrate insuree 0024` moves the insurees back into
`tblInsuree` and restores its foreign keys (as `NOT VALID`; validate them
with `ALTER TABLE ... VALIDATE CONSTRAINT` when convenient). It is refused
while other records point at an insuree's individual (group memberships,
beneficiaries, benefit consumptions, uploads); the check command lists
them. Labels other than `INSUREE` and `json_ext` keys outside the insuree
fields that were added after migrating are lost.

## ORM mapping:
* tblGender > Gender (including alt_language)
* tblPhotos > InsureePhoto
* tblFamilyTypes > FamilyType
* tblFamilies > Family
* tblInsuree (a view, see above) > Insuree
* tblInsuree_history (old insuree versions, no model)
* insuree_InsureeIndividual > InsureeIndividual
* tblInsureePolicy > InsureePolicy
* tblConfirmationTypes > ConfirmationType
* tblProfessions > Profession
* tblEducations > Education
* tblIdentificationTypes > IdentificationType
* tblRelations > Relation
* insuree_InsureeMutation > InsureeMutation
* insuree_FamilyMutation > FamilyMutation
* tblPolicyRenewalDetails > PolicyRenewalDetail

## Listened Django Signals
None

## Services
* create_insuree_renewal_detail: the renewal details are
  insuree-specific data to be renewed. Generally the picture.

## Reports (template can be overloaded via report.ReportDefinition)
None

## GraphQL Queries
* insuree_genders
* insurees
* identification_types
* educations
* professions
* family_types
* confirmation_types
* relations
* families
* family_members
* insuree_officers

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
* create_family
* update_family
* delete_families
* create_insuree
* update_insuree
* delete_insurees
* remove_insurees
* set_family_head
* change_insuree_family

## Configuration options (can be changed via core.ModuleConfiguration)
Rights required:
* gql_query_insurees_perms": (default: `["101101"]`)
* gql_query_insuree_perms": (default: `["101101"]`)
* gql_query_insuree_officers_perms": (default: `[]`),
* gql_insuree_family_members": (default: `["101101"]`),
* gql_query_families_perms": (default: `["101001"]`),
* gql_mutation_create_families_perms": (default: `["101002"]`),
* gql_mutation_update_families_perms": (default: `["101003"]`),
* gql_mutation_delete_families_perms": (default: `["101004"]`),
* gql_mutation_create_insurees_perms": (default: `["101102"]`),
* gql_mutation_update_insurees_perms": (default: `["101103"]`),
* gql_mutation_delete_insurees_perms": (default: `["101104"]`),
* insuree_photos_root_path": None,
* excluded_insuree_chfids": fake insurees (and bound families) used, for
  example, in 'funding' (default: `['999999999']`)
* renewal_photo_age_adult": age (in months) of a picture due for renewal
  for adults (default: `60`)
* renewal_photo_age_child": age (in months) of a picture due for renewal
  for children (default: `12`)
* use_contextual_enrolment_officer_selection": Enables automatic assignment of 
  the current user as the enrolment officer when uploading an insuree photo. If 'True', 
  the officer is inferred from session; if 'False', manual selection remains available. (default: 'False)
* [DEPRECATED] no_location_check (default: False) - since 25.10 - uses the same configuration in be-location module

## openIMIS Modules Dependencies
* location.models.HealthFacility
