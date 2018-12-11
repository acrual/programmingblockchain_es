from io import BytesIO
from unittest import TestCase

from ayudante import (
    codificar_varint,
    h160_a_dire_p2pkh,
    h160_a_dire_p2sh,
    int_a_little_endian,
    read_varint,
)


def script_p2pkh(h160):
    '''Toma un hash160 y devuelve el scriptPubKey'''
    return Script([0x76, 0xa9, h160, 0x88, 0xac])


class Script:

    def __init__(self, cosas):
        self.cosas = cosas

    def __repr__(self):
        res = ''
        for cosa in self.cosas:
            if type(cosa) == int:
                res += '{} '.format(OP_CODES[cosa])
            else:
                res += '{} '.format(cosa.hex())
        return res

    @classmethod
    def parsear(cls, s):
        # obtén la longitud del campo completo
        longitud = read_varint(s)
        # inicializa el array de cosas
        cosas = []
        # inicializa el número de bytes que hemos leído a 0
        contador = 0
        # haz un bucle hasta que leamos la longitud en bytes
        while contador < longitud:
            # obtén el byte actual
            actual = s.read(1)
            # aumenta los bytes que hemos leído
            contador += 1
            # convierte el byte actual a un entero
            byte_actual = actual[0]
            # si el byte actual está entre 1 y 75 ambos incluidos
            if byte_actual >= 1 and byte_actual <= 75:
                # tenemos una cosa como n para ser el byte actual
                n = byte_actual
                # añade los siguientes n bytes como una cosa
                cosas.append(s.read(n))
                # aumenta el contador en n
                contador += n
            else:
                # tenemos un op code. establece el byte actual a op_code
                op_code = byte_actual
                # añade el op_code a la lista de cosas
                cosas.append(op_code)
        return cls(cosas)

    def serializar(self):
        # inicializa lo que enviaremos de vuelta
        res = b''
        # ve a través de cada cosa
        for cosa in self.cosas:
            # si la cosa es un entero, es un op code
            if type(cosa) == int:
                # convierte la cosa en un único byte entero usando int_a_little_endian
                res += int_a_little_endian(cosa, 1)
            else:
                # en otro caso, esto es un elemento
                # obtén la longitud en bytes
                longitud = len(cosa)
                # convierte la longitud en un único byte entero usando int_a_little_endian
                prefijo = int_a_little_endian(longitud, 1)
                # añade al resultado tanto la longitud como la cosa
                res += prefijo + cosa
        # obtén la longitud de todo
        total = len(res)
        # codificar_varint la longitud total de res y anteponlo
        return codificar_varint(total) + res

    def firma(self):
        '''devuelve el elemento firma asumiendo script sig de p2pkh'''
        return self.cosas[0]

    def sec_pubkey(self):
        '''devuelve el elemento pubkey asumiendo script sig p2pkh'''
        return self.cosas[1]

    def dire(self, testnet=False):
        '''Devuelve la dirección correspondiente al script'''
        # HACK: cuenta cuántos elementos hay para determinar de qué tipo es
        if len(self.cosas) == 5:  # p2pkh
            # hash160 es el tercer elemento
            h160 = self.cosas[2]
            # convierte a dire p2pkh usando h160_a_dire_p2pkh (recuerda testnet)
            return h160_a_dire_p2pkh(h160, testnet)
        elif len(self.cosas) == 3:  # p2sh
            # hash160 es el segundo elemento
            h160 = self.cosas[1]
            # convierte a dire p2sh usando h160_a_dire_p2sh (recuerda testnet)
            return h160_a_dire_p2sh(h160, testnet)


