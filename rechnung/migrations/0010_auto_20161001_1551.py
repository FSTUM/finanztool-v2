# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-10-01 13:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rechnung', '0009_auto_20161001_1550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mahnung',
            name='wievielte',
            field=models.IntegerField(blank=True, null=True, verbose_name='Wievielte Mahnung?'),
        ),
    ]
