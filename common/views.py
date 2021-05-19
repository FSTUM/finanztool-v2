# Create your views here.
from typing import Callable

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.forms import MailForm, SettingsForm
from common.models import Mail, Settings

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
    return render(request, "common/settings.html", context)
