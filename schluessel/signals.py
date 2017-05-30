from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import KeyLogEntry


@receiver(post_save, sender=KeyLogEntry)
def finish_logentry_creation(sender, instance, **keywords):
    if instance.key and not instance.key_number:
        KeyLogEntry.objects.filter(pk=instance.pk).update(
            key_deposit=instance.key.keytype.deposit,
            key_keytype=instance.key.keytype,
            key_number=instance.key.number,
            key_comment=instance.key.comment,
        )
    if instance.person and not instance.person_name:
        KeyLogEntry.objects.filter(pk=instance.pk).update(
            person_name=instance.person.name,
            person_firstname=instance.person.firstname,
            person_email=instance.person.email,
            person_address=instance.person.address,
            person_plz = instance.person.plz,
            person_city = instance.person.city,
            person_mobile = instance.person.mobile,
            person_phone = instance.person.phone,
        )
