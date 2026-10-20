import importlib

from django.db import connection
from django.test import TestCase

from insuree.sql import read_sql

ALL_INSUREE_ROWS = """
    SELECT md5(string_agg(t::text, '|' ORDER BY "InsureeID")), count(*)
    FROM (SELECT * FROM "tblInsuree"
          UNION ALL SELECT * FROM "tblInsuree_history") t
"""
TABLE_ROWS = """
    SELECT md5(string_agg(t::text, '|' ORDER BY "InsureeID")), count(*)
    FROM "tblInsuree" t
"""
RELKIND = "SELECT relkind FROM pg_class WHERE relname = 'tblInsuree'"
KEYS_TO_TABLE = """
    SELECT count(*) FROM pg_constraint
    WHERE confrelid = '"tblInsuree"'::regclass
"""
view = importlib.import_module("insuree.migrations.0026_insuree_view")
move = importlib.import_module("insuree.migrations.0027_move_insuree_heads")


def fetch_one(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchone()


def execute(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)


def settle():
    # A real run commits each batch of 0027; here everything shares one
    # transaction, so deferred checks are fired before the next ALTER TABLE.
    execute("SET CONSTRAINTS ALL IMMEDIATE")


class InsureeMigrationRoundTripTest(TestCase):
    """The database side of 0026-0028 backwards and forwards, in the order
    `migrate insuree 0025` and `migrate insuree` run it."""

    def test_migrating_back_restores_the_table_and_forward_the_view(self):
        rows = fetch_one(ALL_INSUREE_ROWS)
        with connection.schema_editor() as editor:
            execute(read_sql("0028_reverse.sql"))
            move.reverse(None, editor)
            settle()
            view.reverse(None, editor)
        self.assertEqual(fetch_one(RELKIND), ("r",))
        self.assertEqual(fetch_one(TABLE_ROWS), rows)
        self.assertEqual(fetch_one(KEYS_TO_TABLE), (10,))

        with connection.schema_editor() as editor:
            view.forward(None, editor)
            move.forward(None, editor)
            settle()
            execute(read_sql("0028_forward.sql"))
        self.assertEqual(fetch_one(RELKIND), ("v",))
        self.assertEqual(fetch_one(ALL_INSUREE_ROWS), rows)
