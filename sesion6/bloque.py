from io import BytesIO
from unittest import TestCase

from ayudante import (
    doble_sha256,
    int_a_little_endian,
    little_endian_a_int,
)


class Bloque:

    def __init__(self, versión, bloque_previo, raiz_merkle, timestamp, bits, nonce):
        self.versión = versión
        self.bloque_previo = bloque_previo
        self.raiz_merkle = raiz_merkle
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea un bloque. Devuelve un objeto Bloque'''
        # s.read(n) leerá n bytes desde el stream
        # versión - 4 bytes, little endian, interpretalo como int
        # bloque_previo - 32 bytes, little endian (usa [::-1] para darle la vuelta)
        # raiz_merkle - 32 bytes, little endian (usa [::-1] para darle la vuelta)
        # timestamp - 4 bytes, little endian, interpretalo como int
        # bits - 4 bytes
        # nonce - 4 bytes
        # inicializa clase
        raise NotImplementedError

    def serializar(self):
        '''Devuelve la cabecera del bloque de 80 bytes'''
        # versión - 4 bytes, little endian
        # bloque_previo - 32 bytes, little endian
        # raiz_merkle - 32 bytes, little endian
        # timestamp - 4 bytes, little endian
        # bits - 4 bytes
        # nonce - 4 bytes
        raise NotImplementedError

    def hash(self):
        '''Devuelve el doble-sha256 interpretado little endian del block'''
        # serializa
        # doble-sha256
        # dale la vuelta
        raise NotImplementedError

    def bip9(self):
        '''Devuelve si este bloque señala estar listo para BIP9'''
        # BIP9 se señaliza si los top 3 bits son 001
        # recuerda que la versión son 32 bytes así que mueve a la derecha 29 (>> 29) y mira si 
        # eso es 001
        raise NotImplementedError

    def bip91(self):
        '''Devuelve si este bloque señala estar listo para BIP91'''
        # BIP91 está señalizado si el 5º bit desde la derecha es 1
        # mueve 4 bits a la derecha y mira si el último es 1
        raise NotImplementedError

    def bip141(self):
        '''Devuelve si este bloque señaliza estar listo para BIP141'''
        # BIP91 señaliza si el 2º bit desde la derecha es 1
        # mueve 1 bit a la derecha y mira si el último bit es 1
        raise NotImplementedError

    def target(self):
        '''Devuelve el target de la prueba de trabajo basado en los bits'''
        # el último byte es el exponente
        # los primeros 3 bytes son el coeficiente en little endian
        # la fórmula es:
        # coeficiente * 256**(exponente-3)
        raise NotImplementedError

    def dificultad(self):
        '''Devuelve la dificultad del bloque basado en los bits'''
        # nota que la dificultad es (target de la mínima dificultad) / (target de self)
        # la mínima dificultad tiene bits iguales a 0xffff001d
        raise NotImplementedError

    def comprobar_pow(self):
        '''Devuelve si este bloque satisface la prueba de trabajo'''
        # obtén el doble_sha256 de la serialización de este bloque
        # interpreta este hash como un número little-endian
        # devuelve si este entero es menos que el target
        raise NotImplementedError


class PruebaBloque(TestCase):

    def prueba_parsear(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertEqual(bloque.versión, 0x20000002)
        want = bytes.fromhex('000000000000000000fd0c220a0a8c3bc5a7b487e8c8de0dfa2373b12894c38e')
        self.assertEqual(bloque.bloque_previo, want)
        want = bytes.fromhex('be258bfd38db61f957315c3f9e9c5e15216857398d50402d5089a8e0fc50075b')
        self.assertEqual(bloque.raiz_merkle, want)
        self.assertEqual(bloque.timestamp, 0x59a7771e)
        self.assertEqual(bloque.bits, bytes.fromhex('e93c0118'))
        self.assertEqual(bloque.nonce, bytes.fromhex('a4ffd71d'))

    def prueba_serializar(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertEqual(bloque.serializar(), bloque_bruto)

    def prueba_hash(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertEqual(bloque.hash(), bytes.fromhex('0000000000000000007e9e4c586439b0cdbe13b1370bdd9435d76a644d047523'))

    def prueba_bip9(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertTrue(bloque.bip9())
        bloque_bruto = bytes.fromhex('0400000039fa821848781f027a2e6dfabbf6bda920d9ae61b63400030000000000000000ecae536a304042e3154be0e3e9a8220e5568c3433a9ab49ac4cbb74f8df8e8b0cc2acf569fb9061806652c27')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertFalse(bloque.bip9())

    def prueba_bip91(self):
        bloque_bruto = bytes.fromhex('1200002028856ec5bca29cf76980d368b0a163a0bb81fc192951270100000000000000003288f32a2831833c31a25401c52093eb545d28157e200a64b21b3ae8f21c507401877b5935470118144dbfd1')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertTrue(bloque.bip91())
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertFalse(bloque.bip91())

    def prueba_bip141(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertTrue(bloque.bip141())
        bloque_bruto = bytes.fromhex('0000002066f09203c1cf5ef1531f24ed21b1915ae9abeb691f0d2e0100000000000000003de0976428ce56125351bae62c5b8b8c79d8297c702ea05d60feabb4ed188b59c36fa759e93c0118b74b2618')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertFalse(bloque.bip141())

    def prueba_target(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertEqual(bloque.target(), 0x13ce9000000000000000000000000000000000000000000)
        self.assertEqual(int(bloque.dificultad()), 888171856257)

    def prueba_comprobar_pow(self):
        bloque_bruto = bytes.fromhex('04000000fbedbbf0cfdaf278c094f187f2eb987c86a199da22bbb20400000000000000007b7697b29129648fa08b4bcd13c9d5e60abb973a1efac9c8d573c71c807c56c3d6213557faa80518c3737ec1')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertTrue(bloque.comprobar_pow())
        bloque_bruto = bytes.fromhex('04000000fbedbbf0cfdaf278c094f187f2eb987c86a199da22bbb20400000000000000007b7697b29129648fa08b4bcd13c9d5e60abb973a1efac9c8d573c71c807c56c3d6213557faa80518c3737ec0')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertFalse(bloque.comprobar_pow())
