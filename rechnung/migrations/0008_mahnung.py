# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-10-01 13:47
from __future__ import unicode_literals

import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import rechnung.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rechnung", "0007_auto_20160927_0045"),
    ]

    operations = [
        migrations.CreateModel(
            name="Mahnung",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wievielte", models.IntegerField(verbose_name="Wievielte Mahnung?")),
                ("gebuehr", models.DecimalField(decimal_places=2, max_digits=6, verbose_name="Mahngebühr")),
                ("mdatum", models.DateField(default=datetime.date.today, verbose_name="Mahndatum")),
                (
                    "mfdatum",
                    models.DateField(default=rechnung.models.get_faelligkeit_default, verbose_name="Neue Fälligkeit"),
                ),
                ("geschickt", models.BooleanField(default=False, verbose_name="Mahnung geschickt?")),
                ("erledigt", models.BooleanField(default=False, verbose_name="Rechnung beglichen")),
                (
                    "ersteller",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
                ("rechnung", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rechnung.Rechnung")),
            ],
        ),
    ]
