from typing import List

from django import forms

from common.models import Mail, Settings


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude: List[str] = []


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        exclude: List[str] = []
