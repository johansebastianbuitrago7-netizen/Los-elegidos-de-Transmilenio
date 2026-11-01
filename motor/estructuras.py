"""Estructuras propias: hashing por encadenamiento, enlaces y mergesort."""

class TablaHash:
    def __init__(self, capacidad=16):
        self.cubetas = [[] for _ in range(capacidad)]
        self.cantidad = 0

    def _indice(self, clave):
        valor = 0
        for letra in clave:
            valor = (valor * 31 + ord(letra)) % len(self.cubetas)
        return valor

    def obtener(self, clave, defecto=None):
        for par in self.cubetas[self._indice(clave)]:
            if par[0] == clave:
                return par[1]
        return defecto

    def guardar(self, clave, valor):
        cubeta = self.cubetas[self._indice(clave)]
        for par in cubeta:
            if par[0] == clave:
                par[1] = valor
                return
        cubeta.append([clave, valor])
        self.cantidad += 1
        if self.cantidad * 4 > len(self.cubetas) * 3:
            anteriores = self.cubetas
            self.cubetas = [[] for _ in range(len(anteriores) * 2)]
            self.cantidad = 0
            for lista in anteriores:
                for clave, valor in lista:
                    self.guardar(clave, valor)

    def borrar(self, clave):
        cubeta = self.cubetas[self._indice(clave)]
        for i in range(len(cubeta)):
            if cubeta[i][0] == clave:
                cubeta[i] = cubeta[-1]
                cubeta.pop()
                self.cantidad -= 1
                return True
        return False

    def elementos(self):
        for cubeta in self.cubetas:
            for clave, valor in cubeta:
                yield clave, valor


class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.anterior = None
        self.siguiente = None


class ListaDoble:
    def __init__(self):
        self.primero = None
        self.ultimo = None
        self.indice = TablaHash()

    def insertar(self, valor, anterior):
        if self.indice.obtener(valor) is not None:
            raise ValueError('La estación ya pertenece a la ruta')
        nodo = Nodo(valor)
        nodo.anterior = anterior
        nodo.siguiente = anterior.siguiente if anterior else self.primero
        if nodo.siguiente:
            nodo.siguiente.anterior = nodo
        else:
            self.ultimo = nodo
        if anterior:
            anterior.siguiente = nodo
        else:
            self.primero = nodo
        self.indice.guardar(valor, nodo)
        return nodo

    def quitar(self, nodo):
        if nodo.anterior:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.primero = nodo.siguiente
        if nodo.siguiente:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.ultimo = nodo.anterior
        self.indice.borrar(nodo.valor)

    def valores(self, inverso=False):
        resultado = []
        nodo = self.ultimo if inverso else self.primero
        while nodo:
            resultado.append(nodo.valor)
            nodo = nodo.anterior if inverso else nodo.siguiente
        return resultado


class Pila:
    def __init__(self):
        self.datos = []

    def apilar(self, valor):
        self.datos.append(valor)

    def sacar(self):
        return self.datos.pop() if self.datos else None

    def vaciar(self):
        self.datos = []


class Cola:
    def __init__(self):
        self.primero = None
        self.ultimo = None
        self.cantidad = 0

    def poner(self, valor):
        nodo = Nodo(valor)
        if self.ultimo:
            self.ultimo.siguiente = nodo
        else:
            self.primero = nodo
        self.ultimo = nodo
        self.cantidad += 1

    def sacar(self):
        if self.primero is None:
            return None
        valor = self.primero.valor
        self.primero = self.primero.siguiente
        self.cantidad -= 1
        if self.primero is None:
            self.ultimo = None
        return valor


def ordenar(arreglo, clave=lambda x: x):
    """Mergesort estable; O(n log n) tiempo y O(n) memoria auxiliar."""
    salida = arreglo[:]
    auxiliar = [None] * len(salida)
    ancho = 1
    while ancho < len(salida):
        inicio = 0
        while inicio < len(salida):
            medio = inicio + ancho
            fin = medio + ancho
            if medio > len(salida):
                medio = len(salida)
            if fin > len(salida):
                fin = len(salida)
            i, j = inicio, medio
            for k in range(inicio, fin):
                if i < medio and (j >= fin or clave(salida[i]) <= clave(salida[j])):
                    auxiliar[k] = salida[i]
                    i += 1
                else:
                    auxiliar[k] = salida[j]
                    j += 1
            inicio += ancho * 2
        salida, auxiliar = auxiliar, salida
        ancho *= 2
    return salida


def limite(arreglo, valor, clave=lambda x: x):
    """Primer índice con clave >= valor (búsqueda binaria propia)."""
    izquierda, derecha = 0, len(arreglo)
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        if clave(arreglo[medio]) < valor:
            izquierda = medio + 1
        else:
            derecha = medio
    return izquierda
