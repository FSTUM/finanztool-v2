from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "aufgaben"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="aufgaben:list_aufgaben"), name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "aufgabe/",
        include(
            [
                path(
                    "list/",
                    include(
                        [
                            path("unerledigt/", views.list_aufgaben_unerledigt, name="list_aufgaben_unerledigt"),
                            path("alle/", views.list_aufgaben, name="list_aufgaben"),
                        ],
                    ),
                ),
                path("add/", views.form_aufgabe, name="add_aufgabe"),
                path("view/<int:aufgabe_id>/", views.view_aufgabe, name="view_aufgabe"),
                path("edit/<int:aufgabe_id>/", views.form_aufgabe, name="edit_aufgabe"),
            ],
        ),
    ),
    path(
        "art/",
        include(
            [
                path("add/", views.form_aufgabenart, name="add_aufgabenart"),
                path("edit/<int:aufgabenart_id>/", views.form_aufgabenart, name="edit_aufgabenart"),
            ],
        ),
    ),
]
