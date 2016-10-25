from django import forms

from .models import User
from .models import Aufgabenart
from .models import Aufgabe


class AufgabeForm(forms.ModelForm):
    class Meta:
        model = Aufgabe
        help_texts = {
                'name': 'Beispiel: impulsiv Anzeigenauftrag',
                'zusatz': 'z. B. impulsiv Anzeige -> Ausgabe 123',
                'bearbeiter': 'Zuordnung einer Aufgabe über "Wer soll sie \
                                erledigen?" Falls jemand anderes übernimmt \
                                wird es nachvollziehbar mit diesem Feld.',
                'text': 'Raum für alle möglichen Anmerkungen',
                }
        widgets = {
                'frist': forms.DateInput(attrs={
                                                'id': 'pick_frist',
                                                })
                }
        fields = (
                'art',
                'zusatz',
                'frist',
                'zustaendig',
                'bearbeiter',
                'jahr',
                'semester',
                'text',
                'erledigt',
                )

    def __init__(self, *args, **kwargs):
        super(AufgabeForm, self).__init__(*args, **kwargs)

        users = User.objects.all()
        self.fields['zustaendig'].choices = [(user.pk, user.get_short_name())
                                             for user in users]
        self.fields['bearbeiter'].choices = [(user.pk, user.get_short_name())
                                             for user in users]
        if self.instance.pk:
            self.fields.pop('zustaendig')
        else:
            self.fields.pop('bearbeiter')
        if self.instance.erledigt:
            self.fields.pop('art')
            self.fields.pop('zusatz')
            self.fields.pop('frist')
            self.fields.pop('jahr')
            self.fields.pop('semester')
            self.fields.pop('erledigt')


class AufgabenartForm(forms.ModelForm):
    class Meta:
        model = Aufgabenart
        help_texts = {
                'name': 'Überdefinition einer Aufgabe, z.B. Umfrageabrechnung',
                }
        fields = (
                'name',
                )

        def __init__(self, *args, **kwargs):
            super(AufgabeForm, self).__init__(*args, **kwargs)


class AufgabeErledigtForm(forms.Form):
    aufgabeerledigt = forms.BooleanField(label='', required=True)
