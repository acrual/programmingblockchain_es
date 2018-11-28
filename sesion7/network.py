import socket
import time

from io import BytesIO
from random import randint
from unittest import TestCase

from bloque import Bloque
from ayudante import (
    doble_sha256,
    codificar_varint,
    int_a_little_endian,
    little_endian_a_int,
    read_varint,
)


TIPO_DATOS_TX = 1
TIPO_DATOS_BLOQUE = 2
TIPO_DATOS_BLOQUE_FILTRADOS = 3
TIPO_DATOS_BLOQUE_COMPACTO = 4

MAGIA_RED = b'\xf9\xbe\xb4\xd9'
MAGIA_RED_TESTNET = b'\x0b\x11\x09\x07'


class NetworkEnvelope:

    def __init__(self, comando, carga, testnet=False):
        self.comando = comando
        self.carga = carga
        if testnet:
            self.magia = MAGIA_RED_TESTNET
        else:
            self.magia = MAGIA_RED

    def __repr__(self):
        return '{}: {}'.format(
            self.comando.decode('ascii'),
            self.carga.hex(),
        )

    @classmethod
    def parsear(cls, s, testnet=False):
        '''Toma un stream y crea un NetworkEnvelope'''
        # commprueba la magia de red
        magia = s.read(4)
        if magia == b'':
            raise RuntimeError('Conexión reseteada!')
        if testnet:
            magia_esperada = MAGIA_RED_TESTNET
        else:
            magia_esperada = MAGIA_RED
        if magia != magia_esperada:
            raise RuntimeError('la magia no es correcta {} vs {}'.format(magia.hex(), magia_esperada.hex()))
        # comando 12 bytes
        # quita los 0's arrastrados
        # la longitud de carga son 4 bytes, little endian
        # checksum son 4 bytes, los primeros cuatro de doble-sha256 de carga
        # carga tiene una longitud de carga_longitud
        # verificar checksum
        raise NotImplementedError

    def serializar(self):
        '''Devuelve la serialización en bytes del mensaje de red completo'''
        # añade la magia de red
        # comando 12 bytes
        # rellénalo con 0's
        # longitud de carga son 4 bytes, little endian
        # checksum son 4 bytes, los primeros 4 de doble-sha256 de carga
        # carga
        raise NotImplementedError

    def stream(self):
        '''Devuelve un stream para parsear la carga'''
        return BytesIO(self.carga)


class PruebaNetworkEnvelope(TestCase):

    def prueba_parsear(self):
        msj = bytes.fromhex('f9beb4d976657261636b000000000000000000005df6e0e2')
        stream = BytesIO(msj)
        envelope = NetworkEnvelope.parsear(stream)
        self.assertEqual(envelope.comando, b'verack')
        self.assertEqual(envelope.carga, b'')
        msj = bytes.fromhex('f9beb4d976657273696f6e0000000000650000005f1a69d2721101000100000000000000bc8f5e5400000000010000000000000000000000000000000000ffffc61b6409208d010000000000000000000000000000000000ffffcb0071c0208d128035cbc97953f80f2f5361746f7368693a302e392e332fcf05050001')
        stream = BytesIO(msj)
        envelope = NetworkEnvelope.parsear(stream)
        self.assertEqual(envelope.comando, b'version')
        self.assertEqual(envelope.carga, msj[24:])

    def prueba_serializar(self):
        msj = bytes.fromhex('f9beb4d976657261636b000000000000000000005df6e0e2')
        stream = BytesIO(msj)
        envelope = NetworkEnvelope.parsear(stream)
        self.assertEqual(envelope.serializar(), msj)
        msj = bytes.fromhex('f9beb4d976657273696f6e0000000000650000005f1a69d2721101000100000000000000bc8f5e5400000000010000000000000000000000000000000000ffffc61b6409208d010000000000000000000000000000000000ffffcb0071c0208d128035cbc97953f80f2f5361746f7368693a302e392e332fcf05050001')
        stream = BytesIO(msj)
        envelope = NetworkEnvelope.parsear(stream)
        self.assertEqual(envelope.serializar(), msj)


