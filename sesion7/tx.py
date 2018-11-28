from io import BytesIO
from unittest import TestCase

import requests

from cce import ClavePrivada, PuntoS256, Firma
from ayudante import (
    decodificar_base58,
    doble_sha256,
    codificar_varint,
    int_a_little_endian,
    little_endian_a_int,
    read_varint,
    SIGHASH_ALL,
)
from script import script_p2pkh, Script


class Tx:

    def __init__(self, versión, tx_ins, tx_outs, locktime, testnet=False):
        self.versión = versión
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime
        self.testnet = testnet

    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'tx: {}\nversión: {}\ntx_ins:\n{}\ntx_outs:\n{}\nlocktime: {}\n'.format(
            self.hash().hex(),
            self.versión,
            tx_ins,
            tx_outs,
            self.locktime,
        )

    def hash(self):
        return doble_sha256(self.serializar())[::-1]

    @classmethod
    def parsear(cls, s, testnet=False):
        '''Toma un stream de bytes y parsea la transacción al comienzo
        devuelve un objeto Tx
        '''
        # s.read(n) devolverá n bytes
        # versión tiene 4 bytes, little-endian, interpretalo como int
        versión = little_endian_a_int(s.read(4))
        # num_inputs es un varint, usa read_varint(s)
        num_inputs = read_varint(s)
        # cada input necesita parseo
        inputs = []
        for _ in range(num_inputs):
            inputs.append(TxIn.parsear(s))
        # num_outputs es un varint, usa read_varint(s)
        num_outputs = read_varint(s)
        # cada output necesita parseo
        outputs = []
        for _ in range(num_outputs):
            outputs.append(TxOut.parsear(s))
        # locktime es 4 bytes, little-endian
        locktime = little_endian_a_int(s.read(4))
        # devuelve una instancia de la clase (cls(...))
        return cls(versión, inputs, outputs, locktime, testnet=testnet)

    def serializar(self):
        '''Devuelve la serialización en bytes de la transacción'''
        # serializar versión (4 bytes, little endian)
        res = int_a_little_endian(self.versión, 4)
        # codificar_varint sobre el número de inputs
        res += codificar_varint(len(self.tx_ins))
        # itera los inputs
        for tx_in in self.tx_ins:
            # serializar cada input
            res += tx_in.serializar()
        # codificar_varint sobre el número de outputs
        res += codificar_varint(len(self.tx_outs))
        # itera sobre los outputs
        for tx_out in self.tx_outs:
            # serializar cada output
            res += tx_out.serializar()
        # serializar locktime (4 bytes, little endian)
        res += int_a_little_endian(self.locktime, 4)
        return res

    def comisión(self):
        '''Devuelve la comisión de esta comisión en satoshi'''
        # inicializa input sum y output sum
        input_sum, output_sum = 0, 0
        # itera por los inputs
        for tx_in in self.tx_ins:
            # para cada input obtén el valor y añádelo a input sum
            input_sum += tx_in.valor(self.testnet)
        # itera los outputs
        for tx_out in self.tx_outs:
            # para cada output obtén la cantidad y añádela a output sum
            output_sum += tx_out.cantidad
        # devuelve input sum - output sum
        return input_sum - output_sum

    def sig_hash(self, índice_input, tipo_hash):
        '''Devuelve la representación entera del hash que debe ser firmado
        para index índice_input'''
        # crea una nueva serie de tx_ins (alt_tx_ins)
        alt_tx_ins = []
        # itera por los self.tx_ins
        for tx_in in self.tx_ins:
            # crea un nuevo TxIn que tenga un script_sig en blanco (b'') y añádelo a alt_tx_ins
            alt_tx_ins.append(TxIn(
                tx_previa=tx_in.tx_previa,
                índice_previo=tx_in.índice_previo,
                script_sig=Script([]),
                sequence=tx_in.sequence,
            ))
        # obtén el input en índice_input
        input_firmante = alt_tx_ins[índice_input]
        # obtén el script_pubkey del input
        script_pubkey = input_firmante.script_pubkey(self.testnet)
        # el script_sig del input_firmante debería ser script_pubkey
        input_firmante.script_sig = script_pubkey
        # crea una transaccción alternativa con las tx_ins modificadas
        alt_tx = self.__class__(
            versión=self.versión,
            tx_ins=alt_tx_ins,
            tx_outs=self.tx_outs,
            locktime=self.locktime)
        # añade el tipo_hash entero 4 bytes, little endian
        res = alt_tx.serializar() + int_a_little_endian(tipo_hash, 4)
        # obtén el doble_sha256 de la serialización de la tx
        s256 = doble_sha256(res)
        # convierte esto a entero big-endian usando usando int.from_bytes(x, 'big')
        return int.from_bytes(s256, 'big')

    def verificar_input(self, índice_input):
        '''Devuelve si el input tiene una firma válida'''
        # obtén el input relevante
        tx_in = self.tx_ins[índice_input]
        # parsea el punto desde el formato sec (tx_in.sec_pubkey())
        punto = PuntoS256.parsear(tx_in.sec_pubkey())
        # parsea la firma desde el formato der (tx_in.firma_der())
        firma = Firma.parsear(tx_in.firma_der())
        # obtén el tipo de hash desde el input (tx_in.tipo_hash())
        tipo_hash = tx_in.tipo_hash()
        # obtén el sig_hash (z)
        z = self.sig_hash(índice_input, tipo_hash)
        # usa punto.verificar sobre z y la firma
        return punto.verificar(z, firma)

    def firmar_input(self, índice_input, clave_privada, tipo_hash):
        '''Firma el input usando la clave privada'''
        # obtén el sig_hash (z)
        z = self.sig_hash(índice_input, tipo_hash)
        # obtén la firma der de z desde la clave privada
        der = clave_privada.firmar(z).der()
        # añade el tipo_hash a der (usa tipo_hash.to_bytes(1, 'big'))
        sig = der + tipo_hash.to_bytes(1, 'big')
        # calcula el sec
        sec = clave_privada.punto.sec()
        # inicializa un nuevo script con [sig, sec] como los elementos
        script_sig = Script([sig, sec])
        # cambia el script_sig del input al nuevo script
        self.tx_ins[índice_input].script_sig = script_sig
        # devuelve si sig es válida usando self.verificar_input
        return self.verificar_input(índice_input)

    def es_coinbase(self):
        '''Devuelve si esta transacción es coinbase o no'''
        # comprueba que hay exactamente 1 input
        if len(self.tx_ins) != 1:
            return False
        # obtén el primer input
        primer_input = self.tx_ins[0]
        # comprueba que la tx_previa del primer input es b'\x00' * 32 bytes
        if primer_input.tx_previa != b'\x00' * 32:
            return False
        # comprueba que el índice previo del primer input es 0xffffffff
        if primer_input.índice_previo != 0xffffffff:
            return False
        return True

    def altura_coinbase(self):
        '''Devuelve la altura del bloque en que está transacción coinbase está
        Devuelve None si esta transacción no es coinbase
        '''
        # si no es una transacción coinbase, devuelve None
        if not self.es_coinbase():
            return None
        # obtén el primer input
        primer_input = self.tx_ins[0]
        # obtén el primer elemento del script_sig (.script_sig.cosas[0])
        primer_elemento = primer_input.script_sig.cosas[0]
        # convierte el primer elemento desde little endian a int
        return little_endian_a_int(primer_elemento)


