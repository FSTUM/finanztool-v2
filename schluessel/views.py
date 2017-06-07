import os
import shutil
import subprocess
from tempfile import mkdtemp, mkstemp

from django import forms
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ObjectDoesNotExist
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .models import Key, Person, KeyLogEntry, SavedKeyChange
from .forms import SelectPersonForm, KeyForm, PersonForm, FilterKeysForm, \
        FilterPersonsForm, SelectPersonFormNoscript, SaveKeyChangeForm


staff_member_required = staff_member_required(login_url='rechnung:login')


@login_required
def view_key(request, key_pk):
    key = get_object_or_404(Key, pk=key_pk)

    logentries = key.keylogentry_set.order_by("date")

    context = {
        'key': key,
        'logentries': logentries,
    }

    return render(request, 'schluessel/view_key.html', context)


@staff_member_required
def add_key(request):
    form = KeyForm(request.POST or None)
    if form.is_valid():
        key = form.save()

        KeyLogEntry.objects.create(
            key=key,
            person=None,
            user=request.user,
            operation=KeyLogEntry.CREATE,
        )

        return redirect('schluessel:view_key', key.id)

    context = {
        'form': form,
    }

    return render(request, 'schluessel/add_key.html', context)


@staff_member_required
def edit_key(request, key_pk):
    key = get_object_or_404(Key, pk=key_pk)

    form = KeyForm(request.POST or None, instance=key)
    if form.is_valid():
        key = form.save()

        KeyLogEntry.objects.create(
            key=key,
            person=None,
            user=request.user,
            operation=KeyLogEntry.EDIT,
        )

        return redirect('schluessel:view_key', key.id)

    context = {
        'key': key,
        'form': form,
    }

    return render(request, 'schluessel/edit_key.html', context)


@staff_member_required
def save_key_change(request, key_pk):
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise SuspiciousOperation("Key is inactive")

    try:
        initial = {'keytype': key.savedkeychange.new_keytype}
    except ObjectDoesNotExist:
        initial = {}
    form = SaveKeyChangeForm(request.POST or None, initial=initial,
            keytype=key.keytype)

    if form.is_valid():
        keytype = form.cleaned_data['keytype']

        if hasattr(key, 'savedkeychange'):
            key.savedkeychange.user = request.user
            key.savedkeychange.new_keytype = keytype
            key.savedkeychange.save()
        else:
            SavedKeyChange.objects.create(
                key=key,
                new_keytype=keytype,
                user=request.user,
            )

        return redirect('schluessel:view_key', key.id)

    context = {
        'key': key,
        'form': form,
    }

    return render(request, 'schluessel/save_key_change.html', context)


@staff_member_required
def delete_key_change(request, key_pk):
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise SuspiciousOperation("Key is inactive")

    try:
        keychange = key.savedkeychange
    except ObjectDoesNotExist:
        raise SuspiciousOperation("Key change does not exist")

    form = forms.Form(request.POST or None)
    if form.is_valid():
        SavedKeyChange.objects.filter(pk=keychange.pk).delete()

        return redirect('schluessel:view_key', key.id)

    context = {
        'key': key,
        'form': form,
    }

    return render(request, 'schluessel/delete_key_change.html', context)


@staff_member_required
def list_key_changes(request):
    keys = Key.objects.filter(active=True).exclude(savedkeychange=None
        ).order_by("keytype__shortname", "number")

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for k in keys:
            try:
                k.keytype = k.savedkeychange.new_keytype
            except ObjectDoesNotExist:
                continue
            k.save()
            SavedKeyChange.objects.filter(pk=k.savedkeychange.pk).delete()
            KeyLogEntry.objects.create(
                key=k,
                person=None,
                user=request.user,
                operation=KeyLogEntry.EDIT,
            )
        return redirect('schluessel:list_key_changes')

    context = {
        'keys': keys,
        'form': form,
    }

    return render(request, 'schluessel/list_key_changes.html', context)


