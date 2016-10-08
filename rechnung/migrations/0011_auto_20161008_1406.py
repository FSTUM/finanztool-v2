# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-08 12:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rechnung', '0010_auto_20161001_1551'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mahnung',
            old_name='erledigt',
            new_name='bezahlt',
        ),
        migrations.AddField(
            model_name='rechnung',
            name='erledigt',
            field=models.BooleanField(default=False, verbose_name='Rechnung erledigt, eventuell durch Mahnung'),
        ),
    ]
