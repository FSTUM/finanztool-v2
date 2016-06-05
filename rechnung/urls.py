from django.conf.urls import url
from . import views

app_name = 'rechnung'


urlpatterns = [

#Index##############################################################

    # ex: /rechnung/
    url(r'^$', views.index, name='index'),


#Rechnung###########################################################

    # ex: /rechnung/5/
    url(r'^(?P<rechnung_id>[0-9]+)/$', views.rechnung, name='rechnung'),

    #ex: /rechnung/5/pdf
    url(r'^(?P<rechnung_id>[0-9]+)/pdf/$', views.rechnungpdf, name='rechnungpdf'),

#    # ex: /rechnung/add
#    url(r'^$', views.rechnung_add, name='rechnung_add'),


#Kunde##############################################################

    # ex: /kunde/5/
    url(r'^kunde/(?P<kunde_id>[0-9]+)/$', views.kunde, name='kunde'),

    #ex: /kunde/
    url(r'^kunde/$', views.form_kunde, name='form_kunde'),


#Posten#############################################################

    # ex: /posten/5/
    url(r'^(?P<posten_id>[0-9]+)/$', views.posten, name='posten'),
]
