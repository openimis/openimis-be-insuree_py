import json
import uuid
from datetime import datetime

from django.db import migrations
from django.db.models import F, Q

SYSTEM_USERNAME = "insuree_legacy"
LABEL_CODE = "INSUREE"

# The insuree fields an individual carries in json_ext. Frozen here: a later
# change to the list is a new migration, not an edit of this one.
INSUREE_PROPERTIES = {
    **{
        name: {"type": "string"}
        for name in (
            "chf_id",
            "gender_code",
            "marital",
            "passport",
            "phone",
            "email",
            "current_address",
            "geolocation",
            "type_of_id_code",
            "status",
            "source",
            "source_version",
            "insuree_uuid",
        )
    },
    **{
        name: {"type": "integer"}
        for name in (
            "family_id",
            "current_village_id",
            "photo_id",
            "relationship_id",
            "profession_id",
            "education_id",
            "health_facility_id",
            "status_reason_id",
        )
    },
    **{name: {"type": "date"} for name in ("photo_date", "status_date")},
    **{
        name: {"type": "boolean"}
        for name in (
            "head",
            "card_issued",
            "offline",
            "vulnerability",
            "dob_unknown",
        )
    },
}


def _merged(properties, additions):
    conflicts = sorted(
        name
        for name, definition in additions.items()
        if name in properties
        and properties[name].get("type") != definition["type"]
    )
    if conflicts:
        raise ValueError(
            "The individual schema already declares %s with another type; "
            "align the type before migrating insurees." % ", ".join(conflicts)
        )
    return {
        **properties,
        **{
            name: additions[name]
            for name in additions
            if name not in properties
        },
    }


def _stored_individual_config(ModuleConfiguration):
    return ModuleConfiguration.objects.filter(
        Q(is_disabled_until=None) | Q(is_disabled_until__lt=datetime.now()),
        module="individual",
        layer="be",
    ).first()


def _system_schema(config):
    from individual.apps import DEFAULT_CONFIG

    stored = (
        json.loads(config.config).get("individual_schema") if config else None
    )
    return json.loads(stored or DEFAULT_CONFIG["individual_schema"])


def _save_system_schema(ModuleConfiguration, config, schema):
    if config is None:
        config = ModuleConfiguration(
            module="individual", layer="be", version="1", config="{}"
        )
    stored = json.loads(config.config)
    stored["individual_schema"] = json.dumps(schema)
    config.config = json.dumps(stored)
    config.save()


def _create_system_user(apps):
    TechnicalUser = apps.get_model("core", "TechnicalUser")
    User = apps.get_model("core", "User")
    if User.objects.filter(username=SYSTEM_USERNAME).exists():
        return
    technical_user = TechnicalUser.objects.create(
        id=uuid.uuid4(),
        username=SYSTEM_USERNAME,
        password="!",
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        id=uuid.uuid4(), username=SYSTEM_USERNAME, t_user=technical_user
    )


def forward(apps, schema_editor):
    _create_system_user(apps)
    IndividualLabel = apps.get_model("individual", "IndividualLabel")
    for label in IndividualLabel.objects.filter(code=LABEL_CODE):
        properties = (label.json_schema or {}).get("properties", {})
        IndividualLabel.objects.filter(pk=label.pk).update(
            json_schema={
                **(label.json_schema or {}),
                "properties": _merged(properties, INSUREE_PROPERTIES),
            },
            date_updated=datetime.now(),
            version=F("version") + 1,
        )
    ModuleConfiguration = apps.get_model("core", "ModuleConfiguration")
    config = _stored_individual_config(ModuleConfiguration)
    schema = _system_schema(config)
    schema["properties"] = _merged(
        schema.get("properties", {}), INSUREE_PROPERTIES
    )
    _save_system_schema(ModuleConfiguration, config, schema)


def reverse(apps, schema_editor):
    IndividualLabel = apps.get_model("individual", "IndividualLabel")
    for label in IndividualLabel.objects.filter(
        code=LABEL_CODE, json_schema__isnull=False
    ):
        properties = {
            name: definition
            for name, definition in label.json_schema.get(
                "properties", {}
            ).items()
            if INSUREE_PROPERTIES.get(name) != definition
        }
        IndividualLabel.objects.filter(pk=label.pk).update(
            json_schema=(
                {**label.json_schema, "properties": properties}
                if properties
                else None
            ),
            date_updated=datetime.now(),
            version=F("version") + 1,
        )
    ModuleConfiguration = apps.get_model("core", "ModuleConfiguration")
    config = _stored_individual_config(ModuleConfiguration)
    if config is None:
        return
    schema = _system_schema(config)
    # A property of the default schema predates this migration (email).
    default_properties = _system_schema(None).get("properties", {})
    schema["properties"] = {
        name: definition
        for name, definition in schema.get("properties", {}).items()
        if name in default_properties
        or INSUREE_PROPERTIES.get(name) != definition
    }
    _save_system_schema(ModuleConfiguration, config, schema)


class Migration(migrations.Migration):

    dependencies = [
        ("insuree", "0024_family_parent_family_family_polygamous_family"),
        ("individual", "0020_label_rights_and_seed"),
        # The historical User needs core's later columns (version,
        # is_superuser).
        ("core", "0038_rightpermission"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
