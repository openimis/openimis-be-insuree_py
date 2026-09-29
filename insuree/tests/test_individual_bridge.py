import uuid

from django.db import connection
from django.test import TestCase

from core.models import User
from individual.models import Group, GroupIndividual, Individual
from insuree.individual_bridge import (
    move_insuree_heads,
    restore_insuree_heads,
)
from insuree.models import InsureeIndividual
from insuree.sql import read_sql
from insuree.test_helpers import create_test_insuree

HISTORY_ROW = 'SELECT * FROM "tblInsuree_history" WHERE "InsureeID" = %s'
VIEW_ROW = 'SELECT * FROM "tblInsuree" WHERE "InsureeID" = %s'


def fetch_one(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def execute(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


class IndividualBridgeTest(TestCase):
    def setUp(self):
        # Seeding writes heads here, as the table held them before 0027.
        execute(
            'ALTER TABLE "tblInsuree_history"'
            ' DROP CONSTRAINT IF EXISTS "tblInsuree_history_copies_only"'
        )
        self.template = create_test_insuree().pk

    def seed_head(self, **columns):
        """A head row as the table held it before the move: copied from an
        insuree the view has, with a fresh id, uuid and number."""
        insuree_id = fetch_one(
            "SELECT nextval('\"tblInsuree_InsureeID_seq\"')", []
        )[0]
        values = {
            "InsureeID": insuree_id,
            "InsureeUUID": str(uuid.uuid4()),
            "CHFID": "9%08d" % insuree_id,
            **columns,
        }
        assignments = ", ".join('"%s" = %%(%s)s' % (k, k) for k in values)
        execute(
            "CREATE TEMP TABLE seed ON COMMIT DROP AS"
            ' SELECT * FROM "tblInsuree" WHERE "InsureeID" = %(template)s;'
            " UPDATE seed SET " + assignments + ";"
            ' INSERT INTO "tblInsuree_history" SELECT * FROM seed;'
            " DROP TABLE seed;",
            {"template": self.template, **values},
        )
        return insuree_id

    def assert_moved_unchanged(self, insuree_id):
        before = fetch_one(HISTORY_ROW, [insuree_id])
        move_insuree_heads(connection)
        self.assertIsNone(fetch_one(HISTORY_ROW, [insuree_id]))
        self.assertEqual(fetch_one(VIEW_ROW, [insuree_id]), before)
        return InsureeIndividual.objects.get(insuree_id=insuree_id)

    def test_a_current_head_reads_the_same_after_the_move(self):
        link = self.assert_moved_unchanged(self.seed_head())
        self.assertEqual(
            Individual.objects.get(id=link.individual_id).labels, ["INSUREE"]
        )

    def test_a_head_without_birth_date_reads_the_same(self):
        self.assert_moved_unchanged(self.seed_head(DOB=None))

    def test_a_head_without_extension_data_reads_the_same(self):
        self.assert_moved_unchanged(self.seed_head(JsonExt=None))

    def test_a_head_with_extension_data_reads_the_same(self):
        self.assert_moved_unchanged(self.seed_head(JsonExt='{"a": [1, 2]}'))

    def test_a_soft_deleted_head_moves_as_a_deleted_individual(self):
        insuree_id = self.seed_head()
        execute(
            'UPDATE "tblInsuree_history" SET "ValidityTo" = "ValidityFrom"'
            ' WHERE "InsureeID" = %s',
            [insuree_id],
        )
        link = self.assert_moved_unchanged(insuree_id)
        self.assertTrue(
            Individual.objects.get(id=link.individual_id).is_deleted
        )

    def test_a_deletion_date_of_its_own_is_kept(self):
        insuree_id = self.seed_head()
        execute(
            'UPDATE "tblInsuree_history"'
            ' SET "ValidityTo" = "ValidityFrom" + interval \'1 day\''
            ' WHERE "InsureeID" = %s',
            [insuree_id],
        )
        self.assert_moved_unchanged(insuree_id)

    def test_an_uppercase_uuid_is_kept(self):
        self.assert_moved_unchanged(
            self.seed_head(InsureeUUID=str(uuid.uuid4()).upper())
        )

    def test_the_individual_is_created_when_its_chain_started(self):
        insuree_id = self.seed_head()
        copy_id = self.seed_head(LegacyID=insuree_id)
        execute(
            'UPDATE "tblInsuree_history"'
            " SET \"ValidityFrom\" = timestamptz '2001-01-01',"
            " \"ValidityTo\" = timestamptz '2002-01-01'"
            ' WHERE "InsureeID" = %s',
            [copy_id],
        )
        link = self.assert_moved_unchanged(insuree_id)
        created = Individual.objects.get(id=link.individual_id).date_created
        self.assertEqual(created.year, 2001)
        self.assertIsNotNone(fetch_one(HISTORY_ROW, [copy_id]))

    def test_a_second_move_finds_nothing(self):
        self.seed_head()
        self.assertEqual(move_insuree_heads(connection), 1)
        self.assertEqual(move_insuree_heads(connection), 0)

    def test_restore_brings_the_rows_back(self):
        insuree_id = self.seed_head()
        before = fetch_one(HISTORY_ROW, [insuree_id])
        move_insuree_heads(connection)
        individual_id = InsureeIndividual.objects.get(
            insuree_id=insuree_id
        ).individual_id
        # As migrating back does: the keys to the links go first, in a
        # transaction with no deferred checks pending.
        execute("SET CONSTRAINTS ALL IMMEDIATE")
        execute(read_sql("0028_reverse.sql"))
        restore_insuree_heads(connection)
        self.assertEqual(fetch_one(HISTORY_ROW, [insuree_id]), before)
        self.assertFalse(Individual.objects.filter(id=individual_id).exists())
        self.assertIsNone(
            fetch_one(
                "SELECT 1 FROM individual_historicalindividual"
                ' WHERE "UUID" = %s',
                [individual_id],
            )
        )
        self.assertFalse(InsureeIndividual.objects.exists())

    def test_restore_is_refused_while_a_group_holds_a_moved_insuree(self):
        user = User.objects.filter(username="Admin").first()
        individual = Individual.objects.get(
            id=InsureeIndividual.objects.get(
                insuree_id=self.template
            ).individual_id
        )
        group = Group(code="G1")
        group.save(user=user)
        GroupIndividual(group=group, individual=individual).save(user=user)
        with self.assertRaisesMessage(
            RuntimeError, "individual_groupindividual"
        ):
            restore_insuree_heads(connection)
        self.assertTrue(
            InsureeIndividual.objects.filter(insuree_id=self.template).exists()
        )