class MensajeVersión:
    comando = b'version'

    def __init__(self, versión=70015, servicios=0, timestamp=None,
                 servicios_receptor=0,
                 ip_receptor=b'\x00\x00\x00\x00', puerto_receptor=8333,
                 servicios_emisor=0,
                 ip_emisor=b'\x00\x00\x00\x00', puerto_emisor=8333,
                 nonce=None, agente_usuario=b'/programmingbloquechain:0.1/',
                 último_bloque=0, retransmisión=True):
        self.versión = versión
        self.servicios = servicios
        if timestamp is None:
            self.timestamp = int(time.time())
        else:
            self.timestamp = timestamp
        self.servicios_receptor = servicios_receptor
        self.ip_receptor = ip_receptor
        self.puerto_receptor = puerto_receptor
        self.servicios_emisor = servicios_emisor
        self.ip_emisor = ip_emisor
        self.puerto_emisor = puerto_emisor
        if nonce is None:
            self.nonce = int_a_little_endian(randint(0, 2**64), 8)
        else:
            self.nonce = nonce
        self.agente_usuario = agente_usuario
        self.último_bloque = último_bloque
        self.retransmisión = retransmisión

    def serializar(self):
        '''Serializa este mensaje para enviarlo a la red'''
        # versión es 4 bytes little endian
        # servicios es 8 bytes little endian
        # timestamp es 8 bytes little endian
        # los servicios del receptor son 8 bytes little endian
        # IPV4 es 10 00 bytes y 2 ff bytes luego ip receptor
        # puerto de receptor son 2 bytes
        # servicios emisor son 8 bytes little endian
        # IPV4 son 10 00 bytes y 2 ff bytes luego ip emisor
        # puerto emisor son 2 bytes
        # nonce deberían ser 8 bytes
        # agente usuario es una cadena variable, luego varint primero
        # el último bloque son 4 bytes little endian
        # retransmisión son 00 si es falso, 01 si es true
        raise NotImplementedError


class PruebaMensajeVersión(TestCase):

    def prueba_serializar(self):
        v = MensajeVersión(timestamp=0, nonce=b'\x00' * 8)
        self.assertEqual(v.serializar().hex(), '7f11010000000000000000000000000000000000000000000000000000000000000000000000ffff000000008d20000000000000000000000000000000000000ffff000000008d2000000000000000001b2f70726f6772616d6d696e67626c6f636b636861696e3a302e312f0000000001')


class ObtenerMensajeCabeceras:
    comando = b'getcabeceras'

    def __init__(self, versión=70015, num_hashes=1, bloque_inicial=None, bloque_final=None):
        self.versión = versión
        self.num_hashes = num_hashes
        if bloque_inicial is None:
            raise RuntimeError('se requiere un bloque inicial')
        self.bloque_inicial = bloque_inicial
        if bloque_final is None:
            self.bloque_final = b'\x00' * 32
        else:
            self.bloque_final = bloque_final

    def serializar(self):
        '''Serializa este mensaje para enviarlo a la red'''
        # la versión del protocolo es 4 bytes little-endian
        # el número de hashes es un varint
        # el bloque inicial es en little-endian
        # el bloque final también es en little-endian
        raise NotImplementedError


class PruebaObtenerMensajeCabeceras(TestCase):

    def prueba_serializar(self):
        bloque_hex = '0000000000000000001237f46acddf58578a37e213d2a6edc4884a2fcad05ba3'
        gh = ObtenerMensajeCabeceras(bloque_inicial=bytes.fromhex(bloque_hex))
        self.assertEqual(gh.serializar().hex(), '7f11010001a35bd0ca2f4a88c4eda6d213e2378a5758dfcd6af437120000000000000000000000000000000000000000000000000000000000000000000000000000000000')


class MensajeCabeceras:
    comando = b'cabeceras'

    def __init__(self, bloques):
        self.bloques = bloques

    @classmethod
    def parsear(cls, stream):
        # número de cabeceras es en un varint
        # inicializa el array de bloques
        # haz un bucle a través del número de cabeceras
            # añade un bloque al array de bloques a base de parsear un stream
            # lee el siguiente varint (num_txs)
            # num_txs debería ser 0 o dar un RuntimeError
        # devuelve una instancia de la clase
        raise NotImplementedError


