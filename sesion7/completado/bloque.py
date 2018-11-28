from io import BytesIO
from unittest import TestCase

from ayudante import (
    doble_sha256,
    int_a_little_endian,
    little_endian_a_int,
    raíz_merkle,
)


HASH_BLOQUE_GENESIS = bytes.fromhex('000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
HASH_BLOQUE_GENESIS_TESTNET = bytes.fromhex('000000000933ea01ad0ee984209779baaec3ced90fa3f408719526f8d77f4943')


class Bloque:

    def __init__(self, versión, bloque_previo, raíz_merkle, timestamp, bits, nonce, tx_hashes=None):
        self.versión = versión
        self.bloque_previo = bloque_previo
        self.raíz_merkle = raíz_merkle
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce
        self.tx_hashes = tx_hashes
        self.árbol_merkle = None

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea un bloque. Devuelve un objeto Bloque'''
        # s.read(n) leerá n bytes desde el stream
        # versión - 4 bytes, little endian, interpretalo como entero
        versión = little_endian_a_int(s.read(4))
        # bloque_previo - 32 bytes, little endian (usa [::-1] para darle la vuelta)
        bloque_previo = s.read(32)[::-1]
        # raíz_merkle - 32 bytes, little endian (usa [::-1] para darle la vuelta)
        raíz_merkle = s.read(32)[::-1]
        # timestamp - 4 bytes, little endian, interpretalo como entero
        timestamp = little_endian_a_int(s.read(4))
        # bits - 4 bytes
        bits = s.read(4)
        # nonce - 4 bytes
        nonce = s.read(4)
        # inicializa clase
        return cls(versión, bloque_previo, raíz_merkle, timestamp, bits, nonce)

    def serializar(self):
        '''Devuelve la cabecera del bloque de 80 bytes'''
        # versión - 4 bytes, little endian
        res = int_a_little_endian(self.versión, 4)
        # bloque_previo - 32 bytes, little endian
        res += self.bloque_previo[::-1]
        # raíz_merkle - 32 bytes, little endian
        res += self.raíz_merkle[::-1]
        # timestamp - 4 bytes, little endian
        res += int_a_little_endian(self.timestamp, 4)
        # bits - 4 bytes
        res += self.bits
        # nonce - 4 bytes
        res += self.nonce
        return res

    def hash(self):
        '''Devuelve el doble_sha256-sha256 interpretado como little endian del bloque'''
        # serializar
        s = self.serializar()
        # doble_sha256
        sha = doble_sha256(s)
        # reverse
        return sha[::-1]

    def bip9(self):
        '''Devuelve si este bloque señaliza estar listo para BIP9'''
        # BIP9 se señaliza si los top 3 bits son 001
        # recuerda que versión son 32 bytes así que muévete a la derecha 29 (>> 29) y comprueba que
        # eso es 001
        return self.versión >> 29 == 0b001

    def bip91(self):
        '''Devuelve si este bloque señaliza estar preparado para BIP91'''
        # BIP91 está señalizado si el 5º bit desde la derecha es 1
        # mueve 4 bits a la derecha y comprueba si el último es 1
        return self.versión >> 4 & 1 == 1

    def bip141(self):
        '''Devuelve si este bloque señaliza estar listo para BIP141'''
        # BIP141 está señalizado si el 2º bit desde la derecha es 1
        # shift 1 bit to the right and see if the last bit is 1
        return self.versión >> 1 & 1 == 1

    def target(self):
        '''Devuelve el objetivo de la prueba de trabajo basándose en los bits'''
        # el último byte es el exponentee
        exponente = self.bits[-1]
        # los primeros 3 bytes son el coeficiente en little-endian
        coeficiente = little_endian_a_int(self.bits[:-1])
        # la fórmula es:
        # coeficiente * 256**(exponente-3)
        return coeficiente * 256**(exponente - 3)

    def dificultad(self):
        '''Devuelve la dificultad del bloque basándose en los bits'''
        # nota que la dificultad es(objetivo de mínima dificultad) / (objetivo de self)
        # la mínima dificultad tiene bits iguales a 0xffff001d
        mínima = 0xffff * 256**(0x1d - 3)
        return mínima / self.target()

    def comprobar_pow(self):
        '''Devuelve si este bloque satisface la prueba de trabajo'''
        # obtén el doble_sha256 de la serialización de este bloque
        sha = doble_sha256(self.serializar())
        # interpreta este hash como un número little-endian
        prueba = little_endian_a_int(sha)
        # devuelve si este entero es menos que el objetivo
        return prueba < self.target()

    def validar_raíz_merkle(self):
        '''Obtiene la raíz merkle de los tx_hashes y comprueba que es
        la misma que la raíz merkle de este bloque
        '''
        # dale la vuelta a todos los hashes de transacciones (self.tx_hashes)
        hashes = [h[::-1] for h in self.tx_hashes]
        # obtén la raíz Merkle
        raíz = raíz_merkle(hashes)
        # dale la vuelta a la raíz Merkle
        # devuelve si la raíz de self.merkle es la misma que
        # el reverso de la raíz merkle calculada
        return raíz[::-1] == self.raíz_merkle


class PruebaBloque(TestCase):

    def prueba_parsear(self):
        bloque_bruto = bytes.fromhex('020000208ec39428b17323fa0ddec8e887b4a7c53b8c0a0a220cfd0000000000000000005b0750fce0a889502d40508d39576821155e9c9e3f5c3157f961db38fd8b25be1e77a759e93c0118a4ffd71d')
        stream = BytesIO(bloque_bruto)
        bloque = Bloque.parsear(stream)
        self.assertEqual(bloque.versión, 0x20000002)
        want = bytes.fromhex('000000000000000000fd0c220a0a8c3bc5a7b487e8c8de0dfa2373b12894c38e')
        self.assertEqual(bloque.bloque_previo, want)
        want = bytes.fromhex('be258bfd38db61f957315c3f9e9c5e15216857398d50402d5089a8e0fc50075b')
        self.assertEqual(bloque.raíz_merkle, want)
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

    def prueba_validar_raíz_merkle(self):
        hashes_hex = [
            'f54cb69e5dc1bd38ee6901e4ec2007a5030e14bdd60afb4d2f3428c88eea17c1',
            'c57c2d678da0a7ee8cfa058f1cf49bfcb00ae21eda966640e312b464414731c1',
            'b027077c94668a84a5d0e72ac0020bae3838cb7f9ee3fa4e81d1eecf6eda91f3',
            '8131a1b8ec3a815b4800b43dff6c6963c75193c4190ec946b93245a9928a233d',
            'ae7d63ffcb3ae2bc0681eca0df10dda3ca36dedb9dbf49e33c5fbe33262f0910',
            '61a14b1bbdcdda8a22e61036839e8b110913832efd4b086948a6a64fd5b3377d',
            'fc7051c8b536ac87344c5497595d5d2ffdaba471c73fae15fe9228547ea71881',
            '77386a46e26f69b3cd435aa4faac932027f58d0b7252e62fb6c9c2489887f6df',
            '59cbc055ccd26a2c4c4df2770382c7fea135c56d9e75d3f758ac465f74c025b8',
            '7c2bf5687f19785a61be9f46e031ba041c7f93e2b7e9212799d84ba052395195',
            '08598eebd94c18b0d59ac921e9ba99e2b8ab7d9fccde7d44f2bd4d5e2e726d2e',
            'f0bb99ef46b029dd6f714e4b12a7d796258c48fee57324ebdc0bbc4700753ab1',
        ]
        hashes = [bytes.fromhex(x) for x in hashes_hex]
        stream = BytesIO(bytes.fromhex('00000020fcb19f7895db08cadc9573e7915e3919fb76d59868a51d995201000000000000acbcab8bcc1af95d8d563b77d24c3d19b18f1486383d75a5085c4e86c86beed691cfa85916ca061a00000000'))
        bloque = Bloque.parsear(stream)
        bloque.tx_hashes = hashes
        self.assertTrue(bloque.validar_raíz_merkle())
