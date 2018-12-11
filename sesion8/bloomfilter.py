from unittest import TestCase

from ayudante import campo_bit_a_bytes, codificar_varint, int_a_little_endian, murmur3


CONSTANTE_BIP37 = 0xfba4c795


class BloomFilter:

    def __init__(self, tamaño, función_contador, tweak):
        self.tamaño = tamaño
        self.bit_field = [0] * (tamaño * 8)
        self.función_contador = función_contador
        self.tweak = tweak

    def add(self, cosa):
        '''Añade una cosa al filtro'''
        # iterate self.función_contador number of times
            # BIP0037 spec seed is i*CONSTANTE_BIP37 + self.tweak
            # get the murmur3 hash given that seed
            # set the bit at the hash mod the bitfield tamaño (self.tamaño*8)
            # set the bit field at bit to be 1
        raise NotImplementedError

    def filtro_bytes(self):
        return campo_bit_a_bytes(self.bit_field)

    def filterload(self, flag=1):
        '''Return the payload that goes in a filterload message'''
        # start with the tamaño of the filter in bytes
        # next cast the filter to bytes
        # function count is 4 bytes little endian
        # tweak is 4 bytes little endian
        # flag is 1 byte little endian
        raise NotImplementedError


class BloomFilterTest(TestCase):

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
        self.assertEqual(bf.filterload().hex(), esperado)