class PruebaMensajeCabeceras(TestCase):

    def prueba_parsear(self):
        hex_msj = '0200000020df3b053dc46f162a9b00c7f0d5124e2676d47bbe7c5d0793a500000000000000ef445fef2ed495c275892206ca533e7411907971013ab83e3b47bd0d692d14d4dc7c835b67d8001ac157e670000000002030eb2540c41025690160a1014c577061596e32e426b712c7ca00000000000000768b89f07044e6130ead292a3f51951adbd2202df447d98789339937fd006bd44880835b67d8001ade09204600'
        stream = BytesIO(bytes.fromhex(hex_msj))
        cabeceras = MensajeCabeceras.parsear(stream)
        self.assertEqual(len(cabeceras.bloques), 2)
        for b in cabeceras.bloques:
            self.assertEqual(b.__class__, Bloque)

class ObtenerMensajeDatos:
    comando = b'getdata'

    def __init__(self):
        self.data = []

    def agregar_datos(self, tipo_datos, identificador):
        self.data.append((tipo_datos, identificador))

    def serializar(self):
        # comienza con el número de cosas como varint
        res = codificar_varint(len(self.data))
        for tipo_datos, identificador in self.data:
            # el tipo de datos es 4 bytes little endian
            res += int_a_little_endian(tipo_datos, 4)
            # el identificador necesita ser en little endian
            res += identificador[::-1]
        return res


class PruebaObtenerMensajeDatos(TestCase):

    def prueba_serializar(self):
        hex_msj = '020300000030eb2540c41025690160a1014c577061596e32e426b712c7ca00000000000000030000001049847939585b0652fba793661c361223446b6fc41089b8be00000000000000'
        obtener_datos = ObtenerMensajeDatos()
        bloque1 = bytes.fromhex('00000000000000cac712b726e4326e596170574c01a16001692510c44025eb30')
        obtener_datos.agregar_datos(TIPO_DATOS_BLOQUE_FILTRADOS, bloque1)
        bloque2 = bytes.fromhex('00000000000000beb88910c46f6b442312361c6693a7fb52065b583979844910')
        obtener_datos.agregar_datos(TIPO_DATOS_BLOQUE_FILTRADOS, bloque2)
        self.assertEqual(obtener_datos.serializar().hex(), hex_msj)


class NodoSimple:

    def __init__(self, host, puerto=None, testnet=False, logging=False):
        if puerto is None:
            if testnet:
                puerto = 18333
            else:
                puerto = 8333
        self.testnet = testnet
        self.logging = logging
        # connect to socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, puerto))
        # create a stream that we can use with the rest of the library
        self.stream = self.socket.makefile('rb', None)

    def handshake(self):
        '''Haz un handshake con el otro nodo. El handshake es enviar un mensaje de versión y obtener un verack de vuelta.'''
        # crea un mensaje de versión
        # envia el comando
        # espera por el mensaje verack
        raise NotImplementedError

    def send(self, comando, carga):
        '''Envia un mensaje al nodo conectado'''
        # crea un network envelope
        envelope = NetworkEnvelope(comando, carga, testnet=self.testnet)
        if self.logging:
            print('enviando: {}'.format(envelope))
        # envia el envelope serializado a través del socket usando sendall
        self.socket.sendall(envelope.serializar())

    def read(self):
        '''Lee un mensaje desde el socket'''
        envelope = NetworkEnvelope.parsear(self.stream, testnet=self.testnet)
        if self.logging:
            print('recibiendo: {}'.format(envelope))
        return envelope

    def esperar_comandos(self, comandos):
        '''Espera a uno de los comandos en la lista'''
        # inicializa el comando que tenemos, que debería ser None
        comando = None
        # haz un bucle hasta que el comando esté entre los comandos que queremos
        while comando not in comandos:
            # obtén el siguiente mensaje de red
            envelope = self.read()
            # establece el comando a ser evaluado
            comando = envelope.comando
            # sabemos como responder a versión y ping, gestiónalo aquí
            if comando == b'version':
                # envía verack
                self.send(b'verack', b'')
            elif comando == b'ping':
                # envía pong
                self.send(b'pong', envelope.carga)
        # devuelve el último envelope que obtuvimos
        return envelope


class PruebaNodoSimple(TestCase):

    def prueba_handshake(self):
        node = NodoSimple('tbtc.programmingbloquechain.com', testnet=True)
        node.handshake()
