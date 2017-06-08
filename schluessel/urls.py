from django.conf.urls import url

from . import views


app_name = 'schluessel'

urlpatterns = [
    url(r'^$', views.list_keys, name='list_keys'),
    url(r'^log/$', views.show_log, name='show_log'),
    url(r'^add/$', views.add_key, name='add_key'),
    url(r'^(?P<key_pk>[0-9]+)/$', views.view_key, name='view_key'),
    url(r'^(?P<key_pk>[0-9]+)/edit/$', views.edit_key, name='edit_key'),
    url(r'^changes/list/$', views.list_key_changes,
        name='list_key_changes'),
    url(r'^changes/apply/$', views.apply_key_change,
        name='apply_key_change'),
    url(r'^changes/apply/(?P<key_pk>[0-9]+)/$', views.apply_key_change,
        name='apply_key_change'),
    url(r'^changes/save/(?P<key_pk>[0-9]+)/$', views.save_key_change,
        name='save_key_change'),
    url(r'^changes/del/(?P<key_pk>[0-9]+)/$', views.delete_key_change,
        name='delete_key_change'),
    url(r'^(?P<key_pk>[0-9]+)/return/$', views.return_key, name='return_key'),
    url(r'^(?P<key_pk>[0-9]+)/give/$', views.give_key, name='give_key'),
    url(r'^(?P<key_pk>[0-9]+)/give/addperson/$', views.give_add_person,
        name='give_add_person'),
    url(r'^(?P<key_pk>[0-9]+)/give/editperson/(?P<person_pk>[0-9]+)/$',
        views.give_edit_person, name='give_edit_person'),
    url(r'^(?P<key_pk>[0-9]+)/give/confirm/(?P<person_pk>[0-9]+)/$',
        views.give_key_confirm, name='give_key_confirm'),
    url(r'^(?P<key_pk>[0-9]+)/kaution/$', views.get_kaution,
        name='get_kaution'),
    url(r'^(?P<key_pk>[0-9]+)/quittung/$', views.get_quittung,
        name='get_quittung'),
    url(r'^person/$', views.list_persons, name='list_persons'),
    url(r'^person/add/$', views.add_person, name='add_person'),
    url(r'^person/(?P<person_pk>[0-9]+)/$', views.view_person,
        name='view_person'),
    url(r'^person/(?P<person_pk>[0-9]+)/edit/$', views.edit_person,
        name='edit_person'),
]
