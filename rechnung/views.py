import os
import shutil
import subprocess  # nosec: fully defined
from tempfile import mkdtemp, mkstemp
from typing import Any, Dict, Optional, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, QuerySet
from django.forms import forms
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from paramiko.ssh_exception import AuthenticationException
from storages.backends.sftpstorage import SFTPStorage
from storages.base import ImproperlyConfigured

from aufgaben.models import Aufgabe
from common.views import AuthWSGIRequest, finanz_staff_member_required
from schluessel.models import Key

from .forms import FilterRechnungenForm, KategorieForm, KundeForm, MahnungForm, PostenForm, RechnungForm
from .models import Kategorie, Kunde, Mahnung, Posten, Rechnung


@login_required(login_url="two_factor:login")
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
    return render(request, "common/willkommen.html", context)


@finanz_staff_member_required
def dashboard(request: AuthWSGIRequest) -> HttpResponse:
    unerledigte_rechnungen = (
        Rechnung.objects.filter(erledigt=False).exclude(name="test").exclude(name="Test").order_by("-rnr")
    )
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")

    context = {
        "unerledigte_rechnungen": unerledigte_rechnungen,
        "aufgaben": aufgaben,
        "not_rechnung": True,
    }
    return render(request, "rechnung/rechnung_dashboard.html", context)


@finanz_staff_member_required
def list_rechnungen(request: AuthWSGIRequest, kategorie_pk_filter: Optional[int] = None) -> HttpResponse:
    rechnungen_liste = Rechnung.objects.order_by("-rnr")  #

    form = FilterRechnungenForm(request.POST or None)
    if kategorie_pk_filter:
        kategorie: Kategorie = get_object_or_404(Kategorie, pk=kategorie_pk_filter)
        rechnungen_liste = rechnungen_liste.filter(kategorie=kategorie)

        form = FilterRechnungenForm(request.POST or None, initial={"kategorie": kategorie})

    if form.is_valid():
        kategorie = form.cleaned_data["kategorie"]
        return redirect("rechnung:list_rechnungen_filter", kategorie_pk_filter=kategorie.pk)
    context = {
        "rechnungen_liste": rechnungen_liste,
        "form": form,
    }
    return render(request, "rechnung/rechnungen/list_rechnungen.html", context)


# Rechnung#####################################################################


@finanz_staff_member_required
def rechnung(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung_obj: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnungen: QuerySet[Mahnung] = Mahnung.objects.filter(rechnung=rechnung_obj.pk).all()
    form = forms.Form(request.POST or None)
    if request.method == "POST":
        if "bezahlt" in request.POST and form.is_valid():
            rechnung_obj.bezahlen()
            return redirect("rechnung:dashboard")

        if "gestellt" in request.POST and form.is_valid():
            rechnung_obj.gestellt = True
            rechnung_obj.save()
            return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)

    context = {"form": form, "rechnung": rechnung_obj, "mahnungen": mahnungen}
    return render(request, "rechnung/rechnungen/rechnung.html", context)


@finanz_staff_member_required
def form_rechnung(request: AuthWSGIRequest, rechnung_id: Optional[int] = None) -> HttpResponse:
    rechnung_obj: Optional[Rechnung] = None
    if rechnung_id:
        rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    form = RechnungForm(request.POST or None, instance=rechnung_obj, initial={"ersteller": request.user})

    if form.is_valid():
        rechnung_form_obj: Rechnung = form.save()
        if rechnung_form_obj.erledigt:
            gen_rechnung_upload_to_sftp(request, rechnung_form_obj.id)
        return redirect("rechnung:rechnung", rechnung_id=rechnung_form_obj.pk)

    context = {"form": form, "rechnung": rechnung_obj}
    return render(request, "rechnung/rechnungen/form_rechnung.html", context)


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
        "rechnung/rechnungen/rechnung_duplizieren.html",
        {"form": form, "rechnung": rechnung_obj},
    )


# Mahnung#######################################################################


@finanz_staff_member_required
def mahnung(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: int) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung_obj = get_object_or_404(Mahnung, pk=mahnung_id)
    if mahnung_obj.rechnung != rechnung_obj:
        raise Http404

    form = forms.Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if "bezahlt" in request.POST:
            mahnung_obj.bezahlen()
            return redirect("rechnung:mahnung", rechnung_id=rechnung_obj.pk, mahnung_id=mahnung_obj.pk)

        if "geschickt" in request.POST:
            mahnung_obj.geschickt = True
            mahnung_obj.save()
            return redirect("rechnung:mahnung", rechnung_id=rechnung_obj.pk, mahnung_id=mahnung_obj.pk)

    context = {
        "form": form,
        "rechnung": rechnung_obj,
        "mahnung": mahnung_obj,
    }
    return render(request, "rechnung/mahnungen/mahnung.html", context)


