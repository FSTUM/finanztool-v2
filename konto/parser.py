import csv
import datetime
import re
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User

from rechnung.models import Rechnung
from getraenke.models import Schulden
from .models import EinzahlungsLog


class Entry:
    datum = None
    verwendungszweck = None
    zahlungspflichtiger = None
    iban = None
    bic = None
    betrag = None

    mapped_rechnung = None
    mapped_mahnung = None
    erwarteter_betrag = None
    betrag_passt = False

    mapped_user = None

    def __repr__(self):
        if self.mapped_rechnung:
            rnr = self.mapped_rechnung.rnr_string
        else:
            rnr = None

        return "Entry <datum={}, verwendungszweck=\"{}\", " \
               "zahlungspflichtiger=\"{}\", iban={}, bic={}, betrag={}, " \
               "mapped_rechnung={}>" \
            .format(self.datum, self.verwendungszweck,
                    self.zahlungspflichtiger, self.iban, self.bic,
                    self.betrag, rnr)


def parse_camt_csv(csvfile):
    results = []
    errors = []

    # hole alle offenen rechnungen
    offene_rechnungen = Rechnung.objects.filter(gestellt=True,
                                                erledigt=False).all()
    regex_cache = {}
    for rechnung in offene_rechnungen:
        regex_cache[rechnung] = re.compile('(.*[^0-9])?{}([^0-9].*)?'
                                           .format(rechnung.rnr_string))

    users = Schulden.objects.all()
    regex_usernames = {}
    for u in users:
        regex_usernames[u] = re.compile('(.*\s+)?{}(\s+.*)?'
                                        .format(u.user))

    try:
        zuletzt_eingetragen = EinzahlungsLog.objects.latest('timestamp').timestamp
    except EinzahlungsLog.DoesNotExist:
        zuletzt_eingetragen = None

    # read CSV file
    csvreader = csv.reader(csvfile, delimiter=';')
    counter = 0
    for row in csvreader:
        counter += 1

        if row[3] == "GUTSCHR. UEBERWEISUNG":
            entry = Entry()

            try:
                entry.datum = datetime.datetime.strptime(row[1], "%d.%m.%y")
                entry.datum = entry.datum.date()
            except ValueError:
                errors.append("Zeile {}: Ungültiges Datum: {}".format(counter,
                                                                      row[1]))
                continue

            entry.verwendungszweck = row[4]
            entry.zahlungspflichtiger = row[11]
            entry.iban = row[12]
            entry.bic = row[13]

            try:
                entry.betrag = Decimal(row[14].replace(',', '.'))
            except InvalidOperation:
                errors.append("Zeile {}: Ungültiger Betrag: {}".format(counter,
                                                                       row[14]))
                continue

            if row[15] != "EUR":
                errors.append("Zeile {}: Eintrag in anderer Währung als "
                              "Euro".format(counter))
                continue

            suche_rechnung(entry, offene_rechnungen, regex_cache)
            if not entry.mapped_rechnung:
                suche_user(entry, users, regex_usernames, zuletzt_eingetragen, errors)

            results.append(entry)

    return results, errors


def suche_rechnung(entry, offene_rechnungen, regex_cache):
    for rechnung in offene_rechnungen:
        tmp = regex_cache[rechnung].match(entry.verwendungszweck)
        if tmp:
            # rechnung gefunden -> setzen
            entry.mapped_rechnung = rechnung

            entry.betrag_passt = entry.betrag == rechnung.gesamtsumme

            # nach mahnungen suchen?
            for mahnung in rechnung.mahnungen:
                entry.betrag_passt = mahnung.mahnsumme == entry.betrag
                if entry.betrag_passt:
                    entry.mapped_mahnung = mahnung

            # erwarteter betrag
            if rechnung.mahnungen:
                entry.erwarteter_betrag = rechnung.mahnungen. \
                    latest('wievielte').mahnsumme
            else:
                entry.erwarteter_betrag = rechnung.gesamtsumme


def suche_user(entry, users, regex_usernames, zuletzt_eingetragen, errors):
    for user in users:
        tmp = regex_usernames[user].fullmatch(entry.verwendungszweck)
        if tmp and zuletzt_eingetragen and zuletzt_eingetragen < entry.datum:
            if entry.mapped_user is not None:
                # If there is a user that was already previously matched,
                # print a duplicate match error and abort the search.
                errors.append('Einzahlung "{}" vom {} hat mehrere Benutzer gematcht: {}, {}.'.format(
                    entry.verwendungszweck,
                    entry.datum,
                    entry.mapped_user,
                    user
                ))
                entry.mapped_user = None
                return
            else:
                # Enter the new user
                entry.mapped_user = user
        elif tmp and zuletzt_eingetragen and zuletzt_eingetragen >= entry.datum:
            # Print an error that this transaction lies beyond the date of the last transaction.
            errors.append('Letzte Einzahlung von {} am {} liegt nach der Einzahlung vom {}.'.format(
                user.user,
                entry.datum,
                zuletzt_eingetragen
            ))
        elif tmp and zuletzt_eingetragen is None:
            errors.append('Nutzer {} hat kein "zuletzt eingetragen" Datum für die Einzahlung vom {}.'.format(
                user.user,
                entry.datum
            ))
