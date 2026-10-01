"""
UBA coverage for the insuree module: the ENROLMENT credential, held on a village.

`Family.location` is a village, so the row filter has to walk the path the module passes
('location__parent__parent', aimed at the district) back down to the village the
credential is held on. That walk is driven by the registry `params` location registers,
which is what these tests exercise end to end.
"""
from django.core.cache import cache
from django.test import TestCase
from django.utils.translation import gettext as _

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


class EnrolmentUbaRightsTest(TestCase):
    """
    The rights side: an enrolment officer holding the insuree rights in the UBA bag only
    may search (the rows being narrowed as above) and write on the villages they hold an
    ENROLMENT link on - and nowhere else, a right in the UBA bag without a link being
    granted nowhere.
    """

    UBA_RIGHTS = [101001, 101002, 101003, 101004, 101101, 101102, 101103, 101104]

    @classmethod
    def setUpTestData(cls):
        cls.linked_village = create_test_village({"name": "UbaRightsLinked"})
        cls.district = cls.linked_village.parent.parent
        cls.other_village = Location.objects.create(
            name="UbaRightsOther", code="UBARO2", type="V",
            parent=cls.linked_village.parent, audit_user_id=-1, validity_from="2019-01-01")

        cls.role = create_test_role(name="UBA enrolment rights", uba_rights=cls.UBA_RIGHTS)
        cls.officer_user = create_test_interactive_user(
            username="ubarightsofficer", roles=[cls.role.id])
        cls.unlinked_user = create_test_interactive_user(
            username="ubarightsunlinked", roles=[cls.role.id])
        cls.global_role = create_test_role(name="Global enrolment rights", rights=cls.UBA_RIGHTS)
        cls.global_user = create_test_interactive_user(
            username="ubarightsglobal", roles=[cls.global_role.id])
        for user in (cls.officer_user, cls.unlinked_user, cls.global_user):
            create_or_update_user_districts(user.i_user, [cls.district.id], -1)
        create_test_user_business_access(
            user=cls.officer_user, business_object=cls.linked_village,
            link_type=ENROLMENT_UBA_LINK_TYPE)

        cls.linked_insuree = create_test_insuree(
            custom_props={"chf_id": "UBARI001", "current_village": cls.linked_village},
            family_custom_props={"location": cls.linked_village})
        cls.other_insuree = create_test_insuree(
            custom_props={"chf_id": "UBARI002", "current_village": cls.other_village},
            family_custom_props={"location": cls.other_village})

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_the_search_is_open_to_a_linked_officer(self):
        from insuree.uba import can_query

        self.assertTrue(can_query(self.officer_user, InsureeConfig.gql_query_families_perms))
        self.assertTrue(can_query(self.officer_user, InsureeConfig.gql_query_insurees_perms))

    def test_the_search_is_closed_without_a_link(self):
        from insuree.uba import can_query

        self.assertFalse(can_query(self.unlinked_user, InsureeConfig.gql_query_families_perms))

    def test_a_write_is_granted_on_the_linked_village_only(self):
        from insuree.uba import has_enrolment_perms

        perms = InsureeConfig.gql_mutation_create_families_perms
        self.assertTrue(has_enrolment_perms(self.officer_user, perms, [self.linked_village]))
        self.assertFalse(has_enrolment_perms(self.officer_user, perms, [self.other_village]))
        self.assertFalse(has_enrolment_perms(self.unlinked_user, perms, [self.linked_village]))

    def test_a_write_touching_two_villages_needs_both(self):
        from insuree.uba import has_enrolment_perms

        self.assertFalse(has_enrolment_perms(
            self.officer_user, InsureeConfig.gql_mutation_update_families_perms,
            [self.linked_village, self.other_village]))

    def test_a_write_on_an_unknown_village_needs_the_global_bag(self):
        from insuree.uba import has_enrolment_perms

        perms = InsureeConfig.gql_mutation_create_insurees_perms
        self.assertFalse(has_enrolment_perms(self.officer_user, perms, [None]))
        self.assertTrue(has_enrolment_perms(self.global_user, perms, [None]))

    def test_the_global_bag_writes_anywhere(self):
        from insuree.uba import has_enrolment_perms

        self.assertTrue(has_enrolment_perms(
            self.global_user, InsureeConfig.gql_mutation_update_insurees_perms,
            [self.other_village]))

    def test_an_insuree_is_located_by_its_family(self):
        from insuree.uba import insuree_village

        self.assertEqual(self.linked_village, insuree_village(self.linked_insuree))

    def test_creating_a_family_on_another_village_is_refused(self):
        from insuree.gql_mutations import CreateFamilyMutation

        errors = CreateFamilyMutation.async_mutate(
            self.officer_user, location_id=self.other_village.id, head_insuree={})
        self.assertTrue(errors)
        self.assertEqual(_("unauthorized"), errors[0]["detail"])

    def test_deleting_families_is_checked_family_by_family(self):
        from insuree.gql_mutations import DeleteFamiliesMutation

        errors = DeleteFamiliesMutation.async_mutate(
            self.officer_user,
            uuids=[self.linked_insuree.family.uuid, self.other_insuree.family.uuid],
            delete_members=False)
        self.assertEqual([{"message": _("unauthorized")}], errors)
        self.assertFalse(Family.objects.filter(
            id=self.linked_insuree.family_id, validity_to__isnull=True).exists())
        self.assertTrue(Family.objects.filter(
            id=self.other_insuree.family_id, validity_to__isnull=True).exists())

    def test_a_batch_write_is_refused_without_a_link(self):
        from django.core.exceptions import PermissionDenied
        from insuree.gql_mutations import DeleteInsureesMutation

        with self.assertRaises(PermissionDenied):
            DeleteInsureesMutation.async_mutate(
                self.unlinked_user, uuids=[self.linked_insuree.uuid])
