# Generated by Django 4.0.3 on 2022-06-27 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0007_settings_at_05_remittance_information_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settings",
            name="at_05_remittance_information",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Used for generating an EPC-QR-Code",
                max_length=35,
                verbose_name="AT-05 Remittance Information (Structured) Creditor Reference (ISO 11649 may be used)",
            ),
        ),
        migrations.AlterField(
            model_name="settings",
            name="at_44_purpose",
            field=models.CharField(
                default="RCPT",
                help_text="Used for generating an EPC-QR-Code",
                max_length=4,
                verbose_name="AT-44 Purpose of the Credit Transfer. See 'EXTERNAL PURPOSE CODES LIST (ISO 20022)'",
            ),
        ),
    ]