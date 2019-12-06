# openIMIS Backend Insuree reference module
This repository holds the files of the openIMIS Backend Insuree reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Code climate (develop branch)

[![Maintainability](https://img.shields.io/codeclimate/maintainability/openimis/openimis-be-insuree_py.svg)](https://codeclimate.com/github/openimis/openimis-be-insuree_py/maintainability)
[![Test Coverage](https://img.shields.io/codeclimate/coverage/openimis/openimis-be-insuree_py.svg)](https://codeclimate.com/github/openimis/openimis-be-insuree_py)

## ORM mapping:
* tblGender > Gender (including alt_language)
* tblPhotos > Photo
* tblFamilyTypes > FamilyType
* tblFamilies > Family
* tblInsuree > Insuree (partially mapped)
* tblInsureePolicy > InsureePolicy

## Listened Django Signals
None

## Services
None

## Reports (template can be overloaded via report.ReportDefinition)
None

## GraphQL Queries
* insurees
* insuree

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
None

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_query_insurees_perms: required rights to call insurees (default: ["101101"])
* gql_query_insuree_perms: required rights to call insuree (default: ["101101"])
* gql_insuree_family_members: required rights to call insuree_family_members (default: ["101101"])

## openIMIS Modules Dependencies
* location.models.HealthFacility
