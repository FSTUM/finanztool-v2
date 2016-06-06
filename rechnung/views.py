from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from .forms import KundeForm
from .forms import RechnungForm
from .forms import KategorieForm
from .forms import KundeSuchenForm

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
    letzte_rechnungen_liste = Rechnung.objects.order_by('-rdatum')[:10]
    context = {'letzte_rechnungen_liste': letzte_rechnungen_liste}
    return render(request, 'rechnung/index.html', context)


#Rechnung#####################################################################

def rechnung(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)
#    anzahlposten = get_object_or_404(AnzahlPosten, pk=rechnung_id)
    return render(request, 'rechnung/rechnung.html', {'rechnung': rechnung})
#    return render(request, 'rechnung/rechnung.html', {'rechnung': rechnung},{'anzahlposten':anzahlposten})

def rechnungsuchen(request):
    return render(request, 'rechnung/rechnungsuchen.html')

def rechnungpdf(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    #create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix='.tex', dir=tmplatex)

    # Pass the TeX template through Django templating engine and into the temp file
    os.write(latex_file, render_to_string('rechnung/latex_rechnung.tex', {'rechnung': rechnung}).encode('utf8'))
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    try:
        subprocess.check_output(["pdflatex", "-halt-on-error", "-output-directory", tmplatex, latex_filename])
    except subprocess.CalledProcessError as e:
        return render(request, 'rechnung/rechnungpdf_error.html', { 'erroroutput': e.output })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="RE%s.pdf"' % rechnung.rnr

    # return path to pdf
    pdf_filename= "%s.pdf" % os.path.splitext(latex_filename)[0]

    with open(pdf_filename, 'rb') as f:
        response.write(f.read())

    shutil.rmtree(tmplatex)

    return response


def form_rechnung(request):
    if request.method == "POST":
        form = RechnungForm(request.POST)

        if form.is_valid():
            rechnung = form.save()
            return redirect('rechnung:rechnung', rechnung_id=rechnung.pk)
    else:
        form = RechnungForm()

    return render(request, 'rechnung/form_rechnung.html', {'form': form})


#Kunde########################################################################

def kunde(request, kunde_id):
    kunde = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, 'rechnung/kunde.html', {'kunde': kunde})

def kundesuchen(request):

    form = KundeSuchenForm(request.POST or None)

    result = None
    new_search = True

    if form.is_valid():
        result = form.get()
        new_search = False

    context = {
            'form': form,
            'result': result,
            'new_search': new_search
            }

    return render(request, 'rechnung/kundesuchen.html', context)

def form_kunde(request):
    if request.method == "POST":
        form = KundeForm(request.POST)

        if form.is_valid():
            kunde = form.save()
            return redirect('rechnung:kunde', kunde_id=kunde.pk)
    else:
        form = KundeForm()

    return render(request, 'rechnung/form_kunde.html', {'form': form})


#Posten#######################################################################

def posten(request, posten_id):
    return HttpResponse("Posten %s." % posten_id)


#Kategorie####################################################################

def kategorie(request, kategorie_id):
    kategorie = get_object_or_404(Kategorie, pk=kategorie_id)
    return render(request, 'rechnung/kategorie.html', {'kategorie': kategorie})

def form_kategorie(request):
    if request.method == "POST":
        form = KategorieForm(request.POST)

        if form.is_valid():
            kategorie = form.save()
            return redirect('rechnung:kategorie', kategorie_id=kategorie.pk)
    else:
        form = KategorieForm()

    return render(request, 'rechnung/form_kategorie.html', {'form': form})
