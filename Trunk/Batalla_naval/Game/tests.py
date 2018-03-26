#!/usr/bin/env python
# encoding: utf-8

from django.db import IntegrityError
from django.test import TestCase
from django.test.client import Client
from Game.models import *

# Views Tests - Test de las VISTAS #

"""Correcciones al 2012-11-27:

* Con el solo hecho de llamar a assertRedirects, ya se está testeando que el
status code sea 302. Ver la doc en:
https://docs.djangoproject.com/en/1.4/topics/testing/#django.test.TestCase.assertRedirects

* Todas las urls que Uds usan como literales (por ejemplo '/Game/algo',
 '/Game/ + str(algo) + /otracosa'), sería mejor obtenerlas con reverse. No hace
 falta cambiarlo, pero me interesa que puedan "ver" esto para futuro código.

* Muy buenos los tests para los casos excepcionales!

* Los tests que no tienen comentarios míos están muy bien!

* Faltaría algún testcase sobre la finalización de una partida, pero realmente
 lo que tienen está muy bien. Felicitaciones!

"""


class RegisterTestCase (TestCase):
    """
    Tests: Vista de registro de usuario.
           CASO DE USO 0 - Modulo USUARIOS de SRS.
    """

    def test_createuser(self):
        """
        -Caso exitoso-

        Descripción:
        El cliente intenta crear un usuario, verifica que realmente lo haga
        """
        self.assertEqual(User.objects.count(), 0)

        kwargs = {'username': 'Alguien',
                  'password1': 'pass', 'password2': 'pass'}
        response = self.client.post('/Game/register/', kwargs)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/Game/')

        amount = User.objects.count()
        self.assertEqual(amount, 1)

        user = User.objects.get()
        self.assertEqual(user.username, 'Alguien')
        can_login = self.client.login(username=user.username, password='pass')
        self.assertTrue(can_login)

    def test_create_twousers(self):
        """
        -Caso excepcional-

        Descripción:
        Verifica que al crear 2 usuarios con el mismo nickname
        muestre los mensajes correctos.
        """
        kwargs = {'username': 'Somebody',
                    'password1': 'psw', 'password2': 'psw'}
        response = self.client.post('/Game/register/', kwargs)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.client, self.client)
        kwargs2 = {'username': 'Somebody',
                    'password1': 'psw2', 'password2': 'psw2'}
        response2 = self.client.post('/Game/register/', kwargs2)
        self.assertEqual(response2.status_code, 200)
        self.assertTemplateUsed(response2, 'register.html')
        error = 'Ya existe un usuario con este nombre.'
        self.assertFormError(response2, 'form', 'username', error)
        amount = User.objects.count()
        self.assertEqual(amount, 1)

    def test_not_fill_fields(self):
        """
        -Caso expcepcional-

        Descripcion:
        Verifica cuando se manda el formulario vacio
        """
        kwargs = {'username': '', 'password1': '', 'password2': ''}
        response = self.client.post('/Game/register/', kwargs)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        error = 'Este campo es obligatorio.'
        self.assertFormError(response, 'form', 'username', error)
        self.assertFormError(response, 'form', 'password1', error)
        self.assertFormError(response, 'form', 'password2', error)

    def test_not_eq_pass(self):
        """
        -Caso expcepcional-

        Descripción:
        Verifica cuando se envia el form con 2 passwords distintas
        """
        kwargs = {'username': '', 'password1': 'a', 'password2': 'b'}
        response = self.client.post('/Game/register/', kwargs)
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Las dos contraseñas no coinciden.')


class LoginTestCase (TestCase):
    """
    Tests: Vista de logueo de usuario.
           CASO DE USO 1 - Modulo USUARIOS de SRS.
    """

    def setUp(self):
        super(LoginTestCase, self).setUp()
        self.user = User.objects.create_user(username='NewUser', password='ps')

    def test_loginuser_vers2(self):
        """
        -Escenario exitoso-

        Descripcion:
        Loguear a un usuario registrado - Views
        """
        kwargs = {'username': 'NewUser', 'password': 'ps'}
        response = self.client.post('/Game/login/', kwargs)
        self.assertRedirects(response, '/Game/')
        self.assertEqual(self.user.is_authenticated(), True)

    def test_login_incorrectuser(self):
        """
        -Escenario excepcional-

        Descripcion:
        Chequeo de lo que sucede al intentar loguear un usuario NO registrado.
        """
        kwargs = {'username': 'ImNotAnUser', 'password': 'ps'}
        response = self.client.post('/Game/login/', kwargs)
        self.assertTemplateUsed(response, 'login.html')
        msg = 'Por favor, introduzca un nombre de usuario '
        msg += 'y contraseña correctos.'
        self.assertContains(response, msg, count=1)

    def test_login_incorrectpass(self):
        """
        -Escenario excepcional-

        Descripcion:
        Chequeo de lo que sucede al intentar loguear un usuario con una
        contraseña incorrecta.
        """
        kwargs = {'username': 'NewUser', 'password': 'IncorrectPassword'}
        response = self.client.post('/Game/login/', kwargs)
        self.assertTemplateUsed(response, 'login.html')
        msg = 'Por favor, introduzca un nombre de usuario '
        msg += 'y contraseña correctos.'
        self.assertContains(response, msg, count=1)

    def test_login_notpassword(self):
        """
        -Escenario excepcional-

        Descripcion:
        Chequeo cuando no relleno el campo password
        """
        kwargs2 = {'username': 'NewUser', 'password': ''}
        response = self.client.post('/Game/login/', kwargs2)
        self.assertTemplateUsed(response, 'login.html')
        msg = 'Este campo es obligatorio.'
        self.assertFormError(response, 'form', 'password', msg)


