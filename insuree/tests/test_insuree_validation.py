from django.test import TestCase

from insuree.apps import InsureeConfig
from insuree.models import Insuree
from insuree.test_helpers import create_test_insuree
from insuree.services import validate_insuree_number


def fail1(x):
    if x == "fail1":
        return ["fail1"]
    else:
        return []


class InsureeValidationTest(TestCase):
    def _unused_insuree_number(self, length, modulo_root=None):
        for base in range(10 ** (length - 2), 10 ** (length - 1)):
            if modulo_root:
                number = f"{base}{base % modulo_root}"
            else:
                number = str(base).ljust(length, "0")
            if not Insuree.objects.filter(chf_id=number, validity_to__isnull=True).exists():
                return number
        raise AssertionError("Unable to find an unused insuree number")

    def test_validator(self):

        InsureeConfig.insuree_number_validator = 'insuree.tests.test_insuree_validation.fail1'
        InsureeConfig.insuree_number_max_length = None
        InsureeConfig.insuree_number_min_length = None
        InsureeConfig.insuree_number_modulo_root = None
        
        self.assertEqual(validate_insuree_number(None), [])
        self.assertEqual(validate_insuree_number("valid"), [])
        self.assertEqual(validate_insuree_number("fail1"), ["fail1"])
        InsureeConfig. insuree_number_validator = None
        InsureeConfig.insuree_number_max_length = None
        InsureeConfig.insuree_number_min_length = None
        InsureeConfig.insuree_number_modulo_root = None
        
        self.assertEqual(validate_insuree_number(None), [])
        self.assertEqual(validate_insuree_number("valid"), [])
        self.assertEqual(validate_insuree_number("fail1"), [])

    def test_len(self):
        InsureeConfig. insuree_number_validator = None
        InsureeConfig.insuree_number_max_length = 5
        InsureeConfig.insuree_number_min_length = 5
        InsureeConfig.insuree_number_modulo_root = None
        
        self.assertEqual(len(validate_insuree_number(None)), 1)
        self.assertEqual(len(validate_insuree_number("")), 1)
        self.assertEqual(len(validate_insuree_number("foo")), 1)
        self.assertEqual(len(validate_insuree_number(self._unused_insuree_number(5))), 0)
        self.assertEqual(len(validate_insuree_number("1234567")), 1)
        InsureeConfig. insuree_number_validator = None
        InsureeConfig.insuree_number_max_length = 7
        InsureeConfig.insuree_number_min_length = 7
        InsureeConfig.insuree_number_modulo_root = None
        
        self.assertEqual(len(validate_insuree_number("12345")), 1)
        self.assertEqual(len(validate_insuree_number(self._unused_insuree_number(7))), 0)

    def test_mod(self):
        InsureeConfig. insuree_number_validator = None
        InsureeConfig.insuree_number_max_length = 5
        InsureeConfig.insuree_number_min_length = 5
        InsureeConfig.insuree_number_modulo_root = 7
        
        self.assertEqual(len(validate_insuree_number(None)), 1)
        self.assertEqual(len(validate_insuree_number(self._unused_insuree_number(5, 7))), 0)
        self.assertEqual(len(validate_insuree_number("12345")), 1)
        self.assertEqual(len(validate_insuree_number("1234567")), 1)
        InsureeConfig. insuree_number_validator = None
        InsureeConfig.insuree_number_max_length = 7
        InsureeConfig.insuree_number_min_length = 7
        InsureeConfig.insuree_number_modulo_root = 5
        
        self.assertEqual(len(validate_insuree_number("12345")), 1)
        self.assertEqual(len(validate_insuree_number(self._unused_insuree_number(7, 5))), 0)
        self.assertEqual(len(validate_insuree_number("1234560")), 1)

    def test_uniqueness(self):
        InsureeConfig.insuree_number_validator = None
        InsureeConfig.insuree_number_max_length = None
        InsureeConfig.insuree_number_min_length = None
        InsureeConfig.insuree_number_modulo_root = None

        insuree = create_test_insuree(custom_props={"chf_id": "123456789"})

        self.assertEqual(len(validate_insuree_number("123456789")), 1)
        self.assertEqual(validate_insuree_number("123456789", insuree.uuid), [])
