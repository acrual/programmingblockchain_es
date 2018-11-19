from io import BytesIO
from unittest import TestCase

from ayudante import (
    little_endian_a_int,
    read_varint,
)
from script import Script

class Tx:

    def __init__(self, version, tx_ins, tx_outs, locktime):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime

    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'version: {}\ntx_ins:\n{}\ntx_outs:\n{}\nlocktime: {}\n'.format(
            self.version,
            tx_ins,
            tx_outs,
            self.locktime,
        )

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea la transacción al principio
        devuelve un objeto Tx
        '''
        # s.read(n) devolverá n bytes
        # la version tiene 4 bytes, little-endian, interprétalo como int
        version = little_endian_a_int(s.read(4))
        # num_inputs es un varint, usa read_varint(s)
        num_inputs = read_varint(s)
        # cada input necesita parseo
        inputs = []
        for _ in range(num_inputs):
            inputs.append(TxIn.parsear(s))
        # num_outputs es un varint, usa read_varint(s)
        num_outputs = read_varint(s)
        # cada output necesita ser parseado
        outputs = []
        for _ in range(num_outputs):
            outputs.append(TxOut.parsear(s))
        # locktime is 4 bytes, little-endian
        locktime = little_endian_a_int(s.read(4))
        # return an instance of the class (cls(...))
        return cls(version, inputs, outputs, locktime)


class TxIn:
    def __init__(self, prev_tx, prev_index, script_sig, sequence):
        self.prev_tx = prev_tx
        self.prev_index = prev_index
        self.script_sig = Script.parsear(script_sig)
        self.sequence = sequence

    def __repr__(self):
        return '{}:{}'.format(
            self.prev_tx.hex(),
            self.prev_index,
        )

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea el tx_input al comienzo
        devuelve un objeto TxIn
        '''
        # s.read(n) devolverá n bytes
        # prev_tx es 32 bytes, little endian
        prev_tx = s.read(32)[::-1]
        # prev_index es 4 bytes, little endian, interprétalo como int
        prev_index = little_endian_a_int(s.read(4))
        # script_sig es un campo variable (longitud seguida de los datos)
        # obtén la longitud usando read_varint(s)
        script_sig_longitud = read_varint(s)
        script_sig = s.read(script_sig_longitud)
        # sequence tiene 4 bytes, little-endian, interprétalo como int
        sequence = little_endian_a_int(s.read(4))
        # devuelve una instancia de la clase (cls(...))
        return cls(prev_tx, prev_index, script_sig, sequence)


class TxOut:

    def __init__(self, cantidad, script_pubkey):
        self.cantidad = cantidad
        self.script_pubkey = Script.parsear(script_pubkey)

    def __repr__(self):
        return '{}:{}'.format(self.cantidad, self.script_pubkey)

    @classmethod
    def parsear(cls, s):
        '''TOma un stream de bytes y parsea la tx_output al comienzo
        devuelve un objeto TxOut
        '''
        # s.read(n) devolverá n bytes
        # cantidad son 8 bytes, little endian, interprétalo como int
        cantidad = little_endian_a_int(s.read(8))
        # script_pubkey es un campo variable (longitud seguida de los datos)
        # obtén la longitud usando read_varint(s)
        script_pubkey_longitud = read_varint(s)
        script_pubkey = s.read(script_pubkey_longitud)
        # devuelve una instancia de la clase (cls(...))
        return cls(cantidad, script_pubkey)


class PruebaTx(TestCase):

    def prueba_parsear_versión(self):
        raw_tx = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(raw_tx)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.version, 1)

    def prueba_parsear_inputs(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(len(tx.tx_ins), 1)
        want = bytes.fromhex('d1c789a9c60383bf715f3f6ad9d14b91fe55f3deb369fe5d9280cb1a01793f81')
        self.assertEqual(tx.tx_ins[0].prev_tx, want)
        self.assertEqual(tx.tx_ins[0].prev_index, 0)
        want = bytes.fromhex('483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a')
        self.assertEqual(tx.tx_ins[0].script_sig.serializar(), want)
        self.assertEqual(tx.tx_ins[0].sequence, 0xfffffffe)

    def prueba_parsear_outputs(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(len(tx.tx_outs), 2)
        want = 32454049
        self.assertEqual(tx.tx_outs[0].cantidad, want)
        want = bytes.fromhex('76a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac')
        self.assertEqual(tx.tx_outs[0].script_pubkey.serializar(), want)
        want = 10011545
        self.assertEqual(tx.tx_outs[1].cantidad, want)
        want = bytes.fromhex('76a9141c4bc762dd5423e332166702cb75f40df79fea1288ac')
        self.assertEqual(tx.tx_outs[1].script_pubkey.serializar(), want)

    def prueba_parsear_locktime(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.locktime, 410393)
