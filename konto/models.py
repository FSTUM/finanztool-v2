from django.contrib.auth.models import User
from django.db import models


class EinzahlungsLog(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    timestamp = models.DateField()
