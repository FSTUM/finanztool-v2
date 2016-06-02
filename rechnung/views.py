from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Rechnung
from .models import Kunde
from .models import Kategorie
from .models import Posten
from .models import AnzahlPosten

def index(request):
    letzte_rechnungen_liste = Rechnung.objects.order_by('-rdatum')[:5]
    context = {'letzte_rechnungen_liste': letzte_rechnungen_liste}
    return render(request, 'rechnung/index.html', context)

def rechnung(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)
    return render(request, 'rechnung/rechnung.html', {'rechnung': rechnung})

def rechnungpdf(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % rechnung.rnr

# temporärer ordner für pdfs
#temporäre datei erstellen darin
# da latex code rein
# latex aufrufen (pdflatex)
# fehler prüfne
# keine fehler: ausgeben und ordner löschen
# fehler: meldung


    return response

#def rechnung_add(request):
#    context = {}
#    return render(request, 'rechnung/rechnung_add.html', context)

def kunde(request, kunde_id):
    response = "Kunde %s."
    return HttpResponse(response % kunde_id)

def posten(request, posten_id):
    return HttpResponse("Posten %s." % posten_id)

