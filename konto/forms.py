from decimal import Decimal

from django import forms

from .models import EinzahlungsLog


class UploadForm(forms.Form):
    csv_file = forms.FileField(label="CSV Datei")


class MappingConfirmationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.mappings = kwargs.pop("mappings")
        self.user = kwargs.pop("user")

        super().__init__(*args, **kwargs)

        for entry in self.mappings:
            key = self.get_key(entry)
            if key:
                self.fields[key] = forms.BooleanField(required=False)

    @staticmethod
    def get_key(entry):
        if entry.mapped_mahnung:
            return f"ma_{entry.mapped_mahnung.pk}"
        if entry.mapped_rechnung:
            return f"re_{entry.mapped_rechnung.pk}"
        if entry.mapped_user:
            return f"us_{entry.mapped_user.pk}"
        return None

    def save(self):
        latest_einzahlung = None
        latest_einzahlung_betrag: Decimal = Decimal("0.0")
        latest_einzahlung_verwendungszweck = ""
        for entry in self.mappings:
            key = self.get_key(entry)
            if key and self.cleaned_data[key]:
                if entry.mapped_mahnung:
                    entry.mapped_mahnung.bezahlen()
                elif entry.mapped_rechnung:
                    entry.mapped_rechnung.bezahlen()
                elif entry.mapped_user:
                    entry.mapped_user.einzahlen(entry.betrag, self.user)
                    if not latest_einzahlung or latest_einzahlung < entry.datum:
                        latest_einzahlung = entry.datum
                        latest_einzahlung_betrag = entry.betrag
                        latest_einzahlung_verwendungszweck = entry.verwendungszweck
        if latest_einzahlung:
            EinzahlungsLog.objects.create(
                user=self.user,
                konto_last_einzahlung=latest_einzahlung,
                latest_einzahlung_betrag=latest_einzahlung_betrag,
                latest_einzahlung_verwendungszweck=latest_einzahlung_verwendungszweck,
            )
