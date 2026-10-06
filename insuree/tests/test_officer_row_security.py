"""An enrolment officer sees the families and insurees of their own villages.

An officer is granted villages, not districts. The family and insuree rules used
to compare at district level only, so an officer matched nothing at all.
"""

from django.core.cache import cache
from django.test import TestCase, override_settings

from core.test_helpers import create_enrolment_officer_role, create_role_user, create_test_officer
from insuree.models import Family, Insuree
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_test_village


@override_settings(ROW_SECURITY=True)
class OfficerRowSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.own_village = create_test_village(custom_props={"code": "OFRSV1"})
        cls.other_village = create_test_village(custom_props={"code": "OFRSV2"})
        cls.own = create_test_insuree(
            with_family=True, is_head=True,
            custom_props={"current_village": cls.own_village},
            family_custom_props={"location": cls.own_village},
        )
        cls.other = create_test_insuree(
            with_family=True, is_head=True,
            custom_props={"current_village": cls.other_village},
            family_custom_props={"location": cls.other_village},
        )
        officer = create_test_officer(
            villages=[cls.own_village], custom_props={"code": "ofrseo", "has_login": True}
        )
        cls.user = create_role_user("ofrseo", create_enrolment_officer_role(), officer=officer)

    def setUp(self):
        cache.clear()

    def test_officer_sees_own_village_families(self):
        ids = set(Family.get_queryset(Family.objects.all(), self.user).values_list("id", flat=True))
        self.assertIn(self.own.family.id, ids)
        self.assertNotIn(self.other.family.id, ids)

    def test_officer_sees_own_village_insurees(self):
        ids = set(Insuree.get_queryset(Insuree.objects.all(), self.user).values_list("id", flat=True))
        self.assertIn(self.own.id, ids)
        self.assertNotIn(self.other.id, ids)