@login_required
def return_key(request, key_pk):
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise SuspiciousOperation("Key is inactive")

    if not key.person:
        raise SuspiciousOperation("Key not given out")

    form = forms.Form(request.POST or None)
    if form.is_valid():
        person = key.person

        Key.objects.filter(pk=key_pk).update(
            person=None,
        )

        KeyLogEntry.objects.create(
            key=key,
            person=person,
            user=request.user,
            operation=KeyLogEntry.RETURN,
        )

        return redirect('schluessel:view_key', key.id)

    context = {
        'key': key,
        'form': form,
    }

    return render(request, 'schluessel/return_key.html', context)


@login_required
def give_key(request, key_pk):
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise SuspiciousOperation("Key is inactive")

    if key.person:
        raise SuspiciousOperation("Key already given out")

    persons = Person.objects.order_by("name", "firstname")

    form = SelectPersonForm(request.POST or None)
    if form.is_valid():
        person_id = form.cleaned_data['person']
        if person_id:
            try:
                person = persons.get(id=person_id)
            except Person.DoesNotExist:
                return redirect('schluessel:give_key', key.id)

            return redirect('schluessel:give_key_confirm', key.id, person.id)
        else:
            return redirect('schluessel:give_key', key.id)

    formns = SelectPersonFormNoscript(request.POST or None)
    if formns.is_valid():
        person = formns.cleaned_data['person']
        return redirect('schluessel:give_key_confirm', key.id, person.id)

    context = {
        'key': key,
        'persons': persons,
        'form': form,
        'formns': formns,
    }

    return render(request, 'schluessel/give_key.html', context)


@login_required
def give_key_confirm(request, key_pk, person_pk):
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise SuspiciousOperation("Key is inactive")

    if key.person:
        raise SuspiciousOperation("Key already given out")

    person = get_object_or_404(Person, pk=person_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        Key.objects.filter(pk=key_pk).update(
            person=person,
        )

        KeyLogEntry.objects.create(
            key=key,
            person=person,
            user=request.user,
            operation=KeyLogEntry.GIVE,
        )

        return redirect('schluessel:view_key', key.id)

    context = {
        'key': key,
        'person': person,
        'form': form,
    }

    return render(request, 'schluessel/give_key_confirm.html', context)


@login_required
def view_person(request, person_pk):
    person = get_object_or_404(Person, pk=person_pk)

    keys = person.key_set.order_by("keytype__shortname", "number")

    logentries = person.keylogentry_set.order_by("date")

    context = {
        'person': person,
        'keys': keys,
        'logentries': logentries,
    }

    return render(request, 'schluessel/view_person.html', context)


@login_required
def add_person(request):
    form = PersonForm(request.POST or None)
    if form.is_valid():
        person = form.save()

        KeyLogEntry.objects.create(
            key=None,
            person=person,
            user=request.user,
            operation=KeyLogEntry.CREATE,
        )

        return redirect('schluessel:view_person', person.id)

    context = {
        'form': form,
    }

    return render(request, 'schluessel/add_person.html', context)


@login_required
def give_add_person(request, key_pk):
    form = PersonForm(request.POST or None)
    if form.is_valid():
        person = form.save()

        KeyLogEntry.objects.create(
            key=None,
            person=person,
            user=request.user,
            operation=KeyLogEntry.CREATE,
        )

        return redirect('schluessel:give_key_confirm', key_pk, person.id)

    context = {
        'form': form,
    }

    return render(request, 'schluessel/add_person.html', context)


@login_required
def edit_person(request, person_pk):
    person = get_object_or_404(Person, pk=person_pk)

    form = PersonForm(request.POST or None, instance=person)
    if form.is_valid():
        person = form.save()

        KeyLogEntry.objects.create(
            key=None,
            person=person,
            user=request.user,
            operation=KeyLogEntry.EDIT,
        )

        return redirect('schluessel:view_person', person.id)

    context = {
        'person': person,
        'form': form,
    }

    return render(request, 'schluessel/edit_person.html', context)


@login_required
def give_edit_person(request, key_pk, person_pk):
    person = get_object_or_404(Person, pk=person_pk)

    form = PersonForm(request.POST or None, instance=person)
    if form.is_valid():
        person = form.save()

        KeyLogEntry.objects.create(
            key=None,
            person=person,
            user=request.user,
            operation=KeyLogEntry.EDIT,
        )

        return redirect('schluessel:give_key_confirm', key_pk, person.id)

    context = {
        'person': person,
        'form': form,
    }

    return render(request, 'schluessel/edit_person.html', context)


@login_required
def get_kaution(request, key_pk):
    return create_pdf(request, key_pk, doc="Kaution")


@login_required
def get_quittung(request, key_pk):
    return create_pdf(request, key_pk, doc="Quittung")


@login_required
def create_pdf(request, key_pk, doc):
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise SuspiciousOperation("Key is inactive")

    if not key.person:
        raise SuspiciousOperation("Key not given out")

    # create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix='.tex', dir=tmplatex)

    logo_path = os.path.join(settings.BASE_DIR, 'schluessel/media/logo')

    # Pass TeX template through Django templating engine and into the temp file
    context = {'key': key, 'user': request.user, 'logo_path': logo_path}

    os.write(latex_file, render_to_string(
        'schluessel/latex_{}.tex'.format(doc), context).encode('utf8'))
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    try:
        subprocess.check_output(["pdflatex", "-halt-on-error",
                                 "-output-directory", tmplatex,
                                 latex_filename])
    except subprocess.CalledProcessError as e:
        return render(request, 'schluessel/pdflatex_error.html',
                {'erroroutput': e.output, 'doc': doc})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;' \
            'filename="{}_{}_{}_{}_{}.pdf"'.format(doc, key.keytype.shortname,
                    key.number, key.person.name, key.person.firstname)

    # return path to pdf
    pdf_filename = "{}.pdf".format(os.path.splitext(latex_filename)[0])

    with open(pdf_filename, 'rb') as f:
        response.write(f.read())

    return response


