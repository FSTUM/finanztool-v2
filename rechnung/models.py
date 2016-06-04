import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from datetime import date
from decimal import Decimal

# Create your models here.
class Rechnung(models.Model):
    name = models.CharField(
            verbose_name='Zweck der Rechnung',
            max_length=50,
            null=True,
            blank=True,
            )
    rnr = models.IntegerField(
            verbose_name='Rechnungsnummer',
            unique=True,
            )
    rdatum = models.DateField(
            verbose_name='Rechnungsdatum',
            default=date.today,
            )
    ldatum = models.DateField(
            verbose_name='Lieferdatum',
            default=date.today,
            null=True,
            blank=True,
            )
    gestellt = models.BooleanField(
            verbose_name='Rechnung gestellt?',
            )
    ersteller = models.ForeignKey(
            User,
            )
    kunde = models.ForeignKey(
            'Kunde',
            )
    einleitung = models.TextField(
            verbose_name='Einleitender Text nach "Sehr geehrte..."',
            max_length=1000,
            )
    posten = models.ManyToManyField(
            'Posten',
            through="AnzahlPosten",
            )
    kategorie = models.ForeignKey(
            'Kategorie',
            )

    def __str__(self):
        return "RE {} ({})".format(self.rnr, self.name)

    @property
    def zwischensumme(self):
        summe = Decimal(0)
        for posten in self.anzahlposten_set.all():
            summe = summe + posten.summenetto
        return Decimal(round(summe,2))

    @property
    def gesamtsumme(self):
        summe = Decimal(0)
        for posten in self.anzahlposten_set.all():
            summe = summe + posten.summebrutto
        return Decimal(round(summe,2))

    def wurde_vor_kurzem_gestellt(self):
        return self.rdatum >= timezone.now() - datetime.timedelta(days=16)

class Kunde(models.Model):
    knr = models.IntegerField(
            verbose_name='Kundennummer',
            unique=True,
            )
    organisation = models.CharField(
            verbose_name='Organisation',
            max_length=100,
            null=True,
            blank=True,
            )
    suborganisation = models.TextField(
            verbose_name='SubOrganisation',
            max_length=500,
            null=True,
            blank=True,
            )
    GESCHLECHT = (
            ('w' , 'Frau'),
            ('m' , 'Herr'),
    )
    anrede = models.CharField(
            verbose_name='Anrede',
            max_length=5,
            choices=GESCHLECHT,
            null=True,
            blank=True,
            )
    name = models.CharField(
            verbose_name='Nachname',
            max_length=50,
            null=True,
            blank=True,
            )
    vorname = models.CharField(
            verbose_name='Vorname',
            max_length=50,
            null=True,
            blank=True,
            )
    strasse = models.CharField(
            verbose_name='Straße',
            max_length=100,
            )
    plz = models.CharField(
            verbose_name='PLZ',
            max_length=20,
            )
    stadt = models.CharField(
            verbose_name='Stadt',
            max_length=200,
            )
    kommentar = models.TextField(
            verbose_name='Kommentar',
            max_length=1000,
            null=True,
            blank=True,
            )
    def __str__(self):
        return "{}: {} ({})".format(self.knr, self.name, self.organisation)

class Kategorie(models.Model):
    name = models.CharField(
            verbose_name='Kategorie',
            max_length=100,
            unique=True,
            )
    def __str__(self):
        return self.name

class Posten(models.Model):
    name = models.CharField(
            verbose_name='Bezeichnung',
            max_length=100,
            )
    einzelpreis = models.DecimalField(
            verbose_name='Einzelpreis',
            decimal_places=6,
            max_digits=20,
            )
    MWSTSATZ = (
            (0 , '0 %'),
            (7 , '7 %'),
            (19 , '19 %'),
            )
    mwst = models.IntegerField(
            verbose_name='Mehrwertsteuersatz',
            choices=MWSTSATZ,
            default = 19,
            )

    @property
    def get_mwst(self):
        return Decimal(int(self.mwst)) / Decimal(100)

    def __str__(self):
        return self.name

class AnzahlPosten(models.Model):
    class Meta:
        unique_together = (
                'posten',
                'rechnung',
                )
    posten = models.ForeignKey(
            'Posten',
            )
    rechnung = models.ForeignKey(
            'Rechnung',
            )
    anzahl = models.IntegerField(
            verbose_name='Anzahl',
            default=1,
            )

    @property
    def summenetto(self):
        summe = self.anzahl * self.posten.einzelpreis
        return Decimal(round(summe,2))

    @property
    def summebrutto(self):
        summe= self.summenetto * (1+self.posten.get_mwst)
        return Decimal(round(summe,2))

    def __str__(self):
        return "{}: {} ({}x)".format(self.rechnung, self.posten, self.anzahl)

