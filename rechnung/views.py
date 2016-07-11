from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required

from .forms import KundeForm
from .forms import RechnungForm
from .forms import PostenForm
from .forms import KundeSuchenForm
from .forms import RechnungSuchenForm

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

def willkommen(request):
    return render(request, 'rechnung/willkommen.html')

@login_required
def index(request):
    letzte_rechnungen_liste = Rechnung.objects.order_by('-rnr')[:10]
    context = {'letzte_rechnungen_liste': letzte_rechnungen_liste}
    return render(request, 'rechnung/index.html', context)

@login_required
def admin(request):
    return render(request, 'rechnung/admin.html')

def login(request):
    return render(request, 'rechnung/login.html')

@login_required
def logout(request):
    return render(request, 'rechnung/logout.html')


#Rechnung#####################################################################

@login_required
def rechnung(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)
    return render(request, 'rechnung/rechnung.html', {'rechnung': rechnung})

@login_required
def form_rechnung(request, rechnung_id=None):
    rechnung = None
    if rechnung_id:
        rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    if request.method == "POST":
        form = RechnungForm(request.POST, instance=rechnung)

        if form.is_valid():
            rechnung = form.save()
            return redirect('rechnung:rechnung', rechnung_id=rechnung.pk)
    else:
        form = RechnungForm(initial={'ersteller':request.user}, instance=rechnung)

    return render(request, 'rechnung/form_rechnung.html', {'form': form, 'rechnung':rechnung})


@login_required
def rechnungsuchen(request):
    form = RechnungSuchenForm(request.POST or None)

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

    return render(request, 'rechnung/rechnungsuchen.html', context)


#Kunde########################################################################

@login_required
def kunde(request, kunde_id):
    kunde = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, 'rechnung/kunde.html', {'kunde': kunde})


@login_required
def form_kunde(request, kunde_id=None):
    kunde = None
    if kunde_id:
        kunde = get_object_or_404(Kunde, pk=kunde_id)

    if request.method == "POST":
        form = KundeForm(request.POST, instance=kunde)

        if form.is_valid():
            kunde = form.save()
            return redirect('rechnung:kunde', kunde_id=kunde.pk)
    else:
        form = KundeForm(instance=kunde)

    return render(request, 'rechnung/form_kunde.html', {'form': form, 'kunde':kunde})

@login_required
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


#Posten#######################################################################

@login_required
def posten(request, posten_id):
    posten = get_object_or_404(Posten, pk=posten_id)
    return render(request, 'rechnung/posten.html', {'posten': posten})

#Vorhandenen Posten bearbeiten
@login_required
def form_exist_posten(request, posten_id):
    posten = get_object_or_404(Posten, pk=posten_id)

    if posten.rechnung.gestellt:
        return redirect('rechnung:rechnung', rechnung_id=posten.rechnung.pk)
    else:
        if request.method == "POST":
            form = PostenForm(request.POST, instance=posten)

            if 'loeschen' in request.POST:
                posten.delete()
            else:
                if form.is_valid():
                    posten = form.save()
            return redirect('rechnung:rechnung', rechnung_id=posten.rechnung.pk)
        else:
            form = PostenForm(instance=posten)

        return render(request, 'rechnung/form_posten_aendern.html', {'form': form})

#Neuen Posten zu vorhandener Rechnung hinzufügen
@login_required
def form_rechnung_posten(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    if rechnung.gestellt:
        return redirect('rechnung:rechnung', rechnung_id=rechnung.pk)
    else:
        if request.method == "POST":
            form = PostenForm(request.POST, instance=Posten())

            if form.is_valid():
                posten = form.save(commit=False)
                posten.rechnung = rechnung
                pisten = form.save()
                if 'zurueck' in request.POST:
                    return redirect('rechnung:rechnung', rechnung_id=rechnung.pk)
                else:
                    return redirect('rechnung:rechnung_posten_neu', rechnung_id=rechnung.pk)
        else:
            form = PostenForm()

        return render(request, 'rechnung/form_posten_neu.html', {'form': form, 'rechnung':rechnung})


#Kategorie####################################################################

@login_required
def kategorie(request):
    kategorien_liste = Kategorie.objects.order_by('name')
    context = {'kategorien_liste': kategorien_liste}
    return render(request, 'rechnung/kategorie.html', context)

@login_required
def kategorie_detail(request, kategorie_id):
    kategorie = get_object_or_404(Kategorie, pk=kategorie_id)
    return render(request, 'rechnung/kategorie_detail.html', {'kategorie': kategorie})

@login_required
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
    response['Content-Disposition'] = 'attachment; filename="RE%s_%s.pdf"' % (rechnung.rnr_string, rechnung.kunde.knr)

    # return path to pdf
    pdf_filename= "%s.pdf" % os.path.splitext(latex_filename)[0]

    with open(pdf_filename, 'rb') as f:
        response.write(f.read())

    shutil.rmtree(tmplatex)

    return response
