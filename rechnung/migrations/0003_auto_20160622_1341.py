# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-22 11:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rechnung', '0002_auto_20160622_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posten',
            name='name',
            field=models.CharField(max_length=70, verbose_name='Bezeichnung'),
        ),
    ]