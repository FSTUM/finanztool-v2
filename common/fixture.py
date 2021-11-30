import random
from datetime import date, timedelta
from decimal import Decimal
from subprocess import run  # nosec: used for flushing the db

import django.utils.timezone
import lorem  # noinspection PyPackageRequirements
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.datetime_safe import datetime

import aufgaben.models as m_aufgaben
import common.models as m_common
import rechnung.models as m_rechnung
import schluessel.models as m_schluessel


def showroom_fixture_state():
    confirmation = input(
        "Do you really want to load the showroom fixture? (This will flush the database) [y/n]",
    )
    if confirmation.lower() != "y":
        return
    showroom_fixture_state_no_confirmation()


def showroom_fixture_state_no_confirmation():
    run(["python3", "manage.py", "flush", "--noinput"], check=True)

    # user
    _generate_superusers()
    _generate_users()

    # app common
    _generate_common_mails()
    _generate_common_settings()
    _generate_qrcodes_posten()

    # app aufgaben
    _generate_aufgaben_aufgabenart()
    _generate_aufgaben_aufgabe()

    # app getraenke
    # ignored because no views exist
    # m_getraenke.Getraenke
    # m_getraenke.Log
    # m_getraenke.Blacklist
    # m_getraenke.Schulden

    # app rechnung
    _generate_rechnung_kategorie()
    _generate_rechnung_kunde()
    _generate_rechnung_rechnung()
    _generate_rechnung_mahnung()
    _generate_rechnung_posten()

    # app schluessel
    _generate_schluessel_key_type()
    _generate_schluessel_person()
    _generate_schluessel_key()
    # _generate_schluessel_key_log_entry()
    # _generate_schluessel_saved_key_change()


def showroom_fixture_state_no_confirmation_staging():
    showroom_fixture_state_no_confirmation()
    m_common.QRCode.objects.all().delete()  # staticfiles are not handled correctly in the staging environment


def rand_company_name():
    cool_names = ["Caliburst", "Ironhide", "Stylor", "Spectro", "Camshaft", "Haywire", "Snarl", "Starscream"]
    violent_names = ["Warpath", "Recoil", "Broadside", "Scattershot", "Thundercracker"]
    lame_names = ["Scrapper", "Streetwise", "Arcana", "Grax", "Drag Strip", "Chromedome", "Slag"]
    return random.choice(cool_names + violent_names + lame_names)


def rand_firstname():
    male_names = ["Wolfgang", "Walter", "Loke", "Waldemar", "Adam", "Gunda", "Hartmut", "Jochen", "Severin", "Elmar"]
    female_names = ["Agnes", "Sylvia", "Karla", "Erika", "Felicitas", "Emma", "Simone", "Linda", "Erika", "Miriam"]
    return random.choice(male_names + female_names)


def rand_last_name():
    ger_last_names = ["Fenstermacher", "Achterberg", "Bergmann", "Reich", "Werner", "Hochberg", "Bruhn", "Schlosser"]
    common_last_names = ["Peters", "Hofer"]
    last_names = ["Essert", "Simons", "Gross", "Mangold", "Sander", "Lorentz", "Hoffmann", "Hennig", "Beyer"]
    return random.choice(ger_last_names + common_last_names + last_names)


def _generate_qrcodes_posten():
    m_common.QRCode.objects.create(pk=0, content="https://www.yo" "utub" "e.com/" "wat" "ch?v=dQw4w" "9WgXcQ")
    links = [
        "https://www.google.com",
        "mpi.fs.tum.de",
        "finanz.mpi.fs.tum.de",
    ]
    for link in links:
        m_common.QRCode.objects.create(content=link)


def _generate_rechnung_posten():
    rechnungen = list(m_rechnung.Rechnung.objects.all())
    for rechnung in rechnungen:
        for _ in range(random.randint(0, 7)):
            m_rechnung.Posten.objects.create(
                rechnung=rechnung,
                name=lorem.sentence()[: random.randint(1, 100)],
                einzelpreis=Decimal(f"{random.randint(0, 100)}.{random.randint(0, 99)}"),
                mwst=random.choice(m_rechnung.Posten.MWSTSATZ)[0],
                anzahl=random.choice((1, 10, 100, random.randint(1, 200), random.randint(200, 3000))),
            )


