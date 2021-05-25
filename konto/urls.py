from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "konto"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="konto:einlesen"), name="index"),
    path("einlesen/", views.einlesen, name="einlesen"),
    path("mapping/", views.mapping, name="mapping"),
]
