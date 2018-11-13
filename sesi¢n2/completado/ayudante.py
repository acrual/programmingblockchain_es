from unittest import TestCase, TestSuite, TextTestRunner

import hashlib


ALFABETO_BASE58 = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def ejecutar_prueba(test):
    suite = TestSuite()
    suite.addTest(test)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una cadena desde bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve una versión bytes desde una cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''little_endian_a_int toma una secuencia de bytes como un número little-endian.
    Devuelve un entero'''
    # usa el método de int from_bytes
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, long):
    '''endian_to_little_endian toma un entero y devuelve una secuencia de bytes little-endian
    de longitud long'''
    # usa el método de n to_bytes
    return n.to_bytes(long, 'little')


def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def doble_sha256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def codificar_base58(s):
    # determina con cuántos bytes 0 (b'\x00') empieza s
    contador = 0
    for c in s:
        if c == 0:
            contador += 1
        else:
            break
    prefijo = b'1' * contador
    # convierte desde binario a hex y después de hex a entero
    num = int(s.hex(), 16)
    res = bytearray()
    while num > 0:
        num, mod = divmod(num, 58)
        res.insert(0, ALFABETO_BASE58[mod])

    return prefijo + bytes(res)



class PruebaAyudante(TestCase):

    def test_bytes(self):
        b = b'hello world'
        s = 'hello world'
        self.assertEqual(b, str_a_bytes(s))
        self.assertEqual(s, bytes_a_str(b))

    def test_little_endian_a_int(self):
        h = bytes.fromhex('99c3980000000000')
        quiero = 10011545
        self.assertEqual(little_endian_a_int(h), quiero)
        h = bytes.fromhex('a135ef0100000000')
        quiero = 32454049
        self.assertEqual(little_endian_a_int(h), quiero)

    def test_int_a_little_endian(self):
        n = 1
        quiero = b'\x01\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 4), quiero)
        n = 10011545
        quiero = b'\x99\xc3\x98\x00\x00\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 8), quiero)