def _generate_rechnung_kategorie():
    names = {lorem.text()[: random.randint(10, 100)] for _ in range(5)}
    for name in names:
        m_rechnung.Kategorie.objects.create(name=name)


def _generate_rechnung_mahnung():
    users = list(get_user_model().objects.all())
    rechnungen = list(m_rechnung.Rechnung.objects.all())
    for rechnung in rechnungen:
        if random.choice((True, False, False, False)):
            mahnungsanzahl = random.choice((1, 1, 1, 1, 1, 2, 5))
            for current_ma in range(mahnungsanzahl):
                m_rechnung.Mahnung.objects.create(
                    rechnung=rechnung,
                    wievielte=current_ma,
                    gebuehr=random.choice(
                        (Decimal("25.00"), Decimal("30.00"), Decimal("0.00"), Decimal("42.00"), Decimal("69.00")),
                    ),
                    mdatum=m_rechnung.get_faelligkeit_default() + timedelta(days=random.randint(0, current_ma * 15)),
                    mfdatum=m_rechnung.get_faelligkeit_default() + timedelta(days=random.randint(0, current_ma * 15)),
                    geschickt=random.choice((True, False)),
                    bezahlt=random.choice((True, False)),
                    gerichtlich=random.choice((True, False)),
                    ersteller=random.choice(users),
                    einleitung=lorem.text(),
                )


def _generate_rechnung_rechnung():
    users = list(get_user_model().objects.all())
    kunden = list(m_rechnung.Kunde.objects.all())
    kategorien = list(m_rechnung.Kategorie.objects.all())
    for _ in range(random.randint(20, 30)):
        m_rechnung.Rechnung.objects.create(
            name=lorem.sentence()[: random.randint(0, 50)] if random.choice((True, True, False)) else "",
            rdatum=date.today()
            if random.choice((True, True, False))
            else date.today() + timedelta(days=random.randint(0, 32)) - timedelta(days=random.randint(0, 32)),
            ldatum=random.choice(
                (
                    date.today(),
                    date.today()
                    + timedelta(days=random.randint(0, 32))
                    - timedelta(
                        days=random.randint(0, 32),
                    ),
                    date.today() + timedelta(days=random.randint(0, 32)),
                ),
            )
            if random.choice((True, True, False))
            else None,
            gestellt=random.choice((True, False)),
            bezahlt=random.choice((True, False)),
            erledigt=random.choice((True, False)),
            ersteller=random.choice(users),
            kunde=random.choice(kunden),
            einleitung=lorem.text(),
            kategorie=random.choice(kategorien),
        )


def _generate_rechnung_kunde():
    for _ in range(random.randint(10, 20)):
        m_rechnung.Kunde.objects.create(
            organisation=f"{rand_company_name()} {random.choice(('AG', 'UG', 'KG', 'OHG', 'GmbH'))}"
            if random.choice((True, True, False))
            else "",
            suborganisation=random.choice(
                (
                    f"{rand_company_name()} {random.choice(('AG', 'UG', 'KG', 'OHG', 'GmbH'))}",
                    lorem.sentence()[: random.randint(300, 500)],
                    "",
                    "",
                ),
            ),
            anrede=random.choice(m_rechnung.Kunde.GESCHLECHT)[0] if random.choice((True, True, False)) else "",
            titel=lorem.sentence()[: random.randint(0, 50)] if random.choice((True, True, False)) else "",
            name=rand_last_name() if random.choice((True, True, False)) else "",
            vorname=rand_firstname() if random.choice((True, True, False)) else "",
            strasse=lorem.sentence()[: random.randint(0, 100)],
            plz=random.choice(("48323", "42368", "86735", "028412", "081231")),
            stadt=lorem.paragraph()[: random.randint(0, 200)],
            land="Deutschland" if random.choice((True, True, False)) else rand_firstname() + "land",
            kommentar=lorem.sentence()[: random.randint(0, 1000)] if random.choice((True, False, False)) else "",
        )


def _generate_schluessel_key_type():
    for i in range(5):
        m_schluessel.KeyType.objects.create(
            shortname=f"{lorem.sentence()[:random.randint(3, 18)]}{i}",
            name=lorem.sentence()[: random.randint(0, 200)],
            deposit=random.choice((random.randint(0, 20), 0, 10)),
            keycard=random.choice((True, False)),
        )


