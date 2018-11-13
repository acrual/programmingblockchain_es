from io import BytesIO
from random import randint
from unittest import TestCase

from ayudante import doble_sha256, codificar_base58, hash160


class ElementoCampo:

    def __init__(self, num, primo):
        self.num = num
        self.primo = primo
        if self.num >= self.primo or self.num < 0:
            error = 'Num {} no está en el rango de campo 0 a {}'.format(
                self.num, self.primo-1)
            raise RuntimeError(error)

    def __eq__(self, otro):
        if otro is None:
            return False
        return self.num == otro.num and self.primo == otro.primo

    def __ne__(self, otro):
        if otro is None:
            return True
        return self.num != otro.num or self.primo != otro.primo

    def __repr__(self):
        return 'ElementoCampo{}({})'.format(self.primo, self.num)

    def __add__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Los números primos deben ser el mismo')
        # self.num y otro.num son los valores reales
        num = (self.num + otro.num) % self.primo
        # self.primo es contra lo que debes calcular el módulo
        primo = self.primo
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)

    def __sub__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Los números primos deben ser el mismo')
        # self.num y otro.num son los valores reales
        num = (self.num - otro.num) % self.primo
        # self.primo es contra lo que debes calcular el módulo
        primo = self.primo
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)

    def __mul__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Ambos primos deben ser el mismo')
        # self.num y otro.num son los valores reales
        num = (self.num * otro.num) % self.primo
        # self.primo es contra lo que debes calcular el módulo
        primo = self.primo
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)

    def __rmul__(self, coeficiente):
        num = (self.num * coeficiente) % self.primo
        return self.__class__(num=num, primo=self.primo)

    def __pow__(self, n):
        # recuerda el teorema pequeño de Fermat:
        # self.num**(p-1) % p == 1
        # te convendrá usar el operador % sobre n
        primo = self.primo
        num = pow(self.num, n % (primo-1), primo)
        return self.__class__(num, primo)

    def __truediv__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Los números primos deben ser iguales')
        # self.num and otro.num son los valores reales
        num = (self.num * pow(otro.num, self.primo - 2, self.primo)) % self.primo
        # self.prime es contra lo que querrás calcular el módulo
        primo = self.primo
        # usa el teorema pequeño de Fermat:
        # self.num**(p-1) % p == 1
        # que implica:
        # 1/n == pow(n, p-2, p)
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)



class PruebaElementoCampo(TestCase):

    def prueba_sumar(self):
        a = ElementoCampo(2, 31)
        b = ElementoCampo(15, 31)
        self.assertEqual(a+b, ElementoCampo(17, 31))
        a = ElementoCampo(17, 31)
        b = ElementoCampo(21, 31)
        self.assertEqual(a+b, ElementoCampo(7, 31))

    def prueba_restar(self):
        a = ElementoCampo(29, 31)
        b = ElementoCampo(4, 31)
        self.assertEqual(a-b, ElementoCampo(25, 31))
        a = ElementoCampo(15, 31)
        b = ElementoCampo(30, 31)
        self.assertEqual(a-b, ElementoCampo(16, 31))

    def prueba_mul(self):
        a = ElementoCampo(24, 31)
        b = ElementoCampo(19, 31)
        self.assertEqual(a*b, ElementoCampo(22, 31))

    def prueba_rmul(self):
        a = ElementoCampo(24, 31)
        b = 2
        self.assertEqual(b*a, a+a)

    def prueba_pow(self):
        a = ElementoCampo(17, 31)
        self.assertEqual(a**3, ElementoCampo(15, 31))
        a = ElementoCampo(5, 31)
        b = ElementoCampo(18, 31)
        self.assertEqual(a**5 * b, ElementoCampo(16, 31))

    def prueba_div(self):
        a = ElementoCampo(3, 31)
        b = ElementoCampo(24, 31)
        self.assertEqual(a/b, ElementoCampo(4, 31))
        a = ElementoCampo(17, 31)
        self.assertEqual(a**-3, ElementoCampo(29, 31))
        a = ElementoCampo(4, 31)
        b = ElementoCampo(11, 31)
        self.assertEqual(a**-4*b, ElementoCampo(13, 31))



