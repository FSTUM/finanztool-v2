# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-18 10:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('schluessel', '0003_auto_20170417_1602'),
    ]

    operations = [
        migrations.AddField(
            model_name='keytype',
            name='keycard',
            field=models.BooleanField(default=False, verbose_name='Schließkarte'),
        ),
    ]
