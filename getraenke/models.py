import datetime

from django.db import models


class Blacklist(models.Model):
    user = models.TextField(blank=True, null=True)
    grund = models.TextField(blank=True, null=True)
    datum = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'blacklist'


class Getraenke(models.Model):
    nummer = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32, blank=True, null=True)
    barcode = models.TextField(blank=True, null=True)
    preis = models.FloatField(blank=True, null=True)
    shortname = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'getraenke'


class Log(models.Model):
    konto = models.CharField(max_length=32, blank=True, null=True)
    gruppe = models.CharField(max_length=32, blank=True, null=True)
    aktion = models.CharField(max_length=32, blank=True, null=True)
    typ = models.CharField(max_length=32, blank=True, null=True)
    betrag = models.FloatField(blank=True, null=True)
    gesamt_jetzt = models.FloatField(blank=True, null=True)
    user = models.CharField(max_length=32, blank=True, null=True)
    datum = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'log'

    def __str__(self):
        return "{} | {} | {} | {} | {} | {} | {} | {}".format(
            self.konto, self.gruppe, self.aktion, self.typ, self.betrag,
            self.gesamt_jetzt, self.user, self.datum)


class Schulden(models.Model):
    user = models.CharField(unique=True, max_length=32)
    betrag = models.FloatField()

    class Meta:
        managed = False
        db_table = 'schulden'

    def get_einzahlungen(self):
        return Log.objects.filter(konto=self.user, aktion="Einzahlung"
                                  ).order_by('-datum')

    def einzahlen(self, betrag, user):
        self.betrag -= float(betrag)
        self.save()
        log = Log.objects.create(
            konto=self.user,
            aktion="Einzahlung",
            betrag=betrag,
            gesamt_jetzt=self.betrag,
            user=user.username,
            datum=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
