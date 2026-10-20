from django.db import migrations

from insuree.individual_bridge import ensure_restorable
from insuree.sql import read_sql


def refuse_if_referenced(apps, schema_editor):
    ensure_restorable(schema_editor.connection)


class Migration(migrations.Migration):

    dependencies = [
        ("insuree", "0027_move_insuree_heads"),
    ]

    operations = [
        migrations.RunSQL(
            read_sql("0028_forward.sql"), read_sql("0028_reverse.sql")
        ),
        # Reversed first: a rollback that 0027 would refuse stops here,
        # before this migration's constraints are dropped.
        migrations.RunPython(migrations.RunPython.noop, refuse_if_referenced),
    ]
