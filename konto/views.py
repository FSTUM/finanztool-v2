from io import TextIOWrapper
from typing import Optional

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.views import AuthWSGIRequest, finanz_staff_member_required

from .forms import MappingConfirmationForm, ReferentForm, UploadForm
from .models import EinzahlungsLog, Referent
from .parser import parse_camt_csv


@finanz_staff_member_required
def einlesen(request: AuthWSGIRequest) -> HttpResponse:
    form = UploadForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        csv_file: Optional[UploadedFile] = request.FILES.get("csv_file")
        if not csv_file:
            raise Http404("You did not attach a file")
        csv_file_text = TextIOWrapper(csv_file.file, encoding="iso-8859-1")
        results, errors = parse_camt_csv(csv_file_text)

        request.session["results"] = results
        request.session["errors"] = errors
        return redirect("konto:mapping")

    try:
        konto_einlesen: Optional[EinzahlungsLog] = EinzahlungsLog.objects.latest("konto_einlesen")
        konto_last_einzahlung: Optional[EinzahlungsLog] = EinzahlungsLog.objects.latest("konto_last_einzahlung")
    except EinzahlungsLog.DoesNotExist:
        konto_einlesen = None
        konto_last_einzahlung = None

    context = {
        "form": form,
        "konto_einlesen": konto_einlesen,
        "konto_last_einzahlung": konto_last_einzahlung,
    }
    return render(request, "konto/konto/einlesen.html", context)


@finanz_staff_member_required
def mapping(request: AuthWSGIRequest) -> HttpResponse:
    try:
        results = request.session["results"]
        errors = request.session["errors"]
    except KeyError:
        return redirect("konto:einlesen")

    mapping_form = MappingConfirmationForm(
        request.POST or None,
        mappings=results,
        user=request.user,
    )

    if mapping_form.is_valid():
        mapping_form.save()
        del request.session["results"]
        del request.session["errors"]

        return redirect("rechnung:dashboard")

    context = {
        "results": results,
        "errors": errors,
        "form": mapping_form,
    }
    return render(request, "konto/konto/mapping.html", context)


@finanz_staff_member_required
def einzahlungslog(request: AuthWSGIRequest) -> HttpResponse:
    context = {
        "einzahlungen": EinzahlungsLog.objects.all(),
    }
    return render(request, "konto/konto/einzahlungslog.html", context)


@finanz_staff_member_required
def add_referent(request: AuthWSGIRequest) -> HttpResponse:
    form = ReferentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("konto:list_referenten")
    context = {"form": form}
    return render(request, "konto/referenten/add_referenten.html", context)


@finanz_staff_member_required
def edit_referent(request: AuthWSGIRequest, referent_pk: int) -> HttpResponse:
    referent: Referent = get_object_or_404(Referent, pk=referent_pk)
    form = ReferentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("konto:list_referenten")
    context = {"form": form, "referent": referent}
    return render(request, "konto/referenten/edit_referenten.html", context)


@finanz_staff_member_required
def del_referent(request: AuthWSGIRequest, referent_pk: int) -> HttpResponse:
    referent: Referent = get_object_or_404(Referent, pk=referent_pk)
    form = forms.Form(request.POST or None)
    if form.is_valid():
        referent.delete()
        return redirect("konto:list_referenten")
    context = {"form": form, "referent": referent}
    return render(request, "konto/referenten/edit_referenten.html", context)


@finanz_staff_member_required
def inc_referent(request: AuthWSGIRequest, referent_pk: int) -> HttpResponse:
    referent: Referent = get_object_or_404(Referent, pk=referent_pk)
    referent.taken_free_beverages += 1
    referent.save()
    return redirect("konto:list_referenten")


@finanz_staff_member_required
def list_referenten(request: AuthWSGIRequest) -> HttpResponse:
    referenten = Referent.objects.all()
    context = {"referenten": referenten}
    return render(request, "konto/referenten/list_referenten.html", context)
