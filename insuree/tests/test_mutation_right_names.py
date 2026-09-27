"""
Each insuree mutation must check the right that matches what it does.

A right is an integer on a role, so a check against the wrong-named constant is
invisible until a deployment configures the two differently - and then it either
denies the users who should be allowed or allows the ones who should not. Two real
cases are pinned here:

  * `UpdateInsureeMutation` checked `gql_mutation_create_insurees_perms` (101102)
    instead of the update right (101103). A role holding only "create insuree" could
    edit any insuree; a role holding only "update insuree" could edit none.
  * `MoveFamilyToParentMutation` / `DeleteFamiliesFromParentMutation` checked no right
    at all - any authenticated user could re-parent or orphan a family by uuid.

The assertions read the constant the mutation actually references, so they stay true if
the right ids are ever renumbered; only the entity/action pairing is pinned.
"""

import ast
import inspect
import re

from django.test import TestCase

from insuree import gql_mutations
from insuree.apps import InsureeConfig

# mutation class -> the config keys it is allowed to check
EXPECTED_PERMS = {
    "CreateFamilyMutation": {"gql_mutation_create_families_perms"},
    "UpdateFamilyMutation": {"gql_mutation_update_families_perms"},
    "DeleteFamiliesMutation": {"gql_mutation_delete_families_perms"},
    "CreateInsureeMutation": {"gql_mutation_create_insurees_perms"},
    "UpdateInsureeMutation": {"gql_mutation_update_insurees_perms"},
    "DeleteInsureesMutation": {"gql_mutation_delete_insurees_perms"},
    "RemoveInsureesMutation": {"gql_mutation_delete_insurees_perms"},
    "SetFamilyHeadMutation": {"gql_mutation_update_families_perms"},
    "MoveFamilyToParentMutation": {"gql_mutation_update_families_perms"},
    "DeleteFamiliesFromParentMutation": {"gql_mutation_update_families_perms"},
    "ChangeInsureeFamilyMutation": {
        "gql_mutation_update_families_perms",
        "gql_mutation_update_insurees_perms",
    },
}

PERM_REF = re.compile(r"InsureeConfig\.(\w*perms\w*)")


def _perms_referenced(class_name):
    """The InsureeConfig perm constants named in that class body, comments excluded."""
    source = inspect.getsource(getattr(gql_mutations, class_name))
    # ast.unparse drops comments, so a commented-out check cannot count as a check
    return set(PERM_REF.findall(ast.unparse(ast.parse(source))))


class MutationRightNameTestCase(TestCase):
    def test_every_mutation_checks_the_expected_right(self):
        for class_name, expected in EXPECTED_PERMS.items():
            with self.subTest(mutation=class_name):
                self.assertEqual(_perms_referenced(class_name), expected)

    def test_no_mutation_is_left_without_a_right_check(self):
        unchecked = [
            name for name in EXPECTED_PERMS if not _perms_referenced(name)
        ]
        self.assertEqual(unchecked, [])

    def test_update_insuree_does_not_check_the_create_right(self):
        """The specific regression: update gated by the create right."""
        self.assertNotIn(
            "gql_mutation_create_insurees_perms",
            _perms_referenced("UpdateInsureeMutation"),
        )

    def test_insuree_create_and_update_are_distinct_rights(self):
        """
        The rename only matters because these differ; if they were ever aliased onto
        one id the mix-up would be unobservable.
        """
        self.assertNotEqual(
            InsureeConfig.gql_mutation_create_insurees_perms,
            InsureeConfig.gql_mutation_update_insurees_perms,
        )

    def test_family_reparenting_requires_the_family_update_right(self):
        for class_name in (
            "MoveFamilyToParentMutation",
            "DeleteFamiliesFromParentMutation",
        ):
            with self.subTest(mutation=class_name):
                self.assertIn(
                    "gql_mutation_update_families_perms",
                    _perms_referenced(class_name),
                )
