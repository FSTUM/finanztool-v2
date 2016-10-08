from django import forms

class UploadForm(forms.Form):
    csv_file = forms.FileField(label='CSV Datei')

class MappingConfirmationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.mappings = kwargs.pop('mappings')

        super(MappingConfirmationForm, self).__init__(*args, **kwargs)

        for entry in self.mappings:
            key = self._get_key(entry)
            self.fields[key] = forms.BooleanField(required=False)

    def _get_key(self, entry):
        if entry.mapped_mahnung:
            return 'ma_{}'.format(entry.mapped_mahnung.pk)
        elif entry.mapped_rechnung:
            return 're_{}'.format(entry.mapped_rechnung.pk)

    def save(self):
        for entry in self.mappings:
            key = self._get_key(entry)
            if self.cleaned_data[key]:
                if entry.mapped_mahnung:
                    entry.mapped_mahnung.erledigt = True
                    entry.mapped_mahnung.save()
                elif entry.mapped_rechnung:
                    entry.mapped_rechnung.bezahlt = True
                    entry.mapped_rechnung.save()
