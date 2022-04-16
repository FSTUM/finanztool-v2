# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-19 13:07
from __future__ import unicode_literals

from typing import Union

from django.db import migrations, models
from django.db.migrations.migration import SwappableTuple


class Migration(migrations.Migration):
    initial = True

    dependencies: list[Union[tuple[str, str], SwappableTuple]] = []

    operations = [
        migrations.CreateModel(
            name="Blacklist",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user", models.TextField(blank=True, null=True)),
                ("grund", models.TextField(blank=True, null=True)),
                ("datum", models.CharField(blank=True, max_length=32, null=True)),
            ],
            options={
                "db_table": "blacklist",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Getraenke",
            fields=[
                ("nummer", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, max_length=32, null=True)),
                ("barcode", models.TextField(blank=True, null=True)),
                ("preis", models.FloatField(blank=True, null=True)),
                ("shortname", models.CharField(blank=True, max_length=16, null=True)),
            ],
            options={
                "db_table": "getraenke",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Log",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("konto", models.CharField(blank=True, max_length=32, null=True)),
                ("gruppe", models.CharField(blank=True, max_length=32, null=True)),
                ("aktion", models.CharField(blank=True, max_length=32, null=True)),
                ("typ", models.CharField(blank=True, max_length=32, null=True)),
                ("betrag", models.FloatField(blank=True, null=True)),
                ("gesamt_jetzt", models.FloatField(blank=True, null=True)),
                ("user", models.CharField(blank=True, max_length=32, null=True)),
                ("datum", models.CharField(blank=True, max_length=32, null=True)),
            ],
            options={
                "db_table": "log",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Schulden",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user", models.CharField(max_length=32, unique=True)),
                ("betrag", models.FloatField()),
            ],
            options={
                "db_table": "schulden",
                "managed": False,
            },
        ),
    ]