@login_required
def list_keys(request):
    keys = Key.objects.filter(active=True).order_by("keytype__shortname",
        "number")

    form = FilterKeysForm(request.POST or None)
    if form.is_valid():
        search = form.cleaned_data['search']
        given = form.cleaned_data['given']
        free = form.cleaned_data['free']
        active = form.cleaned_data['active']
        keytype = form.cleaned_data['keytype']

        keys = Key.objects.all()
        for s in search.split():
            keys = keys.filter(
                Q(keytype__shortname__icontains=s) |
                Q(keytype__name__icontains=s) |
                Q(number__icontains=s) |
                Q(comment__icontains=s) |
                Q(person__name__icontains=s) |
                Q(person__firstname__icontains=s) |
                Q(person__email__icontains=s) |
                Q(person__address__icontains=s) |
                Q(person__plz__icontains=s) |
                Q(person__city__icontains=s) |
                Q(person__mobile__icontains=s) |
                Q(person__phone__icontains=s)
            )

        if given and not free:
            keys = keys.exclude(person=None)
        if free and not given:
            keys = keys.filter(person=None)
        if active:
            keys = keys.filter(active=True)
        if keytype:
            keys = keys.filter(keytype=keytype)

    context = {
        'keys': keys,
        'form': form,
    }

    return render(request, 'schluessel/list_keys.html', context)


@login_required
def list_persons(request):
    persons = Person.objects.order_by("name", "firstname")

    form = FilterPersonsForm(request.POST or None)
    if form.is_valid():
        search = form.cleaned_data['search']

        for s in search.split():
            persons = persons.filter(
                Q(name__icontains=s) |
                Q(firstname__icontains=s) |
                Q(email__icontains=s) |
                Q(address__icontains=s) |
                Q(plz__icontains=s) |
                Q(city__icontains=s) |
                Q(mobile__icontains=s) |
                Q(phone__icontains=s)
            )

    context = {
        'persons': persons,
        'form': form,
    }

    return render(request, 'schluessel/list_persons.html', context)

@staff_member_required
def show_log(request):
    logentries = KeyLogEntry.objects.order_by("-date")[:20]

    context = {
        'logentries': logentries,
    }

    return render(request, 'schluessel/show_log.html', context)
