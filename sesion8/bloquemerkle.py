import math

from io import BytesIO
from unittest import TestCase

from ayudante import (
    bytes_a_campo_bit,
    little_endian_a_int,
    padre_merkle,
    read_varint,
)


class ÁrbolMerkle:

    def __init__(self, total):
        self.total = total
        # computa la profundidad máxima math.ceil(math.log(self.total, 2))
        self.profundidad_máxima = math.ceil(math.log(self.total, 2))
        # inizializa el atributo de los nodos para mantener el árbol actual
        self.nodes = []
        # haz un bucle sobre el número de niveles (profundidad_máxima+1)
        for profundidad in range(self.profundidad_máxima + 1):
            # el número de cosas a esta profundidad es
            # math.ceil(self.total / 2**(self.profundidad_máxima - profundidad))
            num_cosas = math.ceil(self.total / 2**(self.profundidad_máxima - profundidad))
            # crea la lista de los hashes de este nivel con el número correcto de cosas
            nivel_hashes = [None] * num_cosas
            # añade los hashes de este nivel al árbol merkles
            self.nodes.append(nivel_hashes)
        # establece el punter a la raíz (profundidad=0, índice=0)
        self.profundidad_actual = 0
        self.índice_actual = 0

    def __repr__(self):
        res = ''
        for profundidad, nivel in enumerate(self.nodes):
            for índice, h in enumerate(nivel):
                corto = '{}...'.format(h.hex()[:8])
                if profundidad == self.profundidad_actual and índice == self.índice_actual:
                    res += '*{}*, '.format(corto[:-2])
                else:
                    res += '{}, '.format(corto)
            res += '\n'
        return res

    def subir(self):
        # reduce profundidad en 1 y divide entre dos el índice
        self.profundidad_actual -= 1
        self.índice_actual //= 2

    def izquierda(self):
        # aumenta la profundidad en 1 y dobla el índice
        self.profundidad_actual += 1
        self.índice_actual *= 2

    def derecha(self):
        # aumenta la profundidad en 1 y dobla el índice + 1
        self.profundidad_actual += 1
        self.índice_actual = self.índice_actual * 2 + 1

    def raíz(self):
        return self.nodes[0][0]

    def establece_nodo_actual(self, valor):
        self.nodes[self.profundidad_actual][self.índice_actual] = valor

    def obtener_nodo_actual(self):
        return self.nodes[self.profundidad_actual][self.índice_actual]

    def obtener_nodo_izquierdo(self):
        return self.nodes[self.profundidad_actual + 1][self.índice_actual * 2]

    def obtener_nodo_derecho(self):
        return self.nodes[self.profundidad_actual + 1][self.índice_actual * 2 + 1]

    def es_hoja(self):
        return self.profundidad_actual == self.profundidad_máxima

    def derecha_existe(self):
        return len(self.nodes[self.profundidad_actual + 1]) > self.índice_actual * 2 + 1

    def poblar_árbol(self, flag_bits, hashes):
        # poblar hasta que tengamos la raíz
        while self.raíz() is None:
            # si tenemos una hoja, sabemos el hash de esta posición
            if self.es_hoja():
                # obtén el siguiente bit desde flag_bits: flag_bits.pop(0)
                flag_bits.pop(0)
                # establece el nodo actual en el árbol Merkle hasta el siguiente hash: hashes.pop(0)
                self.establece_nodo_actual(hashes.pop(0))
                # sube un nivel
                self.subir()
            # else
            else:
                # obtén el hash izquierdo
                hash_izquierdo = self.obtener_nodo_izquierdo()
                # Ejercicio 6.2: obtén el hash derecho
                # si no tenemos el hash izquierdo
                if hash_izquierdo is None:
                    # si el siguiente flag bit es 0, el siguiente hash es nuestro nodo actual
                    if flag_bits.pop(0) == 0:
                        # establece el nodo actual para ser el siguiente hash
                        self.establece_nodo_actual(hashes.pop(0))
                        # sub-árbol no necesita cálculo, sube
                        self.subir()
                    # else
                    else:
                        # ve al nodo izquierdo
                        self.izquierda()
                # Ejercicio 6.2: si no necesitamos tener el hash derecho
                    # ve al nodo derecho
                # Ejercicio 6.2: else
                    # combina los hashes izquierdo y derecho
                    # hemos completado este subárbol, subamos
                # Ejercicio 7.2: si el hash derecho existe
                elif self.derecha_existe():
                    # obtén el hash derecho
                    hash_derecho = self.obtener_nodo_derecho()
                    # si no tenemos el hash derecho
                    if hash_derecho is None:
                        # ve al nodo derecho
                        self.derecha()
                    # else
                    else:
                        # combina los hashes izquierdo y derecho
                        self.establece_nodo_actual(padre_merkle(hash_izquierdo, hash_derecho))
                        # hemos completado este sub-árbol, sube
                        self.subir()
                # else
                else:
                    # combina el hash izquierdo dos veces
                    self.establece_nodo_actual(padre_merkle(hash_izquierdo, hash_izquierdo))
                    # hemos completado este sub-árbol, sube
                    self.subir()
        if len(hashes) != 0:
            raise RuntimeError('los hashes no están consumidos {}'.format(len(hashes)))
        for flag_bit in flag_bits:
            if flag_bit != 0:
                raise RuntimeError('no todos los flag bits han sido consumidos')


