from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "common"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="schluessel:list_keys"), name="index"),
    path(
        "mail/",
        include(
            [
                path("list/all/", views.list_mail, name="list_mail"),
                path("add/", views.add_mail, name="add_mail"),
                path("edit/<int:mail_pk>/", views.edit_mail, name="edit_mail"),
                path("delete/<int:mail_pk>/", views.del_mail, name="del_mail"),
                path("view/<int:mail_pk>/", views.view_mail, name="view_mail"),
            ],
        ),
    ),
    path("settings/", views.edit_settings, name="edit_settings"),
]
