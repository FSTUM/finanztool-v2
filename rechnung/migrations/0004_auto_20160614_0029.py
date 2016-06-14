# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-13 22:29
from __future__ import unicode_literals

from django.db import migrations, models
import rechnung.models


class Migration(migrations.Migration):

    dependencies = [
        ('rechnung', '0003_auto_20160613_2349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rechnung',
            name='rnr',
            field=models.IntegerField(default=rechnung.models.get_new_highest_rnr, unique=True, verbose_name='Rechnungsnummer *'),
        ),
    ]