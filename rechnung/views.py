import os
import shutil
import subprocess  # nosec: fully defined
from tempfile import mkdtemp, mkstemp
from typing import Any, Dict, Optional, Tuple

from django.contrib import messages
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

from .forms import FilterRechnungenForm, KategorieForm, KundeForm, MahnungForm, PostenForm, RechnungForm
from .models import Kategorie, Kunde, Mahnung, Posten, Rechnung


def get_nicht_bezahlt_rechnungen():
    nicht_bezahlt_rechnungen = Rechnung.objects.filter(gestellt=True, bezahlt=False).values_list("name", flat=True)
    return list(nicht_bezahlt_rechnungen), [1] * nicht_bezahlt_rechnungen.count()


def get_kategorien_cnt():
    kat_cnt = Rechnung.objects.values("kategorie__name").annotate(kategorie_count=Count("kategorie__name"))
    return (
        list(kat_cnt.values_list("kategorie__name", flat=True)),
        list(kat_cnt.values_list("kategorie_count", flat=True)),
    )


@finanz_staff_member_required
def dashboard(request: AuthWSGIRequest) -> HttpResponse:
    kategorien_cnt_labels, kategorien_cnt_values = get_kategorien_cnt()
    nicht_bezahlt_rechnungen_labels, nicht_bezahlt_rechnungen_values = get_nicht_bezahlt_rechnungen()
    context = {
        "nicht_bezahlt_rechnungen_values": nicht_bezahlt_rechnungen_values,
        "nicht_bezahlt_rechnungen_labels": nicht_bezahlt_rechnungen_labels,
        "kategorien_cnt_values": kategorien_cnt_values,
        "kategorien_cnt_labels": kategorien_cnt_labels,
    }
    return render(request, "rechnung/rechnung_dashboard.html", context)


@finanz_staff_member_required
def list_rechnungen_aufgaben_unerledigt(request: AuthWSGIRequest) -> HttpResponse:
    unerledigte_rechnungen = (
        Rechnung.objects.filter(erledigt=False).exclude(name="test").exclude(name="Test").order_by("-rnr")
    )
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")

    context = {
        "unerledigte_rechnungen": unerledigte_rechnungen,
        "aufgaben": aufgaben,
    }
    return render(request, "rechnung/rechnungen/list/list_rechnungen_aufgaben_unerledigt.html", context)


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
    return render(request, "rechnung/rechnungen/list/list_rechnungen.html", context)


# Rechnung#####################################################################


