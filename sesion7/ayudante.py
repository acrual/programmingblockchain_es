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
    '''Devuelve una versión cadena de los bytes'''
    return b.decode(encoding)


def str_a_bytes(s, encoding='ascii'):
    '''Devuelve una versión bytes de la cadena'''
    return s.encode(encoding)


def little_endian_a_int(b):
    '''little_endian_a_int toma una secuencia de bytes como número little-endian.
    Devuelve un entero'''
    # usa el método from_bytes de int
    return int.from_bytes(b, 'little')


def int_a_little_endian(n, long):
    '''int_a_little_endian toma un entero y devuelve la secuencia
    de bytes little-endian de longitud long'''
    # usa el método to_bytes de n
    return n.to_bytes(long, 'little')


def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def doble_sha256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def codificar_base58(s):
    # determina con cuántos 0 bytes (b'\x00') comienza z
    contador = 0
    for c in s:
        if c == 0:
            contador += 1
        else:
            break
    prefijo = b'1' * contador
    # convierte de binario a hex, luego de hex a entero
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
    # codificar_base58 sobre el bruto y el checksum
    base58 = codificar_base58(bruto + checksum)
    # convierte en string con base58.decode('ascii')
    return base58.decode('ascii')


def decodificar_base58(s):
    num = 0
    for c in s.encode('ascii'):
        num *= 58
        num += ALFABETO_BASE58.index(c)
    combinado = num.to_bytes(25, byteorder='big')
    checksum = combinado[-4:]
    if doble_sha256(combinado[:-4])[:4] != checksum:
        raise RuntimeError('bad dire: {} {}'.format(checksum, doble_sha256(combinado)[:4]))
    return combinado[1:-4]


def read_varint(s):
    '''read_varint lee un entero variable desde un stream'''
    i = s.read(1)[0]
    if i == 0xfd:
        # 0xfd significa que los dos bytes siguientes son el número
        return little_endian_a_int(s.read(2))
    elif i == 0xfe:
        # 0xfe significa que los cuatro bytes siguientes son el número
        return little_endian_a_int(s.read(4))
    elif i == 0xff:
        # 0xff significa que los ocho bytes siguientes son el número
        return little_endian_a_int(s.read(8))
    else:
        # cualquier otra cosa es el entero
        return i


def codificar_varint(i):
    '''codifica un entero como varint'''
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
    '''Toma una secuencia de bytes y devuelve una cadena de dirección p2pkh'''
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


def padre_merkle(hash1, hash2):
    '''Toma los hashes en binario y calcula el doble-sha256'''
    # devuelve el doble_sha256 de hash1 + hash2
    raise NotImplementedError


def nivel_padre_merkle(hashes):
    '''Toma una lista de hashes binarios y devuelve una lista de la mitad
    de longitud'''
    # si la lista tiene exactamente 1 elemento, debe dar un error
    # si la lista tiene un número impar de elementos, duplica el último
    #       y ponlo al final para que sea un número par de elementos
    # inicializa el siguiente nivel
    # haz un bucle sobre cada pareja (usa: for i in range(0, len(hashes), 2))
        # obtén el padre merkle de los hashes i y i+1
        # añade el padre al nivel padre
    # devuelve nivel padre
    raise NotImplementedError


