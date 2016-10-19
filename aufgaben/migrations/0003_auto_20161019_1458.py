# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-10-19 12:58
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aufgaben', '0002_auto_20161019_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aufgabe',
            name='bearbeiter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aufgabe_bearbeiter', to=settings.AUTH_USER_MODEL, verbose_name='Wer hat sie erledigt?'),
        ),
        migrations.AlterField(
            model_name='aufgabe',
            name='semester',
            field=models.CharField(blank=True, choices=[('ws', 'Wintersemester'), ('ss', 'Sommersemester')], max_length=2, null=True, verbose_name='Zugehöriges Semester'),
        ),
    ]
