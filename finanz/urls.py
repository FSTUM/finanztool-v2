from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    # Auth
    path("", include(tf_urls)),
    path("logout/", LogoutView.as_view(), name="logout"),
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
