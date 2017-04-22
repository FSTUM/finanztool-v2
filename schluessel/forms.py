from django import forms

from .models import Key, KeyType, Person


class SelectPersonForm(forms.Form):
    person_label = forms.CharField(
            label="Entleiher",
            widget=forms.TextInput(attrs={'size': 80}))
    person = forms.CharField(widget=forms.HiddenInput(), required=False)


class SelectPersonFormNoscript(forms.Form):
    person = forms.ModelChoiceField(
        label="Entleiher",
        queryset=Person.objects.all(),
    )


class KeyForm(forms.ModelForm):
    class Meta:
        model = Key
        exclude = ('person',)


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = '__all__'


class FilterKeysForm(forms.Form):
    search = forms.CharField(
        label="Suchbegriff",
        required=False,
    )
    search.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    given = forms.BooleanField(
        label="Ausgegeben",
        required=False,
    )
    given.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    free = forms.BooleanField(
        label="Verfügbar",
        required=False,
    )
    free.widget.attrs["onchange"]="document.getElementById('filterform').submit()"

    keytype = forms.ModelChoiceField(
        label="Art",
        queryset=KeyType.objects.all(),
        required=False,
    )
    keytype.widget.attrs["onchange"]="document.getElementById('filterform').submit()"


class FilterPersonsForm(forms.Form):
    search = forms.CharField(
        label="Suchbegriff",
        required=False,
    )
    search.widget.attrs["onchange"]="document.getElementById('filterform').submit()"
