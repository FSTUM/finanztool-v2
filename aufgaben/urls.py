from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "aufgaben"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="rechnung:unerledigt"), name="index"),
    path("unerledigt/", views.unerledigt, name="unerledigt"),
    path("alle/", views.alle, name="alle"),
    path("neu/", views.form_aufgabe, name="neu"),
    path("<int:aufgabe_id>/", views.aufgabe, name="aufgabe"),
    path("<int:aufgabe_id>/aendern/", views.form_aufgabe, name="aendern"),
    path(
        "art/",
        include(
            [
                path("neu/", views.form_aufgabenart, name="neu_aufgabenart"),
                path("<int:aufgabenart_id>/aendern/", views.form_aufgabenart, name="aendern_aufgabenart"),
            ],
        ),
    ),
]
