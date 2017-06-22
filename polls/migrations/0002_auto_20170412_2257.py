# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-13 02:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermeals',
            name='cal_eaten',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='usermeals',
            name='carbs',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='usermeals',
            name='fat',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='usermeals',
            name='protein',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='usermeals',
            name='sodium',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='usermeals',
            name='sugar',
            field=models.FloatField(default=0),
        ),
    ]