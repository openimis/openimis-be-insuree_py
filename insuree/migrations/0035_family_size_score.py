from django.db import migrations
from insuree.models import FamilySizeScores

def populate_scores(apps, schema_editor):

    famsize_min=[1,3,5,7,9,11]
    famsize_max=[2,4,6,8,10,999999]
    scores_list=[1,2,3,4,5,6]
    for i in range(len(scores_list)):
        famscore=FamilySizeScores()
        famscore.lower_born=famsize_min[i]
        famscore.higher_born=famsize_max[i]
        famscore.score=scores_list[i]
        famscore.save()

class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0034_score_income_level'),
    ]

    operations = [
        migrations.RunPython(populate_scores),
    ]
