from io import TextIOWrapper

from django.contrib.admin.views.decorators import staff_member_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import MappingConfirmationForm, UploadForm
from .models import EinzahlungsLog
from .parser import parse_camt_csv

staff_member_required = staff_member_required(login_url="rechnung:login")


@staff_member_required
def einlesen(request: WSGIRequest) -> HttpResponse:
    form = UploadForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        csv_file = request.FILES.get("csv_file")
        csv_file_text = TextIOWrapper(csv_file.file, encoding="iso-8859-1")
        results, errors = parse_camt_csv(csv_file_text)

        request.session["results"] = results
        request.session["errors"] = errors
        return redirect("konto:mapping")

    try:
        zuletzt_eingetragen = EinzahlungsLog.objects.latest("timestamp").timestamp
    except EinzahlungsLog.DoesNotExist:
        zuletzt_eingetragen = None

    context = {
        "form": form,
        "zuletzt_eingetragen": zuletzt_eingetragen,
    }
    return render(request, "konto/einlesen.html", context)


@staff_member_required
def mapping(request: WSGIRequest) -> HttpResponse:
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

        return redirect("rechnung:index")

    context = {
        "results": results,
        "errors": errors,
        "form": mapping_form,
    }
    return render(request, "konto/mapping.html", context)