class Punto:

    def __init__(self, x, y, a, b):
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        # cuando x es None e y también None, representa el punto en el infinito
        # Comprueba si esto es así pues en caso contrario la ecuación de abajo no tendrá sentido
        # cuando ambos valores sean None
        if self.x is None and self.y is None:
            return
        # asegúrate de que se satisface la ecuación de la curva elíptica
        # y**2 == x**3 + a*x + b
        if self.y**2 != self.x**3 + a*x + b:
        # en caso contrario, lanza un RuntimeError
            raise RuntimeError('({}, {}) no está en la curva'.format(self.x, self.y))

    def __eq__(self, otro):
        return self.x == otro.x and self.y == otro.y \
            and self.a == otro.a and self.b == otro.b

    def __ne__(self, otro):
        return self.x != otro.x or self.y != otro.y \
            or self.a != otro.a or self.b != otro.b

    def __repr__(self):
        if self.x is None:
            return 'Punto(infinito)'
        else:
            return 'Punto({},{})_{}'.format(self.x.num, self.y.num, self.x.primo)

    def __add__(self, otro):
        if self.a != otro.a or self.b != otro.b:
            raise RuntimeError('Los puntos {}, {} no están en la misma curva'.format(self, otro))
        # Caso 0.0: self es el punto en el infinito, devuelve otro
        if self.x is None:
            return otro
        # Caso 0.1: otro es el punto en el infinito, devuelve self
        if otro.x is None:
            return self

        # Case 1: self.x == otro.x, self.y != otro.y
        # El resultado es el punto en el infinito
        if self.x == otro.x and self.y != otro.y:
        # Recuerda devolver una instancia de esta clase:
        # self.__class__(x, y, a, b)
            return self.__class__(None, None, self.a, self.b)
 
        # Caso 2: self.x != otro.x
        if self.x != otro.x:
        # Fórmula (x3,y3)==(x1,y1)+(x2,y2)
        # s=(y2-y1)/(x2-x1)
            s = (otro.y - self.y) / (otro.x - self.x)
        # x3=s**2-x1-x2
            x = s**2 - self.x - otro.x
        # y3=s*(x1-x3)-y1
            y = s*(self.x-x) - self.y
        # Recuerda devolver una instancia de esta clase:
        # self.__class__(x, y, a, b)
            return self.__class__(x, y, self.a, self.b)

        # Caso 3: self.x == otro.x, self.y == otro.y
        else:
        # Fórmula (x3,y3)=(x1,y1)+(x1,y1)
        # s=(3*x1**2+a)/(2*y1)
            s = (3*self.x**2 + self.a) / (2*self.y)
        # x3=s**2-2*x1
            x = s**2 - 2*self.x
        # y3=s*(x1-x3)-y1
            y = s*(self.x-x) - self.y
        # Recuerda devolver una instancia de esta clase:
        # self.__class__(x, y, a, b)
            return self.__class__(x, y, self.a, self.b)

    def __rmul__(self, coeficiente):
        # rmul calcula coeficiente * self
        # implementa de manera inocente:
        # empieza con producto desde 0 (punto en el infinito)
        # use: self.__class__(None, None, a, b)
        producto = self.__class__(None, None, self.a, self.b)
        # haz bucle coeficiente veces
        # usa: for _ in range(coeficiente):
        for _ in range(coeficiente):
            # continua sumando una y otra vez
            producto += self
        # devuelve el producto
        return producto
        # Extra:
        # una técnica más avanzada es doblando el punto
        # encuentra la representación binaria del coeficiente
        # sigue doblando el punto y si el bit está ahí para coeficiente
        # añade el actual.
        # recuerda devolver una instancia de la clase


class PruebaPunto(TestCase):

    def prueba_en_curva(self):
        with self.assertRaises(RuntimeError):
            Punto(x=-2, y=4, a=5, b=7)
        # estos no deberían lanzar un error
        Punto(x=3, y=-7, a=5, b=7)
        Punto(x=18, y=77, a=5, b=7)

    def prueba_suma0(self):
        a = Punto(x=None, y=None, a=5, b=7)
        b = Punto(x=2, y=5, a=5, b=7)
        c = Punto(x=2, y=-5, a=5, b=7)
        self.assertEqual(a+b, b)
        self.assertEqual(b+a, b)
        self.assertEqual(b+c, a)
    
    def prueba_suma1(self):
        a = Punto(x=3, y=7, a=5, b=7)
        b = Punto(x=-1, y=-1, a=5, b=7)
        self.assertEqual(a+b, Punto(x=2, y=-5, a=5, b=7))

    def prueba_suma2(self):
        a = Punto(x=-1, y=1, a=5, b=7)
        self.assertEqual(a+a, Punto(x=18, y=-77, a=5, b=7))


