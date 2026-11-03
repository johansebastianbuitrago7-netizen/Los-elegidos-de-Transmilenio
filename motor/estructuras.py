"""Estructuras de datos propias del motor Atlas.

Todo se construye con listas usadas como arreglos, tuplas, clases y
referencias entre nodos. No se usa dict, set ni módulos de colecciones.
"""


def hash_texto(texto):
    """Hash polinomial (base 31) de un string, acotado a 32 bits. O(len)."""
    h = 0
    for caracter in texto:
        h = (h * 31 + ord(caracter)) & 0xFFFFFFFF
    return h


class _Entrada:
    __slots__ = ("clave", "valor", "siguiente")

    def __init__(self, clave, valor, siguiente):
        self.clave = clave
        self.valor = valor
        self.siguiente = siguiente


class TablaHash:
    """Tabla hash con encadenamiento separado y redimensionamiento.

    Las claves son strings. Cada cubeta es una lista enlazada simple de
    entradas. Cuando el factor de carga supera 0.75 se duplica la cantidad
    de cubetas, así poner/obtener/eliminar cuestan O(1) en promedio.
    """

    CARGA_MAXIMA = 0.75

    def __init__(self, capacidad=8):
        tam = 8
        while tam < capacidad:
            tam = tam * 2
        self._cubetas = [None] * tam
        self._tamano = 0

    def __len__(self):
        return self._tamano

    def _posicion(self, clave):
        return hash_texto(clave) & (len(self._cubetas) - 1)

    def _buscar(self, clave):
        entrada = self._cubetas[self._posicion(clave)]
        while entrada is not None:
            if entrada.clave == clave:
                return entrada
            entrada = entrada.siguiente
        return None

    def poner(self, clave, valor):
        """Inserta o reemplaza. Devuelve True si la clave era nueva."""
        entrada = self._buscar(clave)
        if entrada is not None:
            entrada.valor = valor
            return False
        pos = self._posicion(clave)
        self._cubetas[pos] = _Entrada(clave, valor, self._cubetas[pos])
        self._tamano += 1
        if self._tamano > len(self._cubetas) * self.CARGA_MAXIMA:
            self._redimensionar(len(self._cubetas) * 2)
        return True

    def obtener(self, clave, defecto=None):
        entrada = self._buscar(clave)
        if entrada is None:
            return defecto
        return entrada.valor

    def contiene(self, clave):
        return self._buscar(clave) is not None

    def eliminar(self, clave):
        """Quita la clave. Devuelve True si existía."""
        pos = self._posicion(clave)
        anterior = None
        entrada = self._cubetas[pos]
        while entrada is not None:
            if entrada.clave == clave:
                if anterior is None:
                    self._cubetas[pos] = entrada.siguiente
                else:
                    anterior.siguiente = entrada.siguiente
                self._tamano -= 1
                return True
            anterior = entrada
            entrada = entrada.siguiente
        return False

    def _redimensionar(self, nueva_capacidad):
        viejas = self._cubetas
        self._cubetas = [None] * nueva_capacidad
        for entrada in viejas:
            while entrada is not None:
                siguiente = entrada.siguiente
                pos = self._posicion(entrada.clave)
                entrada.siguiente = self._cubetas[pos]
                self._cubetas[pos] = entrada
                entrada = siguiente

    def claves(self):
        resultado = []
        for entrada in self._cubetas:
            while entrada is not None:
                resultado.append(entrada.clave)
                entrada = entrada.siguiente
        return resultado

    def valores(self):
        resultado = []
        for entrada in self._cubetas:
            while entrada is not None:
                resultado.append(entrada.valor)
                entrada = entrada.siguiente
        return resultado

    def capacidad(self):
        return len(self._cubetas)

    def cubeta_mas_larga(self):
        """Longitud de la cadena más larga (diagnóstico de colisiones)."""
        mayor = 0
        for entrada in self._cubetas:
            largo = 0
            while entrada is not None:
                largo += 1
                entrada = entrada.siguiente
            if largo > mayor:
                mayor = largo
        return mayor


class NodoDoble:
    __slots__ = ("valor", "anterior", "siguiente")

    def __init__(self, valor):
        self.valor = valor
        self.anterior = None
        self.siguiente = None