class ChangePassTest (TestCase):
    """
    Test: Vista de cambio de contraseña.
          CASO DE USO 4 - Modulos de USUARIOS de SRS
    """

    def setUp(self):
        super(ChangePassTest, self).setUp()
        self.user = User.objects.create_user(username='u', password='p')

    def test_not_loged(self):
        """
        -Escenario exitoso-

        Descripcion:
        Chequeamos que nos redireccione a home si no estamos logueados
        """
        response = self.client.get('/Game/change_pass/')
        self.assertRedirects(response, '/Game/?next=/Game/change_pass/')

    def test_password_change(self):
        """
        -Escenario exitoso-

        Descripcion:
        Chequeamos que el cambio de contraseñas sea el correcto.
        """
        self.client.login(username='u', password='p')
        kwargs = {'old_password': 'p', 'new_password1': 'p2',
                'new_password2': 'p2'}
        response = self.client.post('/Game/change_pass/', kwargs)
        self.assertRedirects(response, '/Game/')
        self.client.logout()
        #Vemos que se puede loguear con la contraseña cambiada.
        response = self.client.login(username='u', password='p2')
        self.assertEqual(response, True)


class LogoutTest (TestCase):
    """
    Test: CASO DE USO 3 - Modulos de USUARIOS de SRS -
    Logout de un usuario
    """
    def setUp(self):
        super(LogoutTest, self).setUp()
        # Creamos un usuario logeado en el sistema
        self.user = User.objects.create_user(username='NewUser', password='pw')
        self.client.login(username='NewUser', password='pw')

    def test_logout(self):
        """
        -Escenario exitoso-

        Descripcion:
        Chequea el logout correcto de un usuario
        """
        response = self.client.get('/Game/logout/')
        self.assertRedirects(response, '/Game/')
        response = self.client.get('/Game/crear_partida/')
        self.assertRedirects(response, '/Game/?next=/Game/crear_partida/')


class CrearPartidaTest(TestCase):
    """
    Test: Vista de Crear Partida
         CASO DE USO 0 y 1- Modulos de PARTIDA de SRS - Crear Partida
    """

    def setUp(self):
        super(CrearPartidaTest, self).setUp()
        #Creacion de 2 usuarios
        self.user1 = User.objects.create_user(username='U1', password='pw')
        self.user2 = User.objects.create_user(username='U2', password='pw')

    def test_create_partida(self):
        """
        -Escenario exitoso-

        Descripcion:
        Crear una partida con los settings dado y ver que está en la BD
        """
        kwargs = {'nombre': 'Nombre de partida',
                    'num_portaaviones': 1,
                    'num_acorazado': 1,
                    'num_fragata': 1,
                    'num_submarino': 1,
                    'num_patrulla': 1,
                    'tam': 9,
                    'max_jugadores': 2
                    }
        response = self.client.login(username='U1', password='pw')
        response = self.client.post('/Game/crear_partida/', kwargs)
        #Verificamos que se haya creado en la BD
        plist = Partida.objects.filter(nombre='Nombre de partida')
        self.assertEqual(len(plist), 1)
        #Verificamos el redirect
        partida = Partida.objects.get(nombre='Nombre de partida')
        new_url = 'Game/' + str(partida.id) + '/addplayer/'
        self.assertRedirects(response, new_url)

        # testeamos todos los atributos de la partida, es decir,
        self.assertEqual(partida.num_portaaviones, kwargs['num_portaaviones'])
        self.assertEqual(partida.num_acorazado, kwargs['num_acorazado'])
        self.assertEqual(partida.num_fragata, kwargs['num_fragata'])
        self.assertEqual(partida.num_submarino, kwargs['num_submarino'])
        self.assertEqual(partida.num_patrulla, kwargs['num_patrulla'])
        self.assertEqual(partida.tam, kwargs['tam'])
        self.assertEqual(partida.max_jugadores, kwargs['max_jugadores'])

    def test_create_partida_notlogged(self):
        """
        -Escenario excepcional-

        Descripcion:
        Un usuario no logueado intentará crear una partida
        """
        kwargs = {'nombre': 'Nombre de partida',
                    'num_portaaviones': 1,
                    'num_acorazado': 1,
                    'num_fragata': 1,
                    'num_submarino': 1,
                    'num_patrulla': 1,
                    'tam': 9,
                    'max_jugadores': 2
                    }
        url = '/Game/crear_partida/'
        response = self.client.post(url, kwargs)
        #Verificamos que se lo haya redirigido a la vista de logueo
        self.assertRedirects(response, '/Game/?next=' + url)

    # Faltan otros casos excepcionales, pero no hace falta que los agreguen
    # porque el requerimiento era hacer al menos los casos exitosos.


