from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path("logout/", LogoutView.as_view(), name="logout"),
    path("common/", include("common.urls")),
    path("rechnung/", include("rechnung.urls")),
    path("konto/", include("konto.urls")),
    path("aufgaben/", include("aufgaben.urls")),
    path("schluessel/", include("schluessel.urls")),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="rechnung:index")),
    path("", include(tf_urls)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
