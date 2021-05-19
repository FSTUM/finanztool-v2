from datetime import date
from io import TextIOWrapper
from typing import Optional

from django.core.files.uploadedfile import UploadedFile
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render

from schluessel.views import AuthWSGIRequest, finanz_staff_member_required

from .forms import MappingConfirmationForm, UploadForm
from .models import EinzahlungsLog
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
        zuletzt_eingetragen: Optional[date] = EinzahlungsLog.objects.latest("timestamp").timestamp
    except EinzahlungsLog.DoesNotExist:
        zuletzt_eingetragen = None

    context = {
        "form": form,
        "zuletzt_eingetragen": zuletzt_eingetragen,
    }
    return render(request, "konto/einlesen.html", context)


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

        return redirect("rechnung:unerledigt")

    context = {
        "results": results,
        "errors": errors,
        "form": mapping_form,
    }
    return render(request, "konto/mapping.html", context)
