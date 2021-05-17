from django.conf.urls import url

from . import views

app_name = "aufgaben"

urlpatterns = [
    # ex: /aufgaben/unerledigt
    url(r"^$", views.unerledigt, name="unerledigt"),
    # ex: /aufgaben/neu/
    url(r"^neu/$", views.form_aufgabe, name="neu"),
    # ex: /aufgaben/4/aendern/
    url(
        r"^(?P<aufgabe_id>[0-9]+)/aendern/$",
        views.form_aufgabe,
        name="aendern",
    ),
    # ex: /aufgaben/art/neu/
    url(r"^art/neu/$", views.form_aufgabenart, name="neu_aufgabenart"),
    # ex: /aufgaben/art/4/aendern/
    url(
        r"^art/(?P<aufgabenart_id>[0-9]+)/aendern/$",
        views.form_aufgabenart,
        name="aendern_aufgabenart",
    ),
    # ex: /aufgaben/4/
    url(r"^(?P<aufgabe_id>[0-9]+)/$", views.aufgabe, name="aufgabe"),
    # ex: /aufgaben/alle/
    url(r"^alle/$", views.alle, name="alle"),
]
