from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "rechnung"
urlpatterns = [
    # Index
    path("",RedirectView.as_view(pattern_name="rechnung:willkommen"), name="index"),
    path("willkommen/", views.willkommen, name="willkommen"),
    path("admin/", views.admin, name="admin"),
    path("unerledigt/", views.unerledigt, name="unerledigt"),
    path("alle/", views.alle, name="alle"),
    # Rechnung
    path("neu/", views.form_rechnung, name="rechnung_neu"),
    path("suchen/", views.rechnungsuchen, name="rechnungsuchen"),
    path("<int:rechnung_id>/", views.rechnung, name="rechnung"),
    path("<int:rechnung_id>/aendern/", views.form_rechnung, name="rechnung_aendern"),
    path("<int:rechnung_id>/duplizieren/", views.duplicate_rechnung, name="rechnung_duplizieren"),
    path("<int:rechnung_id>/posten/neu/", views.form_rechnung_posten, name="rechnung_posten_neu"),
    path("<int:rechnung_id>/pdf/", views.rechnungpdf, name="rechnungpdf"),
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
                path("suchen/", views.kundesuchen, name="kundesuchen"),
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
    # Kategorie
    path(
        "kategorie/",
        include(
            [
                path("", views.kategorie, name="kategorie"),
                path("<int:kategorie_id>/", views.kategorie_detail, name="kategorie_detail"),
            ],
        ),
    ),
]
