from unittest import TestCase, TestSuite, TextTestRunner

import hashlib


ALFABETO_BASE58 = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def ejecutar_prueba(test):
    suite = TestSuite()
    suite.addTest(test)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una versión cadena desde bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve una versión bytes desde una cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''little_endian_a_int toma una secuencia de bytes como un número little-endian.
    Devuelve un entero'''
    # usa el método from_bytes de int
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, long):
    '''endian_to_little_endian toma un entero y devuelve la secuencia de bytes
    little-endian de longitud'''
    # use the to_bytes method of n
    return n.to_bytes(long, 'little')


def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def doble_sha256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def encode_base58(s):
    # determina con cuántos bytes 0 comienza s (b'\x00')
    contador = 0
    for c in s:
        if c == 0:
            contador += 1
        else:
            break
    prefijo = b'1' * contador
    # convertir desde binario a hex, y luego de hex a entero
    num = int(s.hex(), 16)
    res = bytearray()
    while num > 0:
        num, mod = divmod(num, 58)
        res.insert(0, ALFABETO_BASE58[mod])

    return prefijo + bytes(res)


def encode_base58_checksum(s):
    return encode_base58(s + doble_sha256(s)[:4]).decode('ascii')


def decode_base58(s):
    num = 0
    for c in s.encode('ascii'):
        num *= 58
        num += ALFABETO_BASE58.index(c)
    combinado = num.to_bytes(25, byteorder='big')
    checksum = combinado[-4:]
    if doble_sha256(combinado[:-4])[:4] != checksum:
        raise RuntimeError('mala dirección: {} {}'.format(checksum, doble_sha256(combinado)[:4]))
    return combinado[1:-4]


def read_varint(s):
    '''read_varint lee una variable entero desde un stream'''
    i = s.read(1)[0]
    if i == 0xfd:
        # 0xfd significa que los próximos dosbytes son el número
        return little_endian_a_int(s.read(2))
    elif i == 0xfe:
        # 0xfe significa que los próximos 4 bytes son el número
        return little_endian_a_int(s.read(4))
    elif i == 0xff:
        # 0xff significa que los próximos 8 bytes son el número
        return little_endian_a_int(s.read(8))
    else:
        # cualquier otra cosa es el entero
        return i


def encode_varint(i):
    '''encodes un entero como un varint'''
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + int_a_little_endian(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + int_a_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + int_a_little_endian(i, 8)
    else:
        raise RuntimeError('entero demasiado largo: {}'.format(i))


class PruebaAyudante(TestCase):

    def prueba_bytes(self):
        b = b'hello world'
        s = 'hello world'
        self.assertEqual(b, str_a_bytes(s))
        self.assertEqual(s, bytes_a_str(b))

    def prueba_little_endian_a_int(self):
        h = bytes.fromhex('99c3980000000000')
        want = 10011545
        self.assertEqual(little_endian_a_int(h), want)
        h = bytes.fromhex('a135ef0100000000')
        want = 32454049
        self.assertEqual(little_endian_a_int(h), want)

    def prueba_int_a_little_endian(self):
        n = 1
        want = b'\x01\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 4), want)
        n = 10011545
        want = b'\x99\xc3\x98\x00\x00\x00\x00\x00'
        self.assertEqual(int_a_little_endian(n, 8), want)
