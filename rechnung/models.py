import os
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import qrcode
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max
from django.dispatch import receiver
from django.http import Http404
from django.utils import timezone
from PIL import Image, ImageDraw

from common.models import Settings


def get_faelligkeit_default():
    return date.today() + timedelta(days=15)


def get_new_highest_rnr():
    if Rechnung.objects.all().count() == 0:
        return 1
    return (Rechnung.objects.all().aggregate(Max("rnr"))["rnr__max"]) + 1


def get_new_highest_knr():
    if Kunde.objects.all().count() == 0:
        return 1
    return Kunde.objects.all().aggregate(Max("knr"))["knr__max"] + 1


class Rechnung(models.Model):
    class Meta:
        verbose_name_plural = "Rechnungen"

    name = models.CharField(
        verbose_name="Zweck der Rechnung",
        max_length=50,
        null=True,
        blank=True,
    )
    rnr = models.IntegerField(
        verbose_name="Rechnungsnummer *",
        default=get_new_highest_rnr,
        unique=True,
    )
    rdatum = models.DateField(
        verbose_name="Rechnungsdatum *",
        default=date.today,
    )
    ldatum = models.DateField(
        verbose_name="Lieferdatum",
        default=date.today,
        null=True,
        blank=True,
    )
    fdatum = models.DateField(
        verbose_name="Fälligkeitsdatum *",
        default=get_faelligkeit_default,
    )
    gestellt = models.BooleanField(
        verbose_name="Rechnung gestellt?",
        default=False,
    )
    bezahlt = models.BooleanField(
        verbose_name="Rechnung beglichen?",
        default=False,
    )
    erledigt = models.BooleanField(
        verbose_name="Rechnung erledigt, eventuell durch Mahnung",
        default=False,
    )
    ersteller = models.ForeignKey(
        get_user_model(),
        models.CASCADE,
    )
    kunde = models.ForeignKey(
        "Kunde",
        models.CASCADE,
    )
    einleitung = models.TextField(
        verbose_name='Einleitender Text nach "Sehr geehrte..." *',
        max_length=1000,
    )
    kategorie = models.ForeignKey(
        "Kategorie",
        models.CASCADE,
    )
    epc_qr_code = models.ImageField(upload_to="epc_qr_code", blank=True)

    def __str__(self):
        if self.name:
            return f"{self.rnr_string} ({self.name})"
        return self.rnr_string

    @property
    def rnr_string(self) -> str:
        return f"RE{self.rnr:05}"

    @property
    def _at_04_amount(self) -> str:
        """AT-04 Amount of the Credit Transfer in Euro
        Amount must be 0.01 or more and 999999999.99 or less"""
        gesamtsumme = self.gesamtsumme
        if gesamtsumme < Decimal(0.01):
            raise Http404("AT-04 Amount of the Credit Transfer in Euro must be EUR0.01 or more")
        if gesamtsumme > Decimal(999999999.99):
            raise Http404("AT-04 Amount of the Credit Transfer in Euro must be EUR999999999.99 or less")

        return f"EUR{gesamtsumme}"

    @property
    def _epc_qr_code_content(self):
        settings = Settings.load()
        content = [
            "BCD",  # Service Tag
            "002",  # Version
            "1",  # Encoding UTF-8
            "SCT",  # Identification code: Sepa Credit Transfer
            settings.at_23_bic,  # AT-23 BIC of the Beneficiary Bank
            # for SEPA payment transactions involving nonEEA countries.
            settings.at_21_name,  # AT-21 Name of the Beneficiary
            settings.at_20_iban,  # AT-20 Account number of the Beneficiary. Only IBAN is allowed.
            self._at_04_amount,  # AT-20 Account number of the Beneficiary. Only IBAN is allowed.
            settings.at_44_purpose,  # AT-44 Purpose of the Credit Transfer
            settings.at_05_remittance_information,  # AT-05 Remittance Information (Structured) Creditor Reference
            # (ISO 11649 RF Creditor Reference may be used)
            self.rnr_string,  # "Verwendungszweck", unstructured text
            f"Fälligkeitsdatum: {self.fdatum.strftime('%d.%m.%Y')}",  # Beneficiary to originator information
        ]
        return "\n".join(content)

    @property
    def zwischensumme(self):
        summe = Decimal(0)
        for posten in self.posten_set.all():
            summe = summe + posten.summenetto
        return Decimal(round(summe, 2))

    @property
    def summe_mwst_7(self):
        summe = Decimal(0)
        for posten in self.posten_set.filter(mwst=7):
            summe = summe + (posten.summenetto * Decimal(0.07))
        return Decimal(round(summe, 2))

    @property
    def summe_mwst_19(self):
        summe = Decimal(0)
        for posten in self.posten_set.filter(mwst=19):
            summe = summe + (posten.summenetto * Decimal(0.19))
        return Decimal(round(summe, 2))

    @property
    def gesamtsumme(self):
        """Gesamtsumme der Rechnung inkl. MwSt.
        (zwischensumme + summe_mwst_7 + summe_mwst_19)"""
        summe = Decimal(self.zwischensumme + self.summe_mwst_7 + self.summe_mwst_19)
        return Decimal(round(summe, 2))

    @property
    def mahnungen(self):
        return self.mahnung_set.order_by("wievielte")

    def wurde_vor_kurzem_gestellt(self):
        return self.rdatum >= timezone.now() - timedelta(days=16)

    @property
    def faellig(self):
        return self.fdatum < date.today()

    def bezahlen(self):
        self.bezahlt = True
        self.erledigt = True
        self.save()

    def regen_epc_qr_code(self):
        qr_code = qrcode.QRCode(
            # version=13,  # max version according to epc spec
            error_correction=qrcode.constants.ERROR_CORRECT_M,
        )
        qr_code.add_data(self._epc_qr_code_content)
        qr_code.make(fit=True)
        qr_image = qr_code.make_image(fill_color="black", back_color="white")
        with Image.new("RGB", (qr_image.pixel_size, qr_image.pixel_size), "white") as canvas:
            canvas.paste(qr_image)

            # add a rounded rectangle to make it more obvious, that the code should be scanned
            draw = ImageDraw.Draw(canvas)
            draw.rounded_rectangle(((0, 0), canvas.size), radius=50, outline="black", width=15)

            buffer = BytesIO()
            if not self.epc_qr_code:
                canvas.save(buffer, "PNG")
                self.epc_qr_code.save(f"qr_code_{self.rnr_string}.png", File(buffer), save=False)
                self.save()
            else:
                canvas.save(self.epc_qr_code.path)


