from django import forms
from django.db.models import Q

from .models import Kategorie, Kunde, Mahnung, Posten, Rechnung, User


class RechnungForm(forms.ModelForm):
    class Meta:
        model = Rechnung
        help_texts = {
            "name": "Nur für uns, wird nicht nach außen gezeigt.",
            "fdatum": "default: +15 Tage",
            "kunde": "Falls noch nicht angelegt, in neuem Tab anlegen und"
            "dieses Formular neu laden, Daten bleiben erhalten.",
            "einleitung": "Beispiel: für X stellen wir Ihnen hiermit " "folgende Posten in Rechnung:",
        }
        widgets = {
            "rdatum": forms.DateInput(
                attrs={
                    "id": "pick_rdatum",
                },
            ),
            "fdatum": forms.DateInput(
                attrs={
                    "id": "pick_fdatum",
                },
            ),
            "ldatum": forms.DateInput(
                attrs={
                    "id": "pick_ldatum",
                },
            ),
        }
        fields = (
            "rnr",
            "name",
            "rdatum",
            "fdatum",
            "ldatum",
            "ersteller",
            "kunde",
            "einleitung",
            "kategorie",
            "gestellt",
            "bezahlt",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        users = User.objects.all()
        self.fields["ersteller"].choices = [(user.pk, user.get_short_name()) for user in users]
        kategorien = Kategorie.objects.exclude(name="Test").exclude(name="test")
        self.fields["kategorie"].queryset = kategorien
        kunden = Kunde.objects.exclude(name__contains="Test").exclude(organisation__contains="Test").order_by("-knr")
        self.fields["kunde"].queryset = kunden

        self.fields.pop("rnr")
        self.fields.pop("bezahlt")
        if self.instance.gestellt:
            self.fields.pop("rdatum")
            self.fields.pop("fdatum")
            self.fields.pop("ldatum")
            self.fields.pop("ersteller")
            self.fields.pop("einleitung")
            self.fields.pop("gestellt")

            if self.instance.erledigt:
                self.fields.pop("kunde")


class RechnungBezahltForm(forms.Form):
    rechnungbezahlt = forms.BooleanField(label="", required=True)


class MahnungForm(forms.ModelForm):
    class Meta:
        model = Mahnung
        help_texts = {
            "gebuehr": "Bei uns üblich: Bei der 2. Mahnung und allen " "danach 5 € erheben.",
            "mfdatum": "default: +15 Tage",
            "bezahlt": "Markiert diese Mahnungen und die " "Originalrechnung als bezahlt/erledigt.",
            "einleitung": "Beispiel 1. Mahnung: nachstehend aufgeführte "
            "Positionen führen wir noch ohne Ausgleich. "
            "Beispiel 2. Mahnung: nachstehend aufgeführte "
            "Positionen führen wir trotz bereits durch "
            "unsere Schreiben vom 2. und 17. Januar 2016 "
            "erfolgter Mahnungen noch ohne Ausgleich.",
            "gerichtlich": "Wird bei uns in der Regel in der 3. Mahnung " "angedroht.",
        }
        widgets = {
            "mdatum": forms.DateInput(
                attrs={
                    "id": "pick_mdatum",
                },
            ),
            "mfdatum": forms.DateInput(
                attrs={
                    "id": "pick_mfdatum",
                },
            ),
        }
        fields = (
            "wievielte",
            "gebuehr",
            "mdatum",
            "mfdatum",
            "geschickt",
            "bezahlt",
            "ersteller",
            "einleitung",
            "gerichtlich",
        )

    def __init__(self, *args, **kwargs):
        self.rechnung = kwargs.pop("rechnung")
        super().__init__(*args, **kwargs)

        users = User.objects.all()
        self.fields["ersteller"].choices = [(user.pk, user.get_short_name()) for user in users]

        self.fields.pop("wievielte")
        self.fields.pop("bezahlt")
        if self.rechnung.erledigt or self.instance.geschickt:
            self.fields.pop("gebuehr")
            self.fields.pop("mdatum")
            self.fields.pop("mfdatum")
            self.fields.pop("geschickt")
            self.fields.pop("ersteller")
            self.fields.pop("einleitung")
            self.fields.pop("gerichtlich")

    def save(self, commit=True):
        instance = super().save(False)

        instance.rechnung = self.rechnung

        if commit:
            instance.save()

        return instance


class MahnungStatusForm(forms.Form):
    mahnungstatus = forms.BooleanField(label="", required=True)


class PostenForm(forms.ModelForm):
    class Meta:
        model = Posten
        help_texts = {
            "mwst": "Druck, Vereinszweck: 7%",
        }
        fields = (
            "name",
            "einzelpreis",
            "mwst",
            "anzahl",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


#        self._meta.get_fields['name'].widget.attrs.update({'autofocus': ''})
#        if self.instance.rechnung.gestellt:
#            self.fields.pop('einzelpreis')


class KundeForm(forms.ModelForm):
    class Meta:
        model = Kunde
        help_texts = {
            "kommentar": "Nur für uns, wird nicht nach außen gezeigt.",
        }
        fields = (
            "knr",
            "organisation",
            "suborganisation",
            "anrede",
            "titel",
            "name",
            "vorname",
            "strasse",
            "plz",
            "stadt",
            "land",
            "kommentar",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kunde_verwendet = False
        if self.instance.knr:
            self.kunde_verwendet = Rechnung.objects.filter(
                gestellt=True,
                kunde=self.instance,
            ).exists()
            if self.kunde_verwendet:
                self.fields.pop("organisation")
                self.fields.pop("suborganisation")
                self.fields.pop("anrede")
                self.fields.pop("name")
                self.fields.pop("titel")
                self.fields.pop("vorname")
                self.fields.pop("strasse")
                self.fields.pop("plz")
                self.fields.pop("stadt")
                self.fields.pop("land")

        self.fields.pop("knr")


class RechnungSuchenForm(forms.Form):
    pattern = forms.CharField(
        min_length=2,
        max_length=100,
        label=("Suche"),
    )

    def get(self):
        pattern = self.cleaned_data["pattern"]

        return Rechnung.objects.filter(
            Q(name__icontains=pattern)
            | Q(rnr__icontains=pattern)
            | Q(einleitung__icontains=pattern)
            | Q(kategorie__name__icontains=pattern)
            | Q(kunde__knr__icontains=pattern)
            | Q(kunde__organisation__icontains=pattern)
            | Q(kunde__suborganisation__icontains=pattern)
            | Q(kunde__name__icontains=pattern)
            | Q(kunde__vorname__icontains=pattern)
            | Q(kunde__strasse__icontains=pattern)
            | Q(kunde__stadt__icontains=pattern)
            | Q(kunde__kommentar__icontains=pattern),
        ).order_by("-rnr")


class KundeSuchenForm(forms.Form):
    pattern = forms.CharField(
        min_length=2,
        max_length=100,
        label=("Suche"),
    )

    def get(self):
        pattern = self.cleaned_data["pattern"]

        return Kunde.objects.filter(
            Q(vorname__icontains=pattern)
            | Q(knr__icontains=pattern)
            | Q(name__icontains=pattern)
            | Q(organisation__icontains=pattern)
            | Q(suborganisation__icontains=pattern)
            | Q(kommentar__icontains=pattern)
            | Q(strasse__icontains=pattern)
            | Q(stadt__icontains=pattern),
        ).order_by("-knr")