class AgregarJugadorTest(TestCase):
    """
    Test: Vista de Agregar Jugador
         CASO DE USO 2 - Modulos de PARTIDA de SRS - Union de Jugador
    """

    def setUp(self):
        super(AgregarJugadorTest, self).setUp()
        #Creamos una partida
        self.partida = Partida.objects.create(nombre='foo', max_jugadores=2)
        #Creacion de 2 usuarios
        self.user1 = User.objects.create_user(username='U1', password='pw')
        self.user2 = User.objects.create_user(username='U2', password='pw')

    def test_add_player(self):
        """
        -Escenario exitoso-

        Descripcion:
        Chequea que se agreguen correctamente los jugadores
        """
        url = '/Game/' + str(self.partida.id) + '/addplayer/'
        self.client.login(username='U1', password='pw')
        kwargs = {'nickname': 'Mi_nickname'}
        response = self.client.post(url, kwargs)
        new_url = '/Game/' + str(self.partida.id) + '/pos_flota/'
        self.assertRedirects(response, new_url)

        #Chequeamos que se haya creado el jugador
        jugador = Jugador.objects.get()
        self.assertEqual(jugador.user.id, self.user1.id)
        self.assertEqual(jugador.nickname, 'Mi_nickname')

    def test_add_not_login(self):
        """
        -Escenario Excepcional-

        Descripcion:
        Chequea que no se puedan agregar jugadores no logueados
        """
        id_partida = self.partida.id
        url = '/Game/' + str(id_partida) + '/addplayer/'
        response = self.client.get(url)
        self.assertRedirects(response, '/Game/?next=' + url)

    def test_max_players(self):
        """
        -Escenario excepcional-

        Descripcion:
        Chequea que no se puedan agregar mas jugadores de los permitidos
        a nivel de views
        """
        jugador1 = Jugador.objects.create(nickname='Jugador1',
                                        partida=self.partida, user=self.user1)
        jugador2 = Jugador.objects.create(nickname='Jugador2',
                                        partida=self.partida, user=self.user2)
        self.partida.agregar_jugador(jugador1)
        self.partida.agregar_jugador(jugador2)
        assert(self.partida.num_jugadores == 2)
        #Creamos otros usuario y lo intentaremos añadir
        user3 = User.objects.create_user(username='U3', password='password3')
        jugador3 = Jugador.objects.create(user=user3,
                    partida=self.partida, nickname='Nojugador')
        self.client.login(username='U3', password='password3')
        url = '/Game/' + str(self.partida.id) + "/addplayer/"
        kwargs = {'nickname': 'Nojugador'}
        response = self.client.post(url, kwargs)
        # Redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.partida.num_jugadores, 2)

    def test_unique_nickname(self):
        """
        -Escenario excepcional-

        Descripcion:
        Chequea que no se puedan agregar dos jugadores con el mismo nickname
        """
        jugador1 = Jugador.objects.create(nickname='Jugador1',
                                        partida=self.partida, user=self.user1)
        jugador2 = Jugador.objects.create(nickname='Jugador2',
                                        partida=self.partida, user=self.user2)
        self.partida.agregar_jugador(jugador1)
        self.partida.agregar_jugador(jugador2)
        self.client.login(user='U3', password='password3')
        url = '/Game/' + str(self.partida.id) + "/addplayer/"
        kwargs = {'nickname': 'jugador1'}
        response = self.client.post(url, kwargs)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.partida.num_jugadores, 2)

    def test_one_per_username(self):
        """
        Chequea que no se puedan agregar dos jugadores del mismo usuario
        """
        jugador1 = Jugador.objects.create(nickname='Jugador1',
                                        partida=self.partida, user=self.user1)
        self.partida.agregar_jugador(jugador1)
        self.client.login(user='U1', password='password')
        url = '/Game/' + str(self.partida.id) + "/addplayer/"
        kwargs = {'nickname': 'jugador_u1'}
        response = self.client.post(url, kwargs)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.partida.num_jugadores, 1)


