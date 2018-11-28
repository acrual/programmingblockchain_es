import math

from unittest import TestCase

from ayudante import (
    padre_merkle,
)


class ArbolMerkle:

    def __init__(self, total):
        self.total = total
        # computa la profundidad máxima math.ceil(math.log(self.total, 2))
        self.profundidad_máxima = math.ceil(math.log(self.total, 2))
        # inicializa el atributo nodos para mantener el árbol actual
        self.nodos = []
        # haz un bucle por el número de niveles (profundidad_máxima+1)
        for profundidad in range(self.profundidad_máxima + 1):
            # el número de cosas a esta profundidad es
            # math.ceil(self.total / 2**(self.profundidad_máxima - profundidad))
            num_cosas = math.ceil(self.total / 2**(self.profundidad_máxima - profundidad))
            # crea la lista de hashes de este nivel con el número correcto de cosas
            nivel_hashes = [None] * num_cosas
            # añade los hashes de este nivel al árbol de merkle
            self.nodos.append(nivel_hashes)
        # establece el pointer hacia la raiz (profundidad=0, índice=0)
        self.profundidad_actual = 0
        self.indice_actual = 0

    def __repr__(self):
        res = ''
        for profundidad, nivel in enumerate(self.nodos):
            for índice, h in enumerate(nivel):
                corto = '{}...'.format(h.hex()[:8])
                if profundidad == self.profundidad_actual and índice == self.indice_actual:
                    res += '*{}*, '.format(corto[:-2])
                else:
                    res += '{}, '.format(corto)
            res += '\n'
        return res

    def subir(self):
        # reduce profundidad en 1 y divide el índice a la mitad
        self.profundidad_actual -= 1
        self.indice_actual //= 2

    def izquierda(self):
        # incrementa la profundidad en 1 y dobla el índice
        self.profundidad_actual += 1
        self.indice_actual *= 2

    def derecha(self):
        # incrementa profundidad en 1 y dobla el índice + 1
        self.profundidad_actual += 1
        self.indice_actual = self.indice_actual * 2 + 1

    def raiz(self):
        return self.nodos[0][0]

    def establecer_nodo_actual(self, valor):
        self.nodos[self.profundidad_actual][self.indice_actual] = valor

    def obtener_nodo_actual(self):
        return self.nodos[self.profundidad_actual][self.indice_actual]

    def obtener_nodo_izquierdo(self):
        return self.nodos[self.profundidad_actual + 1][self.indice_actual * 2]

    def obtener_nodo_derecho(self):
        return self.nodos[self.profundidad_actual + 1][self.indice_actual * 2 + 1]

    def es_hoja(self):
        return self.profundidad_actual == self.profundidad_máxima

    def existe_derecho(self):
        return len(self.nodos[self.profundidad_actual + 1]) > self.indice_actual * 2 + 1

    def poblar_árbol(self, flag_bits, hashes):
        # poblar hasta que tengamos la raiz
        while self.raiz() is None:
            # si tenemos una hoja, sabemos el hash de esta posición
            if self.es_hoja():
                # obtén el siguiente bit desde flag_bits: flag_bits.pop(0)
                flag_bits.pop(0)
                # establece el nodo actual en el árbol de merkle hacia el siguiente hash: hashes.pop(0)
                self.establecer_nodo_actual(hashes.pop(0))
                # sube un nivel
                self.subir()
            # else
            else:
                # obtén el hash izquierdo
                hash_izquierdo = self.obtener_nodo_izquierdo()
                # Ejercicio 6.2: obtén el hash derecho
                # si no tenemos el hash izquierdo
                if hash_izquierdo is None:
                    # si el siguiente flag bit es 0, el siguiente hash es nuestro nodo actual
                    if flag_bits.pop(0) == 0:
                        # establece el nodo actual para ser el siguiente hash
                        self.establecer_nodo_actual(hashes.pop(0))
                        # el sub-árbol no necesita cálculo, ve arriba
                        self.subir()
                    # else
                    else:
                        # ve al nodo izquierdo
                        self.izquierda()
                # Ejercicio 6.2: si no tenemos el hash derecho
                    # ve al nodo derecho
                # Ejercicio 6.2: else
                    # combina los hashes izquierdo y derecho
                    # hemos completado este sub-árbol, ve arriba
                # Ejercicio 7.2: si el hash derecho existe
                elif self.existe_derecho():
                    # obtén el hash derecho
                    hash_derecho = self.obtener_nodo_derecho()
                    # si no tenemos el hash derecho
                    if hash_derecho is None:
                        # ve al nodo derecho
                        self.derecha()
                    # else
                    else:
                        # combina los hashes izquierdo y derecho
                        self.establecer_nodo_actual(padre_merkle(hash_izquierdo, hash_derecho))
                        # hemos completado este sub-árbol, ve arriba
                        self.subir()
                # else
                else:
                    # combina los hashes izquierdo y derecho
                    self.establecer_nodo_actual(padre_merkle(hash_izquierdo, hash_izquierdo))
                    # hemos completado este sub-árbol, ve arriba
                    self.subir()
        if len(hashes) != 0:
            raise RuntimeError('no todos los hashes están consumidos {}'.format(len(hashes)))
        for flag_bit in flag_bits:
            if flag_bit != 0:
                raise RuntimeError('no todos los flag bits están consumidos')


