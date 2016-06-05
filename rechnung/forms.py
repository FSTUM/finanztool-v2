from django import forms
from django.core.exceptions import ValidationError

from .models import Kunde

class KundeForm(forms.ModelForm):
    class Meta:
        model = Kunde
        fields = (
                'knr',
                'organisation',
                'suborganisation',
                'anrede',
                'name',
                'vorname',
                'strasse',
                'plz',
                'stadt',
                'kommentar',
                )
