from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.contrib.auth import get_user_model

from common.models import Settings

from .models import Aufgabe, Aufgabenart


class ShoppingcartForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields: list[str] = ["officediscount_shoppingcart"]


class AufgabeForm(forms.ModelForm):
    class Meta:
        model = Aufgabe
        help_texts = {
            "name": "Beispiel: impulsiv Anzeigenauftrag",
            "zusatz": "z. B. impulsiv Anzeige -> Ausgabe 123",
            "bearbeiter": 'Zuordnung einer Aufgabe über "Wer soll sie erledigen?" Falls jemand anderes übernimmt wird '
            "es nachvollziehbar mit diesem Feld.",
            "text": "Raum für alle möglichen Anmerkungen",
        }
        widgets = {
            "frist": DatePickerInput(format="%d.%m.%Y"),
        }
        fields = (
            "art",
            "zusatz",
            "frist",
            "zustaendig",
            "bearbeiter",
            "jahr",
            "semester",
            "text",
            "erledigt",
            "attachment",
        )
        localized_fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        users = get_user_model().objects.all()
        self.fields["zustaendig"].choices = [(user.pk, user.get_short_name()) for user in users]
        self.fields["bearbeiter"].choices = [(user.pk, user.get_short_name()) for user in users]
        if self.instance.pk:
            self.fields.pop("zustaendig")
        else:
            self.fields.pop("bearbeiter")
        if self.instance.erledigt:
            self.fields.pop("art")
            self.fields.pop("zusatz")
            self.fields.pop("frist")
            self.fields.pop("jahr")
            self.fields.pop("semester")
            self.fields.pop("erledigt")


class AufgabenartForm(forms.ModelForm):
    class Meta:
        model = Aufgabenart
        help_texts = {
            "name": "Überdefinition einer Aufgabe, z.B. Umfrageabrechnung",
        }
        fields = ("name",)
        localized_fields = "__all__"


class AufgabeErledigtForm(forms.Form):
    aufgabeerledigt = forms.BooleanField(label="", required=True)
