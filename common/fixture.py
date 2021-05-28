import random
from datetime import date, timedelta
from decimal import Decimal
from subprocess import run  # nosec: used for flushing the db

import django.utils.timezone

# noinspection PyPackageRequirements
import lorem
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


def showroom_fixture_state_no_confirmation():  # nosec: this is only used in a fixture
    run(["python3", "manage.py", "flush", "--noinput"], check=True)

    # user
    _generate_superuser_frank()
    _generate_users()

    # app common
    _generate_common_mails()
    _generate_common_settings()

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


def rand_company_name():  # nosec: this is only used in a fixture
    return random.choice(
        [
            "Scattershot",
            "Scrapper",
            "Streetwise",
            "Arcana",
            "Thundercracker",
            "Grax",
            "Caliburst",
            "Broadside",
            "Drag Strip",
            "Warpath",
            "Ironhide",
            "Chromedome",
            "Stylor",
            "Recoil",
            "Spectro",
            "Camshaft",
            "Slag",
            "Haywire",
            "Snarl",
            "Starscream",
        ],
    )


def rand_name():  # nosec: this is only used in a fixture
    return random.choice(
        [
            ("Wolfgang", "Essert"),
            ("Agnes", "Fenstermacher"),
            ("Walter", "Simons"),
            ("Loke", "Hofer"),
            ("Waldemar", "Gross"),
            ("Felicitas", "Achterberg"),
            ("Emma", "Bergmann"),
            ("Simone", "Reich"),
            ("Linda", "Mangold"),
            ("Adam", "Sander"),
            ("Gunda", "Lorentz"),
            ("Sylvia", "Hoffmann"),
            ("Karla", "Peters"),
            ("Hartmut", "Werner"),
            ("Erika", "Hennig"),
            ("Jochen", "Beyer"),
            ("Erika", "Hochberg"),
            ("Severin", "Bruhn"),
            ("Elmar", "Mohren"),
            ("Miriam", "Schlosser"),
        ],
    )


def _generate_rechnung_posten():  # nosec: this is only used in a fixture
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


def _generate_rechnung_kategorie():  # nosec: this is only used in a fixture
    names = {lorem.text()[: random.randint(10, 100)] for _ in range(5)}
    for name in names:
        m_rechnung.Kategorie.objects.create(name=name)


def _generate_rechnung_mahnung():  # nosec: this is only used in a fixture
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


def _generate_rechnung_rechnung():  # nosec: this is only used in a fixture
    users = list(get_user_model().objects.all())
    kunden = list(m_rechnung.Kunde.objects.all())
    kategorien = list(m_rechnung.Kategorie.objects.all())
    for _ in range(random.randint(20, 30)):
        m_rechnung.Rechnung.objects.create(
            name=lorem.sentence()[: random.randint(0, 50)] if random.choice((True, True, False)) else "",
            rdatum=date.today()
            if random.choice((True, True, False))
            else date.today()
            + timedelta(
                days=random.randint(0, 32),
            )
            - timedelta(days=random.randint(0, 32)),
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


def _generate_rechnung_kunde():  # nosec: this is only used in a fixture
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
            name=rand_name()[1] if random.choice((True, True, False)) else "",
            vorname=rand_name()[0] if random.choice((True, True, False)) else "",
            strasse=lorem.sentence()[: random.randint(0, 100)],
            plz=random.choice(("48323", "42368", "86735", "028412", "081231")),
            stadt=lorem.paragraph()[: random.randint(0, 200)],
            land="Deutschland" if random.choice((True, True, False)) else rand_name()[1] + "land",
            kommentar=lorem.sentence()[: random.randint(0, 1000)] if random.choice((True, False, False)) else "",
        )


def _generate_schluessel_key_type():  # nosec: this is only used in a fixture
    for i in range(5):
        m_schluessel.KeyType.objects.create(
            shortname=f"{lorem.sentence()[:random.randint(3, 18)]}{i}",
            name=lorem.sentence()[: random.randint(0, 200)],
            deposit=random.choice((random.randint(0, 20), 0, 10)),
            keycard=random.choice((True, False)),
        )


def _generate_schluessel_person():  # nosec: this is only used in a fixture
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


def _generate_schluessel_key():  # nosec: this is only used in a fixture
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


def _generate_common_settings() -> None:  # nosec: this is only used in a fixture
    all_mail = list(m_common.Mail.objects.all())
    m_common.Settings.objects.create(
        ueberfaellige_rechnung_mail=random.choice(all_mail) if random.choice((True, True, False)) else None,
        zugewiesene_aufgabe_mail=random.choice(all_mail) if random.choice((True, True, False)) else None,
    )


def _generate_common_mails() -> None:  # nosec: this is only used in a fixture
    for _ in range(random.randint(10, 20)):
        m_common.Mail.objects.create(
            subject=lorem.text()[: random.randint(10, 200)],
            text=lorem.text(),
            comment=lorem.text()[: random.randint(10, 200)] if random.choice((True, False, False)) else "",
        )


def _generate_superuser_frank():  # nosec: this is only used in a fixture
    get_user_model().objects.create(
        username="frank",
        password="pbkdf2_sha256$216000$DHqZuXE7LQwJ$i8iIEB3qQN+NXMUTuRxKKFgYYC5XqlOYdSz/0om1FmE=",
        first_name="Frank",
        last_name="Elsinga",
        is_superuser=True,
        is_staff=True,
        is_active=True,
        email="elsinga@fs.tum.de",
        date_joined=django.utils.timezone.make_aware(datetime.today()),
    )


def _generate_users():  # nosec: this is only used in a fixture
    for i in range(random.randint(10, 20)):
        firstname: str = rand_name()[0]
        lastname: str = rand_name()[1]
        get_user_model().objects.create(
            username=f"{lastname.lower()}{i}",
            password=make_password(lorem.sentence()),
            first_name=firstname,
            last_name=lastname,
            is_superuser=random.choice((True, True, False)),
            is_staff=random.choice((True, True, False)),
            is_active=random.choice((True, True, False)),
            email=f"{lastname}@fs.tum.de",
            date_joined=django.utils.timezone.make_aware(
                random.choice(
                    (
                        datetime.today() - timedelta(days=random.randint(0, 32)),
                        datetime.today(),
                    ),
                ),
            ),
        )


def _generate_aufgaben_aufgabenart():  # nosec: this is only used in a fixture
    for _ in range(random.randint(5, 15)):
        m_aufgaben.Aufgabenart.objects.create(name=lorem.sentence()[: random.randint(10, 50)])


def _generate_aufgaben_aufgabe():  # nosec: this is only used in a fixture
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