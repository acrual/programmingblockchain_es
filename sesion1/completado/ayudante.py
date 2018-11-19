from unittest import TestCase, TestSuite, TextTestRunner


def ejecutar_prueba(test):
    suite = TestSuite()
    suite.addTest(test)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una cadena desde bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve bytes desde una cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''little_endian_a_int toma la secuencia de bytes como un little-endian.
    Devuelve un entero'''
    # usa el método from_bytes desde int
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, long):
    '''int_a_little_endian toma un entero y devuelve una secuencia de bytes 
    little-endian de longitud long'''
    # usa el método to_bytes de n
    return n.to_bytes(long, 'little')


class PruebaAyudante(TestCase):

    def prueba_bytes(self):
        b = b'hello world'
        s = 'hello world'
        self.assertEqual(b, str_a_bytes(s))
        self.assertEqual(s, bytes_a_str(b))

    def prueba_little_endian_a_int(self):
        h = bytes.fromhex('99c3980000000000')
        quiero = 10011545
        self.assertEqual(little_endian_a_int(h), quiero)
        h = bytes.fromhex('a135ef0100000000')
        quiero = 32454049
        self.assertEqual(little_endian_a_int(h), quiero)

    def prueba_int_a_little_endian(self):
        n = 1
        quiero = b'\x01\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 4), quiero)
        n = 10011545
        quiero = b'\x99\xc3\x98\x00\x00\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 8), quiero)