def _generate_schluessel_person():
    users = list(get_user_model().objects.all())
    for user in users:
        if random.choice((True, False)):
            m_schluessel.Person.objects.create(
                name=user.last_name,
                firstname=user.first_name,
                email=user.email,
                address=lorem.sentence()[: random.randint(0, 100)],
                plz=random.choice(("48323", "42368", "86735", "028412", "081231")),
                city=lorem.paragraph()[: random.randint(0, 200)],
                mobile="+49" + str(random.randint(1000, 99999999)),
                phone="+4989" + str(random.randint(1000, 99999)) if random.choice((True, False)) else "",
            )


def _generate_schluessel_key():
    personen = list(m_schluessel.Person.objects.all())
    keytypes = list(m_schluessel.KeyType.objects.all())

    for counter in range(int(len(personen) * 1.5)):
        m_schluessel.Key.objects.create(
            keytype=random.choice(keytypes),
            number=counter,
            person=random.choice(personen) if random.choice((True, True, True, False)) else None,
            active=random.choice((True, True, False)),
            comment=lorem.paragraph()[: random.randint(0, 500)],
        )


def _generate_schluessel_key_log_entry():
    pass


def _generate_schluessel_saved_key_change():
    pass


def _generate_common_settings() -> None:
    all_mail = list(m_common.Mail.objects.all())
    m_common.Settings.objects.create(
        ueberfaellige_rechnung_mail=random.choice(all_mail) if random.choice((True, True, False)) else None,
        zugewiesene_aufgabe_mail=random.choice(all_mail) if random.choice((True, True, False)) else None,
    )


def _generate_common_mails() -> None:
    for _ in range(random.randint(10, 20)):
        m_common.Mail.objects.create(
            subject=lorem.text()[: random.randint(10, 200)],
            text=lorem.text(),
            comment=lorem.text()[: random.randint(10, 200)] if random.choice((True, False, False)) else "",
        )


def _generate_superusers():
    users = [
        ("frank", "130120", "Frank", "Elsinga", "elsinga@example.com"),
        ("password", "username", "Nelson 'Big Head'", "Bighetti", "bighetti@example.com"),
    ]
    for username, password, first_name, last_name, email in users:
        get_user_model().objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            is_superuser=True,
            is_staff=True,
            is_active=True,
            email=email,
            date_joined=django.utils.timezone.make_aware(datetime.today()),
        )


def _generate_users():
    for i in range(random.randint(10, 20)):
        firstname: str = rand_firstname()
        lastname: str = rand_last_name()
        get_user_model().objects.create(
            username=f"{lastname.lower()}{i}",
            password=make_password(lorem.sentence()),
            first_name=firstname,
            last_name=lastname,
            is_superuser=random.choice((True, True, False)),
            is_staff=random.choice((True, True, False)),
            is_active=random.choice((True, True, False)),
            email=f"{lastname}@example.com",
            date_joined=django.utils.timezone.make_aware(
                random.choice(
                    (
                        datetime.today() - timedelta(days=random.randint(0, 32)),
                        datetime.today(),
                    ),
                ),
            ),
        )


def _generate_aufgaben_aufgabenart():
    for _ in range(random.randint(5, 15)):
        m_aufgaben.Aufgabenart.objects.create(name=lorem.sentence()[: random.randint(10, 50)])


def _generate_aufgaben_aufgabe():
    aufgabenarten = m_aufgaben.Aufgabenart.objects.all()
    users = get_user_model().objects.all()
    for _ in range(random.randint(5, 15)):
        m_aufgaben.Aufgabe.objects.create(
            art=random.choice(aufgabenarten),
            frist=django.utils.timezone.make_aware(
                random.choice(
                    (
                        datetime.today()
                        - timedelta(days=random.randint(0, 32))
                        + timedelta(
                            days=random.randint(0, 32),
                        ),
                        datetime.today() - timedelta(days=1),
                        datetime.today() + timedelta(days=1),
                        datetime.today(),
                    ),
                ),
            ),
            erledigt=random.choice((True, False, False)),
            zustaendig=random.choice(users),
            bearbeiter=random.choice(users) if random.choice((True, False, False)) else None,
            jahr=random.randint(2018, 2025),
            semester=random.choice(m_aufgaben.Aufgabe.SEMESTER)[0] if random.choice((True, True, False)) else None,
            zusatz=lorem.text()[: random.randint(10, 50)] if random.choice((True, False, False)) else "",
            text=lorem.text() if random.choice((True, False, False)) else "",
        )