class ListaDoble:
    """Lista doblemente enlazada con cabeza y cola.

    Insertar después de un nodo conocido y eliminar un nodo conocido son
    O(1); recorrer en cualquiera de los dos sentidos es O(n).
    """

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._tamano = 0

    def __len__(self):
        return self._tamano

    def agregar_final(self, valor):
        nodo = NodoDoble(valor)
        if self.cola is None:
            self.cabeza = nodo
            self.cola = nodo
        else:
            nodo.anterior = self.cola
            self.cola.siguiente = nodo
            self.cola = nodo
        self._tamano += 1
        return nodo

    def agregar_inicio(self, valor):
        nodo = NodoDoble(valor)
        if self.cabeza is None:
            self.cabeza = nodo
            self.cola = nodo
        else:
            nodo.siguiente = self.cabeza
            self.cabeza.anterior = nodo
            self.cabeza = nodo
        self._tamano += 1
        return nodo

    def insertar_despues(self, nodo, valor):
        """Inserta valor justo después de nodo (None = al inicio)."""
        if nodo is None:
            return self.agregar_inicio(valor)
        if nodo is self.cola:
            return self.agregar_final(valor)
        nuevo = NodoDoble(valor)
        nuevo.anterior = nodo
        nuevo.siguiente = nodo.siguiente
        nodo.siguiente.anterior = nuevo
        nodo.siguiente = nuevo
        self._tamano += 1
        return nuevo

    def eliminar(self, nodo):
        if nodo.anterior is None:
            self.cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self.cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        nodo.anterior = None
        nodo.siguiente = None
        self._tamano -= 1
        return nodo.valor

    def valores(self, al_reves=False):
        resultado = []
        if al_reves:
            nodo = self.cola
            while nodo is not None:
                resultado.append(nodo.valor)
                nodo = nodo.anterior
        else:
            nodo = self.cabeza
            while nodo is not None:
                resultado.append(nodo.valor)
                nodo = nodo.siguiente
        return resultado


class _NodoPila:
    __slots__ = ("valor", "debajo")

    def __init__(self, valor, debajo):
        self.valor = valor
        self.debajo = debajo


class Pila:
    """Pila LIFO enlazada: apilar, desapilar y cima en O(1)."""

    def __init__(self):
        self._cima = None
        self._tamano = 0

    def __len__(self):
        return self._tamano

    def vacia(self):
        return self._cima is None

    def apilar(self, valor):
        self._cima = _NodoPila(valor, self._cima)
        self._tamano += 1

    def desapilar(self):
        if self._cima is None:
            raise IndexError("pila vacía")
        valor = self._cima.valor
        self._cima = self._cima.debajo
        self._tamano -= 1
        return valor

    def cima(self):
        if self._cima is None:
            raise IndexError("pila vacía")
        return self._cima.valor

    def vaciar(self):
        self._cima = None
        self._tamano = 0

    def valores(self):
        """Elementos de la cima hacia el fondo."""
        resultado = []
        nodo = self._cima
        while nodo is not None:
            resultado.append(nodo.valor)
            nodo = nodo.debajo
        return resultado


class Cola:
    """Cola FIFO sobre un arreglo circular que se duplica al llenarse.

    encolar y desencolar cuestan O(1) amortizado; la memoria es O(n)
    respecto a los elementos presentes (no a los que ya salieron).
    """

    def __init__(self, capacidad=16):
        tam = 4
        while tam < capacidad:
            tam = tam * 2
        self._datos = [None] * tam
        self._frente = 0
        self._tamano = 0

    def __len__(self):
        return self._tamano

    def vacia(self):
        return self._tamano == 0

    def encolar(self, valor):
        if self._tamano == len(self._datos):
            self._crecer()
        fin = (self._frente + self._tamano) & (len(self._datos) - 1)
        self._datos[fin] = valor
        self._tamano += 1

    def desencolar(self):
        if self._tamano == 0:
            raise IndexError("cola vacía")
        valor = self._datos[self._frente]
        self._datos[self._frente] = None
        self._frente = (self._frente + 1) & (len(self._datos) - 1)
        self._tamano -= 1
        return valor

    def frente(self):
        if self._tamano == 0:
            raise IndexError("cola vacía")
        return self._datos[self._frente]

    def _crecer(self):
        viejos = self._datos
        mascara = len(viejos) - 1
        nuevos = [None] * (len(viejos) * 2)
        i = 0
        while i < self._tamano:
            nuevos[i] = viejos[(self._frente + i) & mascara]
            i += 1
        self._datos = nuevos
        self._frente = 0
