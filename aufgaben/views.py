from typing import Optional

from django.contrib import messages
from django.forms import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.models import Settings
from common.views import AuthWSGIRequest, finanz_staff_member_required

from .forms import AufgabeForm, AufgabenartForm, ShoppingcartForm
from .models import Aufgabe, Aufgabenart


@finanz_staff_member_required
def list_aufgaben_unerledigt(request: AuthWSGIRequest) -> HttpResponse:
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by("frist")
    meine_aufgaben = Aufgabe.objects.filter(erledigt=False, zustaendig=request.user).order_by("-frist")
    context = {
        "aufgaben": aufgaben,
        "meine_aufgaben": meine_aufgaben,
    }
    return render(request, "aufgaben/aufgaben/list_aufgaben_unerledigt.html", context)


@finanz_staff_member_required
def edit_shoppingcart(request: AuthWSGIRequest) -> HttpResponse:
    settings: Settings = Settings.load()
    form = ShoppingcartForm(request.POST or None, instance=settings)
    if form.is_valid():
        form.save()
        messages.success(request, "Die Merkliste wurde erfolgreich gespeichert.")
        return redirect("aufgaben:edit_shoppingcart")
    messages.warning(
        request,
        "Dieses Formular ist nicht gegen einen mehrbenutzerbetrieb gesichert. "
        "Lediglich eine Person darf zu einer Zeit dieses Formular bearbeiten, "
        "da sonnst die Arbeit von anderen Personen überschrieben wird.",
    )
    context = {
        "form": form,
    }
    return render(request, "aufgaben/aufgaben/form_shoppingcart.html", context)


@finanz_staff_member_required
def form_aufgabe(request: AuthWSGIRequest, aufgabe_id: Optional[int] = None) -> HttpResponse:
    aufgabe: Optional[Aufgabe] = None
    if aufgabe_id:
        aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    form = AufgabeForm(request.POST or None, request.FILES, initial={"zustaendig": request.user}, instance=aufgabe)
    if request.POST and form.is_valid():
        aufgabe_new: Aufgabe = form.save()
        return redirect("aufgaben:view_aufgabe", aufgabe_id=aufgabe_new.pk)

    context = {
        "form": form,
        "aufgabe": aufgabe,
    }

    return render(request, "aufgaben/aufgaben/form_aufgabe.html", context)


@finanz_staff_member_required
def form_aufgabenart(request: AuthWSGIRequest, aufgabenart_id: Optional[int] = None) -> HttpResponse:
    aufgabenart = None
    if aufgabenart_id:
        aufgabenart = get_object_or_404(Aufgabenart, pk=aufgabenart_id)

    if request.method == "POST":
        form = AufgabenartForm(request.POST, instance=aufgabenart)

        if form.is_valid():
            form.save()
            return redirect("aufgaben:add_aufgabe")
    else:
        form = AufgabenartForm()

    context = {
        "form": form,
        "aufgabenart": aufgabenart,
    }

    return render(request, "aufgaben/aufgabenart/form_aufgabenart.html", context)


@finanz_staff_member_required
def list_aufgaben(request: AuthWSGIRequest) -> HttpResponse:
    alle_aufgaben = Aufgabe.objects.all().order_by("-frist")
    context = {
        "alle_aufgaben": alle_aufgaben,
    }
    return render(request, "aufgaben/aufgaben/list_aufgaben.html", context)


@finanz_staff_member_required
def view_aufgabe(request: AuthWSGIRequest, aufgabe_id: int) -> HttpResponse:
    _aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    form = forms.Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if "nicht-erledigt" in request.POST:
            _aufgabe.erledigt = False
        elif "erledigt" in request.POST:
            _aufgabe.erledigt = True
        _aufgabe.save()
        return redirect("aufgaben:view_aufgabe", aufgabe_id=_aufgabe.pk)

    context = {
        "aufgabe": _aufgabe,
        "form": form,
    }
    return render(request, "aufgaben/aufgaben/view_aufgabe.html", context)


@finanz_staff_member_required
def dashboard(request: AuthWSGIRequest) -> HttpResponse:
    context = {"aufgabenstatus": get_aufgabenstatus()}  # TODO
    return render(request, "aufgaben/aufgaben_dashboard.html", context)


def get_aufgabenstatus() -> list[int]:
    erledigte_aufgaben_cnt = Aufgabe.objects.filter(erledigt=True).count()
    unerledigte_aufgaben = Aufgabe.objects.filter(erledigt=False)
    faellige_unerledigte_aufgaben_cnt = len([a for a in unerledigte_aufgaben if a.faellig()])
    nicht_faellige_unerledigte_aufgaben_cnt = (
        Aufgabe.objects.count() - faellige_unerledigte_aufgaben_cnt - erledigte_aufgaben_cnt
    )
    return [erledigte_aufgaben_cnt, nicht_faellige_unerledigte_aufgaben_cnt, faellige_unerledigte_aufgaben_cnt]
