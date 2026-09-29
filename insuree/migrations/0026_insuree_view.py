import django.db.models.deletion
from django.core.exceptions import ImproperlyConfigured
from django.db import migrations, models

from insuree import dependent_views
from insuree.sql import read_sql


def _require_postgresql(connection):
    if connection.vendor != "postgresql":
        raise ImproperlyConfigured(
            "insuree 0026 turns tblInsuree into a view and requires PostgreSQL"
        )


def forward(apps, schema_editor):
    _require_postgresql(schema_editor.connection)
    with schema_editor.connection.cursor() as cursor:
        # Every step below takes an exclusive lock; waiting behind a long
        # report would block every query queued after this migration.
        cursor.execute("SET LOCAL lock_timeout = '5s'")
        views = dependent_views.capture(cursor, '"tblInsuree"')
        dependent_views.drop(cursor, views)
        for name in ("0026_view.sql",):
            cursor.execute(read_sql(name))
        dependent_views.recreate(cursor, views)


def reverse(apps, schema_editor):
    _require_postgresql(schema_editor.connection)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET LOCAL lock_timeout = '5s'")
        views = dependent_views.capture(cursor, '"tblInsuree"')
        dependent_views.drop(cursor, views)
        cursor.execute(read_sql("0026_reverse.sql"))
        dependent_views.recreate(cursor, views)


class Migration(migrations.Migration):

    dependencies = [
        ("insuree", "0025_insuree_schema_and_system_user"),
        ("individual", "0020_label_rights_and_seed"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelOptions(
                    name="insuree", options={"managed": False}
                ),
                migrations.CreateModel(
                    name="InsureeIndividual",
                    fields=[
                        (
                            "insuree_id",
                            models.AutoField(
                                db_column="InsureeID",
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        (
                            "individual",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.DO_NOTHING,
                                to="individual.individual",
                            ),
                        ),
                    ],
                    options={"db_table": "insuree_InsureeIndividual"},
                ),
            ],
            database_operations=[migrations.RunPython(forward, reverse)],
        ),
    ]
