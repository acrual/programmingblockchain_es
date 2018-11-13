from unittest import TestCase, TestSuite, TextTestRunner

import hashlib


ALFABETO_BASE58 = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def ejecutar_prueba(prueba):
    suite = TestSuite()
    suite.addTest(prueba)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una cadena desde bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve bytes desde una cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''little_endian_a_int toma una secuencia de bytes como un número little-endian.
    Devuelve un entero'''
    # usa el método from_bytes de int
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, long):
    '''int_a_little_endian toma un entero y devuelve un la secuencia de bytes
    little endian de longitud long'''
    # usa el método to_bytes de n
    return n.to_bytes(long, 'little')


def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def doble_sha256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def codificar_base58(s):
    # determina cuántos bytes 0 (b'\x00') hay al comienzo de s
    conteo = 0
    for c in s:
        if c == 0:
            conteo += 1
        else:
            break
    prefijo = b'1' * conteo
    # convierte de binario a hex y entonces hex a entero
    num = int(s.hex(), 16)
    res = bytearray()
    while num > 0:
        num, mod = divmod(num, 58)
        res.insert(0, ALFABETO_BASE58[mod])

    return prefijo + bytes(res)



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