class PruebaÁrbolMerkle(TestCase):

    def prueba_init(self):
        árbol = ÁrbolMerkle(9)
        self.assertEqual(len(árbol.nodes[0]), 1)
        self.assertEqual(len(árbol.nodes[1]), 2)
        self.assertEqual(len(árbol.nodes[2]), 3)
        self.assertEqual(len(árbol.nodes[3]), 5)
        self.assertEqual(len(árbol.nodes[4]), 9)

    def prueba_poblar_árbol_1(self):
        hex_hashes = [
            "9745f7173ef14ee4155722d1cbf13304339fd00d900b759c6f9d58579b5765fb",
            "5573c8ede34936c29cdfdfe743f7f5fdfbd4f54ba0705259e62f39917065cb9b",
            "82a02ecbb6623b4274dfcab82b336dc017a27136e08521091e443e62582e8f05",
            "507ccae5ed9b340363a0e6d765af148be9cb1c8766ccc922f83e4ae681658308",
            "a7a4aec28e7162e1e9ef33dfa30f0bc0526e6cf4b11a576f6c5de58593898330",
            "bb6267664bd833fd9fc82582853ab144fece26b7a8a5bf328f8a059445b59add",
            "ea6d7ac1ee77fbacee58fc717b990c4fcccf1b19af43103c090f601677fd8836",
            "457743861de496c429912558a106b810b0507975a49773228aa788df40730d41",
            "7688029288efc9e9a0011c960a6ed9e5466581abf3e3a6c26ee317461add619a",
            "b1ae7f15836cb2286cdd4e2c37bf9bb7da0a2846d06867a429f654b2e7f383c9",
            "9b74f89fa3f93e71ff2c241f32945d877281a6a50a6bf94adac002980aafe5ab",
            "b3a92b5b255019bdaf754875633c2de9fec2ab03e6b8ce669d07cb5b18804638",
            "b5c0b915312b9bdaedd2b86aa2d0f8feffc73a2d37668fd9010179261e25e263",
            "c9d52c5cb1e557b92c84c52e7c4bfbce859408bedffc8a5560fd6e35e10b8800",
            "c555bc5fc3bc096df0a0c9532f07640bfb76bfe4fc1ace214b8b228a1297a4c2",
            "f9dbfafc3af3400954975da24eb325e326960a25b87fffe23eef3e7ed2fb610e",
        ]
        árbol = ÁrbolMerkle(len(hex_hashes))
        hashes = [bytes.fromhex(h) for h in hex_hashes]
        árbol.poblar_árbol([1] * 31, hashes)
        raíz = '597c4bafe3832b17cbbabe56f878f4fc2ad0f6a402cee7fa851a9cb205f87ed1'
        self.assertEqual(árbol.raíz().hex(), raíz)

    def prueba_poblar_árbol_2(self):
        hex_hashes = [
            '42f6f52f17620653dcc909e58bb352e0bd4bd1381e2955d19c00959a22122b2e',
            '94c3af34b9667bf787e1c6a0a009201589755d01d02fe2877cc69b929d2418d4',
            '959428d7c48113cb9149d0566bde3d46e98cf028053c522b8fa8f735241aa953',
            'a9f27b99d5d108dede755710d4a1ffa2c74af70b4ca71726fa57d68454e609a2',
            '62af110031e29de1efcad103b3ad4bec7bdcf6cb9c9f4afdd586981795516577',
        ]
        árbol = ÁrbolMerkle(len(hex_hashes))
        hashes = [bytes.fromhex(h) for h in hex_hashes]
        árbol.poblar_árbol([1] * 11, hashes)
        raíz = 'a8e8bd023169b81bc56854137a135b97ef47a6a7237f4c6e037baed16285a5ab'
        self.assertEqual(árbol.raíz().hex(), raíz)