@finanz_staff_member_required
def view_rechnung(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnungen: QuerySet[Mahnung] = Mahnung.objects.filter(rechnung=rechnung.pk).all()
    form = forms.Form(request.POST or None)
    if request.method == "POST":
        if "bezahlt" in request.POST and form.is_valid():
            rechnung.bezahlen()
            return redirect("rechnung:dashboard")

        if "gestellt" in request.POST and form.is_valid():
            rechnung.gestellt = True
            rechnung.save()
            return redirect("rechnung:view_rechnung", rechnung_id=rechnung.pk)

    context = {"form": form, "rechnung": rechnung, "mahnungen": mahnungen}
    return render(request, "rechnung/rechnungen/view_rechnung.html", context)


@finanz_staff_member_required
def form_rechnung(request: AuthWSGIRequest, rechnung_id: Optional[int] = None) -> HttpResponse:
    rechnung: Optional[Rechnung] = None
    if rechnung_id:
        rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    form = RechnungForm(request.POST or None, instance=rechnung, initial={"ersteller": request.user})

    if form.is_valid():
        rechnung_form: Rechnung = form.save()
        if rechnung_form.erledigt:
            gen_rechnung_upload_to_sftp(request, rechnung_form.id)
        return redirect("rechnung:view_rechnung", rechnung_id=rechnung_form.pk)

    context = {"form": form, "rechnung": rechnung}
    return render(request, "rechnung/rechnungen/form_rechnung.html", context)


@finanz_staff_member_required
def duplicate_rechnung(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    initial = {
        "ersteller": request.user,
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

        return redirect("rechnung:view_rechnung", rechnung_id=rechnung_neu.pk)

    return render(
        request,
        "rechnung/rechnungen/rechnung_duplizieren.html",
        {"form": form, "rechnung": rechnung},
    )


# Mahnung#######################################################################


@finanz_staff_member_required
def view_mahnung(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: int) -> HttpResponse:
    rechnung: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung: Mahnung = get_object_or_404(Mahnung, pk=mahnung_id)
    if mahnung.rechnung != rechnung:
        raise Http404

    form = forms.Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if "bezahlt" in request.POST:
            mahnung.bezahlen()
            return redirect("rechnung:view_mahnung", rechnung_id=rechnung.pk, mahnung_id=mahnung.pk)

        if "geschickt" in request.POST:
            mahnung.geschickt = True
            mahnung.save()
            return redirect("rechnung:view_mahnung", rechnung_id=rechnung.pk, mahnung_id=mahnung.pk)

    context = {
        "form": form,
        "rechnung": rechnung,
        "mahnung": mahnung,
    }
    return render(request, "rechnung/mahnungen/view_mahnung.html", context)


@finanz_staff_member_required
def form_mahnung(request: AuthWSGIRequest, rechnung_id: int, mahnung_id: Optional[int] = None) -> HttpResponse:
    rechnung: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    mahnung: Optional[Mahnung] = None
    if mahnung_id:
        mahnung = get_object_or_404(Mahnung, pk=mahnung_id)
        if mahnung.rechnung != rechnung:
            raise Http404

    form = MahnungForm(
        request.POST or None,
        rechnung=rechnung,
        instance=mahnung,
        initial={"ersteller": request.user},
    )

    if form.is_valid():
        mahnung_form: Mahnung = form.save()
        if mahnung_form.geschickt:
            gen_rechnung_upload_to_sftp(request, rechnung_id, mahnung_form.id)
        return redirect("rechnung:view_mahnung", rechnung_id=rechnung.pk, mahnung_id=mahnung_form.pk)

    return render(
        request,
        "rechnung/mahnungen/form_mahnung.html",
        {"form": form, "rechnung": rechnung, "mahnung": mahnung},
    )


@finanz_staff_member_required
def list_mahnungen(request: AuthWSGIRequest) -> HttpResponse:
    rechnungen = Rechnung.objects.all().order_by("-rnr")
    context = {"rechnungen": rechnungen}
    return render(request, "rechnung/mahnungen/list_mahnungen.html", context)


# Kunde#########################################################################


@finanz_staff_member_required
def view_kunde(request: AuthWSGIRequest, kunde_id: int) -> HttpResponse:
    kunde: Kunde = get_object_or_404(Kunde, pk=kunde_id)
    return render(request, "rechnung/kunden/view_kunde.html", {"kunde": kunde})


@finanz_staff_member_required
def form_kunde(request: AuthWSGIRequest, kunde_id: Optional[int] = None) -> HttpResponse:
    kunde: Optional[Kunde] = None
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
            kunde_pk: int = form.save().pk
            return redirect("rechnung:view_kunde", kunde_id=kunde_pk)
    else:
        form = KundeForm(instance=kunde)

    return render(
        request,
        "rechnung/kunden/form_kunde.html",
        {
            "form": form,
            "kunde": kunde,
            "kunde_verwendet": kunde_verwendet,
        },
    )


@finanz_staff_member_required
def list_kunden(request: AuthWSGIRequest) -> HttpResponse:
    kunden_liste = Kunde.objects.order_by("-knr")
    context = {"kunden_liste": kunden_liste}
    return render(request, "rechnung/kunden/list_kunden.html", context)


# Posten#######################################################################


@finanz_staff_member_required
def view_posten(request: AuthWSGIRequest, posten_id: int) -> HttpResponse:
    posten: Posten = get_object_or_404(Posten, pk=posten_id)
    return render(request, "rechnung/posten/view_posten.html", {"posten": posten})


# Vorhandenen Posten bearbeiten
@finanz_staff_member_required
def form_exist_posten(request: AuthWSGIRequest, posten_id: int) -> HttpResponse:
    posten: Posten = get_object_or_404(Posten, pk=posten_id)
    rechnung_obj = posten.rechnung

    if rechnung_obj.gestellt:
        return redirect("rechnung:view_rechnung", rechnung_id=rechnung_obj.pk)

    form = PostenForm(request.POST or None, instance=posten)
    if request.method == "POST":
        if "loeschen" in request.POST:
            posten.delete()
        elif form.is_valid():
            form.save()
        return redirect("rechnung:view_rechnung", rechnung_id=rechnung_obj.pk)
    context = {"form": form, "rechnung": rechnung_obj, "posten": posten}
    return render(request, "rechnung/posten/edit_posten.html", context)


# Neuen Posten zu vorhandener Rechnung hinzufügen
@finanz_staff_member_required
def form_rechnung_posten(request: AuthWSGIRequest, rechnung_id: int) -> HttpResponse:
    rechnung: Rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    if rechnung.gestellt:
        return redirect("rechnung:view_rechnung", rechnung_id=rechnung.pk)
    if request.method == "POST":
        form = PostenForm(request.POST, instance=Posten())

        if form.is_valid():
            posten_obj = form.save(commit=False)
            posten_obj.rechnung = rechnung
            posten_obj.save()
            if "zurueck" in request.POST:
                return redirect("rechnung:view_rechnung", rechnung_id=rechnung.pk)
            return redirect("rechnung:add_posten", rechnung_id=rechnung.pk)
    posten_suggestions = Posten.objects.filter(rechnung__kategorie=rechnung.kategorie)

    posten_name_suggestions = get_distinct_values_in_order(posten_suggestions, "name")
    posten_einzelpreis_suggestions = get_distinct_values_in_order(posten_suggestions, "einzelpreis")
    posten_anzahl_suggestions = get_distinct_values_in_order(posten_suggestions, "anzahl")
    context = {
        "form": PostenForm(),
        "rechnung": rechnung,
        "posten_name_suggestions": posten_name_suggestions,
        "posten_einzelpreis_suggestions": posten_einzelpreis_suggestions,
        "posten_anzahl_suggestions": posten_anzahl_suggestions,
    }
    return render(request, "rechnung/posten/add_posten.html", context)


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
