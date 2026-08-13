from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0030_altertblProfessions'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS public."tblNoDisability";',
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS public."tblNonDisablingDisease";',
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS public."tblMutualInsuranceCoverage";',
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS public."tblHousingType";',
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS public."tblResidenceEnvironment";',
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.CreateModel(
            name='MutualInsuranceCoverage',
            fields=[
                ('code', models.IntegerField(db_column='Code', primary_key=True, serialize=False)),
                ('mutual_insurance_coverage', models.CharField(blank=True, db_column='MutualInsuranceCoverage', max_length=150, null=True)),
                ('alt_language', models.CharField(blank=True, db_column='AltLanguage', max_length=150, null=True)),
                ('sort_order', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
            ],
            options={
                'db_table': 'tblMutualInsuranceCoverage',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='NoDisability',
            fields=[
                ('code', models.IntegerField(db_column='Code', primary_key=True, serialize=False)),
                ('no_disability_label', models.CharField(blank=True, db_column='NoDisabilityLabel', max_length=100, null=True)),
                ('alt_language', models.CharField(blank=True, db_column='AltLanguage', max_length=100, null=True)),
                ('sort_order', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
            ],
            options={
                'db_table': 'tblNoDisability',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='NonDisablingDisease',
            fields=[
                ('code', models.IntegerField(db_column='Code', primary_key=True, serialize=False)),
                ('non_disabling_disease', models.CharField(blank=True, db_column='NonDisablingDisease', max_length=100, null=True)),
                ('alt_language', models.CharField(blank=True, db_column='AltLanguage', max_length=100, null=True)),
                ('sort_order', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
            ],
            options={
                'db_table': 'tblNonDisablingDisease',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ResidenceEnvironment',
            fields=[
                ('code', models.IntegerField(db_column='Code', primary_key=True, serialize=False)),
                ('residence_environment', models.CharField(blank=True, db_column='ResidenceEnvironment', max_length=100, null=True)),
                ('alt_language', models.CharField(blank=True, db_column='AltLanguage', max_length=100, null=True)),
                ('sort_order', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
            ],
            options={
                'db_table': 'tblResidenceEnvironment',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='HousingType',
            fields=[
                ('code', models.IntegerField(db_column='Code', primary_key=True, serialize=False)),
                ('housing_type', models.CharField(blank=True, db_column='HousingType', max_length=150, null=True)),
                ('alt_language', models.CharField(blank=True, db_column='AltLanguage', max_length=150, null=True)),
                ('sort_order', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
            ],
            options={
                'db_table': 'tblHousingType',
                'managed': True,
            },
        ),
        migrations.AddField(
            model_name='insuree',
            name='mutual_insurance_coverage',
            field=models.ForeignKey(blank=True, db_column='MutualInsuranceCoverage', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='insuree.mutualinsurancecoverage'),
        ),
        migrations.AddField(
            model_name='insuree',
            name='no_disability',
            field=models.ForeignKey(blank=True, db_column='NoDisability', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='insuree.nodisability'),
        ),
        migrations.AddField(
            model_name='insuree',
            name='non_disabling_disease',
            field=models.ForeignKey(blank=True, db_column='NonDisablingDisease', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='insuree.nondisablingdisease'),
        ),
        migrations.AddField(
            model_name='insuree',
            name='residence_environment',
            field=models.ForeignKey(blank=True, db_column='ResidenceEnvironment', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='insuree.residenceenvironment'),
        ),
        migrations.AddField(
            model_name='insuree',
            name='housing_type',
            field=models.ForeignKey(blank=True, db_column='HousingType', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='insuree.housingtype'),
        ),
    ]
