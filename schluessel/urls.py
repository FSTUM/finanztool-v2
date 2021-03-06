from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "schluessel"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="schluessel:list_keys"), name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "schluessel/",
        include(
            [
                path("list/", views.list_keys, name="list_keys"),
                path("add/", views.add_key, name="add_key"),
                path("view/<int:key_pk>/", views.view_key, name="view_key"),
                path("edit/<int:key_pk>/", views.edit_key, name="edit_key"),
                path("log/", views.show_log, name="show_log"),
                path(
                    "changes/",
                    include(
                        [
                            path("list/", views.list_key_changes, name="list_key_changes"),
                            path("apply/", views.apply_key_change, name="apply_key_change_no_key"),
                            path("apply/<int:key_pk>/", views.apply_key_change, name="apply_key_change"),
                            path("save/<int:key_pk>/", views.save_key_change, name="save_key_change"),
                            path("del/<int:key_pk>/", views.del_key_change, name="del_key_change"),
                        ],
                    ),
                ),
                path("return/<int:key_pk>", views.return_key, name="return_key"),
                path(
                    "give/",
                    include(
                        [
                            path("<int:key_pk>/", views.give_key, name="give_key"),
                            path("<int:key_pk>/addperson/", views.give_add_person, name="give_add_person"),
                            path(
                                "<int:key_pk>/confirm/<int:person_pk>/",
                                views.give_key_confirm,
                                name="give_key_confirm",
                            ),
                            path(
                                "<int:key_pk>/editperson/<int:person_pk>/",
                                views.give_edit_person,
                                name="give_edit_person",
                            ),
                        ],
                    ),
                ),
                path(
                    "export/",
                    include(
                        [
                            path("<int:key_pk>/kaution/", views.get_kaution, name="get_kaution"),
                            path("<int:key_pk>/quittung/", views.get_quittung, name="get_quittung"),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "person/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="schluessel:list_persons")),
                path("list/", views.list_persons, name="list_persons"),
                path("add/", views.add_person, name="add_person"),
                path("view/<int:person_pk>/", views.view_person, name="view_person"),
                path("edit/<int:person_pk>/", views.edit_person, name="edit_person"),
            ],
        ),
    ),
    path(
        "schluessel_typ/",
        include(
            [
                path("list/", views.list_key_types, name="list_key_types"),
                path("add/", views.add_key_typ, name="add_key_typ"),
                path("edit/<int:schluessel_typ_pk>/", views.edit_key_typ, name="edit_key_typ"),
                path("del/<int:schluessel_typ_pk>/", views.del_key_typ, name="del_key_typ"),
            ],
        ),
    ),
]
