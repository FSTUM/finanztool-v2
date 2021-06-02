from django.contrib.auth import get_user_model
from django.db import models


class EinzahlungsLog(models.Model):
    user = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.CASCADE)
    konto_einlesen = models.DateTimeField(auto_now_add=True)
    konto_last_einzahlung = models.DateField()

    # odly specific, but this is the standard..
    einzahlungs_betreff = models.CharField(max_length=378, blank=True, null=True)

    def __str__(self):
        return (
            f"{self.konto_einlesen} durch {self.user}. "
            f"Die letzte Einzahlung war {self.einzahlungs_betreff} vom {self.konto_last_einzahlung}"
        )
