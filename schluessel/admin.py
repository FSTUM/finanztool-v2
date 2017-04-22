from django.contrib import admin

from .models import Person, KeyType, Key, KeyLogEntry

admin.site.register(Person)
admin.site.register(KeyType)
admin.site.register(Key)
admin.site.register(KeyLogEntry)