@finanz_staff_member_required
def form_mahnung(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: Optional[int] = None) -> HttpResponse:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung_obj: Optional[Mahnung] = None
    if mahnung_id:
        mahnung_obj = get_object_or_404(Mahnung, pk=mahnung_id)
        if mahnung_obj.rechnung != rechnung_obj:
            raise Http404

    form = MahnungForm(
        request.POST or None,
        rechnung=rechnung_obj,
        instance=mahnung_obj,
        initial={"ersteller": request.user},
    )

    if form.is_valid():
        mahnung_form_obj: Mahnung = form.save()
        if mahnung_form_obj.geschickt:
            gen_rechnung_upload_to_sftp(request, rechnung_id, mahnung_form_obj.id)
        return redirect("rechnung:mahnung", rechnung_id=rechnung_obj.pk, mahnung_id=mahnung_form_obj.pk)

    return render(
        request,
        "rechnung/mahnungen/form_mahnung.html",
        {"form": form, "rechnung": rechnung_obj, "mahnung": mahnung_obj},
    )


@finanz_staff_member_required
def alle_mahnungen(request: AuthWSGIRequest) -> HttpResponse:
    rechnungen = Rechnung.objects.all().order_by("-rnr")
    context = {"rechnungen": rechnungen}
    return render(request, "rechnung/mahnungen/alle_mahnungen.html", context)


# Kunde#########################################################################


@finanz_staff_member_required
def kunde(request: AuthWSGIRequest, kunde_id: int) -> HttpResponse:
    kunde_obj = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, "rechnung/kunden/kunde.html", {"kunde": kunde_obj, "not_rechnung": True})


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
        "rechnung/kunden/form_kunde.html",
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
    return render(request, "rechnung/kunden/kunden_alle.html", context)


# Posten#######################################################################


@finanz_staff_member_required
def posten(request: AuthWSGIRequest, posten_id: int) -> HttpResponse:
    posten_obj = get_object_or_404(Posten, pk=posten_id)
    return render(request, "rechnung/posten/posten.html", {"posten": posten_obj})


# Vorhandenen Posten bearbeiten
@finanz_staff_member_required
def form_exist_posten(request: AuthWSGIRequest, posten_id: int) -> HttpResponse:
    posten_obj = get_object_or_404(Posten, pk=posten_id)
    rechnung_obj = posten_obj.rechnung

    if rechnung_obj.gestellt:
        return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)

    form = PostenForm(request.POST or None, instance=posten_obj)
    if request.method == "POST":
        if "loeschen" in request.POST:
            posten_obj.delete()
        elif form.is_valid():
            form.save()
        return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)
    context = {"form": form, "rechnung": rechnung_obj, "posten": posten_obj}
    return render(request, "rechnung/posten/form_posten_aendern.html", context)


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
            posten_obj.save()
            if "zurueck" in request.POST:
                return redirect("rechnung:rechnung", rechnung_id=rechnung_obj.pk)
            return redirect("rechnung:rechnung_posten_neu", rechnung_id=rechnung_obj.pk)
    posten_suggestions = Posten.objects.filter(rechnung__kategorie=rechnung_obj.kategorie)

    posten_name_suggestions = get_distinct_values_in_order(posten_suggestions, "name")
    posten_einzelpreis_suggestions = get_distinct_values_in_order(posten_suggestions, "einzelpreis")
    posten_anzahl_suggestions = get_distinct_values_in_order(posten_suggestions, "anzahl")
    context = {
        "form": PostenForm(),
        "rechnung": rechnung_obj,
        "posten_name_suggestions": posten_name_suggestions,
        "posten_einzelpreis_suggestions": posten_einzelpreis_suggestions,
        "posten_anzahl_suggestions": posten_anzahl_suggestions,
    }
    return render(request, "rechnung/posten/form_posten_neu.html", context)


def get_distinct_values_in_order(posten_suggestions, field):
    return (
        posten_suggestions.values(field)
        .annotate(c_field=Count(field))
        .order_by("c_field")
        .distinct()
        .values_list(field, flat=True)
    )


# Kategorie####################################################################


@finanz_staff_member_required
def list_kategorien(request: AuthWSGIRequest) -> HttpResponse:
    kategorien_liste = Kategorie.objects.order_by("name")
    context = {"kategorien_liste": kategorien_liste}
    return render(request, "rechnung/kategorien/list_kategorien.html", context)


@finanz_staff_member_required
def add_kategorie(request: AuthWSGIRequest) -> HttpResponse:
    form = KategorieForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("rechnung:list_kategorien")
    context = {"form": form}
    return render(request, "rechnung/kategorien/add_kategorie.html", context)


