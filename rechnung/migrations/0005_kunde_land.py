# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-26 22:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rechnung", "0004_auto_20160622_1355"),
    ]

    operations = [
        migrations.AddField(
            model_name="kunde",
            name="land",
            field=models.CharField(default="Deutschland", max_length=100, verbose_name="Land *"),
        ),
    ]
