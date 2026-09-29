from django.db import migrations

from insuree.sql import read_sql


class Migration(migrations.Migration):

    dependencies = [
        ("insuree", "0027_move_insuree_heads"),
    ]

    operations = [
        migrations.RunSQL(
            read_sql("0028_forward.sql"), read_sql("0028_reverse.sql")
        ),
    ]
