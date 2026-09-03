"""
UBA coverage for the insuree module: the ENROLMENT credential, held on a village.

`Family.location` is a village, so the row filter has to walk the path the module passes
('location__parent__parent', aimed at the district) back down to the village the
credential is held on. That walk is driven by the registry `params` location registers,
which is what these tests exercise end to end.
"""
from django.core.cache import cache
from django.test import TestCase

from core.apps import ENROLMENT_UBA_LINK_TYPE
from core.services.userServices import create_or_update_user_districts
from core.test_helpers import (
    create_test_interactive_user,
    create_test_role,
    create_test_user_business_access,
)
from insuree.apps import InsureeConfig
from insuree.models import Family, Insuree, InsureePolicy
from insuree.test_helpers import create_test_insuree
from location.models import Location
from location.test_helpers import create_test_village


class EnrolmentUbaRowSecurityTest(TestCase):
    """
    An enrolment officer sees the families and insurees of the villages they hold an
    ENROLMENT link on, and nothing else inside their districts.
    """

    @classmethod
    def setUpTestData(cls):
        # two villages under the same district, so the district filter cannot be what
        # tells the two apart
        cls.linked_village = create_test_village({"name": "UbaEnrolLinked"})
        cls.district = cls.linked_village.parent.parent
        cls.other_village = Location.objects.create(
            name="UbaEnrolOther", code="UBAEO2", type="V",
            parent=cls.linked_village.parent, audit_user_id=-1, validity_from="2019-01-01")

        cls.role = create_test_role(
            name="UBA enrolment", uba_rights=[int(InsureeConfig.gql_query_insurees_perms[0])])
        cls.officer_user = create_test_interactive_user(
            username="ubaenrolofficer", roles=[cls.role.id])
        cls.plain_user = create_test_interactive_user(
            username="ubaenrolplain", roles=[cls.role.id])
        for user in (cls.officer_user, cls.plain_user):
            create_or_update_user_districts(user.i_user, [cls.district.id], -1)

        create_test_user_business_access(
            user=cls.officer_user,
            business_object=cls.linked_village,
            link_type=ENROLMENT_UBA_LINK_TYPE,
        )

        cls.linked_insuree = create_test_insuree(
            custom_props={"chf_id": "UBAEI001", "current_village": cls.linked_village},
            family_custom_props={"location": cls.linked_village})
        cls.other_insuree = create_test_insuree(
            custom_props={"chf_id": "UBAEI002", "current_village": cls.other_village},
            family_custom_props={"location": cls.other_village})

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _families_for(self, user):
        return set(
            Family.get_queryset(
                Family.objects.filter(id__in=[self.linked_insuree.family_id,
                                             self.other_insuree.family_id]), user
            ).values_list("location__name", flat=True)
        )

    def _insurees_for(self, user):
        return set(
            Insuree.get_queryset(
                Insuree.objects.filter(chf_id__startswith="UBAEI"), user
            ).values_list("chf_id", flat=True)
        )

    def test_families_are_narrowed_to_the_linked_village(self):
        self.assertEqual({"UbaEnrolLinked"}, self._families_for(self.officer_user))

    def test_a_user_without_a_link_keeps_the_district_scope(self):
        self.assertEqual(
            {"UbaEnrolLinked", "UbaEnrolOther"}, self._families_for(self.plain_user))

    def test_insurees_are_narrowed_to_the_linked_village(self):
        self.assertEqual({"UBAEI001"}, self._insurees_for(self.officer_user))

    def test_insurees_are_not_narrowed_without_a_link(self):
        self.assertEqual({"UBAEI001", "UBAEI002"}, self._insurees_for(self.plain_user))

    def test_a_second_link_widens_to_both_villages(self):
        create_test_user_business_access(
            user=self.officer_user,
            business_object=self.other_village,
            link_type=ENROLMENT_UBA_LINK_TYPE,
        )
        self.assertEqual({"UBAEI001", "UBAEI002"}, self._insurees_for(self.officer_user))

    def test_a_link_outside_the_assigned_districts_grants_nothing(self):
        far_village = create_test_village({"name": "UbaEnrolFar"})
        create_test_insuree(
            custom_props={"chf_id": "UBAEI003", "current_village": far_village},
            family_custom_props={"location": far_village})
        user = create_test_interactive_user(username="ubaenrolfar", roles=[self.role.id])
        create_or_update_user_districts(user.i_user, [self.district.id], -1)
        create_test_user_business_access(
            user=user, business_object=far_village, link_type=ENROLMENT_UBA_LINK_TYPE)
        # the district filter and the credential are AND'ed, and they do not overlap
        self.assertEqual(set(), self._insurees_for(user))

    def test_a_claim_admin_credential_says_nothing_about_a_village(self):
        # CLAIM_ADMIN is declared on the health facility, so on a path that never reaches
        # one it must not narrow anything - and must not empty the queryset either
        from core.apps import CLAIM_ADMIN_UBA_LINK_TYPE
        from location.test_helpers import create_test_health_facility

        hf = create_test_health_facility(
            "UBAEH1", self.district.id, custom_props={"code": "UBAEH1"})
        user = create_test_interactive_user(username="ubaenrolhfonly", roles=[self.role.id])
        create_or_update_user_districts(user.i_user, [self.district.id], -1)
        create_test_user_business_access(
            user=user, business_object=hf, link_type=CLAIM_ADMIN_UBA_LINK_TYPE)
        self.assertEqual({"UBAEI001", "UBAEI002"}, self._insurees_for(user))

    def test_insuree_policies_are_narrowed_the_same_way(self):
        visible = InsureePolicy.get_queryset(
            InsureePolicy.objects.filter(insuree__chf_id__startswith="UBAEI"),
            self.officer_user)
        self.assertNotIn(
            self.other_insuree.id, set(visible.values_list("insuree_id", flat=True)))