class PruebaCCE(TestCase):

    def prueba_en_curva(self):
        # prueba si lo siguientes puntos están o no en la curva
        # y^2=x^3-7 sobre F_223:
        # (192,105) (17,56) (200,119) (1,193) (42,99)
        # los que no estén deberían activar un RuntimeError
        primo = 223
        a = ElementoCampo(0, primo)
        b = ElementoCampo(7, primo)
        
        puntos_válidos = ((192,105), (17,56), (1,193))
        puntos_inválidos = ((200,119), (42,99))
        
        # itera sobre los puntos válidos
        for x_bruto, y_bruto in puntos_válidos:
            # Inicializa los puntos así:
            # x = ElementoCampo(x_raw, prime)
            # y = ElementoCampo(y_raw, prime)
            # Punto(x, y, a, b)
            x = ElementoCampo(x_bruto, primo)
            y = ElementoCampo(y_bruto, primo)
            # Crear el punto no debería dar error
            Punto(x, y, a, b)

        # itera sobre los puntos inválidos
        for x_bruto, y_bruto in puntos_inválidos:
            # Inicializa los puntos de esta manera:
            # x = ElementoCampo(x_bruto, primo)
            # y = ElementoCampo(y_bruto, primo)
            # Punto(x, y, a, b)
            x = ElementoCampo(x_bruto, primo)
            y = ElementoCampo(y_bruto, primo)
            # comprueba que crear el punto resulta en un RuntimeError
            # with self.assertRaises(RuntimeError):
            #     Punto(x, y, a, b)
            with self.assertRaises(RuntimeError):
                Punto(x, y, a, b)

    def prueba_suma1(self):
        # comprueba las siguientes sumas en la curva y^2=x^3-7 sobre F_223:
        # (192,105) + (17,56)
        # (47,71) + (117,141)
        # (143,98) + (76,66)
        primo = 223
        a = ElementoCampo(0, primo)
        b = ElementoCampo(7, primo)

        sumas = (
            # (x1, y1, x2, y2, x3, y3)         
            (192, 105, 17, 56, 170, 142),
            (47, 71, 117, 141, 60, 139),
            (143, 98, 76, 66, 47, 71),
        )
        # iterar sobre las sumas
        for x1_bruto, y1_bruto, x2_bruto, y2_bruto, x3_bruto, y3_bruto in sumas:
            # Inicializa puntos así:
            # x1 = ElementoCampo(x1_bruto, primo)
            # y1 = ElementoCampo(y1_bruto, primo)
            # p1 = Punto(x1, y1, a, b)
            # x2 = ElementoCampo(x2_bruto, primo)
            # y2 = ElementoCampo(y2_bruto, primo)
            # p2 = Punto(x2, y2, a, b)
            # x3 = ElementoCampo(x3_bruto, primo)
            # y3 = ElementoCampo(y3_bruto, primo)
            # p3 = Punto(x3, y3, a, b)
            x1 = ElementoCampo(x1_bruto, primo)
            y1 = ElementoCampo(y1_bruto, primo)
            p1 = Punto(x1, y1, a, b)
            x2 = ElementoCampo(x2_bruto, primo)
            y2 = ElementoCampo(y2_bruto, primo)
            p2 = Punto(x2, y2, a, b)
            x3 = ElementoCampo(x3_bruto, primo)
            y3 = ElementoCampo(y3_bruto, primo)
            p3 = Punto(x3, y3, a, b)
            # check that p1 + p2 == p3
            self.assertEqual(p1+p2, p3)

    def prueba_rmul(self):
        # prueba las siguientes multiplicaciones escalares
        # 2*(192,105)
        # 2*(143,98)
        # 2*(47,71)
        # 4*(47,71)
        # 8*(47,71)
        # 21*(47,71)
        primo = 223
        a = ElementoCampo(0, primo)
        b = ElementoCampo(7, primo)

        multiplicaciones = (
            # (coeficiente, x1, y1, x2, y2)
            (2, 192, 105, 49, 71),
            (2, 143, 98, 64, 168),
            (2, 47, 71, 36, 111),
            (4, 47, 71, 194, 51),
            (8, 47, 71, 116, 55),
            (21, 47, 71, None, None),
        )

        # itera las multiplicaciones
        for s, x1_bruto, y1_bruto, x2_bruto, y2_bruto in multiplicaciones:
            # Inicializa los puntos así:
            # x1 = ElementoCampo(x1_bruto, primo)
            # y1 = ElementoCampo(y1_bruto, primo)
            # p1 = Punto(x1, y1, a, b)
            x1 = ElementoCampo(x1_bruto, primo)
            y1 = ElementoCampo(y1_bruto, primo)
            p1 = Punto(x1, y1, a, b)
            # inicializa el segundo punto según sea el punto en el infinito o no
            # x2 = ElementoCampo(x2_bruto, primo)
            # y2 = ElementoCampo(y2_bruto, primo)
            # p2 = Punto(x2, y2, a, b)
            if x2_bruto is None:
                p2 = Punto(None, None, a, b)
            else:
                x2 = ElementoCampo(x2_bruto, primo)
                y2 = ElementoCampo(y2_bruto, primo)
                p2 = Punto(x2, y2, a, b)
        
            # check that the product is equal to the expected point
            self.assertEqual(s*p1, p2)        


