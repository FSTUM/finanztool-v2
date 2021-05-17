from django.contrib.admin.views.decorators import staff_member_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AufgabeErledigtForm, AufgabeForm, AufgabenartForm
from .models import Aufgabe, Aufgabenart

staff_member_required = staff_member_required(login_url="rechnung:login")


@staff_member_required
def unerledigt(request: WSGIRequest) -> HttpResponse:
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")
    meine_aufgaben = Aufgabe.objects.filter(
        erledigt=False,
        zustaendig=request.user,
    ).order_by("-frist")
    context = {
        "aufgaben": aufgaben,
        "meine_aufgaben": meine_aufgaben,
    }
    return render(request, "aufgaben/unerledigt.html", context)


@staff_member_required
def form_aufgabe(request: WSGIRequest, aufgabe_id=None) -> HttpResponse:
    aufgabe = None
    if aufgabe_id:
        aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    if request.method == "POST":
        form = AufgabeForm(request.POST, instance=aufgabe)

        if form.is_valid():
            aufgabe = form.save()
            return redirect("aufgaben:aufgabe", aufgabe_id=aufgabe.pk)
    else:
        form = AufgabeForm(
            initial={"zustaendig": request.user},
            instance=aufgabe,
        )

    context = {
        "form": form,
        "aufgabe": aufgabe,
    }

    return render(request, "aufgaben/form_aufgabe.html", context)


@staff_member_required
def form_aufgabenart(request: WSGIRequest, aufgabenart_id=None) -> HttpResponse:
    aufgabenart = None
    if aufgabenart_id:
        aufgabenart = get_object_or_404(Aufgabenart, pk=aufgabenart_id)

    if request.method == "POST":
        form = AufgabenartForm(request.POST, instance=aufgabenart)

        if form.is_valid():
            aufgabenart = form.save()
            return redirect("aufgaben:neu")
    else:
        form = AufgabenartForm()

    context = {
        "form": form,
        "aufgabenart": aufgabenart,
    }

    return render(request, "aufgaben/form_aufgabenart.html", context)


@staff_member_required
def alle(request: WSGIRequest) -> HttpResponse:
    alle_aufgaben = Aufgabe.objects.all().order_by("-frist")
    context = {
        "alle_aufgaben": alle_aufgaben,
    }
    return render(request, "aufgaben/alle.html", context)


@staff_member_required
def aufgabe(request: WSGIRequest, aufgabe_id) -> HttpResponse:
    _aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    form = AufgabeErledigtForm(request.POST or None)
    if request.method == "POST":
        if "erledigt" in request.POST:
            if form.is_valid():
                _aufgabe.erledigt = True
                _aufgabe.save()
                return redirect("aufgaben:aufgabe", aufgabe_id=_aufgabe.pk)

    context = {
        "aufgabe": _aufgabe,
        "form": form,
    }
    return render(request, "aufgaben/aufgabe.html", context)
