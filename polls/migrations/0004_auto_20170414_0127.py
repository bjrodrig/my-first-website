# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-14 05:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0003_auto_20170414_0048'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='carbs',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='fat',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='protein',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sodium',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sugar',
            field=models.FloatField(default=0),
        ),
    ]