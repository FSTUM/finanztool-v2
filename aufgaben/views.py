from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .models import Aufgabe, Aufgabenart
from .forms import AufgabeForm, AufgabenartForm, AufgabeErledigtForm


@login_required
def unerledigt(request):
    aufgaben = Aufgabe.objects.filter(erledigt=False).order_by('-frist')
    meine_aufgaben = Aufgabe.objects.filter(erledigt=False,
                                            zustaendig=request.user).order_by('-frist')
    context = {
            'aufgaben': aufgaben,
            'meine_aufgaben': meine_aufgaben,
            }
    return render(request, 'aufgaben/unerledigt.html', context)


@login_required
def form_aufgabe(request, aufgabe_id=None):
    aufgabe = None
    if aufgabe_id:
        aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    if request.method == "POST":
        form = AufgabeForm(request.POST, instance=aufgabe)

        if form.is_valid():
            aufgabe = form.save()
            return redirect('aufgaben:aufgabe', aufgabe_id=aufgabe.pk)
    else:
        form = AufgabeForm(initial={'zustaendig': request.user},
                           instance=aufgabe)

    context = {
            'form': form,
            'aufgabe': aufgabe
            }

    return render(request, 'aufgaben/form_aufgabe.html', context)


@login_required
def form_aufgabenart(request, aufgabenart_id=None):
    aufgabenart = None
    if aufgabenart_id:
        aufgabenart = get_object_or_404(Aufgabenart, pk=aufgabenart_id)

    if request.method == "POST":
        form = AufgabenartForm(request.POST, instance=aufgabenart)

        if form.is_valid():
            aufgabenart = form.save()
            return redirect('aufgaben:neu')
    else:
        form = AufgabenartForm()

    context = {
            'form': form,
            'aufgabenart': aufgabenart
            }

    return render(request, 'aufgaben/form_aufgabenart.html', context)


@login_required
def alle(request):
    alle = Aufgabe.objects.all().order_by('-frist')
    context = {
            'alle': alle,
            }
    return render(request, 'aufgaben/alle.html', context)


@login_required
def aufgabe(request, aufgabe_id):
    aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    form = AufgabeErledigtForm(request.POST or None)
    if request.method == 'POST':
        if 'erledigt' in request.POST:
            if form.is_valid():
                aufgabe.erledigt = True
                aufgabe.save()
                return redirect('aufgaben:aufgabe', aufgabe_id=aufgabe.pk)

    context = {
            'aufgabe': aufgabe,
            'form': form,
            }
    return render(request, 'aufgaben/aufgabe.html', context)
