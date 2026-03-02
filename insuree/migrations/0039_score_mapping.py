from django.db import migrations
from insuree.models import FamilyIncomeScores


def populate_scores(apps, schema_editor):

    min_income = [0, 30000, 40001, 50001, 60001, 75001, 200001, 300001, 600001]
    max_income = [29999, 40000, 50000, 60000, 75000, 200000, 300000, 600000, 2147483640]
    scores     = [9, 8, 7, 6, 5, 4, 3, 2, 1]

    for i in range(len(scores)):
        mapping = FamilyIncomeScores(
            lower_born=min_income[i],
            higher_born=max_income[i],
            score=scores[i]
        )
        print(
            "Creating FamilyIncomeScores:",
            mapping.lower_born,
            mapping.higher_born,
            mapping.score
        )
        mapping.save()


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0038_familyincomescores_insuree_fix_income'),
    ]

    operations = [
        migrations.RunPython(populate_scores),
    ]
