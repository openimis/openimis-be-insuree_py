# Generated by Django 3.2.17 on 2023-06-09 10:16

import core.fields
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0018_auto_20230609_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='insureephoto',
            name='chf_id',
            field=models.CharField(blank=True, db_column='CHFID', max_length=13, null=True),
        ),
    ]