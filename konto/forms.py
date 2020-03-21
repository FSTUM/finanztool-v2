from django import forms

from .models import EinzahlungsLog


class UploadForm(forms.Form):
    csv_file = forms.FileField(label='CSV Datei')


class MappingConfirmationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.mappings = kwargs.pop('mappings')
        self.user = kwargs.pop('user')

        super(MappingConfirmationForm, self).__init__(*args, **kwargs)

        for entry in self.mappings:
            key = self._get_key(entry)
            if key:
                self.fields[key] = forms.BooleanField(required=False)

    def _get_key(self, entry):
        if entry.mapped_mahnung:
            return 'ma_{}'.format(entry.mapped_mahnung.pk)
        elif entry.mapped_rechnung:
            return 're_{}'.format(entry.mapped_rechnung.pk)
        elif entry.mapped_user:
            return 'us_{}'.format(entry.mapped_user.pk)

    def save(self):
        latest_einzahlung = None
        for entry in self.mappings:
            key = self._get_key(entry)
            if key and self.cleaned_data[key]:
                if entry.mapped_mahnung:
                    entry.mapped_mahnung.bezahlen()
                elif entry.mapped_rechnung:
                    entry.mapped_rechnung.bezahlen()
                elif entry.mapped_user:
                    entry.mapped_user.einzahlen(entry.betrag, self.user)
                    if not latest_einzahlung or latest_einzahlung < entry.datum:
                        latest_einzahlung = entry.datum
        if latest_einzahlung:
            EinzahlungsLog.objects.create(
                user=self.user,
                timestamp=latest_einzahlung,
            )
