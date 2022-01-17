from django import forms

from common.models import Mail, QRCode, Settings


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        exclude: list[str] = []
        localized_fields = "__all__"


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        exclude: list[str] = ["officediscount_shoppingcart"]
        localized_fields = "__all__"


class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        exclude: list[str] = ["qr_code"]
        localized_fields = "__all__"