class TxIn:

    cache = {}

    def __init__(self, tx_previa, índice_previo, script_sig, sequence):
        self.tx_previa = tx_previa
        self.índice_previo = índice_previo
        self.script_sig = script_sig
        self.sequence = sequence

    def __repr__(self):
        return '{}:{}'.format(
            self.tx_previa.hex(),
            self.índice_previo,
        )

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea el tx_input al comienzo
        devuelve un objeto TxIn
        '''
        # s.read(n) devolverá n bytes
        # tx_previa es 32 bytes, little endian
        tx_previa = s.read(32)[::-1]
        # índice_previo es 4 bytes, little endian, interpretalo como int
        índice_previo = little_endian_a_int(s.read(4))
        # script_sig es un campo variable (longitud seguida de los datos)
        # puedes usar Script.parsear para tener el script real
        script_sig = Script.parsear(s)
        # sequence es 4 bytes, little-endian, interpretalo como entero
        sequence = little_endian_a_int(s.read(4))
        # devuelve una instancia de la clase (cls(...))
        return cls(tx_previa, índice_previo, script_sig, sequence)

    def serializar(self):
        '''Devuelve la serialización en bytes del input de la transacción'''
        # serializar tx_previa, little endian
        res = self.tx_previa[::-1]
        # serializar índice_previo, 4 bytes, little endian
        res += int_a_little_endian(self.índice_previo, 4)
        # serializar el script_sig
        res += self.script_sig.serializar()
        # serializar sequence, 4 bytes, little endian
        res += int_a_little_endian(self.sequence, 4)
        return res

    @classmethod
    def obtener_url(cls, testnet=False):
        if testnet:
            return 'http://tbtc.programmingblockchain.com:18332'
        else:
            return 'http://btc.programmingblockchain.com:8332'

    def obtener_tx(self, testnet=False):
        if self.tx_previa not in self.cache:
            url = '{}/rest/tx/{}.hex'.format(
                self.obtener_url(testnet), self.tx_previa.hex())
            response = requests.get(url)
            raw = bytes.fromhex(response.text.strip())
            if raw[4] == 0:
                 # esto es segwit, así que conviértelo a no-segwit
                raw = raw[:4] + raw[6:]
            stream = BytesIO(raw)
            tx = Tx.parsear(stream)
            self.cache[self.tx_previa] = tx
        return self.cache[self.tx_previa]

    def valor(self, testnet=False):
        '''Obtén el valor outpoint mirando el hash de la tx
        Devuelve una cantidad en satoshi
        '''
        # usa self.obtener_tx para tener la transacción
        tx = self.obtener_tx(testnet=testnet)
        # obtén el output en self.índice_previo
        # devuelve el atributo cantidad
        return tx.tx_outs[self.índice_previo].cantidad

    def script_pubkey(self, testnet=False):
        '''Obtén el scriptPubKey mirando el hash de la tx
        Devuelve un objeto Script
        '''
        # usa self.obtener_tx para obtener la transacción
        tx = self.obtener_tx(testnet=testnet)
        # obtén el output en self.índice_previo
        # devuelve el atributo script_pubkey
        return tx.tx_outs[self.índice_previo].script_pubkey

    def firma_der(self):
        '''devuelve una firma en formato DER y un tipo_hash si el script_sig
        tiene una firma'''
        firma = self.script_sig.firma()
        # el último byte es el tipo_hash, el resto es la firma
        return firma[:-1]

    def tipo_hash(self):
        '''devuelve una firma en formato DER y tipo_hash si el script_sig
        tiene una firma'''
        firma = self.script_sig.firma()
        # el último byte es el tipo_hash, el resto es la firma
        return firma[-1]

    def sec_pubkey(self):
        '''devuelve el formato SEC público si el script_sig tiene uno'''
        return self.script_sig.sec_pubkey()


class TxOut:

    def __init__(self, cantidad, script_pubkey):
        self.cantidad = cantidad
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return '{}:{}'.format(self.cantidad, self.script_pubkey)

    @classmethod
    def parsear(cls, s):
        '''Toma un stream de bytes y parsea el tx_output al comienzo
        devueve un objeto TxOut
        '''
        # s.read(n) devolverá n bytes
        # cantidad es 8 bytes, little endian, interpretalo como int
        cantidad = little_endian_a_int(s.read(8))
        # script_pubkey es un campo variable (longitud seguida de los datos)
        # puedes usar Script.parsear para obtener el script auténtico
        script_pubkey = Script.parsear(s)
        # devuelve una instancia de la clase (cls(...))
        return cls(cantidad, script_pubkey)

    def serializar(self):
        '''Devuelve la serialización en bytes del output de la transacción'''
        # serializar cantidad, 8 bytes, little endian
        res = int_a_little_endian(self.cantidad, 8)
        # serializar el script_pubkey
        res += self.script_pubkey.serializar()
        return res


class PruebaTx(TestCase):

    def prueba_parsear_versión(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.versión, 1)

    def prueba_parsear_inputs(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(len(tx.tx_ins), 1)
        want = bytes.fromhex('d1c789a9c60383bf715f3f6ad9d14b91fe55f3deb369fe5d9280cb1a01793f81')
        self.assertEqual(tx.tx_ins[0].tx_previa, want)
        self.assertEqual(tx.tx_ins[0].índice_previo, 0)
        want = bytes.fromhex('6b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a')
        self.assertEqual(tx.tx_ins[0].script_sig.serializar(), want)
        self.assertEqual(tx.tx_ins[0].sequence, 0xfffffffe)

    def prueba_parsear_outputs(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(len(tx.tx_outs), 2)
        want = 32454049
        self.assertEqual(tx.tx_outs[0].cantidad, want)
        want = bytes.fromhex('1976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac')
        self.assertEqual(tx.tx_outs[0].script_pubkey.serializar(), want)
        want = 10011545
        self.assertEqual(tx.tx_outs[1].cantidad, want)
        want = bytes.fromhex('1976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac')
        self.assertEqual(tx.tx_outs[1].script_pubkey.serializar(), want)

    def prueba_parsear_locktime(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.locktime, 410393)

    def prueba_firma_der(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        want = '3045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed'
        der = tx.tx_ins[0].firma_der()
        tipo_hash = tx.tx_ins[0].tipo_hash()
        self.assertEqual(der.hex(), want)
        self.assertEqual(tipo_hash, SIGHASH_ALL)

    def prueba_sec_pubkey(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        want = '0349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a'
        self.assertEqual(tx.tx_ins[0].sec_pubkey().hex(), want)

    def prueba_serializar(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.serializar(), tx_bruta)

    def prueba_input_valor(self):
        tx_hash = 'd1c789a9c60383bf715f3f6ad9d14b91fe55f3deb369fe5d9280cb1a01793f81'
        index = 0
        want = 42505594
        tx_in = TxIn(
            tx_previa=bytes.fromhex(tx_hash),
            índice_previo=index,
            script_sig=Script([]),
            sequence=0,
        )
        self.assertEqual(tx_in.valor(), want)

    def prueba_input_pubkey(self):
        tx_hash = 'd1c789a9c60383bf715f3f6ad9d14b91fe55f3deb369fe5d9280cb1a01793f81'
        index = 0
        tx_in = TxIn(
            tx_previa=bytes.fromhex(tx_hash),
            índice_previo=index,
            script_sig=Script([]),
            sequence=0,
        )
        want = bytes.fromhex('1976a914a802fc56c704ce87c42d7c92eb75e7896bdc41ae88ac')
        self.assertEqual(tx_in.script_pubkey().serializar(), want)

    def prueba_comisión(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.comisión(), 40000)
        tx_bruta = bytes.fromhex('010000000456919960ac691763688d3d3bcea9ad6ecaf875df5339e148a1fc61c6ed7a069e010000006a47304402204585bcdef85e6b1c6af5c2669d4830ff86e42dd205c0e089bc2a821657e951c002201024a10366077f87d6bce1f7100ad8cfa8a064b39d4e8fe4ea13a7b71aa8180f012102f0da57e85eec2934a82a585ea337ce2f4998b50ae699dd79f5880e253dafafb7feffffffeb8f51f4038dc17e6313cf831d4f02281c2a468bde0fafd37f1bf882729e7fd3000000006a47304402207899531a52d59a6de200179928ca900254a36b8dff8bb75f5f5d71b1cdc26125022008b422690b8461cb52c3cc30330b23d574351872b7c361e9aae3649071c1a7160121035d5c93d9ac96881f19ba1f686f15f009ded7c62efe85a872e6a19b43c15a2937feffffff567bf40595119d1bb8a3037c356efd56170b64cbcc160fb028fa10704b45d775000000006a47304402204c7c7818424c7f7911da6cddc59655a70af1cb5eaf17c69dadbfc74ffa0b662f02207599e08bc8023693ad4e9527dc42c34210f7a7d1d1ddfc8492b654a11e7620a0012102158b46fbdff65d0172b7989aec8850aa0dae49abfb84c81ae6e5b251a58ace5cfeffffffd63a5e6c16e620f86f375925b21cabaf736c779f88fd04dcad51d26690f7f345010000006a47304402200633ea0d3314bea0d95b3cd8dadb2ef79ea8331ffe1e61f762c0f6daea0fabde022029f23b3e9c30f080446150b23852028751635dcee2be669c2a1686a4b5edf304012103ffd6f4a67e94aba353a00882e563ff2722eb4cff0ad6006e86ee20dfe7520d55feffffff0251430f00000000001976a914ab0c0b2e98b1ab6dbf67d4750b0a56244948a87988ac005a6202000000001976a9143c82d7df364eb6c75be8c80df2b3eda8db57397088ac46430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.comisión(), 140500)

    def prueba_sig_hash(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        tipo_hash = SIGHASH_ALL
        want = int('27e0c5994dec7824e56dec6b2fcb342eb7cdb0d0957c2fce9882f715e85d81a6', 16)
        self.assertEqual(tx.sig_hash(0, tipo_hash), want)

    def prueba_verificar_input(self):
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertTrue(tx.verificar_input(0))

    def prueba_firmar_input(self):
        clave_privada = ClavePrivada(secreto=8675309)
        tx_ins = []
        tx_previa = bytes.fromhex('0025bc3c0fa8b7eb55b9437fdbd016870d18e0df0ace7bc9864efc38414147c8')
        tx_ins.append(TxIn(
            tx_previa=tx_previa,
            índice_previo=0,
            script_sig=Script([]),
            sequence=0xffffffff,
        ))
        tx_outs = []
        h160 = decodificar_base58('mzx5YhAH9kNHtcN481u6WkjeHjYtVeKVh2')
        tx_outs.append(TxOut(cantidad=int(0.99 * 100000000), script_pubkey=script_p2pkh(h160)))
        h160 = decodificar_base58('mnrVtF8DWjMu839VW3rBfgYaAfKk8983Xf')
        tx_outs.append(TxOut(cantidad=int(0.1 * 100000000), script_pubkey=script_p2pkh(h160)))

        tx = Tx(
            versión=1,
            tx_ins=tx_ins,
            tx_outs=tx_outs,
            locktime=0,
            testnet=True,
        )
        self.assertTrue(tx.firmar_input(0, clave_privada, SIGHASH_ALL))

    def prueba_es_coinbase(self):
        tx_bruta = bytes.fromhex('01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5e03d71b07254d696e656420627920416e74506f6f6c20626a31312f4542312f4144362f43205914293101fabe6d6d678e2c8c34afc36896e7d9402824ed38e856676ee94bfdb0c6c4bcd8b2e5666a0400000000000000c7270000a5e00e00ffffffff01faf20b58000000001976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac00000000')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertTrue(tx.es_coinbase())

    def prueba_altura_coinbase(self):
        tx_bruta = bytes.fromhex('01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5e03d71b07254d696e656420627920416e74506f6f6c20626a31312f4542312f4144362f43205914293101fabe6d6d678e2c8c34afc36896e7d9402824ed38e856676ee94bfdb0c6c4bcd8b2e5666a0400000000000000c7270000a5e00e00ffffffff01faf20b58000000001976a914338c84849423992471bffb1a54a8d9b1d69dc28a88ac00000000')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertEqual(tx.altura_coinbase(), 465879)
        tx_bruta = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')
        stream = BytesIO(tx_bruta)
        tx = Tx.parsear(stream)
        self.assertIsNone(tx.altura_coinbase())
