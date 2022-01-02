import os
import re
from io import BytesIO
from typing import Any, Optional, Tuple, TypeVar, Union

import qrcode
from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.db.models import ForeignKey
from django.dispatch import receiver
from django.http import HttpResponse
from django.template import Context, Template
from PIL import Image

from schluessel.models import KeyType

SingletonType = TypeVar("SingletonType", bound="SingletonModel")


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
    def load(cls) -> SingletonType:
        obj: SingletonType
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


def clean_attachable(response: Union[HttpResponse, tuple[str, Any, str]]) -> tuple[str, Any, str]:
    if not isinstance(response, HttpResponse):
        return response
    content_type = response.get("Content-Type", "text/text")
    filename = response.get("Content-Disposition", "filename.txt").replace("inline; filename=", "")
    return filename, response.content, content_type


class Mail(models.Model):
    FINANZ = "Finanz-Referat FSMPI <finanz@fs.tum.de>"
    # ["{{template}}", "description"]
    general_placeholders: list[Tuple[str, str]] = []
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: list[Tuple[str, str, str]] = [
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
            "{{ keycard }}",
            "Schlüsselkarte, deren Typ geändert werden soll",
            "falls in den Einstellungen als Template für eine einzige Typ-Änderung konfiguriert",
        ),
        (
            "{{ keycard.savedkeychange }}",
            "Schlüsselkarten-Änderungsantrag",
            "falls in den Einstellungen als Template für eine einzige Typ-Änderung konfiguriert",
        ),
        (
            "{% for keycard in keycards %}...",
            "Schlüsselkarten, deren Typ geändert werden soll",
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

    def get_mail(self, context: Union[Context, dict[str, Any], None]) -> tuple[str, str]:
        if not isinstance(context, Context):
            context = Context(context or {})

        subject_template = Template(self.subject)
        subject: str = subject_template.render(context).rstrip()

        text_template = Template(self.text)
        text: str = text_template.render(context)

        return subject, text

    def send_mail(
        self,
        context: Union[Context, dict[str, Any], None],
        recipients: Union[list[str], str],
        attachments: Optional[Union[HttpResponse, list[Tuple[str, Any, str]]]] = None,
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
        email = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=Mail.FINANZ,
            to=recipients,
            cc=[Mail.FINANZ],
            reply_to=[Mail.FINANZ],
        )
        if attachments is not None:
            for (filename, content, mimetype) in [clean_attachable(attach) for attach in attachments]:
                email.attach(filename, content, mimetype)
        email.send(fail_silently=False)
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
    set_inactive_key_type = ForeignKey(
        KeyType,
        related_name="set_inactive_key_type+",
        verbose_name="Keycard-Typ-Änderung, die falls dieser Keycard-Typ-Änderungens-antrag angenommen wird, "
        "den Schlüssel als inaktiv setzt. Bisherige Keycards werden nicht behandelt/ geupdated.",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"ueberfaellige_rechnung_mail={self.ueberfaellige_rechnung_mail}, "
            f"zugewiesene_aufgabe_mail={self.zugewiesene_aufgabe_mail}"
        )


class QRCode(models.Model):
    content = models.CharField(max_length=200, unique=True)
    qr_code = models.ImageField(upload_to="qr_codes", blank=True)

    def __str__(self):
        return self.content

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        qr_code = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=19,
            border=1,
        )
        qr_code.add_data(self.content)
        qr_code.make(fit=True)
        qr_image = qr_code.make_image(fill_color="black", back_color="white")

        with Image.new("RGB", (qr_image.pixel_size, qr_image.pixel_size), "white") as canvas:
            canvas.paste(qr_image)

            logo_path = os.path.join(settings.STATIC_ROOT, "logo", "eule_squared.png")
            with Image.open(logo_path) as logo:
                total_usable_height = qr_image.pixel_size - qr_image.box_size * qr_image.border * 2
                usable_height = total_usable_height * 0.3
                size = int(usable_height // qr_image.box_size + 1) * qr_image.box_size
                # current image version can take it to have up to 30% covered up.
                # due to math we are always below that limt
                if ((qr_image.pixel_size - size) // 2 % qr_image.box_size) != 0:
                    size += qr_image.box_size

                t_logo = logo.resize((size, size))
                pos = (qr_image.pixel_size - size) // 2
                canvas.paste(t_logo, (pos, pos))

            # noinspection HttpUrlsUsage
            f_cleaned_content = (
                self.content.replace("https://", "")
                .replace("http://", "")
                .strip("/")
                .replace("/", "-")
                .replace(".", "_")
            )
            buffer = BytesIO()
            canvas.save(buffer, "PNG")
            self.qr_code.save(f"qr_code_{f_cleaned_content}.png", File(buffer), save=False)
            super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=QRCode)
def auto_del_qr_code_on_delete(sender, instance, **_kwargs):
    """
    Deletes file from filesystem
    when corresponding `QRCode` object is deleted.
    """
    _ = sender  # sender is needed, for api. it cannot be renamed, but is unused here.
    if instance.pk and instance.pk != 0 and instance.qr_code and os.path.isfile(instance.qr_code.path):
        os.remove(instance.qr_code.path)
