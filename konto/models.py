from django.contrib.auth import get_user_model
from django.db import models


class EinzahlungsLog(models.Model):
    user = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.CASCADE)
    timestamp = models.DateField()

    def __str__(self):
        return f"{self.user} at {self.timestamp}"
