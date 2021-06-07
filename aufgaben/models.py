import os
from datetime import date

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.dispatch import receiver


class Aufgabenart(models.Model):
    name = models.CharField(
        verbose_name="Bezeichnung",
        max_length=50,
    )

    def __str__(self):
        return self.name


class Aufgabe(models.Model):
    art = models.ForeignKey(
        Aufgabenart,
        models.CASCADE,
    )
    frist = models.DateField(
        verbose_name="Sollte erledigt sein bis *",
    )
    erledigt = models.BooleanField(
        verbose_name="Erledigt? *",
        default=False,
    )
    zustaendig = models.ForeignKey(
        get_user_model(),
        models.CASCADE,
        related_name="aufgabe_zustaendig",
        verbose_name="Wer soll sie erledigen? *",
    )
    bearbeiter = models.ForeignKey(
        get_user_model(),
        models.CASCADE,
        related_name="aufgabe_bearbeiter",
        verbose_name="Wer hat sie erledigt?",
        null=True,
        blank=True,
    )
    jahr = models.IntegerField(
        validators=[MaxValueValidator(9999), MinValueValidator(1000)],
        null=True,
        blank=True,
    )
    SEMESTER = (
        ("ws", "Wintersemester"),
        ("ss", "Sommersemester"),
    )
    semester = models.CharField(
        verbose_name="Zugehöriges Semester",
        choices=SEMESTER,
        max_length=2,
        null=True,
        blank=True,
    )
    zusatz = models.CharField(
        verbose_name="Zusatzinformation",
        max_length=50,
        null=True,
        blank=True,
    )
    text = models.TextField(
        verbose_name="Text",
        null=True,
        blank=True,
    )
    attachment = models.FileField(upload_to="aufgben-attachments", verbose_name="Anhang", null=True, blank=True)

    def __str__(self):
        return f"{self.art.name} - {self.zusatz} ({self.jahr})"

    def faellig(self):
        return self.frist < date.today()


@receiver(models.signals.post_delete, sender=Aufgabe)
def auto_del_aufgabe_attachment_on_delete(sender, instance, **_kwargs):
    """
    Deletes file from filesystem
    when corresponding `Aufgabe` object is deleted.
    """
    _ = sender  # sender is needed, for api. it cannot be renamed, but is unused here.
    if instance.qr_code and os.path.isfile(instance.qr_code.path):
        os.remove(instance.qr_code.path)
