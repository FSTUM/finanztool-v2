import os
import subprocess
from tempfile import mkdtemp, mkstemp
from typing import Callable

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from aufgaben.models import Aufgabe
from schluessel.models import Key

from .forms import (
    KundeForm,
    KundeSuchenForm,
    MahnungForm,
    MahnungStatusForm,
    PostenForm,
    RechnungBezahltForm,
    RechnungForm,
    RechnungSuchenForm,
)
from .models import Kategorie, Kunde, Mahnung, Posten, Rechnung

finanz_staff_member_required: Callable = staff_member_required(login_url="rechnung:login")


@login_required
def willkommen(request: WSGIRequest) -> HttpResponse:
    rechnungen = Rechnung.objects.filter(gestellt=True, erledigt=False).all()
    offene_rechnungen = rechnungen.count()
    faellige_rechnungen = len(list(filter(lambda r: r.faellig, rechnungen)))
    eigene_aufgaben = Aufgabe.objects.filter(
        erledigt=False,
        zustaendig=request.user,
    ).count()
    schluessel = Key.objects.filter(active=True).count()
    verfuegbare_schluessel = Key.objects.filter(
        active=True,
        person=None,
    ).count()
    context = {
        "offene_rechnungen": offene_rechnungen,
        "faellige_rechnungen": faellige_rechnungen,
        "eigene_aufgaben": eigene_aufgaben,
        "schluessel": schluessel,
        "verfuegbare_schluessel": verfuegbare_schluessel,
    }
    return render(request, "rechnung/willkommen.html", context)


@finanz_staff_member_required
def index(request: WSGIRequest) -> HttpResponse:
    unerledigte_rechnungen = (
        Rechnung.objects.filter(erledigt=False).exclude(name="test").exclude(name="Test").order_by("-rnr")
    )
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")

    context = {
        "unerledigte_rechnungen": unerledigte_rechnungen,
        "aufgaben": aufgaben,
    }
    return render(request, "rechnung/index.html", context)


@finanz_staff_member_required
def alle(request: WSGIRequest) -> HttpResponse:
    rechnungen_liste = Rechnung.objects.order_by("-rnr")
    context = {"rechnungen_liste": rechnungen_liste}
    return render(request, "rechnung/alle_rechnungen.html", context)


@finanz_staff_member_required
def admin(request: WSGIRequest) -> HttpResponse:
    return render(request, "rechnung/admin.html")


def login(request: WSGIRequest) -> HttpResponse:
    return render(request, "registration/login.html")


@finanz_staff_member_required
def logout(request: WSGIRequest) -> HttpResponse:
    return render(request, "registration/logout.html")


# Rechnung#####################################################################


@finanz_staff_member_required
def rechnung(request: WSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung_obj: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnungen: Mahnung = Mahnung.objects.filter(rechnung=rechnung_obj.pk)
    form = RechnungBezahltForm(request.POST or None)
    if request.method == "POST":
        if "bezahlt" in request.POST:
            if form.is_valid():
                rechnung_obj.bezahlen()

                return redirect("rechnung:index")

        elif "gestellt" in request.POST:
            if form.is_valid():
                rechnung_obj.gestellt = True
                rechnung_obj.save()
                return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)

    context = {"form": form, "rechnung": rechnung_obj, "mahnungen": mahnungen}
    return render(request, "rechnung/rechnung.html", context)


@finanz_staff_member_required
def form_rechnung(request: WSGIRequest, rechnung_id=None) -> HttpResponse:
    rechnung_obj = None
    if rechnung_id:
        rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    if request.method == "POST":
        form = RechnungForm(request.POST, instance=rechnung_obj)

        if form.is_valid():
            rechnung_obj = form.save()
            return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)
    else:
        form = RechnungForm(
            initial={"ersteller": request.user},
            instance=rechnung_obj,
        )

    return render(
        request,
        "rechnung/form_rechnung.html",
        {"form": form, "rechnung": rechnung_obj},
    )


@finanz_staff_member_required
def duplicate_rechnung(request: WSGIRequest, rechnung_id) -> HttpResponse:
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    initial = {
        "name": rechnung.name,
        "kunde": rechnung.kunde,
        "einleitung": rechnung.einleitung,
        "kategorie": rechnung.kategorie,
    }

    form = RechnungForm(request.POST or None, initial=initial)
    if form.is_valid():
        rechnung_neu = form.save()

        alle_posten = rechnung.posten_set.all()
        for new_posten in alle_posten:
            Posten.objects.create(
                rechnung=rechnung_neu,
                name=new_posten.name,
                einzelpreis=new_posten.einzelpreis,
                mwst=new_posten.mwst,
                anzahl=new_posten.anzahl,
            )

        return redirect("rechnung:rechnung", rechnung_id=rechnung_neu.pk)

    return render(
        request,
        "rechnung/rechnung_duplizieren.html",
        {"form": form, "rechnung": rechnung},
    )


