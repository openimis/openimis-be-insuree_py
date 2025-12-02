from django.db import migrations
from insuree.models import IncomeLevels

def populate_scores(apps, schema_editor):

    id_to_score = {
        1: 9,
        2: 9,
        3: 8,
        4: 7,
        5: 6,
        6: 5,
        7: 4,
        8: 3,
        9: 2,
        10: 1,
    }

    for id, score in id_to_score.items():
        IncomeLevels.objects.filter(id=id).update(score=score)


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0033_score_type_habitation'),
    ]

    operations = [
        migrations.RunPython(populate_scores),
    ]
