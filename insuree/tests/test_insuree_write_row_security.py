"""Family and insuree writes stay in the user's districts (audit H02).

Reads were district-scoped; writes looked their target up by uuid alone and
placed families and insurees anywhere.
"""

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings

from core.test_helpers import create_right_only_user
from insuree.gql_mutations import (
    ChangeInsureeFamilyMutation,
    DeleteFamiliesMutation,
    DeleteInsureesMutation,
    SetFamilyHeadMutation,
)
from insuree.models import Family, Insuree
from insuree.services import InsureeService
from insuree.test_helpers import create_test_insuree
from location.models import Location
from location.test_helpers import create_basic_test_locations

WRITE_PERMS = [
    "gql_mutation_create_insurees_perms",
    "gql_mutation_update_insurees_perms",
    "gql_mutation_delete_insurees_perms",
    "gql_mutation_update_families_perms",
    "gql_mutation_delete_families_perms",
]


@override_settings(ROW_SECURITY=True)
class InsureeWriteRowSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_basic_test_locations()
        cls.villages = {}
        cls.heads = {}
        cls.members = {}
        for key, code in (("a", "R1D1M1V1"), ("b", "R2D1M1V1")):
            village = Location.objects.get(code=code, validity_to__isnull=True)
            head = create_test_insuree(
                with_family=True, is_head=True,
                custom_props={"current_village": village},
                family_custom_props={"location": village},
            )
            cls.members[key] = create_test_insuree(
                with_family=False,
                custom_props={"family": head.family, "current_village": village},
            )
            cls.villages[key] = village
            cls.heads[key] = head
        cls.user_a = create_right_only_user("h02usera", WRITE_PERMS, district_codes=["R1D1"])

    def setUp(self):
        cache.clear()

    def _family_valid(self, key):
        return Family.objects.filter(id=self.heads[key].family.id, validity_to__isnull=True).exists()

    def _insuree(self, key):
        return Insuree.objects.get(id=self.members[key].id)

    def test_delete_family_refuses_foreign_family(self):
        errors = DeleteFamiliesMutation.async_mutate(
            self.user_a, uuids=[self.heads["b"].family.uuid], delete_members=False
        )
        self.assertTrue(errors)
        self.assertTrue(self._family_valid("b"))

    def test_delete_insuree_refuses_foreign_insuree(self):
        errors = DeleteInsureesMutation.async_mutate(self.user_a, uuids=[self.members["b"].uuid])
        self.assertTrue(errors)
        self.assertIsNone(self._insuree("b").validity_to)

    def test_delete_own_insuree(self):
        errors = DeleteInsureesMutation.async_mutate(self.user_a, uuids=[self.members["a"].uuid])
        self.assertFalse(errors)
        self.assertIsNotNone(self._insuree("a").validity_to)

    def test_set_head_refuses_foreign_family(self):
        errors = SetFamilyHeadMutation.async_mutate(
            self.user_a, uuid=self.heads["b"].family.uuid, insuree_uuid=self.members["b"].uuid
        )
        self.assertTrue(errors)
        self.assertEqual(Family.objects.get(id=self.heads["b"].family.id).head_insuree_id, self.heads["b"].id)

    def test_change_family_refuses_foreign_family(self):
        errors = ChangeInsureeFamilyMutation.async_mutate(
            self.user_a, family_uuid=self.heads["b"].family.uuid,
            insuree_uuid=self.members["a"].uuid, cancel_policies=False,
        )
        self.assertTrue(errors)
        self.assertEqual(self._insuree("a").family_id, self.heads["a"].family.id)

    def test_update_refuses_foreign_insuree(self):
        with self.assertRaises(Insuree.DoesNotExist):
            InsureeService(self.user_a).create_or_update(
                {"uuid": self.members["b"].uuid, "last_name": "H02"}
            )
        self.assertNotEqual(self._insuree("b").last_name, "H02")

    def test_create_refuses_foreign_village(self):
        with self.assertRaises(PermissionDenied):
            InsureeService(self.user_a).create_or_update(
                {"chf_id": "H02NEW01", "last_name": "H02", "other_names": "New",
                 "current_village_id": self.villages["b"].id},
                create_only=True,
            )