@receiver(models.signals.post_save, sender=Rechnung)
def auto_regen_epc_qr_code_on_save(sender, instance, **_kwargs):
    """
    Regenerates the QR-Code, once the corresponding `Rechnung` object is updated.
    """
    _ = sender  # sender is needed, for api. it cannot be renamed, but is unused here.
    if Decimal(0.1) < instance.gesamtsumme < Decimal(999999999.99):
        instance.regen_epc_qr_code()


@receiver(models.signals.post_delete, sender=Rechnung)
def auto_del_epc_qr_code_on_delete(sender, instance, **_kwargs):
    """
    Deletes file from filesystem
    when corresponding `Rechnung` object is deleted.
    """
    _ = sender  # sender is needed, for api. it cannot be renamed, but is unused here.
    if instance.pk and instance.pk != 0 and instance.epc_qr_code and os.path.isfile(instance.epc_qr_code.path):
        os.remove(instance.epc_qr_code.path)


class Mahnung(models.Model):
    rechnung = models.ForeignKey(
        Rechnung,
        on_delete=models.CASCADE,
    )
    wievielte = models.IntegerField(
        verbose_name="Wievielte Mahnung?",
        null=True,
        blank=True,
    )
    gebuehr = models.DecimalField(
        verbose_name="Mahngebühr",
        decimal_places=2,
        max_digits=6,
    )
    mdatum = models.DateField(
        verbose_name="Mahndatum",
        default=date.today,
    )
    mfdatum = models.DateField(
        verbose_name="Neue Fälligkeit",
        default=get_faelligkeit_default,
    )
    geschickt = models.BooleanField(
        verbose_name="Mahnung geschickt?",
        default=False,
    )
    bezahlt = models.BooleanField(
        verbose_name="Rechnung beglichen",
        default=False,
    )
    ersteller = models.ForeignKey(
        get_user_model(),
        models.CASCADE,
    )
    einleitung = models.TextField(
        verbose_name='Einleitender Text nach "Sehr geehrte..." *',
        max_length=3000,
        default="",
    )
    gerichtlich = models.BooleanField(
        verbose_name="Gerichtliche Schritte androhen?",
        default=False,
    )

    # durch addieren von gesamtsumme und gebuehr berechnet
    @property
    def mahnsumme(self):
        if self.wievielte == 1:
            mahnsumme = Decimal(self.rechnung.gesamtsumme + self.gebuehr)
        else:
            letzte_mahnung = Mahnung.objects.get(
                rechnung=self.rechnung,
                wievielte=self.wievielte - 1,
            )
            mahnsumme = Decimal(letzte_mahnung.mahnsumme + self.gebuehr)
        return Decimal(round(mahnsumme, 2))

    def faellig(self):
        return self.mfdatum < date.today()

    def save(self, *args, **kwargs):
        if not self.wievielte:
            mahnungen = Mahnung.objects.filter(rechnung=self.rechnung)
            if mahnungen.exists():
                self.wievielte = (
                    mahnungen.aggregate(
                        Max("wievielte"),
                    )["wievielte__max"]
                    + 1
                )
            else:
                self.wievielte = 1
        super().save(*args, **kwargs)

    def bezahlen(self):
        self.bezahlt = True
        self.save()

        self.rechnung.erledigt = True
        self.rechnung.save()

    def __str__(self):
        return f"{self.rechnung.rnr_string}_{self.rechnung.kunde.knr}_M{self.wievielte}"


