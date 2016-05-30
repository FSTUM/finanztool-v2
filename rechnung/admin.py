from django.contrib import admin

from .models import Rechnung, Kunde, Posten, Kategorie

admin.site.register(Rechnung)
admin.site.register(Kunde)
admin.site.register(Posten)
admin.site.register(Kategorie)
