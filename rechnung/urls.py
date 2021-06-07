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
                            path("all/", views.list_rechnungen, name="list_rechnungen"),
                            path(
                                "kategorie/<int:kategorie_pk_filter>/",
                                views.list_rechnungen,
                                name="list_rechnungen_filter",
                            ),
                            path(
                                "unerledigt/",
                                views.list_rechnungen_aufgaben_unerledigt,
                                name="list_rechnungen_aufgaben_unerledigt",
                            ),
                        ],
                    ),
                ),
                path("add/", views.form_rechnung, name="add_rechnung"),
                path("view/<int:rechnung_id>/", views.view_rechnung, name="rechnung"),
                path("edit/<int:rechnung_id>/", views.form_rechnung, name="edit_rechnung"),
                path("duplizieren/<int:rechnung_id>/", views.duplicate_rechnung, name="rechnung_duplizieren"),
            ],
        ),
    ),
    path(
        "mahnung/",
        include(
            [
                path("list/", views.list_mahnungen, name="list_mahnungen"),
                path("add/<int:rechnung_id>/", views.form_mahnung, name="add_mahnung"),
                path("view/<int:rechnung_id>/<int:mahnung_id>/", views.view_mahnung, name="view_mahnung"),
                path("edit/<int:rechnung_id>/<int:mahnung_id>/", views.form_mahnung, name="mahnung_aendern"),
            ],
        ),
    ),
    path(
        "export/",
        include(
            [
                path("<int:rechnung_id>/", views.rechnungpdf, name="rechnungpdf"),
                path("<int:rechnung_id>/<int:mahnung_id>/", views.rechnungpdf, name="mahnungpdf"),
            ],
        ),
    ),
    path(
        "kunde/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="rechnung:list_kunden"), name="kunden_index"),
                path("list/", views.list_kunden, name="list_kunden"),
                path("add/", views.form_kunde, name="add_kunde"),
                path("view/<int:kunde_id>/", views.view_kunde, name="view_kunde"),
                path("edit/<int:kunde_id>/", views.form_kunde, name="kunde_aendern"),
            ],
        ),
    ),
    # Posten
    path(
        "posten/",
        include(
            [
                path("add/<int:rechnung_id>/", views.form_rechnung_posten, name="add_posten"),
                path("view/<int:posten_id>/", views.view_posten, name="view_posten"),
                path("edit/<int:posten_id>/", views.form_exist_posten, name="posten_aendern"),
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
