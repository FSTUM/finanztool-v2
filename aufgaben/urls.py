from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

app_name = 'aufgaben'


urlpatterns = [

    # ex: /aufgaben/unerledigt
    url(r'^$', views.unerledigt, name='unerledigt'),

    # ex: /aufgaben/4/
    url(r'^(?P<aufgabe_id>[0-9]+)/$', views.aufgabe, name='aufgabe'),

    # ex: /aufgaben/alle/
    url(r'^alle/$', views.alle, name='alle'),
]
