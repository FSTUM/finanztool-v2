from typing import List

from django import forms

from common.models import Mail, QRCode, Settings


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude: List[str] = []
        localized_fields = "__all__"


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        exclude: List[str] = []
        localized_fields = "__all__"


class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        exclude: List[str] = ["qr_code"]
        localized_fields = "__all__"
