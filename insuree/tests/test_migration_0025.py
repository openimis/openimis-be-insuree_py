import importlib
import json

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase

from core.models import ModuleConfiguration, User
from individual.models import IndividualLabel
from individual.tests.test_helpers import reload_individual_config

migration = importlib.import_module(
    "insuree.migrations.0025_insuree_schema_and_system_user"
)


def stored_schema():
    config = ModuleConfiguration.objects.filter(
        module="individual", layer="be"
    ).first()
    return json.loads(json.loads(config.config)["individual_schema"])


class InsureeSchemaMigrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        executor = MigrationExecutor(connection)
        cls.state_apps = executor.loader.project_state(
            ("insuree", "0025_insuree_schema_and_system_user")
        ).apps

    def setUp(self):
        self.admin = User.objects.filter(username="Admin").first()
        self.label = IndividualLabel.objects.filter(code="INSUREE").first()
        if self.label is None:
            self.label = IndividualLabel(code="INSUREE", name="Insuree")
            self.label.save(user=self.admin)
        IndividualLabel.objects.filter(pk=self.label.pk).update(
            json_schema=None
        )
        config = ModuleConfiguration.objects.filter(
            module="individual", layer="be"
        ).first()
        self.addCleanup(
            reload_individual_config, config.config if config else "{}"
        )
        ModuleConfiguration.objects.filter(
            module="individual", layer="be"
        ).delete()

    def run_forward(self):
        migration.forward(self.state_apps, None)

    def test_label_gets_the_insuree_properties(self):
        self.run_forward()
        self.label.refresh_from_db()
        self.assertEqual(
            self.label.json_schema["properties"], migration.INSUREE_PROPERTIES
        )

    def test_system_schema_gains_the_properties_and_keeps_its_own(self):
        self.run_forward()
        properties = stored_schema()["properties"]
        for name, definition in migration.INSUREE_PROPERTIES.items():
            self.assertEqual(properties[name], definition)
        self.assertEqual(properties["national_id"], {"type": "string"})

    def test_label_schema_is_a_subset_of_the_system_schema(self):
        self.run_forward()
        self.label.refresh_from_db()
        system = stored_schema()["properties"]
        for name, definition in self.label.json_schema["properties"].items():
            self.assertEqual(system[name]["type"], definition["type"], name)

    def test_same_name_with_another_type_is_refused(self):
        ModuleConfiguration.objects.create(
            module="individual",
            layer="be",
            version="1",
            config=json.dumps(
                {
                    "individual_schema": json.dumps(
                        {"properties": {"chf_id": {"type": "integer"}}}
                    )
                }
            ),
        )
        with self.assertRaisesMessage(ValueError, "chf_id"):
            self.run_forward()

    def test_system_user_is_created_once(self):
        self.run_forward()
        self.run_forward()
        users = User.objects.filter(username=migration.SYSTEM_USERNAME)
        self.assertEqual(users.count(), 1)
        self.assertIsNotNone(users.first().t_user_id)
        self.assertFalse(users.first().t_user.has_usable_password())

    def test_reverse_restores_label_and_system_schema(self):
        self.run_forward()
        migration.reverse(self.state_apps, None)
        self.label.refresh_from_db()
        self.assertIsNone(self.label.json_schema)
        properties = stored_schema()["properties"]
        self.assertNotIn("chf_id", properties)
        self.assertIn("national_id", properties)
        self.assertEqual(properties["email"], {"type": "string"})
