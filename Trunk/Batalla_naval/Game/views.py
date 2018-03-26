#!/usr/bin/env python
# encoding: utf-8

from django.contrib import messages  # para darle feedback al usuario actual
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_protect

from Game.models import *
from Game.forms import *

def home(request):
    """
    Vista HOME, es la vista utilizada para navegar por /Game/

    Le dará al usuario la posibilidad de crear una partida,
    y si el usuario está autenticado, además le mostrará la lista de partidas
    a las que puede unirse.
    """
    partidas = Partida.objects.all()
    return TemplateResponse(request, 'home.html', {'partidas' : partidas})

def register(request):
    """
    Vista de Registro de usuario
    """
    if request.method == "POST":
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/Game/')
    else:
        form = UserCreationForm()

    return TemplateResponse(request, "register.html", {'form': form})

@login_required
def cambiar_password(request):
    """
    Vista de Cambio de contraseña
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Su contraseña fue cambiada.')
            return HttpResponseRedirect(reverse("home"))
    else:
        form = PasswordChangeForm(request.user)
    return TemplateResponse(request, "upload_form.html",
            {'form': form, 'boton': "Cambiar contraseña"})


@login_required
def crear_partida(request):
    """
    Vista de Creacion de la partida, además de crearla, se la configura.
    """
    if request.method == 'POST':
        form = ConfigurarPartidaForm(data=request.POST)
        if form.is_valid():
            form.save()
            partida_id = form.instance.id
            messages.success(request, '¡Felicitaciones! La partida fue creada.')
            new_url = reverse('agregar_p', args=(partida_id,))
            return HttpResponseRedirect(new_url)
    else:
        form = ConfigurarPartidaForm()
    return TemplateResponse(request, "crear_partida.html", {'form': form})


@login_required
def partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    if not partida.usuario_en_partida(request.user):
        new_url = reverse('agregar_p', args=(partida.id,))
    else:
        new_url = reverse('pos_flota', args=(partida.id,))
    return HttpResponseRedirect(new_url)


@login_required
def agregar_jugador(request, partida_id):
    """
    Vista para agregar un jugador se encarga de agregar jugadores a una partida
    determinada por partida_id.

    Escenario exitoso:
    Si el formulario es valido redirecciona a posicionar flota del jugador.
    """
    partida = get_object_or_404(Partida, id=partida_id)
    if request.method == 'POST':
        form = UnirseForm(data=request.POST)
        if form.is_valid():
            if(partida.max_jugadores == partida.num_jugadores):
                messages.error(request, "La partida esta completa")
                return HttpResponseRedirect('/Game/')
            if partida.usuario_en_partida(request.user):
                messages.error(request, "Ya estas unido a esa partida")
                return HttpResponseRedirect('/Game/')
            nick = form.cleaned_data["nickname"]
            if Jugador.objects.filter(partida=partida, nickname=nick).count() > 0:
                messages.error(request, "Ya existe ese nickname en la partida")
                return HttpResponseRedirect('/Game/')
            jugador = Jugador.objects.create(user=request.user,
                                             partida=partida, nickname=nick)
            partida.agregar_jugador(jugador)
            partida.save()
            return HttpResponseRedirect(reverse('pos_flota', args=(partida_id,)))
    else:
        form = UnirseForm()
    return TemplateResponse(request, "start.html", {'form': form})


@login_required
def posicionar_flota(request, partida_id):
    partida = get_object_or_404(Partida, id = partida_id)
    jugador = get_object_or_404(Jugador, partida=partida, user=request.user)
    flota = partida.flota()  # Total de flota a posicionar
    flota_jugador = jugador.flota_posicionada()
    barcos_faltantes = []
    for barco, cantidad in flota.iteritems():
        if flota_jugador[barco] < cantidad:
            barcos_faltantes.append((barco, barco))
    # si se posicionaron todos los barcos redirijo a la vista de espera.
    if len(barcos_faltantes) == 0:
        jugador.listo = True
        jugador.save()
        return HttpResponseRedirect(reverse('esperar', args=(partida_id,)))
    if request.method == 'POST':
        form = PosicionarForm(data=request.POST, barcos=barcos_faltantes)
        if form.is_valid():
            barco = form.save()
            barco.jugador = jugador
            tam_tablero = partida.tam
            if (((barco.orientacion == 'V') and (barco.coordenada1 + barco.default_size > tam_tablero + 1)) or \
                ((barco.orientacion == 'H') and (barco.coordenada2 + barco.default_size > tam_tablero + 1)) or
                barco.coordenada1 is 0 or barco.coordenada2 is 0):
                    msg = "No es posible ubicar allí su barco, intentelo de nuevo"
                    messages.error(request, msg)
            else:
                barco.save()
            return HttpResponseRedirect(reverse('pos_flota', args=(partida_id,)))
    else:
        form = PosicionarForm(barcos=barcos_faltantes)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    return TemplateResponse(request, "pos_flota.html",
            {'form': form, 'tablero': tablero_jugador})


@login_required
def esperar(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    jugador = request.user.jugador_set.get(partida=partida, user=request.user)
    tablero_jugador = jugador.mi_tablero()
    if partida.num_jugadores < partida.max_jugadores:
        msg = "Espera a que todos los jugadores se unan a la partida"
    else:
        jugadores = partida.jugador_set.all()
        ready = True
        for j in jugadores:
            if j.listo is False:
                ready = False
                break
        if ready:
            return HttpResponseRedirect(reverse('jugar', args=(partida_id, )))
        else:
            msg = "Espera a que todos los jugadores posicionen su flota"
    messages.error(request, msg)
    return TemplateResponse(request, "wait.html", {'tablero': tablero_jugador})


def jugar(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    jugador = get_object_or_404(Jugador, partida=partida, user=request.user)
    if jugador.activo == False or jugador.is_out():
        jugador.rendirse()
        jugador.save()
        partida.quitar_jugador(jugador)
        msg = "Usted a perdido la batalla"
        messages.success(request, msg)
        return HttpResponseRedirect(reverse('home'))
    if (len(partida.jugador_set.all()) == 1):
        msg = "¡Ganaste la partida!"
        messages.success(request, msg)
        partida.delete()
        return HttpResponseRedirect(reverse('home'))
    jugadores_partida = partida.jugador_set.filter(activo = False)
    if partida.turno_actual == jugador.mi_turno :
        msg = "¡Juega!"
        messages.success(request, msg)
        return HttpResponseRedirect(reverse('elegir_accion', args=(partida_id,)))
    else:
        msg = "Por favor espere a su turno"
        messages.error(request, msg)
        tablero_jugador = jugador.mi_tablero()
        #print "Turno " + str(partida.turno_actual)
        return TemplateResponse(request, "wait.html",
                {'tablero': tablero_jugador})


@login_required
def elegir_accion(request, partida_id):
    """
    Vista para elegir accion (atacar y defender)
    """
    partida = Partida.objects.get(id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    context = {'view': "ataque/", 'name': "¡Atacar!", 'tablero': tablero_jugador}
    return TemplateResponse(request, "elegir_accion.html", context)


@login_required
def elegir_defensa(request, partida_id):
    """
    Si el usuario eligió realizar una defensa, se la llamará a ésta vista.
    Puede elegir entre los 4 tipos de defensa:
        MovCorto | MovLargo | Escudo | Sumergimiento
    """

    partida = Partida.objects.get(id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    if request.method == 'GET':
        formulario = ElegirDefensaForm()
        contexto = {'form': formulario, 'tablero': tablero_jugador, 'boton': "Enviar"}
        return TemplateResponse(request, "upload_form.html", contexto)
    else:
        form = ElegirDefensaForm(data=request.POST)
        if form.is_valid():
            tipo_defensa = form.cleaned_data['tipo']
            if tipo_defensa == "MovCorto":
                new_url = reverse('d_movcorto', args=(partida_id,))
            elif tipo_defensa == "MovLargo":
                new_url = reverse('d_movlargo', args=(partida_id,))
            elif tipo_defensa == "Escudo":
                new_url = reverse('d_escudo', args=(partida_id,))
            elif tipo_defensa == "Sumergimiento":
                new_url = reverse('d_sumergimiento', args=(partida_id,))
            return HttpResponseRedirect(new_url)


@login_required
def d_movcorto(request, partida_id):
    partida = Partida.objects.get(id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    if request.method == 'GET':
        tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
        formulario = MovCortoForm(iniciador=jugador)
        contexto = {'form': formulario, 'tablero': tablero_jugador, 'boton': "Mover"}
        return TemplateResponse(request, "upload_form.html", contexto)
    else:
        form = MovCortoForm(data=request.POST, iniciador=jugador)
        if form.is_valid():
            defensa = form.instance
            barco_id = form.cleaned_data['barco']
            defensa.barco = Barco.objects.get(id=barco_id)
            try:
                jugador.defender(defensa)
            except BarcoTocado:
                msg = "No puedes mover tu barco, ¡está dañado!"
                messages.error(request, msg)
            partida.siguiente_turno()
            new_url = reverse('esperar', args=(partida_id,))
            return HttpResponseRedirect(new_url)


@login_required
def d_movlargo(request, partida_id):
    partida = Partida.objects.get(id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    if request.method == 'GET':
        formulario = MovLargoForm(iniciador=jugador)
        contexto = {'form': formulario, 'tablero': tablero_jugador, 'boton': "Mover"}
        return TemplateResponse(request, "upload_form.html", contexto)
    else:
        form = MovLargoForm(data=request.POST, iniciador=jugador)
        if form.is_valid():
            defensa = form.instance
            barco_id = form.cleaned_data['barco']
            defensa.barco = Barco.objects.get(id=barco_id)
            try:
                jugador.defender(defensa)
            except AttributeError:
                msg = "No puedes realizar Movimiento Largo para %s. ¡Intentalo de nuevo!" % str(defensa.barco)
                messages.error(request, msg)
                return HttpResponseRedirect(reverse('elegir_defensa', args=(partida_id,)))
            except BarcoTocado:
                msg = "No puedes mover tu barco, ¡está dañado!. ¡Intentalo de nuevo!"
                messages.error(request, msg)
            partida.siguiente_turno()
            new_url = reverse('esperar', args=(partida_id,))
            return HttpResponseRedirect(new_url)


@login_required
def d_escudo(request, partida_id):
    partida = Partida.objects.get(id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    if request.method == 'GET':
        formulario = EscudoForm()
        contexto = {'form': formulario, 'tablero': tablero_jugador, 'boton': "Proteger"}
        return TemplateResponse(request, "upload_form.html", contexto)
    else:
        form = EscudoForm(data=request.POST)
        if form.is_valid():
            defensa = form.instance
            defensa.jugador = jugador
            jugador.defender(defensa)
            partida.siguiente_turno()
            new_url = reverse('esperar', args=(partida_id,))
            return HttpResponseRedirect(new_url)


@login_required
def d_sumergimiento(request, partida_id):
    partida = Partida.objects.get(id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    if request.method == 'GET':
        formulario = SumergimientoForm(iniciador=jugador)
        contexto = {'form': formulario, 'tablero': tablero_jugador, 'boton': "Sumergir"}
        return TemplateResponse(request, "upload_form.html", contexto)
    else:
        form = SumergimientoForm(data=request.POST, iniciador=jugador)
        if form.is_valid():
            defensa = form.instance
            barco_id = form.cleaned_data['Submarino']
            defensa.submarino = Submarino.objects.get(id=barco_id)
            try:
                jugador.defender(defensa)
            except BarcoTocado:
                msg = "No puedes sumergir el submarino, ¡Está dañado!"
                messages.error(request, msg)
            except AccionNoValida as e:
                messages.error(request, e.msg)
            partida.siguiente_turno()
            new_url = reverse('esperar', args=(partida_id,))
            return HttpResponseRedirect(new_url)


# ATAQUES
@login_required
def elegir_ataque(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    jugador = Jugador.objects.get(partida=partida, user=request.user)
    tablero_jugador = partida.estado_partida(jugador, jugador, False, 0)
    context = {}
    if request.method == 'POST':
        form = ElegirForm(request.POST, iniciador=jugador)
        if form.is_valid():
            tipo_ataque = form.cleaned_data['tipo']
            c1 = form.cleaned_data['coordenada1']
            c2 = form.cleaned_data['coordenada2']
            opt = form.cleaned_data['oponente']
            oponente = partida.jugador_set.filter(nickname=opt)[0]
            if tipo_ataque == "Normal":
                ataque_normal = Normal.objects.create(coord_1=c1-1, coord_2=c2-1,
                    turno=jugador.mi_turno, tipo='N', jugador=jugador)
                ataque_normal.save()
                jugador.atacar(ataque_normal, oponente)
                tablero_op = partida.estado_partida(jugador, oponente, False, 0)
            elif tipo_ataque == "Potente":
                ataque_potente = Potente.objects.create(coord_1=c1-1, coord_2=c2-1,
                    turno=jugador.mi_turno, tipo='P', jugador=jugador)
                if jugador.validar_ataque(ataque_potente, 0):
                    ataque_potente.save()
                    jugador.atacar(ataque_potente, oponente)
                    tablero_op = partida.estado_partida(jugador, oponente, False, 0)
                else:
                    messages.error(request, "No cuentas con el acorazado")
                    return HttpResponseRedirect(reverse('ataques', args=(partida_id,)))
            elif tipo_ataque == "Radar":
                ataque_radar = Radar.objects.create(coord_1=c1-1, coord_2=c2-1,
                    turno=jugador.mi_turno, tipo='R', jugador=jugador, oponente=oponente)
                if jugador.validar_ataque(ataque_radar, oponente):
                    c1 = ataque_radar.coord_1
                    c2 = ataque_radar.coord_2
                    region = [(c1, c2), (c1, c2 + 1), (c1, c2 + 2), (c1 + 1, c2),
                            (c1 + 1, c2 + 1), (c1 + 1, c2 + 2), (c1 + 2, c2),
                            (c1 + 2, c2 + 1), (c1 + 2, c2 + 2)]
                    tablero_op = partida.estado_partida(jugador, oponente,
                                True, region)
                else:
                    messages.error(request,
                        "Ya aplicaste radar dos veces a este oponente")
                    return HttpResponseRedirect(reverse('ataques', args=(partida_id,)))
            else:
                messages.error(request, "Tipo de ataque invalido")
            # Luego de un ataque, deberiamos comprobar si todos los barcos del
            #oponente fueron hundidos, y setear el activo
            context = {'tablero_op': tablero_op, 'tablero': tablero_jugador,
                        'partida': partida_id, 'nick': jugador.nickname, 'name': "defender!"}
            return TemplateResponse(request, "estado_juego.html", context)
    else:
        form = ElegirForm(iniciador=jugador)
        context = {'form': form, 'boton': "¡Atacar!"}
    return TemplateResponse(request, "upload_form.html", context)

