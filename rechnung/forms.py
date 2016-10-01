from django import forms
from django.db.models import Q

from .models import Kunde
from .models import Rechnung
from .models import Posten
from .models import User
from .models import Kategorie


class RechnungForm(forms.ModelForm):
    class Meta:
        model = Rechnung
        help_texts = {
                'name': 'Nur für uns, wird nicht nach außen gezeigt.',
                'fdatum': 'default: +15 Tage',
                'kunde': 'Falls noch nicht angelegt, in neuem Tab anlegen und \
                          dieses Formular neu laden, Daten bleiben erhalten.',
                'einleitung': 'Beispiel: für X stellen wir Ihnen hiermit \
                               folgende Posten in Rechnung:',
                }
        widgets = {
                'rdatum': forms.DateInput(attrs={
                                                'id': 'pick_rdatum',
                                                }),
                'fdatum': forms.DateInput(attrs={
                                                'id': 'pick_fdatum',
                                                }),
                'ldatum': forms.DateInput(attrs={
                                                'id': 'pick_ldatum',
                                                })
                }
        fields = (
                'rnr',
                'name',
                'rdatum',
                'fdatum',
                'ldatum',
                'ersteller',
                'kunde',
                'einleitung',
                'kategorie',
                'gestellt',
                'bezahlt',
                )

    def __init__(self, *args, **kwargs):
        super(RechnungForm, self).__init__(*args, **kwargs)

        users = User.objects.all()
        self.fields['ersteller'].choices = [(user.pk, user.get_short_name())
                                            for user in users]
        kategorien = Kategorie.objects.exclude(name='Test'). \
            exclude(name='test')
        self.fields['kategorie'].queryset = kategorien
        kunden = Kunde.objects.exclude(name__contains='Test'). \
            exclude(organisation__contains='Test').order_by('-knr')
        self.fields['kunde'].queryset = kunden

        self.fields.pop('rnr')
        self.fields.pop('bezahlt')
        if self.instance.gestellt:
            self.fields.pop('rdatum')
            self.fields.pop('fdatum')
            self.fields.pop('ldatum')
            self.fields.pop('ersteller')
            self.fields.pop('einleitung')
            self.fields.pop('gestellt')

            if self.instance.bezahlt:
                self.fields.pop('kunde')


class RechnungBezahltForm(forms.Form):
    rechnungbezahlt = forms.BooleanField(label='', required=True)


class PostenForm(forms.ModelForm):
    class Meta:
        model = Posten
        help_texts = {
                'mwst': 'Druck, Vereinszweck: 7%',
                }
        fields = (
                'name',
                'einzelpreis',
                'mwst',
                'anzahl',
                )

    def __init__(self, *args, **kwargs):
        super(PostenForm, self).__init__(*args, **kwargs)
#        self._meta.get_fields['name'].widget.attrs.update({'autofocus': ''})
#        if self.instance.rechnung.gestellt:
#            self.fields.pop('einzelpreis')


class KundeForm(forms.ModelForm):
    class Meta:
        model = Kunde
        help_texts = {
                'kommentar': 'Nur für uns, wird nicht nach außen gezeigt.',
                }
        fields = (
                'knr',
                'organisation',
                'suborganisation',
                'anrede',
                'titel',
                'name',
                'vorname',
                'strasse',
                'plz',
                'stadt',
                'land',
                'kommentar',
                )

    def __init__(self, *args, **kwargs):
        super(KundeForm, self).__init__(*args, **kwargs)
        self.kunde_verwendet = False
        if self.instance.knr:
            self.kunde_verwendet = Rechnung.objects.filter(
                                   gestellt=True, kunde=self.instance).exists()
            if self.kunde_verwendet:
                self.fields.pop('organisation')
                self.fields.pop('suborganisation')
                self.fields.pop('anrede')
                self.fields.pop('name')
                self.fields.pop('vorname')
                self.fields.pop('strasse')
                self.fields.pop('plz')
                self.fields.pop('stadt')

        self.fields.pop('knr')


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
                                       Q(kunde__kommentar__icontains=p)). \
            order_by('-rnr')
        return data


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
                                    Q(stadt__icontains=p)).order_by('-knr')
        return data
