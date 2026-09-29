from django.db import connection, transaction
from django.db.utils import DatabaseError
from django.test import TestCase

from core.models import User
from individual.models import Individual
from individual.services import IndividualService
from insuree.models import InsureeIndividual
from insuree.test_helpers import create_test_insuree
from location.models import Location

GUARD = "this individual is an insuree, change it through the insuree module"


class LinkedIndividualGuardTest(TestCase):
    def setUp(self):
        self.insuree = create_test_insuree()
        self.individual = Individual.objects.get(
            id=InsureeIndividual.objects.get(
                insuree_id=self.insuree.pk
            ).individual_id
        )

    def assert_refused(self, write):
        with self.assertRaisesMessage(DatabaseError, GUARD):
            with transaction.atomic():
                write()

    def test_an_orm_update_of_the_individual_is_refused(self):
        self.individual.first_name = "Changed"
        self.assert_refused(
            lambda: self.individual.save(
                user=User.objects.filter(username="Admin").first()
            )
        )

    def test_an_individual_service_update_is_refused(self):
        user = User.objects.filter(username="Admin").first()
        result = IndividualService(user).update(
            {"id": str(self.individual.id), "first_name": "Changed"}
        )
        self.assertFalse(result["success"])
        self.assertIn(GUARD, result["detail"])

    def test_a_raw_sql_update_is_refused(self):
        def write():
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE individual_individual SET "Json_ext" = %s'
                    ' WHERE "UUID" = %s',
                    ["{}", self.individual.id],
                )

        self.assert_refused(write)

    def test_a_delete_is_refused(self):
        def write():
            with connection.cursor() as cursor:
                cursor.execute(
                    'DELETE FROM individual_individual WHERE "UUID" = %s',
                    [self.individual.id],
                )

        self.assert_refused(write)

    def test_an_individual_that_is_not_an_insuree_is_not_guarded(self):
        user = User.objects.filter(username="Admin").first()
        other = Individual(first_name="A", last_name="B", dob="2000-01-01")
        other.save(user=user)
        other.first_name = "C"
        other.save(user=user)
        self.assertEqual(Individual.objects.get(id=other.id).first_name, "C")


class FamilyLocationTest(TestCase):
    def test_members_without_a_village_follow_their_family(self):
        insuree = create_test_insuree()
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('insuree.via_view', 'on', true)")
            cursor.execute(
                """UPDATE individual_individual
                SET "Json_ext" = "Json_ext" || '{"current_village_id": null}'
                WHERE "UUID" = (SELECT individual_id
                                FROM "insuree_InsureeIndividual"
                                WHERE "InsureeID" = %s)""",
                [insuree.pk],
            )
            cursor.execute(
                "SELECT set_config('insuree.via_view', 'off', true)"
            )
        family = insuree.family
        village = (
            Location.objects.filter(type="V", validity_to__isnull=True)
            .exclude(id=family.location_id)
            .first()
        )
        family.location = village
        family.save()
        link = InsureeIndividual.objects.get(insuree_id=insuree.pk)
        self.assertEqual(
            Individual.objects.get(id=link.individual_id).location_id,
            village.id,
        )

    def test_members_with_their_own_village_stay(self):
        insuree = create_test_insuree()
        own_village = insuree.current_village_id
        family = insuree.family
        family.location = (
            Location.objects.filter(type="V", validity_to__isnull=True)
            .exclude(id=family.location_id)
            .exclude(id=own_village)
            .first()
        )
        family.save()
        link = InsureeIndividual.objects.get(insuree_id=insuree.pk)
        self.assertEqual(
            Individual.objects.get(id=link.individual_id).location_id,
            own_village,
        )