A = 0
B = 7
P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class CampoS256(ElementoCampo):

    def __init__(self, num, primo=None):
        super().__init__(num=num, primo=P)

    def hex(self):
        return '{:x}'.format(self.num).zfill(64)

    def __repr__(self):
        return self.hex()


class PuntoS256(Punto):
    bits = 256

    def __init__(self, x, y, a=None, b=None):
        a, b = CampoS256(A), CampoS256(B)
        if x is None:
            super().__init__(x=None, y=None, a=a, b=b)
        elif type(x) == int:
            super().__init__(x=CampoS256(x), y=CampoS256(y), a=a, b=b)
        else:
            super().__init__(x=x, y=y, a=a, b=b)

    def __repr__(self):
        if self.x is None:
            return 'PuntoS256(infinito)'
        else:
            return 'PuntoS256({},{})'.format(self.x, self.y)

    def __rmul__(self, coeficiente):
        # calcularemos el módulo de N para hacer esto más simple
        coef = coeficiente % N
        # actual pasará por una expansión binaria
        actual = self
        # res es lo que devolvemos y lo empezamos en cero
        res = PuntoS256(None, None)
        # doblamos 256 veces y añadimos allí donde haya un 1 en la representación binaria del coeficiente
        # representation of coefficient
        for i in range(self.bits):
            if coef & 1:
                res += actual
            actual += actual
            # movemos el coeficiente hacia la derecha
            coef >>= 1
        return res

    def sec(self, comprimido=True):
        # devuelve la versión binaria del formato sec, NO hex
        # si está comprimido, empieza con b'\x02' si self.y.num es par, b'\x03' si self.y es impar
        # entonces self.x.num
        # recuerda, debes convertir self.x.num/self.y.num a binario (some_integer.to_bytes(32, 'big'))
        if comprimido:
            if self.y.num % 2 == 0:
                return b'\x02' + self.x.num.to_bytes(32, 'big')
            else:
                return b'\x03' + self.x.num.to_bytes(32, 'big')
        else:
        # si no está comprimido, empieza con b'\x04' seguido de self.x y entonces self.y
            return b'\x04' + self.x.num.to_bytes(32, 'big') + self.y.num.to_bytes(32, 'big')

    def dire(self, comprimido=True, testnet=False):
        '''Devuelve la cadena dirección'''
        # get the sec
        sec = self.sec(comprimido)
        # hash160 the sec
        h160 = hash160(sec)
        # bruto es el hash160 antepuesto por b'\x00' para mainnet, b'\x6f' para testnet
        if testnet:
            prefijo = b'\x6f'
        else:
            prefijo = b'\x00'
        bruto = prefijo + h160
        # checksum son los primeros 4 bytes del doble_sha256 de bruto
        checksum = doble_sha256(bruto)[:4]
        # haz codificar_base58 de bruto + checksum
        dire = codificar_base58(bruto+checksum)
        # devuelve como cadena, puedes usar .decode('ascii') para hacer esto.
        return dire.decode('ascii')


G = PuntoS256(
    0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
    0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)


