from django.db import models
from django.contrib.auth.models import User


class Person(models.Model):
    name = models.CharField(
        verbose_name="Nachname",
        max_length=200,
    )

    firstname = models.CharField(
        verbose_name="Vorname",
        max_length=200,
    )

    email = models.EmailField(
        "E-Mail",
    )

    address = models.CharField(
        verbose_name="Straße + Hausnummer",
        max_length=200,
    )

    plz = models.CharField(
        verbose_name="PLZ",
        max_length=20,
    )

    city = models.CharField(
        verbose_name="Ort",
        max_length=200,
    )

    mobile = models.CharField(
        verbose_name="Mobil",
        max_length=200,
    )

    phone = models.CharField(
        verbose_name="Telefon",
        max_length=200,
        blank=True,
    )

    def __str__(self):
        return "{} {}".format(self.firstname, self.name)


class KeyType(models.Model):
    shortname = models.CharField(
        verbose_name="Kurzname",
        max_length=20,
        unique=True,
    )

    name = models.CharField(
        verbose_name="Name",
        max_length=200,
    )

    deposit = models.FloatField(
        verbose_name="Kaution",
    )

    keycard = models.BooleanField(
        verbose_name="Schließkarte",
        default=False,
    )

    def __str__(self):
        return self.name


class Key(models.Model):
    keytype = models.ForeignKey(
        KeyType,
        verbose_name="Schlüssel-Typ",
        on_delete=models.CASCADE,
    )

    number = models.IntegerField(
        verbose_name="Nummer",
    )

    person = models.ForeignKey(
        Person,
        verbose_name="Entleiher",
        default=None,
        blank=True,
        null=True,
    )

    comment = models.CharField(
        verbose_name="Kommentar",
        max_length=500,
        blank=True,
    )

    @property
    def typename(self):
        if self.keytype.keycard:
            return "Schließkarte"
        else:
            return "Schlüssel"

    def __str__(self):
        return "{} {}".format(self.keytype.shortname, self.number)


class KeyLogEntry(models.Model):
    GIVE="G"
    RETURN="R"
    CREATE="C"

    key = models.ForeignKey(
        Key,
        verbose_name="Schlüssel",
        on_delete=models.CASCADE,
    )

    person = models.ForeignKey(
        Person,
        verbose_name="Entleiher",
        blank=True,
        null=True,
    )

    operation = models.CharField(
        max_length=1,
        verbose_name="Vorgang",
        choices=(
            (GIVE, "Ausgabe"),
            (RETURN, "Rückgabe"),
            (CREATE, "Erstellung"),
        ),
    )

    user = models.ForeignKey(
        User,
        verbose_name="Finanzer",
    )

    date = models.DateTimeField(
        verbose_name="Datum",
        auto_now_add=True,
    )

    def __str__(self):
        if self.operation == KeyLogEntry.GIVE:
            return "Ausgabe von {} an {} durch {} am {}".format(self.key,
                    self.person, self.user.get_full_name(), self.date)
        elif self.operation == KeyLogEntry.RETURN:
            return "Rückgabe von {} von {} an {} am {}".format(self.key,
                    self.person, self.user.get_full_name(), self.date)
        elif self.operation == KeyLogEntry.CREATE:
            return "Erstellung von {} durch {} am {}".format(self.key,
                    self.user.get_full_name(), self.date)
        else:
            return "Unvalid Operation"

