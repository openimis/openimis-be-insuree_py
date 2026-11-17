from django.apps import apps
from django.db import connection
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.test import TestCase

COLUMNS = """
    SELECT attnum, attname, atttypid, atttypmod FROM pg_attribute
    WHERE attrelid = %s::regclass AND attnum > 0 AND NOT attisdropped
    ORDER BY attnum
"""
VIEWS_READING_HISTORY = """
    SELECT count(*) FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid
    WHERE d.refobjid = '"tblInsuree_history"'::regclass
      AND r.ev_class <> d.refobjid
"""
KEYS_TO_HISTORY = """
    SELECT count(*) FROM pg_constraint
    WHERE confrelid = '"tblInsuree_history"'::regclass
"""
ID_SEQUENCE = """
    SELECT pg_get_serial_sequence('"insuree_InsureeIndividual"', 'InsureeID')
"""


def fetch(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


class InsureeViewStructureTest(TestCase):
    def test_view_has_the_columns_order_and_types_of_the_table(self):
        self.assertEqual(
            fetch(COLUMNS, ['"tblInsuree"']),
            fetch(COLUMNS, ['"tblInsuree_history"']),
        )

    def test_tblinsuree_is_a_view(self):
        self.assertEqual(
            fetch("SELECT relkind FROM pg_class WHERE relname = 'tblInsuree'"),
            [("v",)],
        )

    def test_no_view_reads_the_history_table(self):
        self.assertEqual(fetch(VIEWS_READING_HISTORY), [(0,)])

    def test_no_foreign_key_references_the_history_table(self):
        self.assertEqual(fetch(KEYS_TO_HISTORY), [(0,)])

    def test_the_id_sequence_belongs_to_the_link_table(self):
        self.assertEqual(
            fetch(ID_SEQUENCE), [('public."tblInsuree_InsureeID_seq"',)]
        )

    def test_migrations_describe_the_models_this_change_touches(self):
        loader = MigrationLoader(None, ignore_no_migrations=True)
        changes = MigrationAutodetector(
            loader.project_state(), ProjectState.from_apps(apps)
        ).changes(graph=loader.graph, trim_to_apps={"insuree"})
        touched = ("insuree", "insureeindividual")
        pending = [
            operation
            for migration in changes.get("insuree", [])
            for operation in migration.operations
            if getattr(operation, "model_name", getattr(operation, "name", ""))
            .lower() in touched
        ]
        self.assertEqual(pending, [])