class JuegoSimulacion(TestCase):
    """
    Clase base de los ataque test, sus herencias heredaran el setUp
    """
    def setUp(self):
        super(JuegoSimulacion, self).setUp()
        #Creamos una partida
        self.partida = Partida.objects.create(nombre='foo',
                            num_portaaviones=0, num_patrulla=0)

        #Creacion de 2 usuarios
        self.user1 = User.objects.create_user(username='U1', password='pas')
        self.user2 = User.objects.create_user(username='U2', password='pas')
        # Creamos 2 jugador
        self.jugador1 = Jugador.objects.create(user=self.user1,
            partida=self.partida, nickname='jugador1')
        self.jugador2 = Jugador.objects.create(user=self.user2,
            partida=self.partida, nickname='jugador2')
        self.partida.agregar_jugador(self.jugador1)
        self.partida.agregar_jugador(self.jugador2)
        """
        Cada jugador tiene un submarino, un acorazado, y una fragata en las
        mismas posiciones"""
        self.subm1 = Submarino.objects.create(jugador=self.jugador1,
                    coordenada1=1, coordenada2=1, orientacion='H')
        self.fragata1 = Fragata.objects.create(jugador=self.jugador1,
                    coordenada1=3, coordenada2=1, orientacion='H')
        self.acorazado1 = Acorazado.objects.create(jugador=self.jugador1,
                    coordenada1=5, coordenada2=1, orientacion='H')

        self.subm2 = Submarino.objects.create(jugador=self.jugador2,
                    coordenada1=1, coordenada2=1, orientacion='H')
        self.fragata2 = Fragata.objects.create(jugador=self.jugador2,
                    coordenada1=3, coordenada2=1, orientacion='H')
        self.acorazado2 = Acorazado.objects.create(jugador=self.jugador2,
                    coordenada1=5, coordenada2=1, orientacion='H')


