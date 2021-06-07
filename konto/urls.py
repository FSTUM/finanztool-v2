from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "konto"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="konto:einlesen"), name="index"),
    path(
        "konto/",
        include(
            [
                path("einlesen/", views.einlesen, name="einlesen"),
                path("mapping/", views.mapping, name="mapping"),
                path("einzahlungslog/", views.einzahlungslog, name="einzahlungslog"),
            ],
        ),
    ),
    path(
        "referenten/",
        include(
            [
                path("list/", views.list_referenten, name="list_referenten"),
                path("add/", views.add_referent, name="add_referent"),
                path("edit/<int:referent_pk>/", views.edit_referent, name="edit_referent"),
                path("del/<int:referent_pk>/", views.del_referent, name="del_referent"),
                path("inc/<int:referent_pk>/", views.inc_referent, name="inc_referent"),
            ],
        ),
    ),
]