class PruebaScript(TestCase):

    def prueba_parsear(self):
        script_pubkey = BytesIO(bytes.fromhex('6a47304402207899531a52d59a6de200179928ca900254a36b8dff8bb75f5f5d71b1cdc26125022008b422690b8461cb52c3cc30330b23d574351872b7c361e9aae3649071c1a7160121035d5c93d9ac96881f19ba1f686f15f009ded7c62efe85a872e6a19b43c15a2937'))
        script = Script.parsear(script_pubkey)
        want = bytes.fromhex('304402207899531a52d59a6de200179928ca900254a36b8dff8bb75f5f5d71b1cdc26125022008b422690b8461cb52c3cc30330b23d574351872b7c361e9aae3649071c1a71601')
        self.assertEqual(script.cosas[0].hex(), want.hex())
        want = bytes.fromhex('035d5c93d9ac96881f19ba1f686f15f009ded7c62efe85a872e6a19b43c15a2937')
        self.assertEqual(script.cosas[1], want)

    def prueba_serializar(self):
        want = '6a47304402207899531a52d59a6de200179928ca900254a36b8dff8bb75f5f5d71b1cdc26125022008b422690b8461cb52c3cc30330b23d574351872b7c361e9aae3649071c1a7160121035d5c93d9ac96881f19ba1f686f15f009ded7c62efe85a872e6a19b43c15a2937'
        script_pubkey = BytesIO(bytes.fromhex(want))
        script = Script.parsear(script_pubkey)
        self.assertEqual(script.serializar().hex(), want)

    def prueba_p2pkh(self):
        script_pubkey_bruto = bytes.fromhex('1976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac')
        script_pubkey = Script.parsear(BytesIO(script_pubkey_bruto))
        self.assertEqual(script_pubkey.serializar(), script_pubkey_bruto)

        script_sig_bruto = bytes.fromhex('6b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a')
        script_sig = Script.parsear(BytesIO(script_sig_bruto))
        self.assertEqual(script_sig.serializar(), script_sig_bruto)
        self.assertEqual(script_sig.firma(), bytes.fromhex('3045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01'))
        self.assertEqual(script_sig.sec_pubkey(), bytes.fromhex('0349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a'))

    def prueba_p2sh(self):
        script_pubkey_bruto = bytes.fromhex('17a91474d691da1574e6b3c192ecfb52cc8984ee7b6c5687')
        script_pubkey = Script.parsear(BytesIO(script_pubkey_bruto))
        self.assertEqual(script_pubkey.serializar(), script_pubkey_bruto)

        script_sig_bruto = bytes.fromhex('db00483045022100dc92655fe37036f47756db8102e0d7d5e28b3beb83a8fef4f5dc0559bddfb94e02205a36d4e4e6c7fcd16658c50783e00c341609977aed3ad00937bf4ee942a8993701483045022100da6bee3c93766232079a01639d07fa869598749729ae323eab8eef53577d611b02207bef15429dcadce2121ea07f233115c6f09034c0be68db99980b9a6c5e75402201475221022626e955ea6ea6d98850c994f9107b036b1334f18ca8830bfff1295d21cfdb702103b287eaf122eea69030a0e9feed096bed8045c8b98bec453e1ffac7fbdbd4bb7152ae')
        script_sig = Script.parsear(BytesIO(script_sig_bruto))
        self.assertEqual(script_sig.serializar(), script_sig_bruto)

    def prueba_dire(self):
        script_bruto = bytes.fromhex('1976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac')
        script_pubkey = Script.parsear(BytesIO(script_bruto))
        want = '15hZo812Lx266Dot6T52krxpnhrNiaqHya'
        self.assertEqual(script_pubkey.dire(testnet=False), want)
        want = 'mkDX6B619yTLsLHVp23QanB9ehT5bcf89D'
        self.assertEqual(script_pubkey.dire(testnet=True), want)
        script_bruto = bytes.fromhex('17a91474d691da1574e6b3c192ecfb52cc8984ee7b6c5687')
        script_pubkey = Script.parsear(BytesIO(script_bruto))
        want = '3CLoMMyuoDQTPRD3XYZtCvgvkadrAdvdXh'
        self.assertEqual(script_pubkey.dire(testnet=False), want)
        want = '2N3u1R6uwQfuobCqbCgBkpsgBxvr1tZpe7B'
        self.assertEqual(script_pubkey.dire(testnet=True), want)


