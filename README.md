# openIMIS Backend Insuree reference module
This repository holds the files of the openIMIS Backend Insuree reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Code climate (develop branch)

[![Maintainability](https://img.shields.io/codeclimate/maintainability/openimis/openimis-be-insuree_py.svg)](https://codeclimate.com/github/openimis/openimis-be-insuree_py/maintainability)
[![Test Coverage](https://img.shields.io/codeclimate/coverage/openimis/openimis-be-insuree_py.svg)](https://codeclimate.com/github/openimis/openimis-be-insuree_py)

## Content
Current version provides the following ORM mapping:
* tblGender > Gender
* tblInsuree > Insuree (missing fks to tblFamilies, tblPhotos, tblRelations, tblProfessions, tblEducations, tblIdentificationTypes)

## Dependencies

This module depends on the following modules and entities:
* location.HealthFacility