class AtaqueNormalTest(JuegoSimulacion):
    """
    Test: CASO DE USO A1 - Modulos de PARTIDA de SRS - Ataque Normal
    """

    def test_ataque_normal(self):
        """
        -Escenario exitoso-

        Descripcion
        jugador1 ataca a jugador2 en una celda donde jugador2 tiene
        parte de su submarino, por lo tanto se chequea que se a tocado
        el submarino del jugador2, y ademas que se dio en una sola celda
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Normal', 'coordenada1': 1, 'coordenada2': 1,
                    'oponente': self.jugador2.nickname}
        self.client.post(url, kwargs)
        submarino = Submarino.objects.get(id=self.subm2.id)
        self.assertEqual(submarino.tocado, True)
        self.assertEqual(submarino.deterioro(), [1])

    def test_ataque_a_sumergido(self):
        """
        Se chequea que si el jugador1 sumerge el submarino y el jugador2
        ataca a donde esta ese submarino, este no recivira danio al estar
        sumergido
        """
        self.subm1.sumergir()
        self.assertEqual(self.subm1.sumergido, True)
        self.client.login(username='U2', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Normal', 'coordenada1': 1, 'coordenada2': 1,
                    'oponente': self.jugador1.nickname}
        self.client.post(url, kwargs)
        submarino = Submarino.objects.get(id=self.subm1.id)
        self.assertEqual(submarino.tocado, False)

    # acá falta al menos otro test de atacar a una celda que esté protegida
    # por escudo
    # Eso está en el test del Escudo =)


class AtaquePotenteTest(JuegoSimulacion):
    """
      Test: CASO DE USO A2 - Modulos de PARTIDA de SRS - Ataque Potente
    """
    def test_checkbase(self):
        """
         Escenario exitoso.
         Chequea que al realizar un ataque potente sobre un barco, se dañen
         las celdas correspondientes, y se re-direccione a la template para elegir
         defensa
        """
        response = self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Potente', 'coordenada1': 1, 'coordenada2': 1,
                'oponente': self.jugador2.nickname}
        response = self.client.post(url, kwargs)
        #Chequeamos que nos redireccione a la template de defensa
        self.assertEqual(response.template[0].name, "estado_juego.html")
        self.assertEqual(response.context[0]['name'], 'defender!')
        # sub1 debe estar dañado en la celda 1, 2
        submarino = Submarino.objects.get(id=self.subm2.id)
        celdas = submarino.deterioro()
        self.assertNotEqual(celdas, [])
        self.assertEqual(celdas, [1, 2])
        self.assertEqual(submarino.tocado, True)
        # No debe estar sumergido
        self.assertNotEqual(submarino.sumergido, True)

    def test_ataque_potente(self):
        """
        -Escenario exitoso-
        Descripcion
        jugador1 ataca a jugador2 en cuatro celdas donde jugador2 tiene
        parte de su acorazado, por lo tanto se chequea que se a tocado
        el acorazado del jugador2, y ademas que se daño dos celdas de el.
        """
        response = self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Potente', 'coordenada1': 5, 'coordenada2': 1,
                    'oponente': 'jugador2'}
        self.client.post(url, kwargs)
        acorazado = Acorazado.objects.get(id=self.acorazado2.id)
        self.assertEqual(acorazado.tocado, True)
        self.assertEqual(acorazado.deterioro(), [1,2])

    def test_ataque_potente_sin_acorazado(self):
        """ 
        -Escenario exitoso-
        (2da Parte y ultima)
        Descripcion
        Se crea una partida nueva con jugadores nuevos, sin acorazado, y se
        intenta usar el ataque potente para chequear que no se puede usar. 
        """
        p_sin_aco = Partida.objects.create(nombre='foo',
                            num_portaaviones=0, num_patrulla=0, num_acorazado=0)
        user3 = User.objects.create_user(username='U3', password='pas')
        user4 = User.objects.create_user(username='U4', password='pas')
        jugador3 = Jugador.objects.create(user=user3,
            partida=p_sin_aco, nickname='jugador3')
        jugador4 = Jugador.objects.create(user=user4,
            partida=p_sin_aco, nickname='jugador4')
        p_sin_aco.agregar_jugador(jugador3)
        p_sin_aco.agregar_jugador(jugador4)

        subm3 = Submarino.objects.create(jugador=jugador3,
                    coordenada1=1, coordenada2=1, orientacion='H')
        fragata3 = Fragata.objects.create(jugador=jugador3,
                    coordenada1=3, coordenada2=1, orientacion='H')

        subm3 = Submarino.objects.create(jugador=jugador4,
                    coordenada1=1, coordenada2=1, orientacion='H')
        fragata3 = Fragata.objects.create(jugador=jugador4,
                    coordenada1=3, coordenada2=1, orientacion='H')

        response = self.client.login(username='U3', password='pas')
        url = '/Game/' + str(p_sin_aco.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Potente', 'coordenada1': 5, 'coordenada2': 1,
                    'oponente': 'jugador4'}
        redirect = self.client.post(url, kwargs, follow = True)
        # Se chequea que uvo una redireccion y ademas el mensaje de que no se
        # pudo realizar el ataque potente por que no se cuenta con el acorazado
        self.assertEqual(redirect.status_code, 200)
        self.assertContains(redirect,
        "No cuentas con el acorazado", 1, 200)

    # No hay tests para confirmar que luego del ataque potente el acorazado
    # entra en "enfriamiento"? Y que si un jugador tiene un acorazado pero
    # está en enfriamiento, no se puede hacer el ataque potente?


class AtaqueRadarTest(JuegoSimulacion):
    """
    Test: CASO DE USO A3 - Modulos de PARTIDA de SRS - Ataque Radar
    """

    def test_ataque_radar(self):
        """
        Caso de uso: A3 (1ra Parte)
        Se chequea que al utilizar el radar el jugador2 contra el jugador1
        entonces en el template de respuesta se ve la zona de 3x3
        correspondiente, del mapa del jugador1
        """
        self.client.login(username='U2', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Radar', 'coordenada1': 1, 'coordenada2': 1,
                    'oponente': 'jugador1'}
        response = self.client.post(url, kwargs)
        self.assertContains(response, "ch3", 2, 200)
        self.assertContains(response, "mh3", 2, 200)
        self.assertContains(response, "th3", 2, 200)
        self.assertContains(response, "ch4", 2, 200)
        self.assertContains(response, "mh4", 2, 200)
        self.assertContains(response, "th4", 2, 200)
        self.assertContains(response, "ch2", 1, 200)

    def test_ataque_radar_restriccion(self):
        """
        Caso de uso: A3 (2ra Parte y Final)
        Se chequea que no se pueda utilizar mas de dos veces el radar
        para un mismo oponente
        """
        self.client.login(username='U2', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Radar', 'coordenada1': 1, 'coordenada2': 1,
            'oponente': 'jugador1'}
        response = self.client.post(url, kwargs)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, kwargs)
        self.assertEqual(response.status_code, 200)
        redirect = self.client.post(url, kwargs, follow=True)
        self.assertEqual(redirect.status_code, 200)
        self.assertContains(redirect,
        "Ya aplicaste radar dos veces a este oponente", 1, 200)


class DefensaMovCortoTest(JuegoSimulacion):
    """
    Test: CASO DE USO D1 - Modulos de PARTIDA de SRS -
    Defensa Mov Corto
    """
    def test_choose_movcorto(self):
        """
        -Escenario exitoso.

        Descripcion:
        Verificar bien la redireccion cuando se elige el mov corto
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/defensa/"
        kwargs = {'tipo': 'MovCorto'}
        response = self.client.post(url, kwargs)
        new_url = '/Game/' + str(self.partida.id) + '/defensa/mov_corto/'
        self.assertRedirects(response, new_url)

    def test_mov_corto(self):
        """
        -Escenario exitoso-

        Descripcion:
        Verificamos que se realice el movimiento corto
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + '/defensa/mov_corto/'
        kwargs = {'direccion': 'RD', 'barco': self.subm1.id}
        response = self.client.post(url, kwargs)
        submarino = Submarino.objects.get(id=self.subm1.id)
        self.assertEqual(submarino.coordenada1, 1)
        self.assertEqual(submarino.coordenada2, 2)


class DefensaMovLargoTest(JuegoSimulacion):
    """
    Test: CASO DE USO D2 - Modulos de PARTIDA de SRS -
    Defensa Mov Largo
    """
    def test_choose_movlargo(self):
        """
        -Escenario exitoso.

        Descripcion:
        Verificar bien la redireccion cuando se elige el mov largo
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/defensa/"
        kwargs = {'tipo': 'MovLargo'}
        response = self.client.post(url, kwargs)
        new_url = '/Game/' + str(self.partida.id) + '/defensa/mov_largo/'
        self.assertRedirects(response, new_url)

    def test_mov_largo(self):
        """
        -Escenario exitoso-

        Descripcion:
        Verificamos que se realice el movimiento largo
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + '/defensa/mov_largo/'
        kwargs = {'direccion': 'RD', 'barco': self.subm1.id}
        response = self.client.post(url, kwargs)
        submarino = Submarino.objects.get(id=self.subm1.id)
        self.assertEqual(submarino.coordenada1, 1)
        self.assertEqual(submarino.coordenada2, 3)


class DefensaEscudoTest(JuegoSimulacion):
    """
    Test: CASO DE USO D3 - Modulos de PARTIDA de SRS - Defensa Escudo
    """
    def test_defensa_escudo(self):
        """ 
        -Escenario exitoso-
        Descripcion
        Primero el jugador2 protege con el escudo la zona donde tiene el
        submarino. Luego el jugador1 ataca al jugador2 en una celda donde
        jugador2 tiene parte de su submarino, por lo tanto se chequea que
        NO! se a tocado el submarino del jugador2 
        """
        c1 = Client()
        c2 = Client()
        response = c1.login(username='U2', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/defensa/"
        kwargs = {'tipo': 'Escudo'}
        redirect = c1.post(url, kwargs, follow = True)
        self.assertEqual(redirect.status_code, 200)
        url = '/Game/' + str(self.partida.id) + "/defensa/escudo/"
        kwargs = {'coord_1': 1, 'coord_2': 1}
        response = c1.post(url, kwargs)
        
        #Una vez protegida la region del submarino del jugador2 atacar!!!
        response2 = c2.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/ataque/"
        kwargs = {'tipo': 'Normal', 'coordenada1': 1, 'coordenada2': 1,
                    'oponente': 'jugador2'}
        response2 = c2.post(url, kwargs)
        submarino = Submarino.objects.get(id=self.subm2.id)
        #Se chequea que el submarino protegido no se a tocado
        self.assertEqual(submarino.tocado, False)

        # acá está medio mezclado test de ataque con escudo en sí.
        # los tests de ataque normal y potente deberían tener su test
        # para cuando se eligen coordenadas con un escudo del otro lado,
        # y acá solo habría que chequear que el escudo fue creado
        # adecuadamente (y no haría falta hacer ataques en este test).
        # En el test case que sigue, hacen esto mismo que yo sugiero ahora.


class DefensaSumergimientoTest(JuegoSimulacion):
    """
    Test: CASO DE USO D4 - Modulos de PARTIDA de SRS -
    Defensa Sumergimiento
    """
    def test_choose_sumergimiento(self):
        """
        -Escenario exitoso.

        Descripcion:
        Verificar bien la redireccion cuando se elige el sumergimiento
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + "/elegir_accion/defensa/"
        kwargs = {'tipo': 'Sumergimiento'}
        response = self.client.post(url, kwargs)
        new_url = '/Game/' + str(self.partida.id) + '/defensa/sumergimiento/'
        self.assertRedirects(response, new_url)

    def test_sumergir(self):
        """
        -Escenario exitoso-

        Descripcion:
        Verificamos que se realice el sumergimiento
        """
        self.client.login(username='U1', password='pas')
        submarino = Submarino.objects.get(id=self.subm1.id)
        self.assertEqual(submarino.sumergido, False)
        url = '/Game/' + str(self.partida.id) + '/defensa/sumergimiento/'
        kwargs = {'Submarino': self.subm1.id}
        response = self.client.post(url, kwargs)
        submarino = Submarino.objects.get(id=self.subm1.id)
        self.assertEqual(submarino.sumergido, True)


