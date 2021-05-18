from django.urls import path

from . import views

app_name = "konto"

urlpatterns = [
    path("", views.einlesen, name="einlesen"),
    path("mapping/", views.mapping, name="mapping"),
]
