# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-05 16:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('schluessel', '0009_key_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='keylogentry',
            name='key_active',
            field=models.NullBooleanField(verbose_name='Aktiv'),
        ),
    ]
