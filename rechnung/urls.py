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

    #ex: /rechnung/5/aendern
    url(r'^(?P<rechnung_id>[0-9]+)/aendern/$', views.form_rechnung, name='rechnung_aendern'),

    # ex: /rechnung/suchen
    url(r'^suchen/$', views.rechnungsuchen, name='rechnungsuchen'),

    # ex: /rechnung/add
    url(r'^add/$', views.form_rechnung, name='form_rechnung'),


#Kunde##############################################################

    # ex: /rechnung/kunde/5/
    url(r'^kunde/(?P<kunde_id>[0-9]+)/$', views.kunde, name='kunde'),

    # ex: /rechnung/kunde/suchen/
    url(r'^kunde/suchen/$', views.kundesuchen, name='kundesuchen'),

    #ex: /rechnung/kunde/add/
    url(r'^kunde/add/$', views.form_kunde, name='form_kunde'),


#Posten#############################################################

    # ex: /rechnung/posten/5/
    url(r'^posten/(?P<posten_id>[0-9]+)/$', views.posten, name='posten'),

#Kategorie##########################################################

    #ex: /rechnung/kategorie/
    url(r'^kategorie/$', views.kategorie, name='kategorie'),

    #ex: /rechnung/kategorie/5/
    url(r'^kategorie/(?P<kategorie_detail_id>[0-9]+)/$', views.kategorie_detail, name='kategorie_detail'),

    #ex: /rechnung/kategorie/add/
    url(r'^kategorie/add/$', views.form_kategorie, name='form_kategorie'),

]
