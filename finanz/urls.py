from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import RedirectView

import common.views

urlpatterns = [
    # Views
    path("common/", include("common.urls")),
    path("rechnung/", include("rechnung.urls")),
    path("konto/", include("konto.urls")),
    path("aufgaben/", include("aufgaben.urls")),
    path("schluessel/", include("schluessel.urls")),
    # Admin
    path("admin/", admin.site.urls),
    # Index
    path("", RedirectView.as_view(pattern_name="common:dashboard")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.USE_KEYCLOAK:
    urlpatterns += [
        # Auth
        path("logout/", RedirectView.as_view(pattern_name="oidc_logout"), name="logout"),
        path("oidc/", include("mozilla_django_oidc.urls")),
        path("login/failed/", common.views.login_failed),
    ]
else:
    urlpatterns += [
        # Auth
        path("login/", LoginView.as_view(template_name="login.html"), name="login"),
        path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
    ]
