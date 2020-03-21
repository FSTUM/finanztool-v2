from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from datetime import date


class Aufgabenart(models.Model):
    name = models.CharField(
            verbose_name='Bezeichnung',
            max_length=50,
            )

    def __str__(self):
        return "{}".format(self.name)


class Aufgabe(models.Model):
    art = models.ForeignKey(
            Aufgabenart,
        models.CASCADE
            )
    frist = models.DateField(
            verbose_name='Sollte erledigt sein bis *',
            )
    erledigt = models.BooleanField(
            verbose_name='Erledigt? *',
            default=False,
            )
    zustaendig = models.ForeignKey(
            User,
        models.CASCADE,
            related_name='aufgabe_zustaendig',
            verbose_name='Wer soll sie erledigen? *',
            )
    bearbeiter = models.ForeignKey(
            User,
        models.CASCADE,
            related_name='aufgabe_bearbeiter',
            verbose_name='Wer hat sie erledigt?',
            null=True,
            blank=True,
            )
    jahr = models.IntegerField(
           validators=[MaxValueValidator(9999), MinValueValidator(1000)],
           null=True,
           blank=True,
           )
    SEMESTER = (
            ('ws', 'Wintersemester'),
            ('ss', 'Sommersemester'),
            )
    semester = models.CharField(
            verbose_name='Zugehöriges Semester',
            choices=SEMESTER,
            max_length=2,
            null=True,
            blank=True,
            )
    zusatz = models.CharField(
            verbose_name='Zusatzinformation',
            max_length=50,
            null=True,
            blank=True,
            )
    text = models.TextField(
            verbose_name='Text',
            null=True,
            blank=True,
            )

    def __str__(self):
        return "{} - {} ({})".format(self.art.name, self.zusatz, self.jahr)

    def faellig(self):
        return self.frist < date.today()
