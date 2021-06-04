from typing import List

from django import forms

from common.models import Mail, QRCode, Settings


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude: List[str] = []


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        exclude: List[str] = []


class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        exclude: List[str] = ["qr_code"]