@finanz_staff_member_required
def edit_kategorie(request: AuthWSGIRequest, kategorie_pk: int) -> HttpResponse:
    kategorie = get_object_or_404(Kategorie, pk=kategorie_pk)
    form = KategorieForm(request.POST or None, instance=kategorie)
    if form.is_valid():
        form.save()
        return redirect("rechnung:list_kategorien")
    context = {"form": form, "kategorie": kategorie}
    return render(request, "rechnung/kategorien/edit_kategorie.html", context)


@finanz_staff_member_required
def del_kategorie(request: AuthWSGIRequest, kategorie_pk: int) -> HttpResponse:
    kategorie = get_object_or_404(Kategorie, pk=kategorie_pk)
    messages.error(
        request,
        "Wenn du diese Kategorie löschst, dann wirst du alle davon abhängigen Rechnungen mit löschen. "
        "There be dragons.",
    )
    form = forms.Form(request.POST or None)
    if form.is_valid():
        kategorie.delete()
        return redirect("rechnung:list_kategorien")
    context = {"form": form, "kategorie": kategorie}
    return render(request, "rechnung/kategorien/del_kategorie.html", context)


@finanz_staff_member_required
def rechnungpdf(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: Optional[int] = None) -> HttpResponse:
    context, proposed_filename = gen_context(rechnung_id, mahnung_id)
    try:
        path_to_pdf, tmplatex = gen_rechnung(context)
    except subprocess.CalledProcessError as error:
        return render(
            request,
            "rechnung/tex/rechnungpdf_error.html",
            {"erroroutput": error.output},
        )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{proposed_filename}"'

    with open(path_to_pdf, "rb") as pdf:
        response.write(pdf.read())
    shutil.rmtree(tmplatex, ignore_errors=True)

    return response


def gen_context(
    rechnung_id: int,
    mahnung_id: Optional[int] = None,
) -> Tuple[Dict[str, Any], str]:
    rechnung_obj = get_object_or_404(Rechnung, pk=rechnung_id)
    context: Dict[str, Any] = {"rechnung": rechnung_obj}
    proposed_filename = f"RE{rechnung_obj.rnr_string}_{rechnung_obj.kunde.knr}"
    if mahnung_id:
        mahnung_obj = get_object_or_404(Mahnung, pk=mahnung_id)
        vorherige_mahnungen = (
            Mahnung.objects.filter(rechnung=mahnung_obj.rechnung, wievielte__lt=mahnung_obj.wievielte)
            .order_by("wievielte")
            .all()
        )
        context["mahnung"] = mahnung_obj
        context["vorherige_mahnungen"] = vorherige_mahnungen
        proposed_filename += f"_M{mahnung_obj.wievielte}"
    proposed_filename = f"{proposed_filename}.pdf"
    return context, proposed_filename


def gen_rechnung(context: Dict[str, Any]) -> Tuple[str, str]:
    # create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix=".tex", dir=tmplatex)

    rendered_template = render_to_string("rechnung/tex/latex_rechnung.tex", context).encode("utf8")
    os.write(latex_file, rendered_template)
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    subprocess.check_output(  # nosec: fully defined
        [
            "pdflatex",
            "-halt-on-error",
            "-output-directory",
            tmplatex,
            latex_filename,
        ],
    )

    path_to_pdf = f"{os.path.splitext(latex_filename)[0]}.pdf"

    return path_to_pdf, tmplatex


sftp = SFTPStorage()


def gen_rechnung_upload_to_sftp(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: Optional[int] = None) -> None:
    context, proposed_filename = gen_context(rechnung_id, mahnung_id)
    tmplatex = ""  # happy now, mypy?
    if mahnung_id:
        data_type = "Mahnung"
    else:
        data_type = "Rechnung"
    try:
        path_to_pdf, tmplatex = gen_rechnung(context)
        remote_path_to_pdf = sftp.get_valid_name(proposed_filename)
        with open(path_to_pdf, "rb") as pdf:
            sftp.save(remote_path_to_pdf, pdf)
        messages.success(request, f"Die {data_type} '{remote_path_to_pdf}' wurde zu valhalla hinzugefügt.")

    except subprocess.CalledProcessError as error:
        messages.error(
            request,
            f"Beim versuch die datei '{proposed_filename}' zu generieren ist der folgende Fehler "
            f"aufgetreten:\n{error}",
        )
    except (ImproperlyConfigured, AuthenticationException, IOError) as error:
        messages.error(
            request,
            f"Beim versuch die datei '{proposed_filename}' auf valhalla hochzuladen ist der "
            f"folgende Fehler aufgetragen:\n{error}",
        )
    shutil.rmtree(tmplatex, ignore_errors=True)