@finanz_staff_member_required
def rechnungsuchen(request: WSGIRequest) -> HttpResponse:
    form = RechnungSuchenForm(request.POST or None)

    result = None
    new_search = True

    if form.is_valid():
        result = form.get()
        new_search = False

    context = {
        "form": form,
        "result": result,
        "new_search": new_search,
    }

    return render(request, "rechnung/rechnungsuchen.html", context)


# Mahnung#######################################################################


@finanz_staff_member_required
def mahnung(request: WSGIRequest, rechnung_id, mahnung_id) -> HttpResponse:
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung = get_object_or_404(Mahnung, pk=mahnung_id)
    if mahnung.rechnung != rechnung:
        raise Http404

    form = MahnungStatusForm(request.POST or None)
    if request.method == "POST":
        if "bezahlt" in request.POST:
            if form.is_valid():
                mahnung.bezahlen()
                return redirect(
                    "rechnung:mahnung",
                    rechnung_id=rechnung.pk,
                    mahnung_id=mahnung.pk,
                )

        elif "geschickt" in request.POST:
            if form.is_valid():
                mahnung.geschickt = True
                mahnung.save()
                return redirect(
                    "rechnung:mahnung",
                    rechnung_id=rechnung.pk,
                    mahnung_id=mahnung.pk,
                )

    context = {
        "form": form,
        "rechnung": rechnung,
        "mahnung": mahnung,
    }
    return render(request, "rechnung/mahnung.html", context)


@finanz_staff_member_required
def form_mahnung(request: WSGIRequest, rechnung_id, mahnung_id=None) -> HttpResponse:
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung = None
    if mahnung_id:
        mahnung = get_object_or_404(Mahnung, pk=mahnung_id)
        if mahnung.rechnung != rechnung:
            raise Http404

    if request.method == "POST":
        form = MahnungForm(request.POST, rechnung=rechnung, instance=mahnung)

        if form.is_valid():
            mahnung = form.save()
            return redirect(
                "rechnung:mahnung",
                rechnung_id=rechnung.pk,
                mahnung_id=mahnung.pk,
            )
    else:
        form = MahnungForm(
            initial={"ersteller": request.user},
            rechnung=rechnung,
            instance=mahnung,
        )

    return render(
        request,
        "rechnung/form_mahnung.html",
        {"form": form, "rechnung": rechnung, "mahnung": mahnung},
    )


@finanz_staff_member_required
def alle_mahnungen(request: WSGIRequest) -> HttpResponse:
    rechnungen = Rechnung.objects.all().order_by("-rnr")
    context = {"rechnungen": rechnungen}
    return render(request, "rechnung/alle_mahnungen.html", context)


# Kunde#########################################################################


@finanz_staff_member_required
def kunde(request: WSGIRequest, kunde_id) -> HttpResponse:
    kunde = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, "rechnung/kunde.html", {"kunde": kunde})


@finanz_staff_member_required
def form_kunde(request, kunde_id=None) -> HttpResponse:
    kunde = None
    kunde_verwendet = None
    if kunde_id:
        kunde = get_object_or_404(Kunde, pk=kunde_id)
        kunde_verwendet = Rechnung.objects.filter(
            gestellt=True,
            kunde=kunde,
        ).exists()

    if request.method == "POST":
        form = KundeForm(request.POST, instance=kunde)

        if form.is_valid():
            kunde = form.save()
            return redirect("rechnung:kunde", kunde_id=kunde.pk)
    else:
        form = KundeForm(instance=kunde)

    return render(
        request,
        "rechnung/form_kunde.html",
        {
            "form": form,
            "kunde": kunde,
            "kunde_verwendet": kunde_verwendet,
        },
    )


@finanz_staff_member_required
def kunden_alle(request: WSGIRequest) -> HttpResponse:
    kunden_liste = Kunde.objects.order_by("-knr")
    context = {"kunden_liste": kunden_liste}
    return render(request, "rechnung/kunden_alle.html", context)


@finanz_staff_member_required
def kundesuchen(request: WSGIRequest) -> HttpResponse:
    form = KundeSuchenForm(request.POST or None)

    result = None
    new_search = True

    if form.is_valid():
        result = form.get()
        new_search = False

    context = {
        "form": form,
        "result": result,
        "new_search": new_search,
    }

    return render(request, "rechnung/kundesuchen.html", context)


# Posten#######################################################################


