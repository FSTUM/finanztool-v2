from django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = 'rechnung'

urlpatterns = [

    # Index####################################################################

    # ex: /rechnung/
    url(r'^$', views.willkommen, name='willkommen'),

    # ex: /rechnung/index
    url(r'^index/$', views.index, name='index'),

    # ex: /rechnung/alle
    url(r'^alle/$', views.alle, name='alle'),

    # ex: /rechnung/admin/
    url(r'^admin/$', views.admin, name='admin'),

    # ex: /rechnung/login/
    url(r'^login/$',
        LoginView.as_view(),
        name='login'),

    # ex: /rechnung/logout/
    url(r'^logout/$',
        LogoutView.as_view(),
        {'next_page': '/rechnung/'},
        name='logout'),

    # Rechnung###########################################################

    # ex: /rechnung/5/
    url(r'^(?P<rechnung_id>[0-9]+)/$', views.rechnung, name='rechnung'),

    # ex: /rechnung/neu
    url(r'^neu/$', views.form_rechnung, name='rechnung_neu'),

    # ex: /rechnung/5/aendern
    url(r'^(?P<rechnung_id>[0-9]+)/aendern/$', views.form_rechnung,
        name='rechnung_aendern'),

    # ex: /rechnung/5/duplizieren
    url(r'^(?P<rechnung_id>[0-9]+)/duplizieren/$', views.duplicate_rechnung,
        name='rechnung_duplizieren'),

    # ex: /rechnung/5/posten/neu
    url(r'^(?P<rechnung_id>[0-9]+)/posten/neu/$', views.form_rechnung_posten,
        name='rechnung_posten_neu'),

    # ex: /rechnung/5/pdf
    url(r'^(?P<rechnung_id>[0-9]+)/pdf/$', views.rechnungpdf,
        name='rechnungpdf'),

    # ex: /rechnung/suchen
    url(r'^suchen/$', views.rechnungsuchen, name='rechnungsuchen'),

    # Mahnung#############################################################

    # ex: /rechnung/5/mahnung/2/
    url(r'^(?P<rechnung_id>[0-9]+)/mahnung/(?P<mahnung_id>[0-9]+)/$',
        views.mahnung, name='mahnung'),

    # ex: /rechnung/mahnung/alle/
    url(r'^mahnung/alle/$', views.alle_mahnungen, name='alle_mahnungen'),

    # ex: /rechnung/5/mahnung/neu/
    url(r'^(?P<rechnung_id>[0-9]+)/mahnung/neu/$', views.form_mahnung,
        name='mahnung_neu'),

    # ex: /rechnung/5/mahnung/2/aendern
    url(r'^(?P<rechnung_id>[0-9]+)/mahnung/(?P<mahnung_id>[0-9]+)/aendern/$',
        views.form_mahnung, name='mahnung_aendern'),

    # ex: /rechnung/5/mahnung/2/pdf
    url(r'^(?P<rechnung_id>[0-9]+)/mahnung/(?P<mahnung_id>[0-9]+)/pdf/$',
        views.rechnungpdf, name='mahnungpdf'),

    # Kunde##############################################################

    # ex: /rechnung/kunde/5/
    url(r'^kunde/(?P<kunde_id>[0-9]+)/$', views.kunde, name='kunde'),

    # ex: /rechnung/kunde/neu/
    url(r'^kunde/neu/$', views.form_kunde, name='kunde_neu'),

    # ex: /rechnung/kunde/5/aendern/
    url(r'^kunde/(?P<kunde_id>[0-9]+)/aendern/$', views.form_kunde,
        name='kunde_aendern'),

    # ex: /rechnung/kunde/suchen/
    url(r'^kunde/suchen/$', views.kundesuchen, name='kundesuchen'),

    # ex: /rechnung/kunde/alle/
    url(r'^kunde/alle/$', views.kunden_alle, name='kunden_alle'),

    # Posten#############################################################

    # ex: /rechnung/posten/5/
    url(r'^posten/(?P<posten_id>[0-9]+)/$', views.posten, name='posten'),

    # ex: /rechnung/posten/5/aendern
    url(r'^posten/(?P<posten_id>[0-9]+)/aendern/$', views.form_exist_posten,
        name='posten_aendern'),

    # Kategorie##########################################################

    # ex: /rechnung/kategorie/
    url(r'^kategorie/$', views.kategorie, name='kategorie'),

    # ex: /rechnung/kategorie/5/
    url(r'^kategorie/(?P<kategorie_id>[0-9]+)/$', views.kategorie_detail,
        name='kategorie_detail'),

]