OP_CODES = {
    0: 'OP_0',
    76: 'OP_PUSHDATA1',
    77: 'OP_PUSHDATA2',
    78: 'OP_PUSHDATA4',
    79: 'OP_1NEGATE',
    80: 'OP_RESERVED',
    81: 'OP_1',
    82: 'OP_2',
    83: 'OP_3',
    84: 'OP_4',
    85: 'OP_5',
    86: 'OP_6',
    87: 'OP_7',
    88: 'OP_8',
    89: 'OP_9',
    90: 'OP_10',
    91: 'OP_11',
    92: 'OP_12',
    93: 'OP_13',
    94: 'OP_14',
    95: 'OP_15',
    96: 'OP_16',
    97: 'OP_NOP',
    98: 'OP_VER',
    99: 'OP_IF',
    100: 'OP_NOTIF',
    101: 'OP_VERIF',
    102: 'OP_VERNOTIF',
    103: 'OP_ELSE',
    104: 'OP_ENDIF',
    105: 'OP_VERIFY',
    106: 'OP_RETURN',
    107: 'OP_TOALTSTACK',
    108: 'OP_FROMALTSTACK',
    109: 'OP_2DROP',
    110: 'OP_2DUP',
    111: 'OP_3DUP',
    112: 'OP_2OVER',
    113: 'OP_2ROT',
    114: 'OP_2SWAP',
    115: 'OP_IFDUP',
    116: 'OP_DEPTH',
    117: 'OP_DROP',
    118: 'OP_DUP',
    119: 'OP_NIP',
    120: 'OP_OVER',
    121: 'OP_PICK',
    122: 'OP_ROLL',
    123: 'OP_ROT',
    124: 'OP_SWAP',
    125: 'OP_TUCK',
    126: 'OP_CAT',
    127: 'OP_SUBSTR',
    128: 'OP_LEFT',
    129: 'OP_RIGHT',
    130: 'OP_SIZE',
    131: 'OP_INVERT',
    132: 'OP_AND',
    133: 'OP_OR',
    134: 'OP_XOR',
    135: 'OP_EQUAL',
    136: 'OP_EQUALVERIFY',
    137: 'OP_RESERVED1',
    138: 'OP_RESERVED2',
    139: 'OP_1ADD',
    140: 'OP_1SUB',
    141: 'OP_2MUL',
    142: 'OP_2DIV',
    143: 'OP_NEGATE',
    144: 'OP_ABS',
    145: 'OP_NOT',
    146: 'OP_0NOTEQUAL',
    147: 'OP_ADD',
    148: 'OP_SUB',
    149: 'OP_MUL',
    150: 'OP_DIV',
    151: 'OP_MOD',
    152: 'OP_LSHIFT',
    153: 'OP_RSHIFT',
    154: 'OP_BOOLAND',
    155: 'OP_BOOLOR',
    156: 'OP_NUMEQUAL',
    157: 'OP_NUMEQUALVERIFY',
    158: 'OP_NUMNOTEQUAL',
    159: 'OP_LESSTHAN',
    160: 'OP_GREATERTHAN',
    161: 'OP_LESSTHANOREQUAL',
    162: 'OP_GREATERTHANOREQUAL',
    163: 'OP_MIN',
    164: 'OP_MAX',
    165: 'OP_WITHIN',
    166: 'OP_RIPEMD160',
    167: 'OP_SHA1',
    168: 'OP_SHA256',
    169: 'OP_HASH160',
    170: 'OP_HASH256',
    171: 'OP_CODESEPARATOR',
    172: 'OP_CHECKSIG',
    173: 'OP_CHECKSIGVERIFY',
    174: 'OP_CHECKMULTISIG',
    175: 'OP_CHECKMULTISIGVERIFY',
    176: 'OP_NOP1',
    177: 'OP_CHECKLOCKTIMEVERIFY',
    178: 'OP_CHECKSEQUENCEVERIFY',
    179: 'OP_NOP4',
    180: 'OP_NOP5',
    181: 'OP_NOP6',
    182: 'OP_NOP7',
    183: 'OP_NOP8',
    184: 'OP_NOP9',
    185: 'OP_NOP10',
    252: 'OP_NULLDATA',
    253: 'OP_PUBKEYHASH',
    254: 'OP_PUBKEY',
    255: 'OP_INVALIDOPCODE',
}
