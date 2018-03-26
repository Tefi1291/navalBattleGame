#!/usr/bin/env python
# encoding: utf-8
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extension del modelo User que viene por defecto en Django
    Consultar en usr/local/lib/python*/dist-packages/django/contrib/
    """
    user = models.OneToOneField(User)
    avatar = models.ImageField(upload_to='tmp/', blank=True)
    webpage = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "Usuarios"

class Partida(models.Model):
    """
    Clase Partida

    @nombre = Indica el nombre de la sala (room)
    @administrador = Nickname del administrador
    @Ronda
    @num_portaaviones = Cantidad de porta aviones perm. por jugador
    @num_acorazado = idem
    @num_fragata = idem
    @num_submarino = idem
    @num_patrulla = idem
    @tamaño_del_tablero = NxN donde N es un entero
    @max_jugadores = Numero máximo de jugadores
    @orden_turno = lista ascendente de asignacion de turnos
                   orden_turno[0] : Jugador0
                   Jugador 0 tiene el primer turno.
                   si max_jugadores = M => orden_turno[M] = JugadorM
                   Jugador M tiene el turno M.
    """

    nombre = models.CharField(max_length = 30)
    ronda = models.PositiveIntegerField(editable = False, default = 0)
    turno_actual = models.PositiveIntegerField(editable = False, default = 0)
    num_portaaviones = models.PositiveIntegerField(default = 1)
    num_acorazado = models.PositiveIntegerField(default = 1)
    num_fragata = models.PositiveIntegerField(default = 1)
    num_submarino = models.PositiveIntegerField(default = 1)
    num_patrulla = models.PositiveIntegerField(default = 1)
    tam = models.PositiveIntegerField(default=9)
    max_jugadores = models.PositiveIntegerField(default = 2)
    num_jugadores = models.PositiveIntegerField(default = 0, editable=False)

    def siguiente_turno(self):
        """
        Actualiza el turno
        actualiza el estado de la ronda en +1 si ya sucedio.
        """
        if self.turno_actual == 0:
            self.ronda += 1
        self.turno_actual = (self.turno_actual + 1) % self.num_jugadores
        self.save()

    def usuario_en_partida(self, usuario):
        """
        ¿El usuario ya está en la partida?
        """
        user_players = Jugador.objects.filter(user=usuario)
        for player in user_players:
            if player.partida.id is self.id:
                return True
        return False

    def agregar_jugador(self, jugador):
        """
        Agrega un nuevo jugador a la partida.
        """
        if self.num_jugadores < self.max_jugadores:
            jugador.mi_turno = self.num_jugadores
            self.num_jugadores += 1
            self.save()
            jugador.save()

    def atacar(self, ataque, jugador, oponente):
        c1 = ataque.coord_1
        c2 = ataque.coord_2
        tablero_oponente = oponente.mi_tablero()
        flota = oponente.barco_set.all()
        if isinstance(ataque, Normal):
            if tablero_oponente[c1][c2] != 'a':
                for b in flota :
                    # funcion privada del tipo barco, devuelve un booleano
                    # indicando si el barco está ubicado sobre la coordenada
                    # (c1, c2)
                    if b._esta_posicionado(c1, c2):
                        barco = b.child
                        break
                # modifico el estado del barco
                esta_protegido = Escudo.objects.filter(jugador=oponente,
                                turno__gte=self.turno_actual-2,
                                coord_1__gte=c1,coord_2__gte=c2,
                                coord_1__lte=c1+3,
                                coord_2__lte=c2+3).count() > 0
                if isinstance(barco, Submarino) and barco.sumergido:
                    pass
                elif esta_protegido:
                    pass
                else:
                    barco.disparar(c1, c2)
                    barco.save()
        elif isinstance(ataque, Potente):
            # PRE: el jugador debe contar con el acorazado->Validar_ataque
            region = [(c1, c2), (c1, c2 + 1), (c1 +1, c2), (c1+ 1, c2 + 1)]
            for celda in region:
                if tablero_oponente[celda[0]][celda[1]] != 'a':
                    for b in flota:
                        if b._esta_posicionado(celda[0], celda[1]):
                            barco = b.child
                            break
                    esta_protegido = Escudo.objects.filter(jugador=oponente,
                                    turno__gte=self.turno_actual-2,
                                    coord_1__gte=c1,coord_2__gte=c2,
                                    coord_1__lte=celda[0]+3,
                                    coord_2__lte=celda[1]+3).count() > 0
                    if isinstance(barco, Submarino) and barco.sumergido:
                        pass
                    elif esta_protegido:
                        pass
                    else:
                        barco.disparar(celda[0], celda[1])
                        barco.save()


    def defender(self, defensa):
        """
        Realiza la defensa correspondiente.
        """
        if isinstance(defensa, MovCorto):
            defensa.barco.child.mover(defensa.direccion)
        elif isinstance(defensa, MovLargo):
            defensa.barco.child.mov_largo(defensa.direccion)
        elif isinstance(defensa, Escudo):
            defensa.turno = self.turno_actual
            defensa.save()
        elif isinstance(defensa, Sumergimiento):
            defensa.submarino.sumergir()

    def flota(self):
        result = {
        "Portaaviones": self.num_portaaviones,
        "Acorazado": self.num_acorazado,
        "Fragata": self.num_fragata,
        "Submarino": self.num_submarino,
        "Patrulla": self.num_patrulla
        }
        return result

    def estado_partida(self, jugador1, jugador2, espionaje, region_espiada):
        """
        Devuelve el estado de la partida VISIBLE del jugador2 para el jugador1
        en formato de tablero. list(list)

        Si ambos argumentos son iguales
            Significa que quiero saber el estado de la partida actual para el
            jugador actual.
        Si ambos argumentos son distintos
            Estamos hablando de dos jugadores distintos, entonces quiero
            devolver el estado actual de la partida del jugador2 que solo el jugador1
            puede ver.
        """
        # XXX: (no hace falta cambiar)
        # Idealmente, este método debería estar en Jugador bajo la API
        # de "tablero_publico"
        assert(isinstance(jugador1, Jugador))
        assert(isinstance(jugador2, Jugador))
        if jugador1.id == jugador2.id:
            tablero_jugador = jugador1.mi_tablero()
        else:
            tablero_jugador = jugador2.mi_tablero()
            flota = jugador2.barco_set.all()
            for i in range(0, self.tam):
                for j in range(0, self.tam):
                    item = tablero_jugador[i][j]
                    if (espionaje):
                        submarino_sumergido = False
                        for b in flota :
                            if b._esta_posicionado(i, j):
                                barco = b.child
                                if isinstance(barco, Submarino) and barco.sumergido:
                                    submarino_sumergido = True
                                    break
                        if (((i,j) not in region_espiada) or submarino_sumergido):
                            tablero_jugador[i][j] = 'a'
                    else:
                        if (item is not 'a' and item is  not 't'):
                            tablero_jugador[i][j] = 'a'
        return tablero_jugador

    def quitar_jugador(self, jugador):
        assert(jugador.activo != True)
        ultimo_jugador = self.jugador_set.filter(mi_turno=(self.num_jugadores - 1))[0]
        nuevo_turno = jugador.mi_turno
        # borrar a jugador de la base
        jugador.delete()
        ultimo_jugador.mi_turno = nuevo_turno
        ultimo_jugador.save()
        self.num_jugadores -= 1
        # no permitimos agregar jugadores durante la partida
        self.max_jugadores -= 1
        self.save()

    def __unicode__(self):
        return self.nombre

class Jugador(models.Model):
    """
    Clase Jugador, tiene una relacion muchos-uno con Usuario, i.e.
    Un usuario tiene N jugadores, y un jugador tiene un usuario.
    """
    user = models.ForeignKey(User)
    partida = models.ForeignKey(Partida)
    mi_turno = models.PositiveIntegerField(default = 0, editable=False)
    nickname = models.CharField(max_length=100)
    activo = models.BooleanField(blank = True, default = True)
    listo = models.BooleanField(blank = True, default = False, editable = False)


    class Meta:
        unique_together = (('partida', 'nickname'),)
        verbose_name_plural = "Jugadores"

    def rendirse(self): #Ver bien
        self.activo = False

    def is_out(self):
        b = True
        flota = self.barco_set.all()
        for b in flota:
            #print str(len(b.deterioro()))
            #print "tamaño " + str(b.child.default_size)
            if len(b.deterioro()) != b.child.default_size:
                b = False
        return b

    def atacar(self, ataque, oponente):
        self.partida.atacar(ataque, self, oponente)

    def defender(self, defensa):
        self.partida.defender(defensa)

    def validar_ataque(self, ataque, oponente):
        if isinstance(ataque, Potente):
            acorazados = self.barco_set.filter(tipo='AC')
            if len(acorazados) is 0:
                return False
        elif isinstance(ataque, Radar):
            lista = Ataque.objects.filter(tipo = 'R')
            cont = 0
            for att in lista:
                rad = att.child
                if ((rad.jugador == self) and (rad.oponente == oponente)):
                    cont += 1
            if (cont > 2):
                return False
        return True

    def validar_defensa(self):
        pass

    def flota_posicionada(self):
        acorazados = Acorazado.objects.filter(jugador=self)
        submarinos = Submarino.objects.filter(jugador=self)
        fragatas = Fragata.objects.filter(jugador=self)
        patrullas = BotePatrulla.objects.filter(jugador=self)
        portaaviones = PortaAviones.objects.filter(jugador=self)
        r = {
        "Acorazado": acorazados.count(),
        "Submarino": submarinos.count(),
        "Fragata": fragatas.count(),
        "Patrulla": patrullas.count(),
        "Portaaviones": portaaviones.count(),
        }
        return r

    def mi_tablero(self):
        """
        Devuelve la representacion de mi tablero codificado en lista de listas.
        """
        tam_tablero = self.partida.tam
        tablero_inicial = []
        for i in range(0, tam_tablero):
            tablero_inicial.append([])
            for j in range(0, tam_tablero):
                tablero_inicial[i].append([])
                tablero_inicial[i][j] = 'a'
        #tablero_inicial tiene agua, ahora resta rellenar las ub. de los barcos
        for barco in self.barco_set.all():
            i, j = barco.ubicacion()
            i -= 1
            j -= 1
            barco_sentido = barco.sentido()
            barco_tam = barco.dimension()
            c, m, t = self.__dibujar_tablero__(barco)
            if barco_sentido == 'H':
                tablero_inicial[i][j] = c
                for pivot in range(1, barco_tam-1):
                    tablero_inicial[i][j+pivot] = m
                tablero_inicial[i][j+barco_tam-1] = t
                if barco.tocado:
                    deterioro = barco.deterioro()
                    for coordenada in deterioro:
                        tablero_inicial[i][coordenada-1] = 't'
            elif barco_sentido == 'V':
                tablero_inicial[i][j] = c
                for pivot in range(1, barco_tam-1):
                    tablero_inicial[i+pivot][j] = m
                tablero_inicial[i+barco_tam-1][j] = t
                if barco.tocado:
                    deterioro = barco.deterioro()
                    for coordenada in deterioro:
                        tablero_inicial[coordenada-1][j] = 't'
        return tablero_inicial

    def __dibujar_tablero__(self, barco):
        if barco.sentido() == 'H':
            if barco.tipo == 'PO':
                cabecera, mitad, trasero = 'ch1', 'mh1', 'th1'
            elif barco.tipo == 'AC':
                cabecera, mitad, trasero = 'ch2', 'mh2', 'th2'
            elif barco.tipo == 'FR':
                cabecera, mitad, trasero = 'ch3', 'mh3', 'th3'
            elif barco.tipo == 'SU':
                cabecera, mitad, trasero = 'ch4', 'mh4', 'th4'
            elif barco.tipo == 'PA':
                cabecera, mitad, trasero = 'ch5', '', 'th5'
        elif barco.sentido() == 'V':
            if barco.tipo == 'PO':
                cabecera, mitad, trasero = 'cv1', 'mv1', 'tv1'
            elif barco.tipo == 'AC':
                cabecera, mitad, trasero = 'cv2', 'mv2', 'tv2'
            elif barco.tipo == 'FR':
                 cabecera, mitad, trasero = 'cv3', 'mv3', 'tv3'
            elif barco.tipo == 'SU':
                cabecera, mitad, trasero = 'cv4', 'mv4', 'tv4'
            elif barco.tipo == 'PA':
                cabecera, mitad, trasero = 'cv5', '', 'tv5'
        return cabecera, mitad, trasero

    def __unicode__(self):
        return self.nickname

CHOICES_DIR = (
        ('LU', 'Izquierda/Arriba'),
        ('RD', 'Derecha/Abajo'),
        )

GENDER_CHOICES = (
    ('H', 'Horizontal'),
    ('V', 'Vertical'),
    )

SHIP_CHOICES = (
    ('SU', 'Submarino'),
    ('PA', 'Patrulla'),
    ('FR', 'Fragata'),
    ('AC', 'Acorazado'),
    ('PO', 'Porta Avion'),
    )

class Barco(models.Model):
    """
    Clase Barco
    @ubicacion = Indica la esquina superior izquierda
        '12-5' indica que en la fila 12 columna 5 se encuentra la primer celda
        correspondiente al barco.
    @orientacion = Indica si es Horizontal o Vertical
    @tam = Indica el tamaño del barco
    por defecto se agrega _id a cada instancia eso lo podemos usar como id unico
    de cada barco, y nombre seria la representacion de cada tipo de barco
    """
    jugador = models.ForeignKey(Jugador, default=0, editable=False)
    tipo = models.CharField(choices = SHIP_CHOICES, max_length = 2, editable= False)
    coordenada1 = models.PositiveIntegerField()
    coordenada2 = models.PositiveIntegerField()
    orientacion = models.CharField(max_length = 1, choices = GENDER_CHOICES)
    tam = models.PositiveIntegerField(editable=False)
    # atributo para saber si un barco se puede mover o no
    celda_0 = models.BooleanField(default = False, editable=False)
    celda_1 = models.BooleanField(default = False, editable=False)
    celda_2 = models.BooleanField(default = False, editable=False)
    celda_3 = models.BooleanField(default = False, editable=False)
    celda_4 = models.BooleanField(default = False, editable=False)

    @property
    def child(self):
        """
        Método que devuelve instancia de sus subclases segun el tipo
        """
        if self.tipo == 'SU':
            result = self.submarino
        elif self.tipo == 'FR':
            result = self.fragata
        elif self.tipo == 'AC':
            result = self.acorazado
        elif self.tipo == 'PA':
            result = self.botepatrulla
        elif self.tipo == 'PO':
            result = self.portaaviones
        else:
            raise DoesNotExist
        return result

    def save(self, *args, **kwargs):
        """
        Redefinimos el metodo save() para setear el tamaño dependiendo del tipo
        de barco que se instancie
        """
        self.tam = self.default_size
        self.tipo = self.tipo_e
        super(Barco, self).save(*args, **kwargs)

    def mover(self, direccion):
        """
        Si la orientacion es vertical -> direccion e {'U', 'D'} Up Down
        Si la orientacion es horizontal -> direccion e {'R', 'L'} Right Left
        """
        if not self.tocado:
            self.coordenada1 = int(self.coordenada1)
            self.coordenada2 = int(self.coordenada2)
            if self.orientacion == 'V':
                if direccion == "LU":
                    self.coordenada1 -= 1
                elif direccion == "RD":
                    self.coordenada1 += 1
            elif self.orientacion == 'H':
                if direccion == "LU":
                    self.coordenada2 -= 1
                elif direccion == "RD":
                    self.coordenada2 += 1
            self.save()
        else:
            raise BarcoTocado

    def disparar (self, coord1, coord2):
           # Refactorizar
        if self.orientacion == 'H':
            i = coord2 - (self.coordenada2 -1)
        else:
            i = coord1 - (self.coordenada1 -1)
        if i == 0 :
            self.celda_0 = True
        elif i == 1:
            self.celda_1 = True
        elif i==2:
            self.celda_2 = True
        elif i==3:
            self.celda_3 = True
        elif i==4:
            self.celda_4 = True


    def _esta_posicionado (self, c1, c2):
        """ Metodo privado de la clase Barco
          retorna True si el barco se encuentra posicionado
         sobre la celda = (c1, c2). c.c devuelve False
        """
        b = False
        if self.orientacion == 'H':
            i = self.coordenada1 -1
            for item in range(self.tam):
                j = self.coordenada2 -1 + item
                if (i, j) == (c1, c2):
                    b = True
                    break
        else:
            j = self.coordenada2 -1
            for item in range(self.tam):
                i = self.coordenada1 -1 + item
                if (i, j) == (c1, c2):
                    b = True
                    break
        return b

    @property
    def tocado(self):
        """
        Devuelve true si el barco está tocado
        """
        return self.celda_0 or self.celda_1 or self.celda_2 or self.celda_3 or self.celda_4

    def ubicacion(self):
        """
        i, j representa la celda del tablero fila i columna j donde empieza
        la ubicacion del barco (cabeza)
        """
        return int(self.coordenada1), int(self.coordenada2)

    def sentido(self):
        """
        Devuelve la horientacion
            "H" = Horizontal
            "V" = vertical
        """
        return str(self.orientacion)

    def dimension(self):
        """
        Devuelve el tamaño del tablero
        """
        return int(self.tam)

    def deterioro(self):
        """
        Devuelve una lista con el numero de celdas danadas
        Si Barco.sentido() == H se lee de derecha a izquierda,
        Si Barco.sentido() == V se lee de arriba a abajo.
        """
        lista_deterioro = []
        if self.tocado:
            i, j = self.ubicacion()
            if self.orientacion == 'H':
                if self.celda_0:
                    lista_deterioro.append(j)
                if self.celda_1:
                    lista_deterioro.append(j+1)
                if self.celda_2:
                    lista_deterioro.append(j+2)
                if self.celda_3:
                    lista_deterioro.append(j+3)
                if self.celda_4:
                    lista_deterioro.append(j+4)
            elif self.orientacion == 'V':
                if self.celda_0:
                    lista_deterioro.append(i)
                if self.celda_1:
                    lista_deterioro.append(i+1)
                if self.celda_2:
                    lista_deterioro.append(i+2)
                if self.celda_3:
                    lista_deterioro.append(i+3)
                if self.celda_4:
                    lista_deterioro.append(i+4)
        return lista_deterioro

    def __unicode__(self):
        return self.child.__unicode__()

class Submarino(Barco):
    """
    Clase Barco.Submarino

    @sumergimiento = cantidad de veces sumergido
    @sumergido = ¿el submarino esta sumergido?
    """
    default_size = 3
    tipo_e = 'SU'
    sumergimientos = models.PositiveIntegerField(editable = False, default = 0)
    sumergido = models.BooleanField(editable = False, default = False)

    def sumergir(self):
        if not self.sumergido:
            if not self.tocado:
                if self.sumergimientos < 3:
                    self.sumergimientos += 1
                    self.sumergido = True
                    self.save()
                else:
                    raise AccionNoValida("Se agotó la cantidad de sumergimientos")
            else:
                raise BarcoTocado
        else:
            raise AccionNoValida("No puedes sumergir un submarino ya sumergido")

    def mov_largo(self, direccion):
        if not self.tocado and not self.sumergido:
            self.coordenada1 = int(self.coordenada1)
            self.coordenada2 = int(self.coordenada2)
            if self.orientacion == 'V':
                if direccion == "LU":
                    self.coordenada1 -= 2
                elif direccion == "RD":
                    self.coordenada1 += 2
            elif self.orientacion == 'H':
                if direccion == "LU":
                    self.coordenada2 -= 2
                elif direccion == "RD":
                    self.coordenada2 += 2
            self.save()
        else:
            raise BarcoTocado

    def __unicode__(self):
        return "Submarino"


class BotePatrulla(Barco):
    """
    Clase Barco.BotePatrulla
    """
    default_size = 2
    tipo_e = 'PA'

    def mov_largo(self, direccion):
        if not self.tocado:
            self.coordenada1 = int(self.coordenada1)
            self.coordenada2 = int(self.coordenada2)
            if self.orientacion == 'V':
                if direccion == "LU":
                    self.coordenada1 -= 2
                elif direccion == "RD":
                    self.coordenada1 *= 2
            elif self.orientacion == 'H':
                if direccion == "LU":
                    self.coordenada2 -= 2
                elif direccion == "RD":
                    self.coordenada2 += 2
            self.save()
        else:
            raise BarcoTocado

    def __unicode__(self):
        return "Patrulla"

class Fragata(Barco):
    """
    Clase Barco.Fragata
    """
    default_size = 3
    tipo_e = 'FR'

    def mov_largo(self, direccion):
        if not self.tocado:
            self.coordenada1 = int(self.coordenada1)
            self.coordenada2 = int(self.coordenada2)
            if self.orientacion == 'V':
                if direccion == "LU":
                    self.coordenada1 -= 2
                elif direccion == "RD":
                    self.coordenada1 += 2
            elif self.orientacion == 'H':
                if direccion == "LU":
                    self.coordenada2 -= 2
                elif direccion == "RD":
                    self.coordenada2 += 2
            self.save()
        else:
            pass

    def __unicode__(self):
        return "Fragata"

class Acorazado(Barco):
    """
    Clase Barco.Acorazado

    @Congelado = Indica si el acorazado está en su enfriamiento
    """
    default_size = 4
    tipo_e = 'AC'
    congelado = models.BooleanField(editable = False, default = False)

    def enfriamiento(self):
        pass

    def __unicode__(self):
        return "Acorazado"

class PortaAviones(Barco):
    """
    Clase Barco.Porta_Aviones
    """
    default_size = 5
    tipo_e = 'PO'

    def __unicode__(self):
        return "Portaaviones"


BARCOS = {
"Portaaviones": PortaAviones,
"Acorazado": Acorazado,
"Fragata": Fragata,
"Submarino": Submarino,
"Patrulla": BotePatrulla,
}

ATTACK_CHOICES = (
    ('N', 'Normal'),
    ('P', 'Potente'),
    ('R', 'Radar'),
    )


class Ataque(models.Model):
    """
    Clase Turno.Ataque : Especifica la celda donde se realizo el ataque, y el
     turno del jugador en el que se realizo
    """
    coord_1 = models.PositiveIntegerField()
    coord_2 = models.PositiveIntegerField()
    turno = models.PositiveIntegerField(editable=False)
    tipo = models.CharField(choices = ATTACK_CHOICES, max_length = 1, editable= False)
    jugador = models.ForeignKey(Jugador, editable=False)



    @property
    def child(self):
        """
        Método que devuelve instancia de sus subclases segun el tipo
        """
        if self.tipo == 'N':
            result = self.normal
        elif self.tipo == 'P':
            result = self.potente
        elif self.tipo == 'R':
            result = self.radar
        else:
            raise DoesNotExist
        return result



class Normal(Ataque):
    """
    Clase Turno.Ataque.Normal, tambien como Ataque y los demas al mismo nivel
    son acciones(tareas) dificil ver una accion como un objeto.
    Esta accion representa el ataque normal, va dirigido a una celda enemiga.
    """

class Potente(Ataque):
    """
    Clase Turno.Ataque.Potente, es una accion de ataque al enemigo y se
    rompe o daña una region de 2x2
    """

class Radar(Ataque):
    oponente = models.ForeignKey(Jugador, editable=False)
    """
    Clase Turno.Ataque.Radar, es una accion de ataque al enemigo y se descubre
    una seccion del tablero del enemigo de 3x3
    """

class Defensa(models.Model):
    """
    Clase Turno.Defensa, realiza un cambio en el tablero del turno.jugador
    """
    turno = models.PositiveIntegerField(editable=False)
    jugador = models.ForeignKey(Jugador,editable=False)

class MovCorto(Defensa):
    """
    Clase Turno.Defensa.MovCorto, es una accion, la de mover un barco una
    celda en una direccion especifica.
    """
    direccion = models.CharField(max_length = 2, choices = CHOICES_DIR)
    barco = models.ForeignKey(Barco, editable=False)

class MovLargo(Defensa):
    """
    Clase Turno.Defensa.MovLargo, es una accion, la de mover un barco dos
    celdas en una direccion especifica.
    """
    direccion = models.CharField(max_length = 2, choices = CHOICES_DIR)
    barco = models.ForeignKey(Barco, editable=False)

class Escudo(Defensa):
    """
    Clase Turno.Defensa.Escudo, activa el escudo por una ronda en una zona
    del tablero de 3x3.
    """
    coord_1 = models.PositiveIntegerField()
    coord_2 = models.PositiveIntegerField()

class Sumergimiento(Defensa):
    """
    Clase Turno.Defensa.Sumergimiento, sumerge el submarino subm.
    """
    submarino = models.ForeignKey(Submarino, editable=False)


class BarcoTocado(Exception):
    def __init__(self):
        pass

class AccionNoValida(Exception):
    def __init__(self, msg):
        self.msg = msg

class LayoutIncorrecto(Exception):
    def __init__(self):
        pass

