from typing import List

from django.contrib.auth.models import User  # pylint: disable=imported-auth-user

from aufgaben.models import Aufgabe
from rechnung.models import Rechnung

from .models import Mail, Settings


def ueberfaellige_rechnung_reminder() -> None:
    if Settings.objects.exists():
        settings = Settings.objects.first()
        if settings and settings.ueberfaellige_rechnung_mail:
            rechnung_obj: Rechnung
            rechnungen: List[Rechnung] = [
                rechnung_obj for rechnung_obj in Rechnung.objects.all() if rechnung_obj.faellig()
            ]
            settings.ueberfaellige_rechnung_mail.send_mail({"rechnungen": rechnungen}, Mail.FINANZ)


def zugewiesene_aufgabe_reminder() -> None:
    if Settings.objects.exists():
        settings = Settings.objects.first()
        if settings and settings.zugewiesene_aufgabe_mail:
            zustaendige_user: List[User] = [
                User.objects.get(aufg["zustaendig"])
                for aufg in Aufgabe.objects.filter(erledigt=False).values("zustaendig").distinct()
            ]
            user: User
            for user in zustaendige_user:
                aufgaben: List[Aufgabe] = list(Aufgabe.objects.filter(zustaendig=user, erledigt=False).all())
                settings.zugewiesene_aufgabe_mail.send_mail({"aufgaben": aufgaben}, user.email)
