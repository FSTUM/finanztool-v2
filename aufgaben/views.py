from typing import Optional

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.views import AuthWSGIRequest, finanz_staff_member_required

from .forms import AufgabeErledigtForm, AufgabeForm, AufgabenartForm
from .models import Aufgabe, Aufgabenart


@finanz_staff_member_required
def unerledigt(request: AuthWSGIRequest) -> HttpResponse:
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")
    meine_aufgaben = Aufgabe.objects.filter(erledigt=False, zustaendig=request.user).order_by("-frist")
    context = {
        "aufgaben": aufgaben,
        "meine_aufgaben": meine_aufgaben,
    }
    return render(request, "aufgaben/unerledigt.html", context)


@finanz_staff_member_required
def form_aufgabe(request: AuthWSGIRequest, aufgabe_id: Optional[int] = None) -> HttpResponse:
    aufgabe_obj: Optional[Aufgabe] = None
    if aufgabe_id:
        aufgabe_obj = get_object_or_404(Aufgabe, pk=aufgabe_id)

    if request.method == "POST":
        form = AufgabeForm(request.POST, instance=aufgabe_obj)

        if form.is_valid():
            aufgabe_pk: int = form.save().pk
            return redirect("aufgaben:aufgabe", aufgabe_id=aufgabe_pk)
    else:
        form = AufgabeForm(initial={"zustaendig": request.user}, instance=aufgabe_obj)

    context = {
        "form": form,
        "aufgabe": aufgabe_obj,
    }

    return render(request, "aufgaben/form_aufgabe.html", context)


@finanz_staff_member_required
def form_aufgabenart(request: AuthWSGIRequest, aufgabenart_id: Optional[int] = None) -> HttpResponse:
    aufgabenart = None
    if aufgabenart_id:
        aufgabenart = get_object_or_404(Aufgabenart, pk=aufgabenart_id)

    if request.method == "POST":
        form = AufgabenartForm(request.POST, instance=aufgabenart)

        if form.is_valid():
            form.save()
            return redirect("aufgaben:neu")
    else:
        form = AufgabenartForm()

    context = {
        "form": form,
        "aufgabenart": aufgabenart,
    }

    return render(request, "aufgaben/form_aufgabenart.html", context)


@finanz_staff_member_required
def alle(request: AuthWSGIRequest) -> HttpResponse:
    alle_aufgaben = Aufgabe.objects.all().order_by("-frist")
    context = {
        "alle_aufgaben": alle_aufgaben,
    }
    return render(request, "aufgaben/alle.html", context)


@finanz_staff_member_required
def aufgabe(request: AuthWSGIRequest, aufgabe_id: int) -> HttpResponse:
    _aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    form = AufgabeErledigtForm(request.POST or None)
    if request.method == "POST" and "erledigt" in request.POST and form.is_valid():
        _aufgabe.erledigt = True
        _aufgabe.save()
        return redirect("aufgaben:aufgabe", aufgabe_id=_aufgabe.pk)

    context = {
        "aufgabe": _aufgabe,
        "form": form,
    }
    return render(request, "aufgaben/aufgabe.html", context)
