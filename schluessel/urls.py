from django.conf.urls import include
from django.urls import path

from . import views

app_name = "schluessel"

urlpatterns = [
    path("", views.list_keys, name="list_keys"),
    path("log/", views.show_log, name="show_log"),
    path("add/", views.add_key, name="add_key"),
    path("<int:key_pk>/", views.view_key, name="view_key"),
    path("<int:key_pk>/edit/", views.edit_key, name="edit_key"),
    path(
        "changes/",
        include(
            [
                path("list/", views.list_key_changes, name="list_key_changes"),
                path("apply/", views.apply_key_change, name="apply_key_change"),
                path("apply/<int:key_pk>/", views.apply_key_change, name="apply_key_change"),
                path("save/<int:key_pk>/", views.save_key_change, name="save_key_change"),
                path("del/<int:key_pk>/", views.delete_key_change, name="delete_key_change"),
            ],
        ),
    ),
    path("<int:key_pk>/return/", views.return_key, name="return_key"),
    path(
        "<int:key_pk>/give/",
        include(
            [
                path("", views.give_key, name="give_key"),
                path("addperson/", views.give_add_person, name="give_add_person"),
                path("editperson/<int:person_pk>/", views.give_edit_person, name="give_edit_person"),
                path("confirm/<int:person_pk>/", views.give_key_confirm, name="give_key_confirm"),
            ],
        ),
    ),
    path("<int:key_pk>/kaution/", views.get_kaution, name="get_kaution"),
    path("<int:key_pk>/quittung/", views.get_quittung, name="get_quittung"),
    path(
        "person/",
        include(
            [
                path("", views.list_persons, name="list_persons"),
                path("add/", views.add_person, name="add_person"),
                path("<int:person_pk>/", views.view_person, name="view_person"),
                path("<int:person_pk>/edit/", views.edit_person, name="edit_person"),
            ],
        ),
    ),
]