class PosicionarFlotaTest(TestCase):
    """
    Test: Vista Posicionar la Flota
    """
    def setUp(self):
        super(PosicionarFlotaTest, self).setUp()
        #Creamos una partida
        self.partida = Partida.objects.create(nombre='foo', num_acorazado=0,
                            num_fragata=0, num_submarino=1,
                            num_patrulla=1, num_portaaviones=0)
        #Creacion de 1 usuario
        self.user = User.objects.create_user(username='U1', password='pas')
        # Creamos 1 jugador
        self.jugador = Jugador.objects.create(user=self.user,
            partida=self.partida, nickname='jugador')
        self.partida.agregar_jugador(self.jugador)

    def test_posflota(self):
        """
        -Escenario exitoso-

        Descripcion: Posicionaremos 2 submarinos y una patrulla
        veremos que se han creado y posicionado realmente los barcos.
        """
        self.client.login(username='U1', password='pas')
        url = '/Game/' + str(self.partida.id) + '/pos_flota/'
        kwargs = {'coordenada1': 1,
                    'coordenada2': 1,
                    'orientacion': 'H',
                    'barco': "Submarino"
                }
        response = self.client.post(url, kwargs)
        #Verificamos que lo haya creado
        sub = Submarino.objects.filter(jugador=self.jugador)[0]
        self.assertEqual(sub.coordenada1, 1)
        self.assertEqual(sub.coordenada2, 1)
        self.assertEqual(sub.orientacion, 'H')
        kwargs = {'coordenada1': 2,
                    'coordenada2': 2,
                    'orientacion': 'H',
                    'barco': "Patrulla"
                }
        response = self.client.post(url, kwargs)
        #Verificamos que lo haya creado
        bp = BotePatrulla.objects.filter(jugador=self.jugador)[0]
        self.assertEqual(bp.coordenada1, 2)
        self.assertEqual(bp.coordenada2, 2)
        self.assertEqual(bp.orientacion, 'H')
        #verificamos que haya redireccionado a la vista de espera
        new_url = 'Game/' + str(self.partida.id) + '/esperar/'
        response = self.client.get(url)
        self.assertRedirects(response, new_url)


