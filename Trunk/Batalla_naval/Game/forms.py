#!/usr/bin/env python
# encoding: utf-8

from django import forms
from django.forms import ModelForm

from Game.models import *

TITLE_CHOICES=(
    (Submarino, 'Submarino'),
    (BotePatrulla, 'BotePatrulla'),
    (Fragata, 'Fragata'),
    (Acorazado, 'Acorazado'),
    (PortaAviones, 'PortaAviones'),
    )

class UnirseForm(forms.Form):
    """
    Formulario para Unirse a una Partida ya creada
    """
    nickname = forms.CharField(max_length=30)
    #ready =  forms.BooleanField()
    #class Meta:
    #    model = Jugador


class ConfigurarPartidaForm(ModelForm):
    """
    Formluario para crear una Partida
    y configurarla, se configura aquí:
        | nombre de la partida := nombre
        | maxima cantidad de jugadores := max_jugadores
        | numero de portaaviones := num_portaaviones
        | numero de acorazado := num_acorazado
        | numero de fragata := num_fragata
        | numero de submarino := num_submarino
        | numero de patrulla := num_patrulla
    """
    class Meta:
        model = Partida

class PosicionarForm(ModelForm):
    class Meta:
        model = Barco

    def __init__(self, *args, **kwargs):
        barco_choices = kwargs.pop('barcos', [])
        super(PosicionarForm, self).__init__(*args, **kwargs)
        self.fields['barco'] = forms.ChoiceField(choices=barco_choices)

    def save(self, commit=False):
        barco = BARCOS[self.cleaned_data['barco']]
        cx = self.cleaned_data['coordenada1']
        cy = self.cleaned_data['coordenada2']
        o = self.cleaned_data['orientacion']
        m = barco.objects.create(coordenada1=cx, coordenada2=cy, orientacion=o)
        return m

class ElegirDefensaForm(forms.Form):
    DEFENSA_CHOICES=(
        ('MovCorto', 'Movimiento Corto'),
        ('MovLargo', 'Movimiento Largo'),
        ('Escudo', 'Escudo'),
        ('Sumergimiento', 'Sumergimiento'),
        )
    """
    Formulario para elegir una defensa
    """
    tipo = forms.ChoiceField(choices = DEFENSA_CHOICES)

class MovCortoForm(ModelForm):
    """
    Formulario para Movimiento Corto
    """
    class Meta:
        model = MovCorto

    def __init__(self, *args, **kwargs):
        iniciador = kwargs.pop('iniciador')
        super(MovCortoForm, self).__init__(*args, **kwargs)
        # choices = Todos los barcos del jugador
        choices = [(b.id, str(b) + ' ' + str(b.id))
                  for b in Barco.objects.filter(jugador=iniciador)]
        self.fields['barco'] = forms.ChoiceField(choices=choices)

class MovLargoForm(ModelForm):
    """
    Formulario para Movimiento Largo
    """
    class Meta:
        model = MovLargo

    def __init__(self, *args, **kwargs):
        iniciador = kwargs.pop('iniciador')
        super(MovLargoForm, self).__init__(*args, **kwargs)
        # choices = Todos los barcos del jugador
        choices = [(b.id, str(b) + ' ' + str(b.id))
                  for b in Barco.objects.filter(jugador=iniciador)]
        self.fields['barco'] = forms.ChoiceField(choices=choices)

class EscudoForm(ModelForm):
    """
    Formulario para Escudo
    """
    class Meta:
        model = Escudo

class SumergimientoForm(ModelForm):
    """
    Formulario para Sumergimiento
    """
    class Meta:
        model = Sumergimiento

    def __init__(self, *args, **kwargs):
        iniciador = kwargs.pop('iniciador')
        super(SumergimientoForm, self).__init__(*args, **kwargs)
        # choices = Todos los barcos submarinos del jugador
        choices = [(b.id, str(b) + ' ' + str(b.id))
                  for b in Submarino.objects.filter(jugador=iniciador)]
        self.fields['Submarino'] = forms.ChoiceField(choices=choices)

# Formularios para ataques
class ElegirForm(forms.Form):
    ATAQUE_CHOICES = (
        ('Normal', 'Ataque normal'),
        ('Potente', 'Ataque potente'),
        ('Radar', 'Ataque radar')
        )
    tipo = forms.ChoiceField(choices = ATAQUE_CHOICES)
    #  coordenada1 / 2 <= tam_tablero, max_value = Partida.tam
    coordenada1 = forms.IntegerField(required = True, min_value = 1)
    coordenada2 = forms.IntegerField(required = True, min_value = 1)

    def __init__(self, *args, **kwargs):
        iniciador = kwargs.pop('iniciador')
        super(ElegirForm, self).__init__(*args, **kwargs)
        # choices = todos los jugadores en partida, excluyendo al atacante
        choices = [(j.nickname, j.nickname)
                  for j in Jugador.objects.filter(partida=iniciador.partida)
                  if j != iniciador]
        self.fields['oponente'] = forms.ChoiceField(choices=choices)
