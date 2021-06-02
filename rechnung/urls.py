from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "rechnung"
urlpatterns = [
    # Index
    path("", RedirectView.as_view(pattern_name="rechnung:dashboard"), name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # Rechnung
    path(
        "rechnung/",
        include(
            [
                path(
                    "list/",
                    include(
                        [
                            path("", views.list_rechnungen, name="list_rechnungen"),
                            path("<int:kategorie_pk_filter>/", views.list_rechnungen, name="list_rechnungen_filter"),
                        ],
                    ),
                ),
                path("neu/", views.form_rechnung, name="rechnung_neu"),
                path("<int:rechnung_id>/", views.rechnung, name="rechnung"),
                path("<int:rechnung_id>/aendern/", views.form_rechnung, name="rechnung_aendern"),
                path("<int:rechnung_id>/duplizieren/", views.duplicate_rechnung, name="rechnung_duplizieren"),
                path("<int:rechnung_id>/posten/neu/", views.form_rechnung_posten, name="rechnung_posten_neu"),
                path("<int:rechnung_id>/pdf/", views.rechnungpdf, name="rechnungpdf"),
            ],
        ),
    ),
    # Mahnung
    path(
        "mahnung/",
        include(
            [
                path("alle/", views.alle_mahnungen, name="alle_mahnungen"),
                path("<int:rechnung_id>/neu/", views.form_mahnung, name="mahnung_neu"),
                path("<int:rechnung_id>/<int:mahnung_id>/", views.mahnung, name="mahnung"),
                path("<int:rechnung_id>/<int:mahnung_id>/aendern/", views.form_mahnung, name="mahnung_aendern"),
                path("<int:rechnung_id>/<int:mahnung_id>/pdf/", views.rechnungpdf, name="mahnungpdf"),
            ],
        ),
    ),
    # Kunde
    path(
        "kunde/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="rechnung:kunden_alle"), name="kunden_index"),
                path("alle/", views.kunden_alle, name="kunden_alle"),
                path("neu/", views.form_kunde, name="kunde_neu"),
                path("<int:kunde_id>/", views.kunde, name="kunde"),
                path("<int:kunde_id>/aendern/", views.form_kunde, name="kunde_aendern"),
            ],
        ),
    ),
    # Posten
    path(
        "posten/",
        include(
            [
                path("<int:posten_id>/", views.posten, name="posten"),
                path("<int:posten_id>/aendern/", views.form_exist_posten, name="posten_aendern"),
            ],
        ),
    ),
    path(
        "kategorie/",
        include(
            [
                path("list/", views.list_kategorien, name="list_kategorien"),
                path("add/", views.add_kategorie, name="add_kategorie"),
                path("edit/<int:kategorie_pk>/", views.edit_kategorie, name="edit_kategorie"),
                path("del/<int:kategorie_pk>/", views.del_kategorie, name="del_kategorie"),
            ],
        ),
    ),
]
