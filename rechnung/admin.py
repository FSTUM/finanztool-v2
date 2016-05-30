from django.contrib import admin

from .models import Rechnung, Kunde, Posten, Kategorie, AnzahlPosten

class AnzahlPostenInline(admin.TabularInline):
    model = AnzahlPosten
    extra = 1

class RechnungAdmin(admin.ModelAdmin):
    inlines = (
            AnzahlPostenInline,
            )

admin.site.register(Rechnung)
admin.site.register(Kunde)
admin.site.register(Posten)
admin.site.register(Kategorie)
admin.site.register(AnzahlPosten)
