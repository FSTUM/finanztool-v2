from typing import List

from django import forms

from .models import Key, KeyType, Person


class SelectPersonForm(forms.Form):
    person = forms.ModelChoiceField(
        label="Entleiher*in",
        queryset=Person.objects.all().order_by("name", "firstname"),
    )


class SaveKeyChangeForm(forms.Form):
    keytype = forms.ModelChoiceField(
        label="Neuer Schlüssel-Typ",
        queryset=KeyType.objects.filter(keycard=True).order_by("name"),
    )

    comment = forms.CharField(
        label="Kommentar",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        keytype = kwargs.pop("keytype")
        super().__init__(*args, **kwargs)
        self.fields["keytype"].queryset = (
            KeyType.objects.filter(
                keycard=True,
            )
            .exclude(pk=keytype.pk)
            .order_by("name")
        )


class KeyForm(forms.ModelForm):
    class Meta:
        model = Key
        exclude = ("person",)


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = "__all__"


class FilterKeysForm(forms.Form):
    given = forms.BooleanField(
        label="ausgegeben",
        required=False,
    )
    given.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"

    free = forms.BooleanField(
        label="verfügbar",
        required=False,
    )
    free.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"

    active = forms.BooleanField(
        label="aktiv",
        required=False,
        initial=True,
    )
    active.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"

    keytype = forms.ModelChoiceField(
        label="Art",
        queryset=KeyType.objects.all().order_by("name"),
        required=False,
    )
    keytype.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"


class FilterPersonsForm(forms.Form):
    search = forms.CharField(
        label="Suchbegriff",
        required=False,
    )
    search.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"


class KeyTypeForm(forms.ModelForm):
    class Meta:
        model = KeyType
        exclude: List[str] = []
