import os
import subprocess  # nosec: fully defined
from tempfile import mkdtemp, mkstemp
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from aufgaben.models import Aufgabe
from common.views import AuthWSGIRequest, finanz_staff_member_required
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


@login_required(login_url="login")
def willkommen(request: AuthWSGIRequest) -> HttpResponse:
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
def unerledigt(request: AuthWSGIRequest) -> HttpResponse:
    unerledigte_rechnungen = (
        Rechnung.objects.filter(erledigt=False).exclude(name="test").exclude(name="Test").order_by("-rnr")
    )
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")

    context = {
        "unerledigte_rechnungen": unerledigte_rechnungen,
        "aufgaben": aufgaben,
        "not_rechnung": True,
    }
    return render(request, "rechnung/index.html", context)


@finanz_staff_member_required
def alle(request: AuthWSGIRequest) -> HttpResponse:
    rechnungen_liste = Rechnung.objects.order_by("-rnr")
    context = {"rechnungen_liste": rechnungen_liste}
    return render(request, "rechnung/alle_rechnungen.html", context)


@finanz_staff_member_required
def admin(request: AuthWSGIRequest) -> HttpResponse:
    return render(request, "rechnung/admin.html")


# Rechnung#####################################################################


@finanz_staff_member_required
def rechnung(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung_obj: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnungen: QuerySet[Mahnung] = Mahnung.objects.filter(rechnung=rechnung_obj.pk).all()
    form = RechnungBezahltForm(request.POST or None)
    if request.method == "POST":
        if "bezahlt" in request.POST and form.is_valid():
            rechnung_obj.bezahlen()
            return redirect("rechnung:unerledigt")

        if "gestellt" in request.POST and form.is_valid():
            rechnung_obj.gestellt = True
            rechnung_obj.save()
            return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)

    context = {"form": form, "rechnung": rechnung_obj, "mahnungen": mahnungen}
    return render(request, "rechnung/rechnung.html", context)


@finanz_staff_member_required
def form_rechnung(request: AuthWSGIRequest, rechnung_id: Optional[int] = None) -> HttpResponse:
    rechnung_obj: Optional[Rechnung] = None
    if rechnung_id:
        rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    if request.method == "POST":
        form = RechnungForm(request.POST, instance=rechnung_obj)

        if form.is_valid():
            rechnung_form_obj: Rechnung = form.save()
            return redirect("rechnung:rechnung", rechnung_id=rechnung_form_obj.pk)
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
def duplicate_rechnung(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    initial = {
        "name": rechnung_obj.name,
        "kunde": rechnung_obj.kunde,
        "einleitung": rechnung_obj.einleitung,
        "kategorie": rechnung_obj.kategorie,
    }

    form = RechnungForm(request.POST or None, initial=initial)
    if form.is_valid():
        rechnung_neu = form.save()

        alle_posten = rechnung_obj.posten_set.all()
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
        {"form": form, "rechnung": rechnung_obj},
    )


@finanz_staff_member_required
def rechnungsuchen(request: AuthWSGIRequest) -> HttpResponse:
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
def mahnung(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: int) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung_obj = get_object_or_404(Mahnung, pk=mahnung_id)
    if mahnung_obj.rechnung != rechnung_obj:
        raise Http404

    form = MahnungStatusForm(request.POST or None)
    if request.method == "POST":
        if "bezahlt" in request.POST and form.is_valid():
            mahnung_obj.bezahlen()
            return redirect("rechnung:mahnung", rechnung_id=rechnung_obj.pk, mahnung_id=mahnung_obj.pk)

        if "geschickt" in request.POST and form.is_valid():
            mahnung_obj.geschickt = True
            mahnung_obj.save()
            return redirect("rechnung:mahnung", rechnung_id=rechnung_obj.pk, mahnung_id=mahnung_obj.pk)

    context = {
        "form": form,
        "rechnung": rechnung_obj,
        "mahnung": mahnung_obj,
    }
    return render(request, "rechnung/mahnung.html", context)


@finanz_staff_member_required
def form_mahnung(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: Optional[int] = None) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung_obj: Optional[Mahnung] = None
    if mahnung_id:
        mahnung_obj = get_object_or_404(Mahnung, pk=mahnung_id)
        if mahnung_obj.rechnung != rechnung_obj:
            raise Http404

    if request.method == "POST":
        form = MahnungForm(request.POST, rechnung=rechnung_obj, instance=mahnung_obj)

        if form.is_valid():
            mahnung_form_obj: Mahnung = form.save()
            return redirect(
                "rechnung:mahnung",
                rechnung_id=rechnung_obj.pk,
                mahnung_id=mahnung_form_obj.pk,
            )
    else:
        form = MahnungForm(
            initial={"ersteller": request.user},
            rechnung=rechnung_obj,
            instance=mahnung_obj,
        )

    return render(
        request,
        "rechnung/form_mahnung.html",
        {"form": form, "rechnung": rechnung_obj, "mahnung": mahnung_obj},
    )


@finanz_staff_member_required
def alle_mahnungen(request: AuthWSGIRequest) -> HttpResponse:
    rechnungen = Rechnung.objects.all().order_by("-rnr")
    context = {"rechnungen": rechnungen}
    return render(request, "rechnung/alle_mahnungen.html", context)


# Kunde#########################################################################


@finanz_staff_member_required
def kunde(request: AuthWSGIRequest, kunde_id: int) -> HttpResponse:
    kunde_obj = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, "rechnung/kunde.html", {"kunde": kunde_obj, "not_rechnung": True})


