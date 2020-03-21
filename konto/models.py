from django.db import models
from django.contrib.auth.models import User


class EinzahlungsLog(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    timestamp = models.DateField()
