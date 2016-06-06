from django import forms
from django.core.exceptions import ValidationError

from .models import Kunde
from .models import Rechnung
from .models import Kategorie

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

class RechnungForm(forms.ModelForm):
    class Meta:
        model = Rechnung
        fields = (
                'rnr',
                'name',
                'rdatum',
                'ldatum',
                'gestellt',
                'ersteller',
                'kunde',
                'einleitung',
                'kategorie',
                )

class KategorieForm(forms.ModelForm):
    class Meta:
        model = Kategorie
        fields = (
                'name',
                )
