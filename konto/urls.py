from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

app_name = 'konto'


urlpatterns = [

    # Index########################################################################

    # ex: /konto/
    url(r'^$', views.einlesen, name='einlesen'),
]
