# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-26 22:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rechnung", "0006_kunde_titel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="kunde",
            name="titel",
            field=models.CharField(blank=True, default="", max_length=50, null=True, verbose_name="Titel"),
        ),
    ]
