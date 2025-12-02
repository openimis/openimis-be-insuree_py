from django.db import migrations
from insuree.models import ScoreContributionMapping
from contribution_plan.models import ContributionPlan


def populate_scores(apps, schema_editor):

    min_score=[0,2.5,3.75,5,6.25,7.5,9.75,10]
    max_score=[2.5,3.75,5,6.25,7.5,9.75,10,999999]
    contrib_code=['AMOG','AMOE','AMOS','AMOS1','AMOS2','AMOS3','AMOS4','AMS']

    for i in range(len(contrib_code)):
        contrib=ContributionPlan.objects.all().filter(code=contrib_code[i]).first()
        if contrib:
            mapping=ScoreContributionMapping(
                lower_born=min_score[i],
                higher_born=max_score[i],
                contribution_plan=contrib
            )
            print("Creating ScoreContributionMapping:", mapping.lower_born, mapping.higher_born, mapping.contribution_plan.code)
            mapping.save()

class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0036_alter_scorecontributionmapping_higher_born_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_scores),
    ]
