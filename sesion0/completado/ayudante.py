from unittest import TestCase, TestSuite, TextTestRunner


def ejecutar_prueba(test):
    suite = TestSuite()
    suite.addTest(test)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una cadena desde bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve una versión en bytes desde una cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''esta función toma una secuencia de bytes como un número little-endian.
    Devuelve un entero'''
    # use the from_bytes method of int
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, length):
    '''endian_to_little_endian takes an integer and returns the little-endian
    byte sequence of length'''
    # usa el método to_bytes de n
    return n.to_bytes(length, 'little')


class PruebaAyudante(TestCase):

    def prueba_bytes(self):
        b = b'hello world'
        s = 'hello world'
        self.assertEqual(b, str_a_bytes(s))
        self.assertEqual(s, bytes_to_str(b))

    def prueba_little_endian_a_int(self):
        h = bytes.fromhex('99c3980000000000')
        quiero = 10011545
        self.assertEqual(little_endian_a_int(h), quiero)
        h = bytes.fromhex('a135ef0100000000')
        quiero = 32454049
        self.assertEqual(little_endian_a_int(h), quiero)

    def prueba_int_a_little_endian(self):
        n = 1
        want = b'\x01\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 4), quiero)
        n = 10011545
        quiero = b'\x99\xc3\x98\x00\x00\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 8), quiero)
