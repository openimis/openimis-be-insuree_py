from django.db import connection, transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from insuree.test_helpers import create_test_insuree

KEYS_TO_LINKS = """
    SELECT conrelid::regclass::text FROM pg_constraint
    WHERE confrelid = '"insuree_InsureeIndividual"'::regclass
      AND contype = 'f'
    ORDER BY 1
"""


def fetch(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def plan(sql, params):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL enable_seqscan = off")
        cursor.execute("EXPLAIN " + sql, params)
        return "\n".join(row[0] for row in cursor.fetchall())


class InsureeConstraintsTest(TestCase):
    def assert_violates_at_commit(self, sql, params):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_the_tables_that_referenced_insurees_reference_the_links(self):
        self.assertEqual(
            [table for (table,) in fetch(KEYS_TO_LINKS)],
            sorted(
                [
                    '"insuree_InsureeMutation"',
                    '"tblClaim"',
                    '"tblClaimDedRem"',
                    '"tblContractDetails"',
                    '"tblFamilies"',
                    '"tblHealthStatus"',
                    '"tblInsureePolicy"',
                    '"tblPolicyHolderInsuree"',
                    '"tblPolicyRenewalDetails"',
                    '"tblPolicyRenewals"',
                ]
            ),
        )

    def test_a_referenced_insuree_keeps_its_link(self):
        insuree = create_test_insuree()
        self.assert_violates_at_commit(
            'DELETE FROM "insuree_InsureeIndividual" WHERE "InsureeID" = %s',
            [insuree.pk],
        )

    def test_a_reference_to_no_insuree_is_refused(self):
        insuree = create_test_insuree()
        self.assert_violates_at_commit(
            'UPDATE "tblFamilies" SET "InsureeID" = 999999999'
            ' WHERE "FamilyID" = %s',
            [insuree.family_id],
        )

    def test_only_copies_can_enter_the_history_table(self):
        insuree = create_test_insuree()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO "tblInsuree_history"'
                        ' SELECT * FROM "tblInsuree"'
                        ' WHERE "InsureeID" = %s',
                        [insuree.pk],
                    )

    def test_lookups_by_number_and_uuid_use_the_indexes(self):
        self.assertIn(
            "insuree_chf_id",
            plan('SELECT * FROM "tblInsuree" WHERE "CHFID" = %s', ["1"]),
        )
        self.assertIn(
            "insuree_uuid",
            plan('SELECT * FROM "tblInsuree" WHERE "InsureeUUID" = %s', ["x"]),
        )
        self.assertIn(
            "insuree_validity_from",
            plan(
                'SELECT * FROM "tblInsuree" WHERE "ValidityTo" IS NULL'
                ' ORDER BY "ValidityFrom" DESC LIMIT 10',
                [],
            ),
        )
        self.assertIn(
            "insuree_family_id",
            plan('SELECT * FROM "tblInsuree" WHERE "FamilyID" = %s', [1]),
        )
