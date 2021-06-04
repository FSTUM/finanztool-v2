# Create your views here.
from typing import Callable

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from aufgaben.models import Aufgabe
from common.forms import MailForm, QRCodeForm, SettingsForm
from common.models import Mail, QRCode, Settings
from rechnung.models import Rechnung
from schluessel.models import Key

finanz_staff_member_required: Callable = staff_member_required(login_url="login")


class AuthWSGIRequest(WSGIRequest):
    user: User


@finanz_staff_member_required
def list_mail(request: AuthWSGIRequest) -> HttpResponse:
    if Settings.objects.exists():
        settings = Settings.objects.first()
    else:
        settings = Settings.objects.create()
    context = {"mails": Mail.objects.all(), "settings": settings}
    return render(request, "common/mail/list_email_templates.html", context)


@finanz_staff_member_required
def view_mail(request: AuthWSGIRequest, mail_pk: int) -> HttpResponse:
    mail = Mail.objects.get(pk=mail_pk)

    context = {
        "mail": mail,
    }
    return render(request, "common/mail/email_details.html", context)


@finanz_staff_member_required
def add_mail(request: AuthWSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("common:list_mail")

    context = {
        "form": form,
        "mail": Mail,
    }
    return render(request, "common/mail/add_email.html", context)


@finanz_staff_member_required
def edit_mail(request: AuthWSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()
        return redirect("common:list_mail")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "common/mail/edit_email.html", context)


@finanz_staff_member_required
def del_mail(request: AuthWSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()
        return redirect("common:list_mail")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "common/mail/delete_email.html", context)


@finanz_staff_member_required
def edit_settings(request: AuthWSGIRequest) -> HttpResponse:
    if Settings.objects.exists():
        settings = Settings.objects.first()
    else:
        settings = Settings.objects.create()
    form = SettingsForm(request.POST or None, instance=settings)
    if form.is_valid():
        form.save()
        return redirect("common:list_mail")

    context = {
        "form": form,
    }
    return render(request, "common/settings/settings.html", context)


@login_required(login_url="login")
def willkommen(request: AuthWSGIRequest) -> HttpResponse:
    rechnungen = Rechnung.objects.filter(gestellt=True, erledigt=False).all()
    offene_rechnungen = rechnungen.count()
    faellige_rechnungen = len(list(filter(lambda r: r.faellig, rechnungen)))
    eigene_aufgaben = Aufgabe.objects.filter(
        erledigt=False,
        zustaendig=request.user,
    ).count()
    schluessel = Key.objects.filter(active=True).count()
    verfuegbare_schluessel = Key.objects.filter(
        active=True,
        person=None,
    ).count()
    context = {
        "offene_rechnungen": offene_rechnungen,
        "faellige_rechnungen": faellige_rechnungen,
        "eigene_aufgaben": eigene_aufgaben,
        "schluessel": schluessel,
        "verfuegbare_schluessel": verfuegbare_schluessel,
    }
    return render(request, "common/willkommen.html", context)


@finanz_staff_member_required
def list_qr_codes(request: WSGIRequest) -> HttpResponse:
    context = {"qr_codes": QRCode.objects.all()}
    return render(request, "common/qr-codes/list_qr_codes.html", context)


@finanz_staff_member_required
def add_qr_code(request: WSGIRequest) -> HttpResponse:
    form = QRCodeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("common:list_qr_codes")

    context = {
        "form": form,
    }
    return render(request, "common/qr-codes/add_qr_code.html", context)


@finanz_staff_member_required
def del_qr_code(request: WSGIRequest, qr_code_pk: int) -> HttpResponse:
    qr_code: QRCode = get_object_or_404(QRCode, id=qr_code_pk)
    if qr_code.pk == 0:
        messages.error(request, "Finanztool sagt nein. Rick wird da bleiben.")
        redirect("")
    form = forms.Form(request.POST or None)
    if form.is_valid():
        qr_code.delete()
        messages.success(request, "Der QRCode wurde erfolgreich gelöscht")
        return redirect("common:list_qr_codes")
    messages.warning(
        request,
        "Be aware that deleting this deletes the actual file from the server. This means that if an "
        "other user has included this image via a hardlink, this image will not be loaded anymore. "
        "There be dragons.",
    )
    context = {"form": form, "qr_code": qr_code}
    return render(request, "common/qr-codes/del_qr_code.html", context)
