from django.contrib.auth import get_user_model
from django.db import models


class EinzahlungsLog(models.Model):
    user = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.CASCADE)
    konto_einlesen = models.DateTimeField(auto_now_add=True)
    konto_last_einzahlung = models.DateField(blank=True, null=True)

    # odly specific, but this is the standard..
    latest_einzahlung_verwendungszweck = models.CharField(max_length=378, blank=True, null=True)

    latest_einzahlung_betrag = models.DecimalField(decimal_places=6, max_digits=20, blank=True, null=True)

    def __str__(self):
        return (
            f"{self.konto_einlesen} durch {self.user}. "
            f"Die letzte Einzahlung war {self.latest_einzahlung_verwendungszweck} ({self.latest_einzahlung_betrag}€) "
            f"vom {self.konto_last_einzahlung or '?'}"
        )
