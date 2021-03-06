# Generated by Django 2.1.14 on 2019-12-02 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0003_insureepolicy'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmationType',
            fields=[
                ('code', models.CharField(db_column='ConfirmationTypeCode', max_length=3, primary_key=True, serialize=False)),
                ('confirmationtype', models.CharField(db_column='ConfirmationType', max_length=50)),
                ('sortorder', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
                ('altlanguage', models.CharField(blank=True, db_column='AltLanguage', max_length=50, null=True)),
            ],
            options={
                'db_table': 'tblConfirmationTypes',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.SmallIntegerField(db_column='EducationId', primary_key=True, serialize=False)),
                ('education', models.CharField(db_column='Education', max_length=50)),
                ('sortorder', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
                ('altlanguage', models.CharField(blank=True, db_column='AltLanguage', max_length=50, null=True)),
            ],
            options={
                'db_table': 'tblEducations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Profession',
            fields=[
                ('id', models.SmallIntegerField(db_column='ProfessionId', primary_key=True, serialize=False)),
                ('profession', models.CharField(db_column='Profession', max_length=50)),
                ('sortorder', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
                ('altlanguage', models.CharField(blank=True, db_column='AltLanguage', max_length=50, null=True)),
            ],
            options={
                'db_table': 'tblProfessions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.SmallIntegerField(db_column='RelationId', primary_key=True, serialize=False)),
                ('relation', models.CharField(db_column='Relation', max_length=50)),
                ('sortorder', models.IntegerField(blank=True, db_column='SortOrder', null=True)),
                ('altlanguage', models.CharField(blank=True, db_column='AltLanguage', max_length=50, null=True)),
            ],
            options={
                'db_table': 'tblRelations',
                'managed': False,
            },
        ),
    ]