@finanz_staff_member_required
def posten(request: WSGIRequest, posten_id) -> HttpResponse:
    posten = get_object_or_404(Posten, pk=posten_id)
    return render(request, "rechnung/posten.html", {"posten": posten})


# Vorhandenen Posten bearbeiten
@finanz_staff_member_required
def form_exist_posten(request: WSGIRequest, posten_id) -> HttpResponse:
    posten = get_object_or_404(Posten, pk=posten_id)

    if posten.rechnung.gestellt:
        return redirect("rechnung:rechnung", rechnung_id=posten.rechnung.pk)
    else:
        if request.method == "POST":
            form = PostenForm(request.POST, instance=posten)

            if "loeschen" in request.POST:
                posten.delete()
            else:
                if form.is_valid():
                    posten = form.save()
            return redirect(
                "rechnung:rechnung",
                rechnung_id=posten.rechnung.pk,
            )
        else:
            form = PostenForm(instance=posten)

        return render(
            request,
            "rechnung/form_posten_aendern.html",
            {"form": form},
        )


# Neuen Posten zu vorhandener Rechnung hinzufügen
@finanz_staff_member_required
def form_rechnung_posten(request: WSGIRequest, rechnung_id) -> HttpResponse:
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    if rechnung.gestellt:
        return redirect("rechnung:rechnung", rechnung_id=rechnung.pk)
    else:
        if request.method == "POST":
            form = PostenForm(request.POST, instance=Posten())

            if form.is_valid():
                posten = form.save(commit=False)
                posten.rechnung = rechnung
                posten = form.save()
                if "zurueck" in request.POST:
                    return redirect(
                        "rechnung:rechnung",
                        rechnung_id=rechnung.pk,
                    )
                else:
                    return redirect(
                        "rechnung:rechnung_posten_neu",
                        rechnung_id=rechnung.pk,
                    )
        else:
            form = PostenForm()

        return render(
            request,
            "rechnung/form_posten_neu.html",
            {"form": form, "rechnung": rechnung},
        )


# Kategorie####################################################################


@finanz_staff_member_required
def kategorie(request: WSGIRequest) -> HttpResponse:
    kategorien_liste = Kategorie.objects.order_by("name")
    context = {"kategorien_liste": kategorien_liste}
    return render(request, "rechnung/kategorie.html", context)


@finanz_staff_member_required
def kategorie_detail(request: WSGIRequest, kategorie_id) -> HttpResponse:
    kategorie = get_object_or_404(Kategorie, pk=kategorie_id)
    return render(
        request,
        "rechnung/kategorie_detail.html",
        {"kategorie": kategorie},
    )


@finanz_staff_member_required
def rechnungpdf(request: WSGIRequest, rechnung_id, mahnung_id=None) -> HttpResponse:
    rechnung = get_object_or_404(Rechnung, pk=rechnung_id)
    mahnung = None
    if mahnung_id:
        mahnung = get_object_or_404(Mahnung, pk=mahnung_id)
        vorherige_mahnungen = (
            Mahnung.objects.filter(
                rechnung=mahnung.rechnung,
                wievielte__lt=mahnung.wievielte,
            )
            .order_by("wievielte")
            .all()
        )

    # create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix=".tex", dir=tmplatex)

    # Pass TeX template through Django templating engine and into the temp file
    if mahnung_id:
        context = {
            "mahnung": mahnung,
            "rechnung": rechnung,
            "vorherige_mahnungen": vorherige_mahnungen,
        }
    else:
        context = {"rechnung": rechnung}

    os.write(
        latex_file,
        render_to_string(
            "rechnung/latex_rechnung.tex",
            context,
        ).encode("utf8"),
    )
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    try:
        subprocess.check_output(
            [
                "pdflatex",
                "-halt-on-error",
                "-output-directory",
                tmplatex,
                latex_filename,
            ],
        )
    except subprocess.CalledProcessError as e:
        return render(
            request,
            "rechnung/rechnungpdf_error.html",
            {"erroroutput": e.output},
        )

    response = HttpResponse(content_type="application/pdf")
    if mahnung_id:
        response[
            "Content-Disposition"
        ] = f'attachment; filename="RE{rechnung.rnr_string}_{rechnung.kunde.knr}_M{mahnung.wievielte}.pdf"'
    else:
        response["Content-Disposition"] = f'attachment;filename="RE{rechnung.rnr_string}_{rechnung.kunde.knr}.pdf"'

    # return path to pdf
    pdf_filename = f"{os.path.splitext(latex_filename)[0]}.pdf"

    with open(pdf_filename, "rb") as pdf:
        response.write(pdf.read())
    # shutil.rmtree(tmplatex)

    return response
