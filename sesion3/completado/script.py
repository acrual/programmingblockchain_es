from io import BytesIO
from unittest import TestCase


class Script:

    def __init__(self, elementos):
        self.elementos = elementos

    def __repr__(self):
        res = ''
        for elemento in self.elementos:
            if type(elemento) == int:
                res += '{} '.format(OP_CODES[elemento])
            else:
                res += '{} '.format(elemento.hex())
        return res

    @classmethod
    def parsear(cls, binario):
        s = BytesIO(binario)
        elementos = []
        actual = s.read(1)
        while actual != b'':
            op_code = actual[0]
            if op_code > 0 and op_code <= 75:
                # tenemos un elemento
                elementos.append(s.read(op_code))
            else:
                elementos.append(op_code)
            actual = s.read(1)
        return cls(elementos)

    def tipo(self):
        '''Algunos scripts pay-to standard.'''
        if len(self.elementos) == 0:
            return 'blanco'
        elif self.elementos[0] == 0x76 \
           and self.elementos[1] == 0xa9 \
           and type(self.elementos[2]) == bytes \
           and len(self.elementos[2]) == 0x14 \
           and self.elementos[3] == 0x88 \
           and self.elementos[4] == 0xac:
            # p2pkh:
            # OP_DUP OP_HASH160 <20-byte hash> <OP_EQUALVERIFY> <OP_CHECKSIG>
            return 'p2pkh'
        elif self.elementos[0] == 0xa9 \
             and type(self.elementos[1]) == bytes \
             and len(self.elementos[1]) == 0x14 \
           and self.elementos[-1] == 0x87:
            # p2sh:
            # OP_HASH160 <20-byte hash> <OP_EQUAL>
            return 'p2sh'
        elif type(self.elementos[0]) == bytes \
             and len(self.elementos[0]) in (0x47, 0x48, 0x49) \
             and type(self.elementos[1]) == bytes \
             and len(self.elementos[1]) in (0x21, 0x41):
            # p2pkh scriptSig:
            # <firma> <pubkey>
            return 'p2pkh sig'
        elif len(self.elementos) > 1 \
             and type(self.elementos[1]) == bytes \
             and len(self.elementos[1]) in (0x47, 0x48, 0x49) \
             and self.elementos[-1][-1] == 0xae:
            # HACK: asume que p2sh es multisig
            # p2sh multifirma:
            # <x> <firma1> ... <firmam> <redeemscript termina con OP_CHECKMULTISIG>
            return 'p2sh sig'
        else:
            return 'desconocido'

    def serializar(self):
        res = b''
        for elemento in self.elementos:
            if type(elemento) == int:
                res += bytes([elemento])
            else:
                res += bytes([len(elemento)]) + elemento
        return res

    def firma(self, index=0):
        '''index no se usa para p2pkh, para p2sh, significa una de m firmas'''
        tipo_firma = self.tipo()
        if tipo_firma == 'p2pkh':
            return self.elementos[0]
        elif tipo_firma == 'p2sh':
            return self.elementos[index+1]
        else:
            raise RuntimeError('el tipo de script debe ser p2pkh o p2sh')

    def sec_pubkey(self, index=0):
        '''index no se usa para p2pkh, para p2sh, significa una de n claves públicas'''
        tipo_firma = self.tipo()
        if tipo_firma == 'p2pkh':
            return self.elementos[1]
        elif tipo_firma == 'p2sh':
            # HACK: asume que p2sh es una multifirma
            redeem_script = Script.parsear(self.elementos[-1])
            return redeem_script.elementos[index+1]


class PruebaScript(TestCase):

    def prueba_p2pkh(self):
        script_pubkey_bruto = bytes.fromhex('76a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac')
        script_pubkey = Script.parsear(script_pubkey_bruto)
        self.assertEqual(script_pubkey.tipo(), 'p2pkh')
        self.assertEqual(script_pubkey.serializar(), script_pubkey_bruto)

        script_sig_bruto = bytes.fromhex('483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a')
        script_sig = Script.parsear(script_sig_bruto)
        self.assertEqual(script_sig.tipo(), 'p2pkh')
        self.assertEqual(script_sig.serializar(), script_sig_bruto)
        self.assertEqual(script_sig.firma(), bytes.fromhex('3045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01'))
        self.assertEqual(script_sig.sec_pubkey(), bytes.fromhex('0349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a'))

    def prueba_p2sh(self):
        script_pubkey_bruto = bytes.fromhex('a91474d691da1574e6b3c192ecfb52cc8984ee7b6c5687')
        script_pubkey = Script.parsear(script_pubkey_bruto)
        self.assertEqual(script_pubkey.tipo(), 'p2sh')
        self.assertEqual(script_pubkey.serializar(), script_pubkey_bruto)

        script_sig_bruto = bytes.fromhex('00483045022100dc92655fe37036f47756db8102e0d7d5e28b3beb83a8fef4f5dc0559bddfb94e02205a36d4e4e6c7fcd16658c50783e00c341609977aed3ad00937bf4ee942a8993701483045022100da6bee3c93766232079a01639d07fa869598749729ae323eab8eef53577d611b02207bef15429dcadce2121ea07f233115c6f09034c0be68db99980b9a6c5e75402201475221022626e955ea6ea6d98850c994f9107b036b1334f18ca8830bfff1295d21cfdb702103b287eaf122eea69030a0e9feed096bed8045c8b98bec453e1ffac7fbdbd4bb7152ae')
        script_sig = Script.parsear(script_sig_bruto)
        self.assertEqual(script_sig.tipo(), 'p2sh sig')
        self.assertEqual(script_sig.serializar(), script_sig_bruto)
        self.assertEqual(script_sig.firma(index=0), bytes.fromhex('3045022100dc92655fe37036f47756db8102e0d7d5e28b3beb83a8fef4f5dc0559bddfb94e02205a36d4e4e6c7fcd16658c50783e00c341609977aed3ad00937bf4ee942a8993701'))
        self.assertEqual(script_sig.firma(index=1), bytes.fromhex('3045022100da6bee3c93766232079a01639d07fa869598749729ae323eab8eef53577d611b02207bef15429dcadce2121ea07f233115c6f09034c0be68db99980b9a6c5e75402201'))
        self.assertEqual(script_sig.sec_pubkey(index=0), bytes.fromhex('022626e955ea6ea6d98850c994f9107b036b1334f18ca8830bfff1295d21cfdb70'))
        self.assertEqual(script_sig.sec_pubkey(index=1), bytes.fromhex('03b287eaf122eea69030a0e9feed096bed8045c8b98bec453e1ffac7fbdbd4bb71'))


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
  177: 'OP_NOP2',
  177: 'OP_CHECKLOCKTIMEVERIFY',
  178: 'OP_NOP3',
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