class PruebaÁrbolMerkle(TestCase):

    def prueba_init(self):
        árbol= ArbolMerkle(9)
        self.assertEqual(len(árbol.nodos[0]), 1)
        self.assertEqual(len(árbol.nodos[1]), 2)
        self.assertEqual(len(árbol.nodos[2]), 3)
        self.assertEqual(len(árbol.nodos[3]), 5)
        self.assertEqual(len(árbol.nodos[4]), 9)

    def prueba_poblar_árbol_1(self):
        hex_hashes = [
            "9745f7173ef14ee4155722d1cbf13304339fd00d900b759c6f9d58579b5765fb",
            "5573c8ede34936c29cdfdfe743f7f5fdfbd4f54ba0705259e62f39917065cb9b",
            "82a02ecbb6623b4274dfcab82b336dc017a27136e08521091e443e62582e8f05",
            "507ccae5ed9b340363a0e6d765af148be9cb1c8766ccc922f83e4ae681658308",
            "a7a4aec28e7162e1e9ef33dfa30f0bc0526e6cf4b11a576f6c5de58593898330",
            "bb6267664bd833fd9fc82582853ab144fece26b7a8a5bf328f8a059445b59add",
            "ea6d7ac1ee77fbacee58fc717b990c4fcccf1b19af43103c090f601677fd8836",
            "457743861de496c429912558a106b810b0507975a49773228aa788df40730d41",
            "7688029288efc9e9a0011c960a6ed9e5466581abf3e3a6c26ee317461add619a",
            "b1ae7f15836cb2286cdd4e2c37bf9bb7da0a2846d06867a429f654b2e7f383c9",
            "9b74f89fa3f93e71ff2c241f32945d877281a6a50a6bf94adac002980aafe5ab",
            "b3a92b5b255019bdaf754875633c2de9fec2ab03e6b8ce669d07cb5b18804638",
            "b5c0b915312b9bdaedd2b86aa2d0f8feffc73a2d37668fd9010179261e25e263",
            "c9d52c5cb1e557b92c84c52e7c4bfbce859408bedffc8a5560fd6e35e10b8800",
            "c555bc5fc3bc096df0a0c9532f07640bfb76bfe4fc1ace214b8b228a1297a4c2",
            "f9dbfafc3af3400954975da24eb325e326960a25b87fffe23eef3e7ed2fb610e",
        ]
        árbol= ArbolMerkle(len(hex_hashes))
        hashes = [bytes.fromhex(h) for h in hex_hashes]
        árbol.poblar_árbol([1] * 31, hashes)
        raiz = '597c4bafe3832b17cbbabe56f878f4fc2ad0f6a402cee7fa851a9cb205f87ed1'
        self.assertEqual(árbol.raiz().hex(), raiz)

    def prueba_poblar_árbol_2(self):
        hex_hashes = [
            '42f6f52f17620653dcc909e58bb352e0bd4bd1381e2955d19c00959a22122b2e',
            '94c3af34b9667bf787e1c6a0a009201589755d01d02fe2877cc69b929d2418d4',
            '959428d7c48113cb9149d0566bde3d46e98cf028053c522b8fa8f735241aa953',
            'a9f27b99d5d108dede755710d4a1ffa2c74af70b4ca71726fa57d68454e609a2',
            '62af110031e29de1efcad103b3ad4bec7bdcf6cb9c9f4afdd586981795516577',
        ]
        árbol= ArbolMerkle(len(hex_hashes))
        hashes = [bytes.fromhex(h) for h in hex_hashes]
        árbol.poblar_árbol([1] * 11, hashes)
        raiz = 'a8e8bd023169b81bc56854137a135b97ef47a6a7237f4c6e037baed16285a5ab'
        self.assertEqual(árbol.raiz().hex(), raiz)
