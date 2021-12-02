from typing import List

from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.db.models import QuerySet

from aufgaben.models import Aufgabe
from rechnung.models import Rechnung

from .models import Mail, Settings


def ueberfaellige_rechnung_reminder() -> None:
    settings: Settings = Settings.load()
    if settings and settings.ueberfaellige_rechnung_mail:
        rechnungen_qs: QuerySet[Rechnung] = Rechnung.objects.all()
        faellige_rechnungen: List[Rechnung] = [rechnung for rechnung in rechnungen_qs if rechnung.faellig()]
        settings.ueberfaellige_rechnung_mail.send_mail({"rechnungen": faellige_rechnungen}, Mail.FINANZ)


def zugewiesene_aufgabe_reminder() -> None:
    settings: Settings = Settings.load()
    if settings and settings.zugewiesene_aufgabe_mail:
        zustaendige_user: List[User] = [
            User.objects.get(aufg["zustaendig"])
            for aufg in Aufgabe.objects.filter(erledigt=False).values("zustaendig").distinct()
        ]
        user: User
        for user in zustaendige_user:
            aufgaben: List[Aufgabe] = list(Aufgabe.objects.filter(zustaendig=user, erledigt=False).all())
            settings.zugewiesene_aufgabe_mail.send_mail({"aufgaben": aufgaben}, user.email)
