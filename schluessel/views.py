import os
import subprocess  # nosec: fully defined
from tempfile import mkdtemp, mkstemp
from typing import Optional

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from common.views import AuthWSGIRequest, finanz_staff_member_required

from .forms import (
    FilterKeysForm,
    FilterPersonsForm,
    KeyForm,
    PersonForm,
    SaveKeyChangeForm,
    SelectPersonForm,
    SelectPersonFormNoscript,
)
from .models import Key, KeyLogEntry, Person, SavedKeyChange


@login_required(login_url="login")
def view_key(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    logentries = key.keylogentry_set.order_by("date")

    context = {
        "key": key,
        "logentries": logentries,
    }

    return render(request, "schluessel/view_key.html", context)


@finanz_staff_member_required
def add_key(request: AuthWSGIRequest) -> HttpResponse:
    form = KeyForm(request.POST or None)
    if form.is_valid():
        key = form.save()

        KeyLogEntry.objects.create(
            key=key,
            person=None,
            user=request.user,
            operation=KeyLogEntry.CREATE,
        )

        return redirect("schluessel:view_key", key.id)

    context = {
        "form": form,
    }

    return render(request, "schluessel/add_key.html", context)


@finanz_staff_member_required
def edit_key(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
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

        return redirect("schluessel:view_key", key.id)

    context = {
        "key": key,
        "form": form,
    }

    return render(request, "schluessel/edit_key.html", context)


@finanz_staff_member_required
def save_key_change(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if not key.keytype.keycard:
        raise Http404("Key is not a keycard")

    try:
        initial = {
            "keytype": key.savedkeychange.new_keytype,
            "comment": key.savedkeychange.comment,
        }
    except ObjectDoesNotExist:
        initial = {}
    form = SaveKeyChangeForm(
        request.POST or None,
        initial=initial,
        keytype=key.keytype,
    )

    if form.is_valid():
        keytype = form.cleaned_data["keytype"]
        comment = form.cleaned_data["comment"]

        if hasattr(key, "savedkeychange"):
            key.savedkeychange.user = request.user
            key.savedkeychange.new_keytype = keytype
            key.savedkeychange.comment = comment
            key.savedkeychange.save()
        else:
            SavedKeyChange.objects.create(
                key=key,
                new_keytype=keytype,
                comment=comment,
                user=request.user,
            )

        return redirect("schluessel:view_key", key.id)

    context = {
        "key": key,
        "form": form,
    }

    return render(request, "schluessel/save_key_change.html", context)


@finanz_staff_member_required
def delete_key_change(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if not key.keytype.keycard:
        raise Http404("Key is not a keycard")

    try:
        keychange = key.savedkeychange
    except ObjectDoesNotExist:
        raise Http404("Key change does not exist")  # pylint: disable=raise-missing-from

    form = forms.Form(request.POST or None)
    if form.is_valid():
        SavedKeyChange.objects.filter(pk=keychange.pk).delete()

        return redirect("schluessel:view_key", key.id)

    context = {
        "key": key,
        "form": form,
    }

    return render(request, "schluessel/delete_key_change.html", context)


@finanz_staff_member_required
def apply_key_change(request: AuthWSGIRequest, key_pk: Optional[int] = None) -> HttpResponse:
    key: Optional[Key] = None
    keys: QuerySet[Key] = (
        Key.objects.filter(keytype__keycard=True, active=True)
        .exclude(savedkeychange=None)
        .order_by("keytype__shortname", "number")
    )

    if key_pk:
        key = get_object_or_404(Key, pk=key_pk)
        key_state_check(key)
        keys = keys.filter(pk=key_pk)
    if not keys.exists():
        raise Http404("There are no key changes")

    form = forms.Form(request.POST or None)
    if form.is_valid():
        not_applied_keys = []
        applied_keys = []
        for key in keys:
            try:
                saved_key_change = key.savedkeychange
            except ObjectDoesNotExist:
                continue
            if saved_key_change.violated_key:
                not_applied_keys.append(key)
            else:
                old_keytype = key.keytype
                key.keytype = saved_key_change.new_keytype
                key.save()
                applied_keys.append((old_keytype, key))
                SavedKeyChange.objects.filter(pk=key.savedkeychange.pk).delete()
                KeyLogEntry.objects.create(
                    key=key,
                    person=None,
                    user=request.user,
                    operation=KeyLogEntry.EDIT,
                )
        if not_applied_keys:
            concatinated_unaplied_keys = ", ".join(
                [f"{k} -> {k.savedkeychange.new_keytype.shortname} {k.number}" for k in not_applied_keys],
            )
            messages.error(
                request,
                f"Die folgenden Änderungen konnten nicht angewendet werden, weil eine solche Schließkarte bereits "
                f"existiert: {concatinated_unaplied_keys}",
            )
        if applied_keys:
            concatinated_aplied_keys = ", ".join(
                [
                    f"{okt.shortname} {k.number} -> {k}" + (f" ({k.person})" if k.person else "")
                    for okt, k in applied_keys
                ],
            )
            messages.success(
                request,
                f"Folgende Änderungen wurden erfolgreich angewendet. Bitte informiere ggf. die momentanen "
                f"Entleiher*innen (in Klammern): {concatinated_aplied_keys}",
            )
        if key:
            return redirect("schluessel:view_key", key.id)
        return redirect("schluessel:list_key_changes")

    context = {
        "cur_key": key,
        "keys": keys,
        "form": form,
    }

    return render(request, "schluessel/apply_key_change.html", context)


def key_state_check(key: Key) -> None:
    if not key.active:
        raise Http404("Key is inactive")
    if not key.keytype.keycard:
        raise Http404("Key is not a keycard")
    try:
        if key.savedkeychange.violated_key:
            raise Http404("Key change is violating another key")
    except ObjectDoesNotExist:
        raise Http404("Key change does not exist")  # pylint: disable=raise-missing-from


@finanz_staff_member_required
def list_key_changes(request: AuthWSGIRequest) -> HttpResponse:
    keys = (
        Key.objects.filter(
            keytype__keycard=True,
            active=True,
        )
        .exclude(savedkeychange=None)
        .order_by("keytype__shortname", "number")
    )

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
        return redirect("schluessel:list_key_changes")

    context = {
        "keys": keys,
        "form": form,
    }

    return render(request, "schluessel/list_key_changes.html", context)


@login_required(login_url="login")
def return_key(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if not key.person:
        raise Http404("Key not given out")

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

        return redirect("schluessel:view_key", key.id)

    context = {
        "key": key,
        "form": form,
    }

    return render(request, "schluessel/return_key.html", context)


@login_required(login_url="login")
def give_key(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if key.person:
        raise Http404("Key already given out")

    persons = Person.objects.order_by("name", "firstname")

    form = SelectPersonForm(request.POST or None)
    if form.is_valid():
        person_id = form.cleaned_data["person"]
        if person_id:
            try:
                person = persons.get(id=person_id)
            except Person.DoesNotExist:
                return redirect("schluessel:give_key", key.id)

            return redirect("schluessel:give_key_confirm", key.id, person.id)
        return redirect("schluessel:give_key", key.id)

    formns = SelectPersonFormNoscript(request.POST or None)
    if formns.is_valid():
        person = formns.cleaned_data["person"]
        return redirect("schluessel:give_key_confirm", key.id, person.id)

    context = {
        "key": key,
        "persons": persons,
        "form": form,
        "formns": formns,
    }

    return render(request, "schluessel/give_key.html", context)


@login_required(login_url="login")
def give_key_confirm(request: AuthWSGIRequest, key_pk: int, person_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if key.person:
        raise Http404("Key already given out")

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

        return redirect("schluessel:view_key", key.id)

    context = {
        "key": key,
        "person": person,
        "form": form,
    }

    return render(request, "schluessel/give_key_confirm.html", context)


@login_required(login_url="login")
def view_person(request: AuthWSGIRequest, person_pk: int) -> HttpResponse:
    person = get_object_or_404(Person, pk=person_pk)

    keys = person.key_set.order_by("keytype__shortname", "number")

    logentries = person.keylogentry_set.order_by("date")

    context = {
        "person": person,
        "keys": keys,
        "logentries": logentries,
    }

    return render(request, "schluessel/view_person.html", context)


@login_required(login_url="login")
def add_person(request: AuthWSGIRequest) -> HttpResponse:
    form = PersonForm(request.POST or None)
    if form.is_valid():
        person = form.save()

        KeyLogEntry.objects.create(
            key=None,
            person=person,
            user=request.user,
            operation=KeyLogEntry.CREATE,
        )

        return redirect("schluessel:view_person", person.id)

    context = {
        "form": form,
    }

    return render(request, "schluessel/add_person.html", context)


@login_required(login_url="login")
def give_add_person(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    form = PersonForm(request.POST or None)
    if form.is_valid():
        person = form.save()

        KeyLogEntry.objects.create(
            key=None,
            person=person,
            user=request.user,
            operation=KeyLogEntry.CREATE,
        )

        return redirect("schluessel:give_key_confirm", key_pk, person.id)

    context = {
        "form": form,
    }

    return render(request, "schluessel/add_person.html", context)


@login_required(login_url="login")
def edit_person(request: AuthWSGIRequest, person_pk: int) -> HttpResponse:
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

        return redirect("schluessel:view_person", person.id)

    context = {
        "person": person,
        "form": form,
    }

    return render(request, "schluessel/edit_person.html", context)


@login_required(login_url="login")
def give_edit_person(request: AuthWSGIRequest, key_pk: int, person_pk: int) -> HttpResponse:
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

        return redirect("schluessel:give_key_confirm", key_pk, person.id)

    context = {
        "person": person,
        "form": form,
    }

    return render(request, "schluessel/edit_person.html", context)


@login_required(login_url="login")
def get_kaution(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    return create_pdf(request, key_pk, doc="Kaution")


@login_required(login_url="login")
def get_quittung(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    return create_pdf(request, key_pk, doc="Quittung")


@login_required(login_url="login")
def create_pdf(request: AuthWSGIRequest, key_pk: int, doc: str) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if not key.person:
        raise Http404("Key not given out")

    if doc == "Quittung" and key.keytype.deposit == 0:
        raise Http404("Key has no deposit")

    # create temporary files
    tmplatex = mkdtemp()
    latex_file, latex_filename = mkstemp(suffix=".tex", dir=tmplatex)

    logo_path = os.path.join(settings.BASE_DIR, "static/logo")

    # Pass TeX template through Django templating engine and into the temp file
    context = {"key": key, "user": request.user, "logo_path": logo_path}

    os.write(
        latex_file,
        render_to_string(
            f"schluessel/latex_{doc}.tex",
            context,
        ).encode("utf8"),
    )
    os.close(latex_file)

    # Compile the TeX file with PDFLaTeX
    try:
        subprocess.check_output(  # nosec: fully defined
            [
                "pdflatex",
                "-halt-on-error",
                "-output-directory",
                tmplatex,
                latex_filename,
            ],
        )
    except subprocess.CalledProcessError as error:
        return render(
            request,
            "schluessel/pdflatex_error.html",
            {"erroroutput": error.output, "doc": doc},
        )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment;filename="{doc}_{key.keytype.shortname}_{key.number}_'
        f'{key.person.name}_{key.person.firstname}.pdf"'
    )

    # return path to pdf
    pdf_filename = f"{os.path.splitext(latex_filename)[0]}.pdf"

    with open(pdf_filename, "rb") as pdf:
        response.write(pdf.read())

    return response


@login_required(login_url="login")
def list_keys(request: AuthWSGIRequest) -> HttpResponse:
    keys = Key.objects.filter(active=True).order_by(
        "keytype__shortname",
        "number",
    )

    form = FilterKeysForm(request.POST or None)
    if form.is_valid():
        search = form.cleaned_data["search"]
        given = form.cleaned_data["given"]
        free = form.cleaned_data["free"]
        active = form.cleaned_data["active"]
        keytype = form.cleaned_data["keytype"]

        keys = Key.objects.all()
        for search_term in search.split():
            keys = keys.filter(
                Q(keytype__shortname__icontains=search_term)
                | Q(keytype__name__icontains=search_term)
                | Q(number__icontains=search_term)
                | Q(comment__icontains=search_term)
                | Q(person__name__icontains=search_term)
                | Q(person__firstname__icontains=search_term)
                | Q(person__email__icontains=search_term)
                | Q(person__address__icontains=search_term)
                | Q(person__plz__icontains=search_term)
                | Q(person__city__icontains=search_term)
                | Q(person__mobile__icontains=search_term)
                | Q(person__phone__icontains=search_term),
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
        "keys": keys,
        "form": form,
    }

    return render(request, "schluessel/list_keys.html", context)


@login_required(login_url="login")
def list_persons(request: AuthWSGIRequest) -> HttpResponse:
    persons = Person.objects.order_by("name", "firstname")

    form = FilterPersonsForm(request.POST or None)
    if form.is_valid():
        search = form.cleaned_data["search"]

        for search_term in search.split():
            persons = persons.filter(
                Q(name__icontains=search_term)
                | Q(firstname__icontains=search_term)
                | Q(email__icontains=search_term)
                | Q(address__icontains=search_term)
                | Q(plz__icontains=search_term)
                | Q(city__icontains=search_term)
                | Q(mobile__icontains=search_term)
                | Q(phone__icontains=search_term),
            )

    context = {
        "persons": persons,
        "form": form,
    }

    return render(request, "schluessel/list_persons.html", context)


@finanz_staff_member_required
def show_log(request: AuthWSGIRequest) -> HttpResponse:
    logentries = KeyLogEntry.objects.order_by("-date")[:20]

    context = {
        "logentries": logentries,
    }

    return render(request, "schluessel/show_log.html", context)
