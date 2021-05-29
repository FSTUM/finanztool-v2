import re
from typing import Any, Dict, List, Optional, Tuple, Union

from django.core.cache import cache
from django.core.mail import EmailMessage, send_mail
from django.db import models
from django.db.models import ForeignKey
from django.http import HttpResponse
from django.template import Context, Template


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        pass

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):
        self.pk = 1  # pylint: disable=invalid-name
        super().save(*args, **kwargs)
        self.set_cache()

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)


def clean_attachable(response: Union[HttpResponse, Tuple[str, Any, str]]) -> Tuple[str, Any, str]:
    if not isinstance(response, HttpResponse):
        return response
    content_type = response.get("Content-Type", "text/text")
    filename = response.get("Content-Disposition", "filename.txt").replace("inline; filename=", "")
    return filename, response.content, content_type


class Mail(models.Model):
    FINANZ = "Finanz-Referat FSMPI <finanz@fs.tum.de>"
    # ["{{template}}", "description"]
    general_placeholders: List[Tuple[str, str]] = []
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: List[Tuple[str, str, str]] = [
        (
            "{% for rechnung in rechnungen %}...",
            "Alle überfälligen Rechnungen",
            "falls in den Einstellungen als Mailbenachrichtigung bei überfälligen Rechnungen konfiguriert",
        ),
        (
            "{% for aufgabe in aufgaben %}...",
            "zugewiesene Aufgaben pro User",
            "falls in den Einstellungen als Mailbenachrichtigung bei zugewiesene Aufgaben konfiguriert",
        ),
        (
            "keycard",
            "Schlüsselkare, deren Typ geändert werden soll",
            "falls in den Einstellungen als Template für eine einzige Typ-Änderung konfiguriert",
        ),
        (
            "keycard.savedkeychange",
            "Keycard-Änderungsantrag",
            "falls in den Einstellungen als Template für eine einzige Typ-Änderung konfiguriert",
        ),
        (
            "{% for key in keycards %}...",
            "Schlüsselkaren, deren Typ geändert werden soll",
            "falls in den Einstellungen als Template für mehrere Typ-Änderungen konfiguriert",
        ),
    ]
    notes: str = ""

    subject = models.CharField("Email subject", max_length=200, help_text="You may use placeholders for the subject.")

    text = models.TextField("Text", help_text="You may use placeholders for the text.")

    comment = models.CharField(
        "Comment",
        max_length=200,
        default="",
        blank=True,
    )

    def __str__(self):
        if self.comment:
            return f"{self.subject} ({self.comment})"
        return str(self.subject)

    def get_mail(self, context: Union[Context, Dict[str, Any], None]) -> Tuple[str, str]:
        if not isinstance(context, Context):
            context = Context(context or {})

        subject_template = Template(self.subject)
        subject: str = subject_template.render(context).rstrip()

        text_template = Template(self.text)
        text: str = text_template.render(context)

        return subject, text

    def send_mail(
        self,
        context: Union[Context, Dict[str, Any], None],
        recipients: Union[List[str], str],
        attachments: Optional[Union[HttpResponse, List[Tuple[str, Any, str]]]] = None,
    ) -> bool:
        if isinstance(recipients, str):
            recipients = [recipients]
        if not isinstance(context, Context):
            context = Context(context or {})
        subject_template = Template(self.subject)
        subject = subject_template.render(context).rstrip()

        text_template = Template(self.text)
        text = text_template.render(context)

        regex = r"({{.*?}})"
        subject_matches = re.match(regex, subject, re.MULTILINE)
        text_matches = re.match(regex, text, re.MULTILINE)

        if subject_matches is not None or text_matches is not None:
            return False
        if attachments is None:
            send_mail(subject, text, Mail.FINANZ, recipients, fail_silently=False)
        else:
            mail = EmailMessage(subject, text, Mail.FINANZ, recipients)
            for (filename, content, mimetype) in [clean_attachable(attach) for attach in attachments]:
                mail.attach(filename, content, mimetype)
            mail.send(fail_silently=False)
        return True


class Settings(SingletonModel):
    ueberfaellige_rechnung_mail = ForeignKey(
        Mail,
        related_name="ueberfaellige_rechnung_mail+",
        verbose_name="Mailbenachrichtigung bei überfälligen Rechnungen",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    zugewiesene_aufgabe_mail = ForeignKey(
        Mail,
        related_name="zugewiesene_aufgabe_mail+",
        verbose_name="Mailbenachrichtigung über zugewiesene Aufgaben",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    typ_aenderungs_beauftragter = models.EmailField(
        verbose_name="Emailadresse, an die die Keycard-Typ-Änderngs-anfragen geschickt werden",
        null=True,
        blank=True,
    )
    typ_aenderung_single = ForeignKey(
        Mail,
        related_name="typ_aenderung_single+",
        verbose_name="Template, das ausgewählt wird, wenn eine einzige Keycard-Typ-Änderung versendet werden soll",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    typ_aenderung_multiple = ForeignKey(
        Mail,
        related_name="typ_aenderung_single+",
        verbose_name="Template, das ausgewählt wird, wenn mehrere Keycard-Typ-Änderungen versendet werden sollen",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"ueberfaellige_rechnung_mail={self.ueberfaellige_rechnung_mail}, "
            f"zugewiesene_aufgabe_mail={self.zugewiesene_aufgabe_mail}"
        )
