from django.contrib import admin

from .models import Kategorie, Kunde, Mahnung, Posten, Rechnung

admin.site.register(Rechnung)
admin.site.register(Mahnung)
admin.site.register(Kunde)
admin.site.register(Posten)
admin.site.register(Kategorie)
