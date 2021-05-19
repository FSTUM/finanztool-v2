from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(template_name="registration/logout.html"), name="logout"),
    path("rechnung/", include("rechnung.urls")),
    path("konto/", include("konto.urls")),
    path("aufgaben/", include("aufgaben.urls")),
    path("schluessel/", include("schluessel.urls")),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="rechnung:index")),
]
