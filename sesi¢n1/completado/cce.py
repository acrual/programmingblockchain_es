from unittest import TestCase


class ElementoCampo:

    def __init__(self, num, primo):
        self.num = num
        self.primo = primo
        if self.num >= self.primo or self.num < 0:
            error = 'Num {} no está en el rango 0 a {}'.format(
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
        # self.prime es contra lo que deberás calcular el módulo
        primo = self.primo
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)

    def __sub__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Los números primos deben ser el mismo')
        # self.num y otro.num son los valores reales
        num = (self.num - otro.num) % self.primo
        # self.prime es contra lo que deberás calcular el módulo
        primo = self.primo
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)

    def __mul__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Los números primos deben ser iguales')
        # self.num y otro.num son los valores reales
        num = (self.num * otro.num) % self.primo
        # self.prime es contra lo que deberás calcular el módulo
        primo = self.primo
        # Debes devolver un elemento de la misma clase
        # usa: self.__class__(num, primo)
        return self.__class__(num, primo)

    def __pow__(self, n):
        # Ejercicio 3.2: recuerda el teorema pequeño de Fermat
        # Ejercicio 3.2: self.num**(p-1) % p == 1
        # Ejercicio 3.2: podrías querer usar el operador % sobre n
        primo = self.primo
        num = pow(self.num, n % (primo-1), primo)
        return self.__class__(num, primo)

    def __truediv__(self, otro):
        if self.primo != otro.primo:
            raise RuntimeError('Los números primos deben ser iguales')
        # self.num y otro.num son los valores reales
        num = (self.num * pow(otro.num, self.primo - 2, self.primo)) % self.primo
        # self.prime es contra lo que deberás calcular el módulo
        primo = self.primo
        # usa el teorema pequeño de Fermat:
        # self.num**(p-1) % p == 1
        # esto implica:
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
        # el punto en el infinito se representa con x siendo None e y siendo también None
        # Comprueba esto aquí porque si no las ecuaciones de abajo no tendrán sentido
        # con ambos teniendo un valor de None.
        if self.x is None and self.y is None:
            return
        # asegúrate de que se cumple la curva elíptica
        # y**2 == x**3 + a*x + b
        if self.y**2 != self.x**3 + a*x + b:
        # si no, haz un raise RuntimeError
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

        # Caso 1: self.x == otro.x, self.y != otro.y
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


class PruebaPunto(TestCase):

    def prueba_en_curva(self):
        with self.assertRaises(RuntimeError):
            Punto(x=-2, y=4, a=5, b=7)
        # estos no deberían dar error
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
