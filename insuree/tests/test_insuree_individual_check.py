import uuid
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase

from core.models import User
from individual.models import Group, GroupIndividual, Individual
from insuree.models import InsureeIndividual
from insuree.test_helpers import create_test_insuree


def execute(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def validated():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT bool_and(convalidated) FROM pg_constraint"
            " WHERE conname LIKE '%fk_insuree_individual'"
            " OR conname = 'tblInsuree_history_copies_only'"
        )
        return cursor.fetchone()[0]


class InsureeIndividualCheckTest(TestCase):
    def check(self, *args):
        out = StringIO()
        try:
            call_command("insuree_individual_check", *args, stdout=out)
        except CommandError:
            return False, out.getvalue()
        return True, out.getvalue()

    def finalize(self):
        passed, out = self.check("--finalize")
        self.assertTrue(passed, out)
        return out

    def seed_head(self, **columns):
        execute(
            'ALTER TABLE "tblInsuree_history"'
            ' DROP CONSTRAINT IF EXISTS "tblInsuree_history_copies_only"'
        )
        insuree = create_test_insuree()
        values = {
            "InsureeID": insuree.pk + 100000,
            "InsureeUUID": str(uuid.uuid4()),
            "CHFID": "8%08d" % insuree.pk,
            **columns,
        }
        assignments = ", ".join('"%s" = %%(%s)s' % (k, k) for k in values)
        execute(
            "CREATE TEMP TABLE seed ON COMMIT DROP AS SELECT * FROM"
            ' "tblInsuree" WHERE "InsureeID" = %(id)s;'
            " UPDATE seed SET " + assignments + ";"
            ' INSERT INTO "tblInsuree_history" SELECT * FROM seed;'
            " DROP TABLE seed;",
            {"id": insuree.pk, **values},
        )
        return insuree

    def test_unvalidated_constraints_block_until_finalized(self):
        if validated():
            self.skipTest("the test database was finalized already")
        passed, out = self.check()
        self.assertFalse(passed)
        self.assertIn("--finalize", out)

    def test_finalize_validates_every_new_constraint(self):
        out = self.finalize()
        self.assertTrue(validated())
        self.assertIn("VACUUM skipped", out)

    def test_an_insuree_left_in_the_history_table_blocks(self):
        self.seed_head()
        passed, out = self.check()
        self.assertFalse(passed)
        self.assertIn("still in the history table", out)

    def test_a_uuid_an_individual_already_has_blocks(self):
        insuree = create_test_insuree()
        taken = InsureeIndividual.objects.get(insuree_id=insuree.pk)
        self.seed_head(InsureeUUID=str(taken.individual_id))
        passed, out = self.check()
        self.assertFalse(passed)
        self.assertIn("an individual already has", out)

    def test_unresolved_audit_users_are_listed(self):
        self.seed_head(AuditUserID=424242)
        _, out = self.check()
        self.assertIn("424242: 1", out)

    def test_group_members_show_that_rollback_is_refused(self):
        insuree = create_test_insuree()
        user = User.objects.filter(username="Admin").first()
        individual = Individual.objects.get(
            id=InsureeIndividual.objects.get(
                insuree_id=insuree.pk
            ).individual_id
        )
        group = Group(code="G2")
        group.save(user=user)
        GroupIndividual(group=group, individual=individual).save(user=user)
        _, out = self.check()
        self.assertIn("individual_groupindividual", out)

    def test_an_individual_with_a_non_integer_family_id_stays_writable(self):
        user = User.objects.filter(username="Admin").first()
        other = Individual(
            first_name="A",
            last_name="B",
            dob="2000-01-01",
            json_ext={"family_id": "F-1"},
        )
        other.save(user=user)
        self.assertEqual(
            Individual.objects.get(id=other.id).json_ext["family_id"], "F-1"
        )
