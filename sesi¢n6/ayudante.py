from unittest import TestCase, TestSuite, TextTestRunner

import hashlib


SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
ALFABETO_BASE58 = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def ejecutar_prueba(test):
    suite = TestSuite()
    suite.addTest(test)
    TextTestRunner().run(suite)


def bytes_a_str(b, encoding='ascii'):
    '''Devuelve una cadena versión de los bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve una versión en bytes de la cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''little_endian_a_int toma una secuencia de bytes como un número little-endian.
    Devuelve un entero'''
    # usa el método from_bytes de int
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, long):
    '''int_a_little_endian toma un entero y devuelve la secuencia de bytes little-endian
    de longitud long'''
    # usa el método to_bytes de n
    return n.to_bytes(long, 'little')


def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def doble_sha256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def codificar_base58(s):
    # determina con cuántos 0 bytes (b'\x00') empieza s
    contador = 0
    for c in s:
        if c == 0:
            contador += 1
        else:
            break
    prefijo = b'1' * contador
    # convierte desde binario a hex, luego de hex a entero
    num = int(s.hex(), 16)
    res = bytearray()
    while num > 0:
        num, mod = divmod(num, 58)
        res.insert(0, ALFABETO_BASE58[mod])

    return prefijo + bytes(res)


def codificar_base58_checksum(bruto):
    '''Toma bytes y los convierte en codificación base58 con checksum'''
    # checksum son los primeros 4 bytes del doble_sha256
    checksum = doble_sha256(bruto)[:4]
    # codificar_base58 sobre bruto y el checksum
    base58 = codificar_base58(bruto + checksum)
    # convierte a cadena con base58.decode('ascii')
    return base58.decode('ascii')


def decodificar_base58(s):
    num = 0
    for c in s.encode('ascii'):
        num *= 58
        num += ALFABETO_BASE58.index(c)
    combinado = num.to_bytes(25, byteorder='big')
    checksum = combinado[-4:]
    if doble_sha256(combinado[:-4])[:4] != checksum:
        raise RuntimeError('dirección mala: {} {}'.format(checksum, doble_sha256(combinado)[:4]))
    return combinado[1:-4]


def read_varint(s):
    '''read_varint lee un entero variable desde un stream'''
    i = s.read(1)[0]
    if i == 0xfd:
        # 0xfd significa que los próximos dos bytes son el número
        return little_endian_a_int(s.read(2))
    elif i == 0xfe:
        # 0xfe significa que los próximos dos bytes son el número
        return little_endian_a_int(s.read(4))
    elif i == 0xff:
        # 0xff significa que los próximos dos bytes son el número
        return little_endian_a_int(s.read(8))
    else:
        # cualquier otra cosa es el entero
        return i


def codificar_varint(i):
    '''codifica un entero como un varint'''
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + int_a_little_endian(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + int_a_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + int_a_little_endian(i, 8)
    else:
        raise RuntimeError('entero demasiado grande: {}'.format(i))


def h160_a_dire_p2pkh(h160, testnet=False):
    '''Toma una secuencia de bytes hash160 y devuelve una cadena de dirección p2pkh'''
    # p2pkh tiene un prefijo de b'\x00' para mainnet, b'\x6f' para testnet
    if testnet:
        prefijo = b'\x6f'
    else:
        prefijo = b'\x00'
    return codificar_base58_checksum(prefijo + h160)


def h160_a_dire_p2sh(h160, testnet=False):
    '''Toma una secuencia de bytes hash160 y devuelve una cadena de dirección p2sh'''
    # p2sh tiene un prefijo de b'\x05' para mainnet, b'\xc4' para testnet
    if testnet:
        prefijo = b'\xc4'
    else:
        prefijo = b'\x05'
    return codificar_base58_checksum(prefijo + h160)


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

    def prueba_base58(self):
        dire = 'mnrVtF8DWjMu839VW3rBfgYaAfKk8983Xf'
        h160 = decodificar_base58(dire).hex()
        want = '507b27411ccf7f16f10297de6cef3f291623eddf'
        self.assertEqual(h160, want)
        got = codificar_base58_checksum(b'\x6f' + bytes.fromhex(h160))
        self.assertEqual(got, dire)

    def prueba_dire_p2pkh(self):
        h160 = bytes.fromhex('74d691da1574e6b3c192ecfb52cc8984ee7b6c56')
        want = '1BenRpVUFK65JFWcQSuHnJKzc4M8ZP8Eqa'
        self.assertEqual(h160_a_dire_p2pkh(h160, testnet=False), want)
        want = 'mrAjisaT4LXL5MzE81sfcDYKU3wqWSvf9q'
        self.assertEqual(h160_a_dire_p2pkh(h160, testnet=True), want)

    def prueba_dire_p2sh(self):
        h160 = bytes.fromhex('74d691da1574e6b3c192ecfb52cc8984ee7b6c56')
        want = '3CLoMMyuoDQTPRD3XYZtCvgvkadrAdvdXh'
        self.assertEqual(h160_a_dire_p2sh(h160, testnet=False), want)
        want = '2N3u1R6uwQfuobCqbCgBkpsgBxvr1tZpe7B'
        self.assertEqual(h160_a_dire_p2sh(h160, testnet=True), want)