class Kunde(models.Model):
    knr = models.IntegerField(
        verbose_name="Kundennummer *",
        default=get_new_highest_knr,
        unique=True,
    )
    organisation = models.CharField(
        verbose_name="Organisation",
        max_length=100,
        null=True,
        blank=True,
    )
    suborganisation = models.TextField(
        verbose_name="SubOrganisation",
        max_length=500,
        null=True,
        blank=True,
    )
    GESCHLECHT = (
        ("w", "Frau"),
        ("m", "Herr"),
    )
    anrede = models.CharField(
        verbose_name="Anrede",
        max_length=5,
        choices=GESCHLECHT,
        null=True,
        blank=True,
    )
    titel = models.CharField(
        verbose_name="Titel",
        max_length=50,
        null=True,
        blank=True,
        default="",
    )
    name = models.CharField(
        verbose_name="Nachname",
        max_length=50,
        null=True,
        blank=True,
    )
    vorname = models.CharField(
        verbose_name="Vorname",
        max_length=50,
        null=True,
        blank=True,
    )
    strasse = models.CharField(
        verbose_name="Straße *",
        max_length=100,
    )
    plz = models.CharField(
        verbose_name="PLZ *",
        max_length=20,
    )
    stadt = models.CharField(
        verbose_name="Stadt *",
        max_length=200,
    )
    land = models.CharField(
        verbose_name="Land *",
        max_length=100,
        default="Deutschland",
    )
    kommentar = models.TextField(
        verbose_name="Kommentar",
        max_length=1000,
        null=True,
        blank=True,
    )

    def __str__(self):
        description = f"{self.knr}: "
        if self.organisation:
            if self.name:
                description += f"{self.organisation} - {self.name}"
            else:
                description += f"{self.organisation}"

        elif self.name:
            if self.vorname:
                description += f"{self.name}, {self.vorname}"
            else:
                description += f"{self.name}"
        if self.kommentar:
            description += f" ({self.kommentar})"
        return description


class Kategorie(models.Model):
    name = models.CharField(
        verbose_name="Kategorie *",
        max_length=100,
        unique=True,
    )

    def __str__(self):
        return self.name


class Posten(models.Model):
    rechnung = models.ForeignKey(
        Rechnung,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Bezeichnung",
        max_length=100,
    )
    einzelpreis = models.DecimalField(
        verbose_name="Einzelpreis",
        decimal_places=5,
        max_digits=15,
        help_text="Einzelpreis ohne MWSt in EUR",
    )
    MWSTSATZ = (
        (0, "0 %"),
        (7, "7 %"),
        (19, "19 %"),
    )
    mwst = models.IntegerField(
        verbose_name="Mehrwertsteuersatz",
        choices=MWSTSATZ,
        default=7,
    )
    anzahl = models.IntegerField(
        verbose_name="Anzahl",
        validators=[MinValueValidator(0)],
        default=1,
    )

    @property
    def get_mwst(self):
        return Decimal(int(self.mwst)) / Decimal(100)

    @property
    def summenetto(self):
        return self.anzahl * self.einzelpreis

    @property
    def summenettogerundet(self):
        return Decimal(round(self.summenetto, 2))

    @property
    def summebrutto(self):
        return self.summenetto * (1 + self.get_mwst)

    def __str__(self):
        return self.name