class BloqueMerkle:

    def __init__(self, versión, bloque_previo, raíz_merkle, timestamp, bits, nonce, total, hashes, flags):
        self.versión = versión
        self.bloque_previo = bloque_previo
        self.raíz_merkle = raíz_merkle
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce
        self.total = total
        self.hashes = hashes
        self.flags = flags

    def __repr__(self):
        res = '{}\n'.format(self.total)
        for h in self.hashes:
            res += '\t{}\n'.format(h.hex())
        res += '{}'.format(self.flags.hex())

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea un bloque merkle. Devuelve un objeto Bloque Merkle'''
        # s.read(n) leerá n bytes desde el stream
        # versión - 4 bytes, little endian, interpretalo como int
        versión = little_endian_a_int(s.read(4))
        # bloque_previo - 32 bytes, little endian (usa [::-1] para darle la vuelta)
        bloque_previo = s.read(32)[::-1]
        # raíz_merkle - 32 bytes, little endian (usa [::-1] para darle la vuelta)
        raíz_merkle = s.read(32)[::-1]
        # timestamp - 4 bytes, little endian, interprétalo como int
        timestamp = little_endian_a_int(s.read(4))
        # bits - 4 bytes
        bits = s.read(4)
        # nonce - 4 bytes
        nonce = s.read(4)
        # el número total de transacciónes (4 bytes, little endian)
        total = little_endian_a_int(s.read(4))
        # el número de hashes es un varint
        num_txs = read_varint(s)
        # inicializa el array de hashes
        hashes = []
        # haz un bucle tantas veces como el número de hashes
        for _ in range(num_txs):
            # cada hash es 32 bytes, little endian
            hashes.append(s.read(32)[::-1])
        # obtén la longitud del campo de flags como un varint
        longitud_flags = read_varint(s)
        # lee el campo de flags
        flags = s.read(longitud_flags)
        # inicializa la clase
        return cls(versión, bloque_previo, raíz_merkle, timestamp, bits, nonce,
                   total, hashes, flags)

    def es_válido(self):
        '''Verifica si la información en el árbol de merkle valida a la raíz merkles'''
        # convierte el campo de flags a campo de bits usando bytes_a_campo_bit
        # dale la vuelta a los hashes para botener la lista de hashes para el cálculo de la raíz merkle
        # inicializa el árbol de merkle
        # puebla el árbol con flag bits y hashes
        # comprueba si la raíz computada [::-1] es la misma que la raíz de merkle
        raise NotImplementedError


class PruebaBloqueMerkle(TestCase):

    def prueba_parsear(self):
        bloque_merkle_hex = '00000020df3b053dc46f162a9b00c7f0d5124e2676d47bbe7c5d0793a500000000000000ef445fef2ed495c275892206ca533e7411907971013ab83e3b47bd0d692d14d4dc7c835b67d8001ac157e670bf0d00000aba412a0d1480e370173072c9562becffe87aa661c1e4a6dbc305d38ec5dc088a7cf92e6458aca7b32edae818f9c2c98c37e06bf72ae0ce80649a38655ee1e27d34d9421d940b16732f24b94023e9d572a7f9ab8023434a4feb532d2adfc8c2c2158785d1bd04eb99df2e86c54bc13e139862897217400def5d72c280222c4cbaee7261831e1550dbb8fa82853e9fe506fc5fda3f7b919d8fe74b6282f92763cef8e625f977af7c8619c32a369b832bc2d051ecd9c73c51e76370ceabd4f25097c256597fa898d404ed53425de608ac6bfe426f6e2bb457f1c554866eb69dcb8d6bf6f880e9a59b3cd053e6c7060eeacaacf4dac6697dac20e4bd3f38a2ea2543d1ab7953e3430790a9f81e1c67f5b58c825acf46bd02848384eebe9af917274cdfbb1a28a5d58a23a17977def0de10d644258d9c54f886d47d293a411cb6226103b55635'
        mb = BloqueMerkle.parsear(BytesIO(bytes.fromhex(bloque_merkle_hex)))
        versión = 0x20000000
        self.assertEqual(mb.versión, versión)
        raíz_merkle_hex = 'ef445fef2ed495c275892206ca533e7411907971013ab83e3b47bd0d692d14d4'
        raíz_merkle = bytes.fromhex(raíz_merkle_hex)[::-1]
        self.assertEqual(mb.raíz_merkle, raíz_merkle)
        bloque_previo_hex = 'df3b053dc46f162a9b00c7f0d5124e2676d47bbe7c5d0793a500000000000000'
        bloque_previo = bytes.fromhex(bloque_previo_hex)[::-1]
        self.assertEqual(mb.bloque_previo, bloque_previo)
        timestamp = little_endian_a_int(bytes.fromhex('dc7c835b'))
        self.assertEqual(mb.timestamp, timestamp)
        bits = bytes.fromhex('67d8001a')
        self.assertEqual(mb.bits, bits)
        nonce = bytes.fromhex('c157e670')
        self.assertEqual(mb.nonce, nonce)
        total = little_endian_a_int(bytes.fromhex('bf0d0000'))
        self.assertEqual(mb.total, total)
        hex_hashes = [
            'ba412a0d1480e370173072c9562becffe87aa661c1e4a6dbc305d38ec5dc088a',
            '7cf92e6458aca7b32edae818f9c2c98c37e06bf72ae0ce80649a38655ee1e27d',
            '34d9421d940b16732f24b94023e9d572a7f9ab8023434a4feb532d2adfc8c2c2',
            '158785d1bd04eb99df2e86c54bc13e139862897217400def5d72c280222c4cba',
            'ee7261831e1550dbb8fa82853e9fe506fc5fda3f7b919d8fe74b6282f92763ce',
            'f8e625f977af7c8619c32a369b832bc2d051ecd9c73c51e76370ceabd4f25097',
            'c256597fa898d404ed53425de608ac6bfe426f6e2bb457f1c554866eb69dcb8d',
            '6bf6f880e9a59b3cd053e6c7060eeacaacf4dac6697dac20e4bd3f38a2ea2543',
            'd1ab7953e3430790a9f81e1c67f5b58c825acf46bd02848384eebe9af917274c',
            'dfbb1a28a5d58a23a17977def0de10d644258d9c54f886d47d293a411cb62261',
        ]
        hashes = [bytes.fromhex(h)[::-1] for h in hex_hashes]
        self.assertEqual(mb.hashes, hashes)
        flags = bytes.fromhex('b55635')
        self.assertEqual(mb.flags, flags)

    def prueba_es_válido(self):
        bloque_merkle_hex = '00000020df3b053dc46f162a9b00c7f0d5124e2676d47bbe7c5d0793a500000000000000ef445fef2ed495c275892206ca533e7411907971013ab83e3b47bd0d692d14d4dc7c835b67d8001ac157e670bf0d00000aba412a0d1480e370173072c9562becffe87aa661c1e4a6dbc305d38ec5dc088a7cf92e6458aca7b32edae818f9c2c98c37e06bf72ae0ce80649a38655ee1e27d34d9421d940b16732f24b94023e9d572a7f9ab8023434a4feb532d2adfc8c2c2158785d1bd04eb99df2e86c54bc13e139862897217400def5d72c280222c4cbaee7261831e1550dbb8fa82853e9fe506fc5fda3f7b919d8fe74b6282f92763cef8e625f977af7c8619c32a369b832bc2d051ecd9c73c51e76370ceabd4f25097c256597fa898d404ed53425de608ac6bfe426f6e2bb457f1c554866eb69dcb8d6bf6f880e9a59b3cd053e6c7060eeacaacf4dac6697dac20e4bd3f38a2ea2543d1ab7953e3430790a9f81e1c67f5b58c825acf46bd02848384eebe9af917274cdfbb1a28a5d58a23a17977def0de10d644258d9c54f886d47d293a411cb6226103b55635'
        mb = BloqueMerkle.parsear(BytesIO(bytes.fromhex(bloque_merkle_hex)))
        self.assertTrue(mb.es_válido())
