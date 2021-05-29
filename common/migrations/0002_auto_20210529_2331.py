# Generated by Django 3.2.3 on 2021-05-29 21:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='typ_aenderung_multiple',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='typ_aenderung_single+', to='common.mail', verbose_name='Template, das ausgewählt wird, wenn mehrere Keycard-Typ-Änderungen versendet werden sollen'),
        ),
        migrations.AddField(
            model_name='settings',
            name='typ_aenderung_single',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='typ_aenderung_single+', to='common.mail', verbose_name='Template, das ausgewählt wird, wenn eine einzige Keycard-Typ-Änderung versendet werden soll'),
        ),
        migrations.AddField(
            model_name='settings',
            name='typ_aenderungs_beauftragter',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Emailadresse, ab die die Keycard-Typ-Änderngs-anfragen geschickt werden'),
        ),
    ]
