from django.db import migrations
from insuree.models import HousingType

def populate_scores(apps, schema_editor):

    code_to_score = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        11: 11,
        12: 12,
        13: 13,
        15: 15,
        16: 16,
        17: 17,
        18: 18,
        19: 19,
        20: 20,
        21: 21,
    }

    for code, score in code_to_score.items():
        HousingType.objects.filter(code=code).update(score=score)


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0032_familysizescores_housingtype_score_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_scores),
    ]
