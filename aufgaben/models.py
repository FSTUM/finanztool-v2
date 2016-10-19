from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Aufgabenart(models.Model):
    name = models.CharField(
            verbose_name='Bezeichnung',
            max_length=50,
            )


class Aufgabe(models.Model):
    art = models.ForeignKey(
            Aufgabenart,
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
            related_name='aufgabe_zustaendig',
            verbose_name='Wer soll sie erledigen? *',
            )
    bearbeiter = models.ForeignKey(
            User,
            related_name='aufgabe_bearbeiter',
            verbose_name='Wer hat sie erledigt? *',
            )
    jahr = models.IntegerField(
           validators=[MaxValueValidator(9999), MinValueValidator(1000)],
           )
    SEMESTER = (
            ('ws', 'Wintersemester'),
            ('ss', 'Sommersemester'),
            )
    semester = models.CharField(
            verbose_name='Zugehöriges Semester *',
            choices=SEMESTER,
            max_length=2,
            )
    zusatz = models.CharField(
            verbose_name='Zusatzinformation',
            max_length=50,
            null=True,
            blank=True,
            )
    text = models.TextField(
            verbose_name='Text',
            )