def raiz_merkle(hashes):
    '''Toma una lista de hashes binarios y devuelve la raiz merkle
    '''
    # el nivel actual comienza como hashes
    # haz un bucle hasta que haya exactamente 1 elemento
        # el nivel actual se conierte en el nivel de padre merkle
    # devuelve el primer elemento del nivel_actual
    raise NotImplementedError


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

    def prueba_padre_merkle(self):
        tx_hash0 = bytes.fromhex('c117ea8ec828342f4dfb0ad6bd140e03a50720ece40169ee38bdc15d9eb64cf5')
        tx_hash1 = bytes.fromhex('c131474164b412e3406696da1ee20ab0fc9bf41c8f05fa8ceea7a08d672d7cc5')
        want = bytes.fromhex('8b30c5ba100f6f2e5ad1e2a742e5020491240f8eb514fe97c713c31718ad7ecd')
        self.assertEqual(padre_merkle(tx_hash0, tx_hash1), want)

    def prueba_nivel_padre_merkle(self):
        hex_hashes = [
            'c117ea8ec828342f4dfb0ad6bd140e03a50720ece40169ee38bdc15d9eb64cf5',
            'c131474164b412e3406696da1ee20ab0fc9bf41c8f05fa8ceea7a08d672d7cc5',
            'f391da6ecfeed1814efae39e7fcb3838ae0b02c02ae7d0a5848a66947c0727b0',
            '3d238a92a94532b946c90e19c49351c763696cff3db400485b813aecb8a13181',
            '10092f2633be5f3ce349bf9ddbde36caa3dd10dfa0ec8106bce23acbff637dae',
            '7d37b3d54fa6a64869084bfd2e831309118b9e833610e6228adacdbd1b4ba161',
            '8118a77e542892fe15ae3fc771a4abfd2f5d5d5997544c3487ac36b5c85170fc',
            'dff6879848c2c9b62fe652720b8df5272093acfaa45a43cdb3696fe2466a3877',
            'b825c0745f46ac58f7d3759e6dc535a1fec7820377f24d4c2c6ad2cc55c0cb59',
            '95513952a04bd8992721e9b7e2937f1c04ba31e0469fbe615a78197f68f52b7c',
            '2e6d722e5e4dbdf2447ddecc9f7dabb8e299bae921c99ad5b0184cd9eb8e5908',
        ]
        tx_hashes = [bytes.fromhex(x) for x in hex_hashes]
        want_hex_hashes = [
            '8b30c5ba100f6f2e5ad1e2a742e5020491240f8eb514fe97c713c31718ad7ecd',
            '7f4e6f9e224e20fda0ae4c44114237f97cd35aca38d83081c9bfd41feb907800',
            'ade48f2bbb57318cc79f3a8678febaa827599c509dce5940602e54c7733332e7',
            '68b3e2ab8182dfd646f13fdf01c335cf32476482d963f5cd94e934e6b3401069',
            '43e7274e77fbe8e5a42a8fb58f7decdb04d521f319f332d88e6b06f8e6c09e27',
            '1796cd3ca4fef00236e07b723d3ed88e1ac433acaaa21da64c4b33c946cf3d10',
        ]
        want_tx_hashes = [bytes.fromhex(x) for x in want_hex_hashes]
        self.assertEqual(nivel_padre_merkle(tx_hashes), want_tx_hashes)

    def prueba_raiz_merkle(self):
        hex_hashes = [
            'c117ea8ec828342f4dfb0ad6bd140e03a50720ece40169ee38bdc15d9eb64cf5',
            'c131474164b412e3406696da1ee20ab0fc9bf41c8f05fa8ceea7a08d672d7cc5',
            'f391da6ecfeed1814efae39e7fcb3838ae0b02c02ae7d0a5848a66947c0727b0',
            '3d238a92a94532b946c90e19c49351c763696cff3db400485b813aecb8a13181',
            '10092f2633be5f3ce349bf9ddbde36caa3dd10dfa0ec8106bce23acbff637dae',
            '7d37b3d54fa6a64869084bfd2e831309118b9e833610e6228adacdbd1b4ba161',
            '8118a77e542892fe15ae3fc771a4abfd2f5d5d5997544c3487ac36b5c85170fc',
            'dff6879848c2c9b62fe652720b8df5272093acfaa45a43cdb3696fe2466a3877',
            'b825c0745f46ac58f7d3759e6dc535a1fec7820377f24d4c2c6ad2cc55c0cb59',
            '95513952a04bd8992721e9b7e2937f1c04ba31e0469fbe615a78197f68f52b7c',
            '2e6d722e5e4dbdf2447ddecc9f7dabb8e299bae921c99ad5b0184cd9eb8e5908',
            'b13a750047bc0bdceb2473e5fe488c2596d7a7124b4e716fdd29b046ef99bbf0',
        ]
        tx_hashes = [bytes.fromhex(x) for x in hex_hashes]
        want_hex_hash = 'acbcab8bcc1af95d8d563b77d24c3d19b18f1486383d75a5085c4e86c86beed6'
        want_hash = bytes.fromhex(want_hex_hash)
        self.assertEqual(raiz_merkle(tx_hashes), want_hash)
