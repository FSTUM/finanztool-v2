import os
import subprocess  # nosec: fully defined
from tempfile import mkdtemp, mkstemp
from typing import Optional

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Exists, OuterRef, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from common.models import Settings
from common.views import AuthWSGIRequest, finanz_staff_member_required

from .forms import FilterKeysForm, KeyForm, KeyTypeForm, PersonForm, SaveKeyChangeForm, SelectPersonForm
from .models import Key, KeyLogEntry, KeyType, Person, SavedKeyChange


@login_required()
def view_key(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    logentries = key.keylogentry_set.order_by("date")

    context = {
        "key": key,
        "logentries": logentries,
    }

    return render(request, "schluessel/key/view_key.html", context)


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

    return render(request, "schluessel/key/add_key.html", context)


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

    return render(request, "schluessel/key/edit_key.html", context)


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
    common_settings: Settings = Settings.load()
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

        if "email-und-vormerken" in request.POST:
            if not common_settings.typ_aenderungs_beauftragter:
                messages.error(request, "Es ist kein Keycard-Typ-Änderungs-Beauftragter eingetragen")
            elif not common_settings.typ_aenderung_single:
                messages.error(
                    request,
                    "Es ist kein Keycard-Typ-Änderungs-Template für mehrere Keycard-Typ-Änderungen eingetragen",
                )
            else:
                mail_context = {"keycard": key}
                common_settings.typ_aenderung_single.send_mail(
                    mail_context,
                    common_settings.typ_aenderungs_beauftragter,
                )
                messages.success(
                    request,
                    "Keycard-Typ-Änderungs-Antrag wurden per email an den Keycard-Typ-Änderungs-Beauftragten gesendet",
                )

        return redirect("schluessel:view_key", key.id)

    context = {
        "key": key,
        "form": form,
        "settings": common_settings,
    }

    return render(request, "schluessel/key_change/save_key_change.html", context)


@finanz_staff_member_required
def del_key_change(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
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

    return render(request, "schluessel/key_change/del_key_change.html", context)


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

    setting: Settings = Settings.load()
    if not setting.set_inactive_key_type:
        messages.warning(
            request,
            "Es is kein Key-Typ als Keycard-Typ-Änderung, die den schlüssel als inaktiv setzt, "
            "eingestellt. Dies wird also im folgenden nicht gemacht.",
        )
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
                if setting.set_inactive_key_type and key.keytype == setting.set_inactive_key_type:
                    key.active = False
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
        "settings": Settings.load(),
    }

    return render(request, "schluessel/key_change/apply_key_change.html", context)


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
        common_settings: Settings = Settings.load()
        if not common_settings.typ_aenderungs_beauftragter:
            messages.error(request, "Es ist kein Keycard-Typ-Änderungs-Beauftragter eingetragen")
        elif not common_settings.typ_aenderung_multiple:
            messages.error(
                request,
                "Es ist kein Keycard-Typ-Änderungs-Template für mehrere Keycard-Typ-Änderungen eingetragen",
            )
        else:
            mail_context = {"keycards": keys}
            common_settings.typ_aenderung_multiple.send_mail(mail_context, common_settings.typ_aenderungs_beauftragter)

            messages.success(request, "Keycards wurden per email an den Keycard-Typ-Änderungs-Beauftragten gesendet")
        return redirect("schluessel:list_key_changes")

    context = {
        "keys": keys,
        "form": form,
        "settings": Settings.load(),
    }

    return render(request, "schluessel/key_change/list_key_changes.html", context)


@login_required()
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

    return render(request, "schluessel/key/return_key.html", context)


@login_required()
def give_key(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    key = get_object_or_404(Key, pk=key_pk)

    if not key.active:
        raise Http404("Key is inactive")

    if key.person:
        raise Http404("Key already given out")

    persons = Person.objects.order_by("name", "firstname")

    form = SelectPersonForm(request.POST or None)
    if form.is_valid():
        person: Person = form.cleaned_data["person"]
        return redirect("schluessel:give_key_confirm", key.id, person.id)

    context = {
        "key": key,
        "persons": persons,
        "form": form,
    }

    return render(request, "schluessel/key/give_key.html", context)


@login_required()
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

    return render(request, "schluessel/key/give_key_confirm.html", context)


@login_required()
def view_person(request: AuthWSGIRequest, person_pk: int) -> HttpResponse:
    person = get_object_or_404(Person, pk=person_pk)

    keys = person.key_set.order_by("keytype__shortname", "number")

    logentries = person.keylogentry_set.order_by("date")

    context = {
        "person": person,
        "keys": keys,
        "logentries": logentries,
    }

    return render(request, "schluessel/person/view_person.html", context)


@login_required()
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

    return render(request, "schluessel/person/add_person.html", context)


@login_required()
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

    return render(request, "schluessel/person/add_person.html", context)


@login_required()
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

    return render(request, "schluessel/person/edit_person.html", context)


@login_required()
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

    return render(request, "schluessel/person/edit_person.html", context)


@login_required()
def get_kaution(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    return create_pdf(request, key_pk, doc="Kaution")


@login_required()
def get_quittung(request: AuthWSGIRequest, key_pk: int) -> HttpResponse:
    return create_pdf(request, key_pk, doc="Quittung")


@login_required()
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

    # Pass TeX template through Django templating engine and into the temp file
    context = {"key": key, "user": request.user}

    rendered_template = render_to_string(f"schluessel/tex/latex_{doc}.tex", context).encode("utf8")
    os.write(latex_file, rendered_template)
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
            "schluessel/tex/pdflatex_error.html",
            {"erroroutput": error.output, "doc": doc},
        )

    response = HttpResponse(content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f'inline;filename="{doc}_{key.keytype.shortname}_{key.number}_{key.person.name}_{key.person.firstname}.pdf"'

    # return path to pdf
    pdf_filename = f"{os.path.splitext(latex_filename)[0]}.pdf"

    with open(pdf_filename, "rb") as pdf:
        response.write(pdf.read())

    return response


@login_required()
def list_keys(request: AuthWSGIRequest) -> HttpResponse:
    keys = Key.objects.filter(active=True).order_by(
        "keytype__shortname",
        "number",
    )

    form = FilterKeysForm(request.POST or None)
    if form.is_valid():
        given = form.cleaned_data["given"]
        free = form.cleaned_data["free"]
        active = form.cleaned_data["active"]
        keytype = form.cleaned_data["keytype"]

        keys = Key.objects.all()
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

    return render(request, "schluessel/key/list_keys.html", context)


@login_required()
def list_persons(request: AuthWSGIRequest) -> HttpResponse:
    persons = Person.objects.order_by("name", "firstname")

    context = {
        "persons": persons,
    }
    return render(request, "schluessel/person/list_persons.html", context)


@finanz_staff_member_required
def show_log(request: AuthWSGIRequest) -> HttpResponse:
    logentries = KeyLogEntry.objects.order_by("-date")[:20]

    context = {
        "logentries": logentries,
    }

    return render(request, "schluessel/key_change/show_log.html", context)


@finanz_staff_member_required
def list_key_types(request: AuthWSGIRequest) -> HttpResponse:
    key_types_liste = KeyType.objects.order_by("name")
    context = {"key_types_liste": key_types_liste}
    return render(request, "schluessel/key-typen/list_key-typen.html", context)


@finanz_staff_member_required
def add_key_typ(request: AuthWSGIRequest) -> HttpResponse:
    form = KeyTypeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("schluessel:list_key_types")
    context = {"form": form}
    return render(request, "schluessel/key-typen/add_key-typen.html", context)


@finanz_staff_member_required
def edit_key_typ(request: AuthWSGIRequest, schluessel_typ_pk: int) -> HttpResponse:
    schluessel_typ = get_object_or_404(KeyType, pk=schluessel_typ_pk)
    form = KeyTypeForm(request.POST or None, instance=schluessel_typ)
    if form.is_valid():
        form.save()
        return redirect("schluessel:list_key_types")
    context = {"form": form, "schluessel_typ": schluessel_typ}
    return render(request, "schluessel/key-typen/edit_key-typen.html", context)


@finanz_staff_member_required
def del_key_typ(request: AuthWSGIRequest, schluessel_typ_pk: int) -> HttpResponse:
    schluessel_typ = get_object_or_404(KeyType, pk=schluessel_typ_pk)
    messages.error(
        request,
        "Wenn du diesen Schlüssel-Typ löschst, dann wirst du alle davon abhängigen Schlüssel mit löschen. "
        "There be dragons.",
    )
    form = forms.Form(request.POST or None)
    if form.is_valid():
        schluessel_typ.delete()
        return redirect("schluessel:list_key_types")
    context = {"form": form, "schluessel_typ": schluessel_typ}
    return render(request, "schluessel/key-typen/del_key-typen.html", context)


def get_key_status(is_keycard: bool) -> list[int]:
    aktive_keys = Key.objects.filter(active=True, keytype__keycard=is_keycard)

    key_change_event = SavedKeyChange.objects.filter(key=OuterRef("pk"))
    assigned_keys_count = aktive_keys.exclude(person=None).filter(~Exists(key_change_event)).count()
    keys_change_request_cnt: int = 0
    if is_keycard:
        keys_change_request_cnt = aktive_keys.exclude(person=None).filter(Exists(key_change_event)).count()

    no_person_cnt = aktive_keys.filter(person=None).count()
    if is_keycard:
        return [assigned_keys_count, no_person_cnt, keys_change_request_cnt]
    return [assigned_keys_count, no_person_cnt]


def get_key_usage_statistic_by_key_type():
    # key=Null means that this is a person being created
    logs = (
        KeyLogEntry.objects.filter(key__isnull=True)
        .order_by("date")
        .values("date", "key_keytype", "operation", "key")
        .all()
    )
    key_types = KeyType.objects.all()
    key_asignement = {}
    key_asignement_cnt = {kt.pk: 0 for kt in key_types}
    key_avaliability_cnt = {kt.pk: 0 for kt in key_types}
    usage_statistic = {kt.pk: ([], []) for kt in key_types}
    for log in logs:
        operation, keytype, key = log["operation"], log["key_keytype"], log["key"]

        # adjust avaliable key count
        if operation == KeyLogEntry.EDIT:
            if key not in key_asignement:
                raise RuntimeError(
                    f"Key {key} was edited before initial assignment to a person. " f"This violates an assumption",
                )
            if key_asignement[key] != keytype:
                key_avaliability_cnt[key_asignement[key]] -= 1
                key_asignement[key] = keytype
                key_avaliability_cnt[keytype] += 1
        if operation == KeyLogEntry.CREATE:
            key_avaliability_cnt[keytype] += 1

        if operation == KeyLogEntry.GIVE:
            key_asignement[key] = keytype
            key_asignement_cnt[keytype] += 1
        if operation == KeyLogEntry.RETURN:
            del key_asignement[key]
            key_asignement_cnt[keytype] -= 1

        usage_statistic[keytype][0].append(log["date"].strftime("%Y-%m-%d %H:%M"))
        if (key_avaliability_cnt[keytype]) == 0:
            # make it obvious, that the
            usage_statistic[keytype][1].append(-key_asignement_cnt[keytype])
        else:
            usage_statistic[keytype][1].append(100 * key_asignement_cnt[keytype] / key_avaliability_cnt[keytype])

    return [(get_object_or_404(KeyType, pk=key), dates, values) for key, (dates, values) in usage_statistic.items()]


def get_key_tpye_cnt_by_key_type():
    aktive_keys = Key.objects.filter(active=True)
    kt_cnts = aktive_keys.values("keytype").annotate(keytype_count=Count("keytype"))

    return (
        [keytype["keytype_count"] for keytype in kt_cnts],
        [KeyType.objects.get(pk=keytype["keytype"]).shortname for keytype in kt_cnts],
    )


@finanz_staff_member_required
def dashboard(request: AuthWSGIRequest) -> HttpResponse:
    key_card_status = get_key_status(True)
    key_status = get_key_status(False)
    key_types_values, key_types_labels = get_key_tpye_cnt_by_key_type()
    KeyLogEntry.objects.values("key__keytype", "date")
    dates = list(KeyLogEntry.objects.values_list("date", flat=True))
    context = {
        "key_card_status": key_card_status,
        "key_status": key_status,
        "key_types_values": key_types_values,
        "key_types_labels": key_types_labels,
        "usage_statistic": get_key_usage_statistic_by_key_type(),
        "date_range": [min(dates).strftime("%Y-%m-%d %H:%M"), max(dates).strftime("%Y-%m-%d %H:%M")],
    }
    return render(request, "schluessel/schluessel_dashboard.html", context)
