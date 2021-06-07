import os

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.dispatch import receiver

from common.models import QRCode


class EinzahlungsLog(models.Model):
    user = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.CASCADE)
    konto_einlesen = models.DateTimeField(auto_now_add=True)
    konto_last_einzahlung = models.DateField(blank=True, null=True)

    # odly specific, but this is the standard..
    latest_einzahlung_verwendungszweck = models.CharField(max_length=378, blank=True, null=True)

    latest_einzahlung_betrag = models.DecimalField(decimal_places=6, max_digits=20, blank=True, null=True)

    def __str__(self):
        return (
            f"{self.konto_einlesen} durch {self.user}. "
            f"Die letzte Einzahlung war {self.latest_einzahlung_verwendungszweck} ({self.latest_einzahlung_betrag}€) "
            f"vom {self.konto_last_einzahlung or '?'}"
        )


class Referent(models.Model):
    _beverage_cnt_validators = [
        MaxValueValidator(20),
        MinValueValidator(0),
    ]
    allowed_free_beverages = models.IntegerField(
        default=10,
        validators=_beverage_cnt_validators,
        verbose_name="Anzahl an Freigetränke, die diesem Referenten zustehen",
    )
    taken_free_beverages = models.IntegerField(
        default=0,
        validators=_beverage_cnt_validators,
        verbose_name="Anzahl an Freigetränke, die dieser Referenten sachon getrunken hat",
    )
    counter_image = models.ImageField(
        null=True,
        blank=True,
        upload_to="bevarage_counter_image",
        verbose_name="Name wird als hintergrund für die statistik genommen, wie viele "
        "Getränke man schon getrunken hat",
    )
    referenten_name = models.CharField(max_length=40, default="Rick Sanchez", verbose_name="Name des/der Referent*in")

    def __str__(self):
        return f"{self.referenten_name}: {self.taken_free_beverages}/{self.allowed_free_beverages}"

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        if not self.counter_image:
            replacement_image = QRCode.objects.get(pk=0)
            if replacement_image.qr_code:
                new_file = ContentFile(content=replacement_image.qr_code.read(), name=replacement_image.qr_code.name)
                self.counter_image = new_file
        super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=Referent)
def auto_del_qr_code_on_delete(sender, instance, **_kwargs):
    """
    Deletes file from filesystem
    when corresponding `QRCode` object is deleted.
    """
    _ = sender  # sender is needed, for api. it cannot be renamed, but is unused here.
    if instance.counter_image and os.path.isfile(instance.qr_code.path):
        os.remove(instance.qr_code.path)
