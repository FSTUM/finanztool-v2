import csv
import datetime
import re

from decimal import Decimal, InvalidOperation

from rechnung.models import Rechnung


class Entry:
    datum = None
    verwendungszweck = None
    zahlungspflichtiger = None
    iban = None
    bic = None
    betrag = None

    mapped_rechnung = None

    def __repr__(self):
        if self.mapped_rechnung:
            rnr = self.mapped_rechnung.rnr_string
        else:
            rnr = None

        return "Entry <datum={}, verwendungszweck=\"{}\", " \
               "zahlungspflichtiger=\"{}\", iban={}, bic={}, betrag={}, " \
               "mapped_rechnung={}" \
               .format(self.datum, self.verwendungszweck,
                       self.zahlungspflichtiger, self.iban, self.bic,
                       self.betrag, rnr)


def parse_camt_csv(csvfile):
    results = []
    errors = []

    # hole alle offenen rechnungen
    offene_rechnungen = Rechnung.objects.filter(gestellt=True,
                                                bezahlt=False).all()
    regex_cache = {}
    for rechnung in offene_rechnungen:
        regex_cache[rechnung] = re.compile('(.*[^0-9])?{}([^0-9].*)?'
                                           .format(rechnung.rnr_string))

    # read CSV file
    csvreader = csv.reader(csvfile, delimiter=';')
    counter = 0
    for row in csvreader:
        counter += 1

        if row[3] == "GUTSCHRIFT":
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

            entry.mapped_rechnung = suche_rechnung(entry, offene_rechnungen,
                                                   regex_cache)

            results.append(entry)

    return results, errors


def suche_rechnung(entry, offene_rechnungen, regex_cache):
    for rechnung in offene_rechnungen:
        tmp = regex_cache[rechnung].match(entry.verwendungszweck)
        if tmp:
            return rechnung

    return None
