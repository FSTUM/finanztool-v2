# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-17 14:02
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schluessel", "0002_auto_20170417_1306"),
    ]

    operations = [
        migrations.AlterField(
            model_name="key",
            name="person",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="schluessel.Person",
                verbose_name="Entleiher",
            ),
        ),
        migrations.AlterField(
            model_name="keylogentry",
            name="operation",
            field=models.CharField(
                choices=[("G", "Ausgabe"), ("R", "Rückgabe"), ("C", "Erstellung")],
                max_length=1,
                verbose_name="Vorgang",
            ),
        ),
        migrations.AlterField(
            model_name="keylogentry",
            name="person",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="schluessel.Person",
                verbose_name="Entleiher",
            ),
        ),
    ]
