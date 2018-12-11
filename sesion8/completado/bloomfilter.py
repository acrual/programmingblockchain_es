from unittest import TestCase

from ayudante import campo_bit_a_bytes, codificar_varint, int_a_little_endian, murmur3


CONSTANTE_BIP37 = 0xfba4c795


class BloomFilter:

    def __init__(self, tamaño, función_contador, ajuste):
        self.tamaño = tamaño
        self.campo_bit = [0] * (tamaño * 8)
        self.función_contador = función_contador
        self.ajuste = ajuste

    def add(self, cosa):
        '''Añada una cosa al filtro'''
        # itera self.función_contador un número de veces
        for i in range(self.función_contador):
            # La semilla BIP0037 spec es i*CONSTANTE_BIP37 + self.ajuste
            semilla = i * CONSTANTE_BIP37 + self.ajuste
            # obtén el hash murmur3 dada esa semilla
            h = murmur3(cosa, semilla=semilla)
            # establece el bit en el hash módulo por el tamaño del campo bit (self.tamaño*8)
            bit = h % (self.tamaño * 8)
            # establece el campo bit en el bit para ser 1
            self.campo_bit[bit] = 1

    def filtro_bytes(self):
        return campo_bit_a_bytes(self.campo_bit)

    def filtrocarga(self, flag=1):
        '''Devuelve la carga que va en un mensaje filtrocarga'''
        # comienza con el tamaño del filtro en bytes
        carga = codificar_varint(self.tamaño)
        # luego súmale el filtro a bytes
        carga += self.filtro_bytes()
        # la función contador es 4 bytes little endian
        carga += int_a_little_endian(self.función_contador, 4)
        # ajuste is 4 bytes little endian
        carga += int_a_little_endian(self.ajuste, 4)
        # flag es 1 byte little endian
        carga += int_a_little_endian(flag, 1)
        return carga


class PruebaBloomFilter(TestCase):

    def prueba_sumar(self):
        bf = BloomFilter(10, 5, 99)
        cosa = b'Hello World'
        bf.add(cosa)
        esperado = '0000000a080000000140'
        self.assertEqual(bf.filtro_bytes().hex(), esperado)
        cosa = b'Goodbye!'
        bf.add(cosa)
        esperado = '4000600a080000010940'
        self.assertEqual(bf.filtro_bytes().hex(), esperado)

    def prueba_filtrocarga(self):
        bf = BloomFilter(10, 5, 99)
        cosa = b'Hello World'
        bf.add(cosa)
        cosa = b'Goodbye!'
        bf.add(cosa)
        esperado = '0a4000600a080000010940050000006300000001'
        self.assertEqual(bf.filtrocarga().hex(), esperado)
