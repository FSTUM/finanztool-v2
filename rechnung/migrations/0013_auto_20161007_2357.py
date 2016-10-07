# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-10-07 21:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rechnung', '0012_mahnung_gerichtlich'),
    ]

    operations = [
        migrations.AddField(
            model_name='mahnung',
            name='ungueltig',
            field=models.BooleanField(default=False, verbose_name='Vorherige Mahnungen beglichen'),
        ),
        migrations.AlterField(
            model_name='mahnung',
            name='erledigt',
            field=models.BooleanField(default=False, verbose_name='Mahnung beglichen'),
        ),
    ]
