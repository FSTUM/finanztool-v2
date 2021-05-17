from django.conf.urls import url

from . import views

app_name = "konto"

urlpatterns = [
    # Index########################################################################
    # ex: /konto/
    url(r"^$", views.einlesen, name="einlesen"),
    url(r"^mapping/$", views.mapping, name="mapping"),
]
