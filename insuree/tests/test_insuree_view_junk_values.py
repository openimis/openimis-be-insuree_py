from django.db import connection
from django.test import TestCase

from core.models import User
from individual.models import Individual
from insuree.test_helpers import create_test_insuree

# (json_ext key, a value an individual that is not an insuree may hold,
#  a filter on the view column read from that key)
JUNK = [
    ("head", "x", '"IsHead"'),
    ("card_issued", "yes", '"CardIssued"'),
    ("offline", 1, '"isOffline"'),
    ("vulnerability", "high", '"Vulnerability"'),
    ("dob_unknown", "maybe", '"DOB" IS NULL'),
    ("photo_id", "abc", '"PhotoID" = 5'),
    ("family_id", "F-1", '"FamilyID" = 5'),
    ("current_village_id", 12.5, '"CurrentVillage" = 5'),
    ("health_facility_id", "HF-7", '"HFID" = 5'),
    ("education_id", 99999, '"Education" = 1'),
    ("profession_id", "clerk", '"Profession" = 1'),
    ("relationship_id", "-", '"Relationship" = 1'),
    ("status_reason_id", "none", '"StatusReason" = 1'),
    ("photo_date", "2021-02-30", "\"PhotoDate\" = DATE '2021-02-28'"),
    ("status_date", "yesterday", "\"status_date\" = DATE '2021-02-28'"),
    ("validity_to", "soon", '"ValidityTo" IS NOT NULL'),
]


class InsureeViewJunkValuesTest(TestCase):
    """Other individuals share json_ext keys with insurees; what they hold
    there must not break a query on the view."""

    def test_filtering_the_view_ignores_other_individuals_values(self):
        insuree = create_test_insuree()
        user = User.objects.filter(username="Admin").first()
        other = Individual(
            first_name="Not",
            last_name="Insuree",
            dob="2000-01-01",
            json_ext={key: value for key, value, _ in JUNK},
        )
        other.save(user=user)
        with connection.cursor() as cursor:
            for key, _, condition in JUNK:
                with self.subTest(key=key):
                    cursor.execute(
                        'SELECT count(*) FROM "tblInsuree" WHERE ' + condition
                    )
                    cursor.fetchone()
            cursor.execute(
                'SELECT count(*) FROM "tblInsuree" WHERE "InsureeID" = %s',
                [insuree.pk],
            )
            self.assertEqual(cursor.fetchone(), (1,))
