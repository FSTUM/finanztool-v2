from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from .forms import KundeForm
from .forms import RechnungForm
from .forms import PostenForm
from .forms import KundeSuchenForm
from .forms import RechnungSuchenForm
from .forms import RechnungBezahltForm

from tempfile import mkdtemp, mkstemp
import os
import subprocess
import shutil

from .models import Rechnung
from .models import Mahnung
from .models import Kunde
from .models import Kategorie
from .models import Posten


def willkommen(request):
    if request.user.is_authenticated():
        offene_rechnungen = Rechnung.objects.filter(gestellt=True,
                                                    bezahlt=False).count()
        context = {'offene_rechnungen': offene_rechnungen}
        return render(request, 'rechnung/willkommen.html', context)
    else:
        return render(request, 'rechnung/willkommen.html')


@login_required
def index(request):
    letzte_rechnungen_liste = Rechnung.objects.filter(bezahlt=False). \
        exclude(name='test').exclude(name='Test').order_by('-rnr')

    context = {
            'letzte_rechnungen_liste': letzte_rechnungen_liste,
            }
    return render(request, 'rechnung/index.html', context)


@login_required
def alle(request):
    rechnungen_liste = Rechnung.objects.order_by('-rnr')
    context = {'rechnungen_liste': rechnungen_liste}
    return render(request, 'rechnung/alle_rechnungen.html', context)


@login_required
def admin(request):
    return render(request, 'rechnung/admin.html')


def login(request):
    return render(request, 'rechnung/login.html')


@login_required
def logout(request):
    return render(request, 'rechnung/logout.html')


# Rechnung#####################################################################


@login_required
def rechnung(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)
    form = RechnungBezahltForm(request.POST or None)
    if request.method == 'POST':
        if 'bezahlt' in request.POST:
            if form.is_valid():
                rechnung.bezahlt = True
                rechnung.save()

                return redirect('rechnung:index')

        elif 'gestellt' in request.POST:
            if form.is_valid():
                rechnung.gestellt = True
                rechnung.save()
                return redirect('rechnung:rechnung', rechnung_id=rechnung.pk)

    context = {'form': form, 'rechnung': rechnung}
    return render(request, 'rechnung/rechnung.html', context)


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
        form = RechnungForm(initial={'ersteller': request.user},
                            instance=rechnung)

    return render(request, 'rechnung/form_rechnung.html',
                  {'form': form, 'rechnung': rechnung})


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


# Mahnung#######################################################################


@login_required
def mahnung(request, mahnung_id):
    mahnung = get_object_or_404(Mahnung, pk=mahnung_id)
    return render(request, 'rechnung/mahnung.html', {'mahnung': mahnung})


@login_required
def alle_mahnungen(request):
    mahnungen_liste = Mahnung.objects.all()
    context = {'mahnungen_liste': mahnungen_liste}
    return render(request, 'rechnung/alle_mahnungen.html', context)


# Kunde#########################################################################


@login_required
def kunde(request, kunde_id):
    kunde = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, 'rechnung/kunde.html', {'kunde': kunde})


@login_required
def form_kunde(request, kunde_id=None):
    kunde = None
    if kunde_id:
        kunde = get_object_or_404(Kunde, pk=kunde_id)
        kunde_verwendet = Rechnung.objects.filter(
                               gestellt=True, kunde=kunde).exists()

    if request.method == "POST":
        form = KundeForm(request.POST, instance=kunde)

        if form.is_valid():
            kunde = form.save()
            return redirect('rechnung:kunde', kunde_id=kunde.pk)
    else:
        form = KundeForm(instance=kunde)

    return render(request, 'rechnung/form_kunde.html', {
                    'form': form,
                    'kunde': kunde,
                    'kunde_verwendet': kunde_verwendet
                    })


@login_required
def kunden_alle(request):
    kunden_liste = Kunde.objects.order_by('-knr')
    context = {'kunden_liste': kunden_liste}
    return render(request, 'rechnung/kunden_alle.html', context)


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


# Posten#######################################################################

@login_required
def posten(request, posten_id):
    posten = get_object_or_404(Posten, pk=posten_id)
    return render(request, 'rechnung/posten.html', {'posten': posten})


# Vorhandenen Posten bearbeiten
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
            return redirect('rechnung:rechnung',
                            rechnung_id=posten.rechnung.pk)
        else:
            form = PostenForm(instance=posten)

        return render(request, 'rechnung/form_posten_aendern.html',
                      {'form': form})


# Neuen Posten zu vorhandener Rechnung hinzufügen
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
                posten = form.save()
                if 'zurueck' in request.POST:
                    return redirect('rechnung:rechnung',
                                    rechnung_id=rechnung.pk)
                else:
                    return redirect('rechnung:rechnung_posten_neu',
                                    rechnung_id=rechnung.pk)
        else:
            form = PostenForm()

        return render(request, 'rechnung/form_posten_neu.html',
                      {'form': form, 'rechnung': rechnung})


# Kategorie####################################################################

@login_required
def kategorie(request):
    kategorien_liste = Kategorie.objects.order_by('name')
    context = {'kategorien_liste': kategorien_liste}
    return render(request, 'rechnung/kategorie.html', context)


@login_required
def kategorie_detail(request, kategorie_id):
    kategorie = get_object_or_404(Kategorie, pk=kategorie_id)
    return render(request, 'rechnung/kategorie_detail.html',
                  {'kategorie': kategorie})


@login_required
def rechnungpdf(request, rechnung_id):
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    # create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix='.tex', dir=tmplatex)

    # Pass TeX template through Django templating engine and into the temp file
    os.write(latex_file, render_to_string('rechnung/latex_rechnung.tex',
                                          {'rechnung': rechnung}).
             encode('utf8'))
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    try:
        subprocess.check_output(["pdflatex", "-halt-on-error",
                                 "-output-directory", tmplatex,
                                 latex_filename])
    except subprocess.CalledProcessError as e:
        return render(request, 'rechnung/rechnungpdf_error.html',
                      {'erroroutput': e.output})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="RE%s_%s.pdf"' % (rechnung.rnr_string, rechnung.kunde.knr)

    # return path to pdf
    pdf_filename = "%s.pdf" % os.path.splitext(latex_filename)[0]

    with open(pdf_filename, 'rb') as f:
        response.write(f.read())

    shutil.rmtree(tmplatex)

    return response
