from django.contrib import admin

from .models import Key, KeyLogEntry, KeyType, Person

admin.site.register(Person)
admin.site.register(KeyType)
admin.site.register(Key)
admin.site.register(KeyLogEntry)
