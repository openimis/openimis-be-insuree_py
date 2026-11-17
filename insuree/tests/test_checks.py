from types import SimpleNamespace
from unittest import mock

from django.db import connections
from django.test import SimpleTestCase

from insuree import checks
from insuree.models import Insuree


def model(label, **fields):
    return SimpleNamespace(
        _meta=SimpleNamespace(
            label=label,
            get_fields=lambda: [
                SimpleNamespace(
                    name=name,
                    concrete=True,
                    is_relation=True,
                    related_model=Insuree,
                    db_constraint=constraint,
                )
                for name, constraint in fields.items()
            ],
        )
    )


class InsureeSystemChecksTest(SimpleTestCase):
    def test_the_installed_assembly_passes(self):
        self.assertEqual(checks.check_individual_installed(), [])
        self.assertEqual(checks.check_postgresql(), [])
        self.assertEqual(checks.check_references_to_insuree(), [])

    def test_a_missing_individual_module_is_an_error(self):
        with mock.patch.object(
            checks.apps, "is_installed", return_value=False
        ):
            self.assertEqual(
                [e.id for e in checks.check_individual_installed()],
                ["insuree.E001"],
            )

    def test_another_database_is_an_error(self):
        with mock.patch.object(connections["default"], "vendor", "microsoft"):
            self.assertEqual(
                [e.id for e in checks.check_postgresql()], ["insuree.E002"]
            )

    def test_a_new_constrained_reference_is_an_error(self):
        models = [
            model("claim.Claim", insuree=True),
            model("grievance.Ticket", insuree=True, reporter=False),
        ]
        with mock.patch.object(checks.apps, "get_models", return_value=models):
            errors = checks.check_references_to_insuree()
        self.assertEqual([e.id for e in errors], ["insuree.E003"])
        self.assertIn("grievance.Ticket.insuree", errors[0].msg)
