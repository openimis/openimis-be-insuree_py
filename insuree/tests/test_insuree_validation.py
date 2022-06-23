from django.test import TestCase

from insuree.services import validate_insuree_number


class InsureeValidationTest(TestCase):
    def test_validator(self):
        def fail1(x):
            if x == "fail1":
                return ["fail1"]
            else:
                return []

        with self.settings(
                INSUREE_NUMBER_VALIDATOR=fail1,
                INSUREE_NUMBER_LENGTH=None,
                INSUREE_NUMBER_MODULE_ROOT=None):
            self.assertEqual(validate_insuree_number(None), [])
            self.assertEqual(validate_insuree_number("valid"), [])
            self.assertEqual(validate_insuree_number("fail1"), ["fail1"])
        with self.settings(
                INSUREE_NUMBER_VALIDATOR=None,
                INSUREE_NUMBER_LENGTH=None,
                INSUREE_NUMBER_MODULE_ROOT=None):
            self.assertEqual(validate_insuree_number(None), [])
            self.assertEqual(validate_insuree_number("valid"), [])
            self.assertEqual(validate_insuree_number("fail1"), [])

    def test_len(self):
        with self.settings(
                INSUREE_NUMBER_VALIDATOR=None,
                INSUREE_NUMBER_LENGTH=5,
                INSUREE_NUMBER_MODULE_ROOT=None):
            self.assertEqual(len(validate_insuree_number(None)), 1)
            self.assertEqual(len(validate_insuree_number("")), 1)
            self.assertEqual(len(validate_insuree_number("foo")), 1)
            self.assertEqual(len(validate_insuree_number("12345")), 0)
            self.assertEqual(len(validate_insuree_number("1234567")), 1)
        with self.settings(
                INSUREE_NUMBER_VALIDATOR=None,
                INSUREE_NUMBER_LENGTH=7,
                INSUREE_NUMBER_MODULE_ROOT=None):
            self.assertEqual(len(validate_insuree_number("12345")), 1)
            self.assertEqual(len(validate_insuree_number("1234567")), 0)

    def test_mod(self):
        with self.settings(
                INSUREE_NUMBER_VALIDATOR=None,
                INSUREE_NUMBER_LENGTH=5,
                INSUREE_NUMBER_MODULE_ROOT=7):
            self.assertEqual(len(validate_insuree_number(None)), 1)
            self.assertEqual(len(validate_insuree_number("12342")), 0)
            self.assertEqual(len(validate_insuree_number("12345")), 1)
            self.assertEqual(len(validate_insuree_number("1234567")), 1)
        with self.settings(
                INSUREE_NUMBER_VALIDATOR=None,
                INSUREE_NUMBER_LENGTH=7,
                INSUREE_NUMBER_MODULE_ROOT=5):
            self.assertEqual(len(validate_insuree_number("12345")), 1)
            self.assertEqual(len(validate_insuree_number("1234561")), 0)
            self.assertEqual(len(validate_insuree_number("1234560")), 1)
