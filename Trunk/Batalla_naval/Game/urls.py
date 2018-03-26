#!/usr/bin/env python
# encoding: utf-8

from django.conf.urls import patterns, include, url

from Game.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url('^$', home, name="home"),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': "login.html"}),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', {'login_url': "/Game/"}),
    url(r'^register/$', register),
    url(r'^change_pass/$', cambiar_password),
    url(r'^(\d+)/$', partida, name="partida"),
    url(r'^(\d+)/addplayer/$', agregar_jugador, name="agregar_p"),
    url(r'^(\d+)/pos_flota/$', posicionar_flota, name="pos_flota"),
    url(r'^crear_partida/$', crear_partida),
    url(r'^(\d+)/elegir_accion/$', elegir_accion, name="elegir_accion"),
    # urls defensas
    url(r'^(\d+)/elegir_accion/defensa/$', elegir_defensa, name="elegir_defensa"),
    url(r'^(\d+)/defensa/mov_corto/$', d_movcorto, name="d_movcorto"),
    url(r'^(\d+)/defensa/mov_largo/$', d_movlargo, name="d_movlargo"),
    url(r'^(\d+)/defensa/escudo/$', d_escudo, name="d_escudo"),
    url(r'^(\d+)/defensa/sumergimiento/$', d_sumergimiento, name="d_sumergimiento"),
    # urls ataques
    url(r'^(\d+)/elegir_accion/ataque/$', elegir_ataque, name="ataques"),
    # urls de juego
    url(r'^(\d+)/esperar/$', esperar, name="esperar"),
    url(r'^(\d+)/jugar/$', jugar, name="jugar"),
)