# Models test - Testing a nivel Models #


class PartidaModelTest(TestCase):
    """
    Test: Modelo Partida
    """

    def setUp(self):
        super(PartidaModelTest, self).setUp()
        #Creamos una partida
        self.partida = Partida.objects.create(nombre='foo', max_jugadores=2)
        #Creacion de 2 usuarios
        self.user1 = User.objects.create_user(username='U1', password='pw')
        self.user2 = User.objects.create_user(username='U2', password='pw')
        # Creamos dos jugadores
        self.jugador1 = Jugador.objects.create(user=self.user1,
                        partida=self.partida, nickname='jugador1')
        self.jugador2 = Jugador.objects.create(user=self.user2,
                        partida=self.partida, nickname='jugador2')

    def test_add_player(self):
        """
        Testea que agregue jugadores correctamente
        """
        self.partida.agregar_jugador(self.jugador1)
        # debemos tener un solo jugador en la partida
        self.assertEqual(self.partida.num_jugadores, 1)
        self.assertEqual(self.partida.usuario_en_partida(self.jugador1), True)
        # => el jugador tiene el turno 1
        self.assertEqual(self.jugador1.mi_turno, 0)

    def test_full_game(self):
        """
        Agregaremos todos los jugadores posibles, y veremos bien la asignacion
        de turnos
        """
        self.partida.agregar_jugador(self.jugador1)
        self.assertEqual(self.partida.usuario_en_partida(self.jugador1), True)

        self.partida.agregar_jugador(self.jugador2)
        self.assertEqual(self.partida.usuario_en_partida(self.jugador2), True)
        # Tenemos solo 2 jugadores
        self.assertEqual(self.partida.num_jugadores, 2)
        self.assertEqual(self.jugador1.mi_turno, 0)
        self.assertEqual(self.jugador2.mi_turno, 1)

    def test_deleteplayer(self):
        """
        Agregaremos todos los jugadores posibles, y veremos si luego
        de quitarlos los quita bien
        """
        self.partida.agregar_jugador(self.jugador1)
        self.partida.agregar_jugador(self.jugador2)
        # por qué llaman a los dos, rendirse() y quitar_jugador()?
        self.jugador1.rendirse()
        self.partida.quitar_jugador(self.jugador1)
        self.assertEqual(self.partida.num_jugadores, 1)
        # volvemos a obtener al jugador2 de la base de datos
        # y verificamos que su turno cambió
        j2 = Jugador.objects.get(nickname='jugador2')
        self.assertEqual(j2.mi_turno, 0)

    def test_rondacount(self):
        """
        Chequea que se contabilicen bien las rondas
        """
        self.partida.agregar_jugador(self.jugador1)
        self.partida.agregar_jugador(self.jugador2)
        ronda_actual = self.partida.ronda
        self.partida.siguiente_turno()
        self.assertEqual(ronda_actual + 1, self.partida.ronda)

    def test_unique_nick(self):
        """
        -Escenario excepcional-

        Descripcion:
        Chequea que no se puedan agregar dos jugadores con el mismo nickname
        """
        self.partida.agregar_jugador(self.jugador1)
        self.partida.agregar_jugador(self.jugador2)

        user3 = User.objects.create_user(username='U3', password='password3')
        self.assertRaises(IntegrityError, lambda: Jugador.objects.create
                      (user=user3, partida=self.partida, nickname='jugador1'))


