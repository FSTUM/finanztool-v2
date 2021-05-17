from django.contrib.auth.models import User
from django.db import models


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
        return f"{self.firstname} {self.name}"


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
    class Meta:
        unique_together = (("keytype", "number"),)

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
        models.CASCADE,
        verbose_name="Entleiher*in",
        default=None,
        blank=True,
        null=True,
    )

    comment = models.CharField(
        verbose_name="Kommentar",
        max_length=500,
        blank=True,
    )

    active = models.BooleanField(
        verbose_name="Aktiv",
        default=True,
    )

    @property
    def typename(self):
        if self.keytype.keycard:
            return "Schließkarte"
        return "Schlüssel"

    def __str__(self):
        return f"{self.keytype.shortname} {self.number}"


class KeyLogEntry(models.Model):
    GIVE = "G"
    RETURN = "R"
    CREATE = "C"
    EDIT = "E"

    key = models.ForeignKey(
        Key,
        verbose_name="Schlüssel",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    key_deposit = models.FloatField(
        verbose_name="Kaution",
        blank=True,
        null=True,
    )

    key_keytype = models.ForeignKey(
        KeyType,
        verbose_name="Schlüssel-Typ",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    key_number = models.IntegerField(
        verbose_name="Nummer",
        blank=True,
        null=True,
    )

    key_comment = models.CharField(
        verbose_name="Kommentar",
        max_length=500,
        blank=True,
        null=True,
    )

    key_active = models.NullBooleanField(
        verbose_name="Aktiv",
        default=True,
        blank=True,
        null=True,
    )

    person = models.ForeignKey(
        Person,
        models.CASCADE,
        verbose_name="Entleiher*in",
        blank=True,
        null=True,
    )

    person_name = models.CharField(
        verbose_name="Nachname",
        max_length=200,
        blank=True,
        null=True,
    )

    person_firstname = models.CharField(
        verbose_name="Vorname",
        max_length=200,
        blank=True,
        null=True,
    )

    person_email = models.EmailField(
        "E-Mail",
        blank=True,
        null=True,
    )

    person_address = models.CharField(
        verbose_name="Straße + Hausnummer",
        max_length=200,
        blank=True,
        null=True,
    )

    person_plz = models.CharField(
        verbose_name="PLZ",
        max_length=20,
        blank=True,
        null=True,
    )

    person_city = models.CharField(
        verbose_name="Ort",
        max_length=200,
        blank=True,
        null=True,
    )

    person_mobile = models.CharField(
        verbose_name="Mobil",
        max_length=200,
        blank=True,
        null=True,
    )

    person_phone = models.CharField(
        verbose_name="Telefon",
        max_length=200,
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
            (EDIT, "Bearbeitung"),
        ),
    )

    user = models.ForeignKey(
        User,
        models.CASCADE,
        verbose_name="Finanzer*in",
    )

    date = models.DateTimeField(
        verbose_name="Datum",
        auto_now_add=True,
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # Fill some duplicating fields in case original model is deleted:
        if self.key and not self.key_number:
            self.key_deposit = self.key.keytype.deposit
            self.key_keytype = self.key.keytype
            self.key_number = self.key.number
            self.key_comment = self.key.comment
            self.key_active = self.key.active

        if self.person and not self.person_name:
            self.person_name = self.person.name
            self.person_firstname = self.person.firstname
            self.person_email = self.person.email
            self.person_address = self.person.address
            self.person_plz = self.person.plz
            self.person_city = self.person.city
            self.person_mobile = self.person.mobile
            self.person_phone = self.person.phone

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        if self.operation == KeyLogEntry.GIVE:
            return "Ausgabe von {} an {} durch {} am {}".format(
                self.key,
                self.person,
                self.user.get_full_name(),
                self.date,
            )
        elif self.operation == KeyLogEntry.RETURN:
            return "Rückgabe von {} von {} an {} am {}".format(
                self.key,
                self.person,
                self.user.get_full_name(),
                self.date,
            )
        elif self.operation == KeyLogEntry.CREATE and self.key:
            return "Erstellung von {} durch {} am {}".format(
                self.key,
                self.user.get_full_name(),
                self.date,
            )
        elif self.operation == KeyLogEntry.CREATE and self.person:
            return "Erstellung von {} durch {} am {}".format(
                self.person,
                self.user.get_full_name(),
                self.date,
            )
        elif self.operation == KeyLogEntry.EDIT and self.key:
            return f"Bearbeitung von {self.key} durch {self.user.get_full_name()} am {self.date}"
        elif self.operation == KeyLogEntry.EDIT and self.person:
            return f"Bearbeitung von {self.person} durch {self.user.get_full_name()} am {self.date}"
        else:
            return "Unvalid Operation"


class SavedKeyChange(models.Model):
    key = models.OneToOneField(
        Key,
        verbose_name="Schlüssel",
        on_delete=models.CASCADE,
    )

    new_keytype = models.ForeignKey(
        KeyType,
        models.CASCADE,
        verbose_name="Neuer Schlüssel-Typ",
    )

    comment = models.CharField(
        verbose_name="Kommentar",
        max_length=500,
        blank=True,
    )

    user = models.ForeignKey(
        User,
        models.CASCADE,
        verbose_name="Finanzer*in",
    )

    date = models.DateTimeField(
        verbose_name="Datum",
        auto_now=True,
    )

    @property
    def violated_key(self):
        violated_key = Key.objects.filter(
            keytype=self.new_keytype,
            number=self.key.number,
        )
        if violated_key.exists():
            return violated_key.get()
        return None
