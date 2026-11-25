from django.test import TestCase

from core.gql.max_length_constraints import build_max_length_constraints


class MaxLengthConstraintsTestCase(TestCase):
    def test_build_max_length_constraints_returns_insuree_fields(self):
        constraints = build_max_length_constraints()

        self.assertIn("insuree", constraints)
        self.assertIn("insuree", constraints["insuree"])
        self.assertEqual(
            constraints["insuree"]["insuree"],
            {
                "uuid": 36,
                "chfId": 50,
                "lastName": 100,
                "otherNames": 100,
                "marital": 1,
                "passport": 25,
                "phone": 50,
                "email": 100,
                "currentAddress": 200,
                "geolocation": 250,
                "status": 2,
            },
        )
