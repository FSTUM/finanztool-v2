from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from tempfile import mkdtemp, mkstemp
from subprocess import call
import os
import subprocess
import shutil
import sys

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

    #create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix='.tex', dir=tmplatex)

    # Pass the TeX template through Django templating engine and into the temp file
    os.write(latex_file, render_to_string('rechnung/rechnung.tex', {'content': 'whatever'}).encode('utf8'))
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    try:
        subprocess.check_output(["pdflatex", "-halt-on-error", "-output-directory", tmplatex, latex_filename])
    except subprocess.CalledProcessError as e:
        return render(request, 'rechnung/rechnungpdf_error.html', { 'erroroutput': e.output })


    # replace '%RECHNUNGSINHALT%'
#    latex = template.replace('%RECHNUNGSINHALT%', latex_code)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="RE%s.pdf"' % rechnung.rnr

# da latex code rein
# latex aufrufen (pdflatex)
# fehler prüfne
# keine fehler: ausgeben und ordner löschen
# fehler: meldung

    # return path to pdf
    pdf_filename= "%s.pdf" % os.path.splitext(latex_filename)[0]

    with open(pdf_filename, 'rb') as f:
        response.write(f.read())

    return response


#def rechnung_add(request):
#    context = {}
#    return render(request, 'rechnung/rechnung_add.html', context)


def kunde(request, kunde_id):
    response = "Kunde %s."
    return HttpResponse(response % kunde_id)


def posten(request, posten_id):
    return HttpResponse("Posten %s." % posten_id)

