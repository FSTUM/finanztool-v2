import datetime
import re
from csv import DictReader
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Pattern

from django.db.models import QuerySet

from getraenke.models import Schulden
from rechnung.models import Mahnung, Rechnung

from .models import EinzahlungsLog


@dataclass
class Entry:  # pylint: disable=too-many-instance-attributes
    datum: datetime.date
    verwendungszweck: str
    zahlungspflichtiger: str
    iban: str
    bic: str
    betrag: Decimal

    mapped_rechnung: Optional[Rechnung] = None
    mapped_mahnung: Optional[Mahnung] = None
    erwarteter_betrag: Optional[Decimal] = None
    betrag_passt: Optional[bool] = False

    mapped_user: Optional[Schulden] = None

    def __repr__(self):
        if self.mapped_rechnung:
            rnr = self.mapped_rechnung.rnr_string
        else:
            rnr = None

        return (
            f'Entry <datum={self.datum}, verwendungszweck="{self.verwendungszweck}", '
            f'zahlungspflichtiger="{self.zahlungspflichtiger}", iban={self.iban}, bic={self.bic}, '
            f"betrag={self.betrag}, mapped_rechnung={rnr}>"
        )


def parse_camt_csv(csvfile):
    results: List[Entry] = []
    errors: List[str] = []

    # hole alle offenen rechnungen
    offene_rechnungen: QuerySet[Rechnung] = Rechnung.objects.filter(gestellt=True, erledigt=False).all()
    regex_cache: Dict[Rechnung, Pattern[str]] = {}
    rechnung: Rechnung
    for rechnung in offene_rechnungen:
        regex_cache[rechnung] = re.compile(fr"(.*\D)?{rechnung.rnr_string}(\D.*)?")

    users: QuerySet[Schulden] = Schulden.objects.all()
    regex_usernames: Dict[Schulden, Pattern[str]] = {}
    user: Schulden
    for user in users:
        regex_usernames[user] = re.compile(fr"(.*\W)?{user.user}(\W.*)?")

    try:
        zuletzt_einlesen: Optional[datetime.date] = EinzahlungsLog.objects.latest("konto_einlesen").konto_einlesen
    except EinzahlungsLog.DoesNotExist:
        zuletzt_einlesen = None

    # read CSV file
    csvcontents = DictReader(csvfile, delimiter=";")
    for counter, row in enumerate(csvcontents):
        buchungstext: str = row["Buchungstext"]
        if buchungstext in ["GUTSCHR. UEBERWEISUNG", "ECHTZEIT-GUTSCHRIFT"]:
            entry: Optional[Entry] = pre_process_entry(counter, row, errors)
            if entry:
                suche_rechnung(entry, offene_rechnungen, regex_cache)
                if not entry.mapped_rechnung:
                    suche_user(entry, users, regex_usernames, zuletzt_einlesen, errors)
                results.append(entry)
        elif buchungstext in [
            "ENTGELTABSCHLUSS",
            "ONLINE-UEBERWEISUNG",
            "RECHNUNG",
            "FOLGELASTSCHRIFT",
            "BARGELDAUSZAHLUNG KASSE",
        ]:
            pass
        else:
            errors.append(f"Transaktion in Zeile {counter} mit Typ {buchungstext} nicht erkannt")
    return results, errors


def pre_process_entry(counter: int, row: Any, errors: List[str]) -> Optional[Entry]:
    try:
        datum = datetime.datetime.strptime(row["Buchungstag"], "%d.%m.%y").date()
    except ValueError:
        try:
            # if a file is opened in exel this is converted this way..
            datum = datetime.datetime.strptime(row["Buchungstag"], "%d.%m.%Y").date()
        except ValueError:
            errors.append(f"Zeile {counter}: Ungültiges Datum: {row[1]}")
            return None

    betrag = row["Betrag"]
    try:
        betrag = Decimal(betrag.replace(",", "."))
    except InvalidOperation:
        errors.append(f"Zeile {counter}: Ungültiger Betrag: {betrag}")
        return None
    waehrung = row["Waehrung"]
    if waehrung != "EUR":
        errors.append(f"Zeile {counter}: Eintrag in anderer Währung als Euro")
        return None

    return Entry(
        verwendungszweck=row["Verwendungszweck"],
        zahlungspflichtiger=row["Beguenstigter/Zahlungspflichtiger"],
        iban=row["Kontonummer/IBAN"],
        bic=row["BIC (SWIFT-Code)"],
        datum=datum,
        betrag=betrag,
    )


def suche_rechnung(
    entry: Entry,
    offene_rechnungen: QuerySet[Rechnung],
    regex_cache: Dict[Rechnung, Pattern[str]],
) -> None:
    rechnung: Rechnung
    for rechnung in offene_rechnungen:
        tmp = regex_cache[rechnung].match(entry.verwendungszweck)
        if tmp:
            # rechnung gefunden -> setzen
            entry.mapped_rechnung = rechnung

            entry.betrag_passt = entry.betrag == rechnung.gesamtsumme

            # nach mahnungen suchen?
            mahnung: Mahnung
            for mahnung in rechnung.mahnungen:
                entry.betrag_passt = mahnung.mahnsumme == entry.betrag
                if entry.betrag_passt:
                    entry.mapped_mahnung = mahnung

            # erwarteter betrag
            if rechnung.mahnungen:
                entry.erwarteter_betrag = rechnung.mahnungen.latest("wievielte").mahnsumme
            else:
                entry.erwarteter_betrag = rechnung.gesamtsumme


def suche_user(
    entry: Entry,
    users: QuerySet[Schulden],
    regex_usernames: Dict[Schulden, Pattern[str]],
    zuletzt_einlesen: Optional[datetime.date],
    errors: List[str],
) -> None:
    user: Schulden
    for user in users:
        tmp = regex_usernames[user].fullmatch(entry.verwendungszweck)
        if tmp:
            if zuletzt_einlesen and zuletzt_einlesen < entry.datum:
                if entry.mapped_user is not None:
                    # If there is a user that was already previously matched,
                    # print a duplicate match error and abort the search.
                    errors.append(
                        f'Einzahlung "{entry.verwendungszweck}" vom {entry.datum} hat mehrere Benutzer gematcht: '
                        f"{entry.mapped_user}, {user}.",
                    )
                    entry.mapped_user = None
                    return
                # Enter the new user
                entry.mapped_user = user
            elif zuletzt_einlesen and zuletzt_einlesen >= entry.datum:
                # Print an error that this transaction lies beyond the date of the last transaction.
                errors.append(
                    f"Letzte Einzahlung von {user.user} am {entry.datum} liegt nach der "
                    f"Einzahlung vom {zuletzt_einlesen}.",
                )
            else:
                # zuletzt_eingetragen is None:
                errors.append(
                    f'Nutzer {user.user} hat kein "zuletzt eingetragen" Datum für die Einzahlung vom {entry.datum}.',
                )
