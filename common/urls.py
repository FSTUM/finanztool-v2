from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "common"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="common:list_mail"), name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "management/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="common:list_mail"), name="management"),
                path(
                    "mail/",
                    include(
                        [
                            path("list/all/", views.list_mail, name="list_mail"),
                            path("add/", views.add_mail, name="add_mail"),
                            path("edit/<int:mail_pk>/", views.edit_mail, name="edit_mail"),
                            path("del/<int:mail_pk>/", views.del_mail, name="del_mail"),
                            path("view/<int:mail_pk>/", views.view_mail, name="view_mail"),
                        ],
                    ),
                ),
                path("settings/", views.edit_settings, name="edit_settings"),
                path(
                    "qr-codes/",
                    include(
                        [
                            path("list/", views.list_qr_codes, name="list_qr_codes"),
                            path("add/", views.add_qr_code, name="add_qr_code"),
                            path("del/<int:qr_code_pk>/", views.del_qr_code, name="del_qr_code"),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
