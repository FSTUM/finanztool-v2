from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .models import Aufgabe, Aufgabenart


@login_required
def unerledigt(request):
    aufgaben = Aufgabe.objects.filter(erledigt=False)
    meine_aufgaben = Aufgabe.objects.filter(erledigt=False,
                                            zustaendig=request.user)
    context = {
            'aufgaben': aufgaben,
            'meine_aufgaben': meine_aufgaben,
            }
    return render(request, 'aufgaben/unerledigt.html', context)


@login_required
def alle(request):
    alle = Aufgabe.objects.all()
    context = {
            'alle': alle,
            }
    return render(request, 'aufgaben/alle.html', context)


@login_required
def aufgabe(request, aufgabe_id):
    aufgabe = get_object_or_404(Aufgabe, pk=aufgabe_id)

    context = {
            'aufgabe': aufgabe,
            }
    return render(request, 'aufgaben/aufgabe.html', context)
