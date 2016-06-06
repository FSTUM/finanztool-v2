from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

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

class KundeSuchenForm(forms.Form):
    pattern = forms.CharField(
        min_length=2,
        max_length=100,
        label=("Suche"),
    )

    def get(self):
        p = self.cleaned_data['pattern']

        data = Kunde.objects.filter(Q(vorname__icontains=p) |
                                            Q(knr__icontains=p) |
                                            Q(name__icontains=p) |
                                            Q(organisation__icontains=p) |
                                            Q(suborganisation__icontains=p) |
                                            Q(kommentar__icontains=p) |
                                            Q(strasse__icontains=p) |
                                            Q(stadt__icontains=p))
        return data

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

class RechnungSuchenForm(forms.Form):
    pattern = forms.CharField(
        min_length=2,
        max_length=100,
        label=("Suche"),
    )

    def get(self):
        p = self.cleaned_data['pattern']

        data = Rechnung.objects.filter(Q(name__icontains=p) |
                                            Q(rnr__icontains=p) |
                                            Q(einleitung__icontains=p) |
                                            Q(kategorie__name__icontains=p) |
                                            Q(kunde__knr__icontains=p) |
                                            Q(kunde__organisation__icontains=p) |
                                            Q(kunde__suborganisation__icontains=p) |
                                            Q(kunde__name__icontains=p) |
                                            Q(kunde__vorname__icontains=p) |
                                            Q(kunde__strasse__icontains=p) |
                                            Q(kunde__stadt__icontains=p) |
                                            Q(kunde__kommentar__icontains=p))
        return data

class KategorieForm(forms.ModelForm):
    class Meta:
        model = Kategorie
        fields = (
                'name',
                )