class PruebaS256(TestCase):

    def prueba_orden(self):
        punto = N*G
        self.assertIsNone(punto.x)

    def prueba_puntopub(self):
        # escribe una prueba para el punto público para los siguientes:
        puntos = (
            # secreto, x, y
            (7, 0x5cbdf0646e5db4eaa398f365f2ea7a0e3d419b7e0330e39ce92bddedcac4f9bc, 0x6aebca40ba255960a3178d6d861a54dba813d0b813fde7b5a5082628087264da),
            (1485, 0xc982196a7466fbbbb0e27a940b6af926c1a74d5ad07128c82824a11b5398afda, 0x7a91f9eae64438afb9ce6448a1c133db2d8fb9254e4546b6f001637d50901f55),
            (2**128, 0x8f68b9d2f63b5f339239c1ad981f162ee88c5678723ea3351b7b444c9ec4c0da, 0x662a9f2dba063986de1d90c2b6be215dbbea2cfe95510bfdf23cbf79501fff82),
            (2**240+2**31, 0x9577ff57c8234558f293df502ca4f09cbc65a6572c842b39b366f21717945116, 0x10b49c67fa9365ad7b90dab070be339a1daf9052373ec30ffae4f72d5e66d053),
        )

        # itera sobre los puntos
        for secreto, x, y in puntos:
            # inicializa el punto secp256k1 (PuntoS256)
            punto = PuntoS256(x, y)
            # comprpueba que secreto*G es el mismo que el punto
            self.assertEqual(secreto*G, punto)

    def prueba_sec(self):
        coeficiente = 999**3
        descomprimido = '049d5ca49670cbe4c3bfa84c96a8c87df086c6ea6a24ba6b809c9de234496808d56fa15cc7f3d38cda98dee2419f415b7513dde1301f8643cd9245aea7f3f911f9'
        comprimido = '039d5ca49670cbe4c3bfa84c96a8c87df086c6ea6a24ba6b809c9de234496808d5'
        punto = coeficiente*G
        self.assertEqual(punto.sec(comprimido=False), bytes.fromhex(descomprimido))
        self.assertEqual(punto.sec(comprimido=True), bytes.fromhex(comprimido))
        coeficiente = 123
        descomprimido = '04a598a8030da6d86c6bc7f2f5144ea549d28211ea58faa70ebf4c1e665c1fe9b5204b5d6f84822c307e4b4a7140737aec23fc63b65b35f86a10026dbd2d864e6b'
        comprimido = '03a598a8030da6d86c6bc7f2f5144ea549d28211ea58faa70ebf4c1e665c1fe9b5'
        punto = coeficiente*G
        self.assertEqual(punto.sec(comprimido=False), bytes.fromhex(descomprimido))
        self.assertEqual(punto.sec(comprimido=True), bytes.fromhex(comprimido))
        coeficiente = 42424242
        descomprimido = '04aee2e7d843f7430097859e2bc603abcc3274ff8169c1a469fee0f20614066f8e21ec53f40efac47ac1c5211b2123527e0e9b57ede790c4da1e72c91fb7da54a3'
        comprimido = '03aee2e7d843f7430097859e2bc603abcc3274ff8169c1a469fee0f20614066f8e'
        punto = coeficiente*G
        self.assertEqual(punto.sec(comprimido=False), bytes.fromhex(descomprimido))
        self.assertEqual(punto.sec(comprimido=True), bytes.fromhex(descomprimido))

    def prueba_dire(self):
        secreto = 888**3
        dire_mainnet = '148dY81A9BmdpMhvYEVznrM45kWN32vSCN'
        dire_testnet = 'mieaqB68xDCtbUBYFoUNcmZNwk74xcBfTP'
        punto = secreto*G
        self.assertEqual(
            punto.dire(comprimido=True, testnet=False), dire_mainnet)
        self.assertEqual(
            punto.dire(comprimido=True, testnet=True), dire_testnet)
        secreto = 321
        dire_mainnet = '1S6g2xBJSED7Qr9CYZib5f4PYVhHZiVfj'
        dire_testnet = 'mfx3y63A7TfTtXKkv7Y6QzsPFY6QCBCXiP'
        punto = secreto*G
        self.assertEqual(
            punto.dire(comprimido=False, testnet=False), dire_mainnet)
        self.assertEqual(
            punto.dire(comprimido=False, testnet=True), dire_testnet)
        secreto = 4242424242
        dire_mainnet = '1226JSptcStqn4Yq9aAmNXdwdc2ixuH9nb'
        dire_testnet = 'mgY3bVusRUL6ZB2Ss999CSrGVbdRwVpM8s'
        punto = secreto*G
        self.assertEqual(
            punto.dire(comprimido=False, testnet=False), dire_mainnet)
        self.assertEqual(
            punto.dire(comprimido=False, testnet=True), dire_testnet)

