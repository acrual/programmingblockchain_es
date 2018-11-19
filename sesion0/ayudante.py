from unittest import TestCase, TestSuite, TextTestRunner


def ejecutar_prueba(test):
    suite = TestSuite()
    suite.addTest(test)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una cadena desde bytes'''
    raise NotImplementedError


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve una versión en bytes desde una cadena'''
    raise NotImplementedError


def little_endian_a_int(b):
    '''esta función toma una secuencia de bytes como un número little-endian.
    Devuelve un entero'''
    # usa el método from_bytes de int
    raise NotImplementedError


def int_a_little_endian(n, longitud):
    '''int_a_little_endian toma un entero y devuelve la secuencia de bytes
    little-endian de longitud'''
    # usa el método to_bytes de n
    raise NotImplementedError


class PruebaAyudante(TestCase):

    def prueba_bytes(self):
        b = b'hello world'
        s = 'hello world'
        self.assertEqual(b, str_a_bytes(s))
        self.assertEqual(s, bytes_a_str(b))

    def prueba_little_endian_a_int(self):
        h = bytes.fromhex('99c3980000000000')
        deseo = 10011545
        self.assertEqual(little_endian_a_int(h), deseo)
        h = bytes.fromhex('a135ef0100000000')
        deseo = 32454049
        self.assertEqual(little_endian_a_int(h), deseo)

    def prueba_int_a_little_endian(self):
        n = 1
        deseo = b'\x01\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 4), deseo)
        n = 10011545
        deseo = b'\x99\xc3\x98\x00\x00\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 8), deseo)