class BarcoTestCase(TestCase):

    def setUp(self):
        """
        Crearemos una flota determinada para un jugador y verificaremos
        sus defensas y ataques
        """
        super(BarcoTestCase, self).setUp()

        #Creamos una partida
        self.partida = Partida.objects.create(nombre='foo')
        #Creacion de 1 usuarios
        self.user1 = User.objects.create(username='U1', password='password')
        # Creamos 1 jugador
        self.jugador1 = Jugador.objects.create(user=self.user1,
                        partida=self.partida, nickname='jugador1')
        #Jugador 1 tiene un barco de cada tipo
        self.submarino = Submarino.objects.create(jugador=self.jugador1,
                    coordenada1=1, coordenada2=1, orientacion='H')
        self.fragata = Fragata.objects.create(jugador=self.jugador1,
                    coordenada1=2, coordenada2=2, orientacion='H')
        self.portaavion = PortaAviones.objects.create(jugador=self.jugador1,
                    coordenada1=3, coordenada2=3, orientacion='H')
        self.patrulla = BotePatrulla.objects.create(jugador=self.jugador1,
                    coordenada1=4, coordenada2=4, orientacion='H')
        self.acorazado = Acorazado.objects.create(jugador=self.jugador1,
                    coordenada1=5, coordenada2=5, orientacion='H')

    def test_verifying_init(self):
        barcos = self.jugador1.flota_posicionada()
        #Verificamos que estan posicionados
        for values in barcos.values():
            self.assertEqual(values, 1)
        #Verificamos que no están tocados
        self.assertEqual(self.submarino.tocado, False)
        self.assertEqual(self.fragata.tocado, False)
        self.assertEqual(self.portaavion.tocado, False)
        self.assertEqual(self.patrulla.tocado, False)
        self.assertEqual(self.acorazado.tocado, False)
        #Verificamos que no tiene deterioro
        self.assertEqual(self.submarino.deterioro(), [])
        self.assertEqual(self.fragata.deterioro(), [])
        self.assertEqual(self.portaavion.deterioro(), [])
        self.assertEqual(self.patrulla.deterioro(), [])
        self.assertEqual(self.acorazado.deterioro(), [])

    def test_mov_corto(self):
        self.defensa_movcorto = MovCorto.objects.create(jugador=self.jugador1,
            turno=self.jugador1.mi_turno, direccion='RD', barco=self.submarino)
        #Aplicamos la defensa
        self.jugador1.defender(self.defensa_movcorto)
        #Veamos que efectivamente se haya movido
        submarino = Submarino.objects.get(id=self.submarino.id)
        self.assertEqual(submarino.coordenada1, 1)
        self.assertEqual(submarino.coordenada2, 2)
        #Lo movemos nuevamente a su posicion normal
        self.defensa_movcorto = MovCorto.objects.create(jugador=self.jugador1,
                turno=self.jugador1.mi_turno, direccion='LU', barco=submarino)
        self.jugador1.defender(self.defensa_movcorto)
        #Veamos que efectivamente se haya movido
        submarino = Submarino.objects.get(id=self.submarino.id)
        self.assertEqual(submarino.coordenada1, 1)
        self.assertEqual(submarino.coordenada2, 1)

    def test_mov_largo(self):
        self.defensa_movlargo = MovLargo.objects.create(jugador=self.jugador1,
            turno=self.jugador1.mi_turno, direccion='RD', barco=self.submarino)
        #Aplicamos la defensa
        self.jugador1.defender(self.defensa_movlargo)
        #Veamos que efectivamente se haya movido
        submarino = Submarino.objects.get(id=self.submarino.id)
        self.assertEqual(submarino.coordenada1, 1)
        self.assertEqual(submarino.coordenada2, 3)
        #Lo movemos nuevamente a su posicion normal
        self.defensa_movlargo = MovLargo.objects.create(jugador=self.jugador1,
                turno=self.jugador1.mi_turno, direccion='LU', barco=submarino)
        self.jugador1.defender(self.defensa_movlargo)
        #Veamos que efectivamente se haya movido
        submarino = Submarino.objects.get(id=self.submarino.id)
        self.assertEqual(submarino.coordenada1, 1)
        self.assertEqual(submarino.coordenada2, 1)