@finanz_staff_member_required
def form_kunde(request: AuthWSGIRequest, kunde_id: Optional[int] = None) -> HttpResponse:
    kunde_obj = None
    kunde_verwendet = None
    if kunde_id:
        kunde_obj = get_object_or_404(Kunde, pk=kunde_id)
        kunde_verwendet = Rechnung.objects.filter(
            gestellt=True,
            kunde=kunde_obj,
        ).exists()

    if request.method == "POST":
        form = KundeForm(request.POST, instance=kunde_obj)

        if form.is_valid():
            kunde_pk: int = form.save().pk
            return redirect("rechnung:kunde", kunde_id=kunde_pk)
    else:
        form = KundeForm(instance=kunde_obj)

    return render(
        request,
        "rechnung/form_kunde.html",
        {
            "form": form,
            "kunde": kunde_obj,
            "kunde_verwendet": kunde_verwendet,
            "not_rechnung": True,
        },
    )


@finanz_staff_member_required
def kunden_alle(request: AuthWSGIRequest) -> HttpResponse:
    kunden_liste = Kunde.objects.order_by("-knr")
    context = {"kunden_liste": kunden_liste, "not_rechnung": True}
    return render(request, "rechnung/kunden_alle.html", context)


@finanz_staff_member_required
def kundesuchen(request: AuthWSGIRequest) -> HttpResponse:
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
        "not_rechnung": True,
    }

    return render(request, "rechnung/kundesuchen.html", context)


# Posten#######################################################################


@finanz_staff_member_required
def posten(request: AuthWSGIRequest, posten_id: int) -> HttpResponse:
    posten_obj = get_object_or_404(Posten, pk=posten_id)
    return render(request, "rechnung/posten.html", {"posten": posten_obj})


# Vorhandenen Posten bearbeiten
@finanz_staff_member_required
def form_exist_posten(request: AuthWSGIRequest, posten_id: int) -> HttpResponse:
    posten_obj = get_object_or_404(Posten, pk=posten_id)

    if posten_obj.rechnung.gestellt:
        return redirect("rechnung:rechnung", rechnung_id=posten_obj.rechnung.pk)
    if request.method == "POST":
        form = PostenForm(request.POST, instance=posten_obj)

        if "loeschen" in request.POST:
            posten_obj.delete()
        elif form.is_valid():
            posten_obj = form.save()
        return redirect("rechnung:rechnung", rechnung_id=posten_obj.rechnung.pk)
    context = {"form": PostenForm(instance=posten_obj)}
    return render(request, "rechnung/form_posten_aendern.html", context)


# Neuen Posten zu vorhandener Rechnung hinzufügen
@finanz_staff_member_required
def form_rechnung_posten(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    if rechnung_obj.gestellt:
        return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)
    if request.method == "POST":
        form = PostenForm(request.POST, instance=Posten())

        if form.is_valid():
            posten_obj = form.save(commit=False)
            posten_obj.rechnung = rechnung_obj
            posten_obj = form.save()  # TODO: WTF??
            if "zurueck" in request.POST:
                return redirect(
                    "rechnung:rechnung",
                    rechnung_id=rechnung_obj.pk,
                )
            return redirect(
                "rechnung:rechnung_posten_neu",
                rechnung_id=rechnung_obj.pk,
            )
    return render(
        request,
        "rechnung/form_posten_neu.html",
        {"form": PostenForm(), "rechnung": rechnung_obj},
    )


# Kategorie####################################################################


@finanz_staff_member_required
def kategorie(request: AuthWSGIRequest) -> HttpResponse:
    kategorien_liste = Kategorie.objects.order_by("name")
    context = {"kategorien_liste": kategorien_liste}
    return render(request, "rechnung/kategorie.html", context)


@finanz_staff_member_required
def kategorie_detail(request: AuthWSGIRequest, kategorie_id: int) -> HttpResponse:
    kategorie_obj = get_object_or_404(Kategorie, pk=kategorie_id)
    return render(request, "rechnung/kategorie_detail.html", {"kategorie": kategorie_obj})


@finanz_staff_member_required
def rechnungpdf(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: Optional[int] = None) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)
    mahnung_obj = None

    if mahnung_id:
        mahnung_obj = get_object_or_404(Mahnung, pk=mahnung_id)
        vorherige_mahnungen = (
            Mahnung.objects.filter(
                rechnung=mahnung_obj.rechnung,
                wievielte__lt=mahnung_obj.wievielte,
            )
            .order_by("wievielte")
            .all()
        )
        context = {
            "mahnung": mahnung_obj,
            "rechnung": rechnung_obj,
            "vorherige_mahnungen": vorherige_mahnungen,
        }
    else:
        context = {"rechnung": rechnung_obj}

    # create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix=".tex", dir=tmplatex)

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
        subprocess.check_output(  # nosec: fully defined
            [
                "pdflatex",
                "-halt-on-error",
                "-output-directory",
                tmplatex,
                latex_filename,
            ],
        )
    except subprocess.CalledProcessError as error:
        return render(
            request,
            "rechnung/rechnungpdf_error.html",
            {"erroroutput": error.output},
        )

    response = HttpResponse(content_type="application/pdf")
    content_disposition = f'attachment; filename="RE{rechnung_obj.rnr_string}_{rechnung_obj.kunde.knr}'
    if mahnung_id and mahnung_obj:
        content_disposition += f"_M{mahnung_obj.wievielte}"
    response["Content-Disposition"] = content_disposition + '.pdf"'

    # return path to pdf
    pdf_filename = f"{os.path.splitext(latex_filename)[0]}.pdf"

    with open(pdf_filename, "rb") as pdf:
        response.write(pdf.read())
    # shutil.rmtree(tmplatex)

    return response
