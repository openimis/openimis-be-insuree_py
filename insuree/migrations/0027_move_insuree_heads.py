from django.db import migrations

from insuree.individual_bridge import move_insuree_heads, restore_insuree_heads


def forward(apps, schema_editor):
    move_insuree_heads(schema_editor.connection)


def reverse(apps, schema_editor):
    restore_insuree_heads(schema_editor.connection)


class Migration(migrations.Migration):
    # One transaction per batch: a move of millions of rows must not hold every
    # lock and all of its WAL until the end, and must resume where it stopped.
    atomic = False

    dependencies = [
        ("insuree", "0026_insuree_view"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
