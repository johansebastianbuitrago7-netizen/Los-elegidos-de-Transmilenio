"""Estructuras de datos propias del motor (sin librerias, solo list/dict/set)."""


# ---------------------------------------------------------------- Pila / Cola
class _Nodo:
    __slots__ = ("valor", "sig", "ant")

    def __init__(self, valor):
        self.valor = valor
        self.sig = None
        self.ant = None


class Pila:
    """Pila (LIFO) sobre lista enlazada simple. Todo O(1)."""

    def __init__(self):
        self._tope = None
        self._n = 0

    def apilar(self, valor):
        nodo = _Nodo(valor)
        nodo.sig = self._tope
        self._tope = nodo
        self._n += 1

    def desapilar(self):
        """Devuelve el tope o None si esta vacia."""
        nodo = self._tope
        if nodo is None:
            return None
        self._tope = nodo.sig
        self._n -= 1
        return nodo.valor

    def vaciar(self):
        self._tope = None
        self._n = 0

    def vacia(self):
        return self._n == 0

    def __len__(self):
        return self._n


class Cola:
    """Cola (FIFO) sobre lista enlazada con puntero a la cola. Todo O(1)."""

    def __init__(self):
        self._frente = None
        self._final = None
        self._n = 0

    def encolar(self, valor):
        nodo = _Nodo(valor)
        if self._final is None:
            self._frente = nodo
        else:
            self._final.sig = nodo
        self._final = nodo
        self._n += 1

    def desencolar(self):
        """Devuelve el primero o None si esta vacia."""
        nodo = self._frente
        if nodo is None:
            return None
        self._frente = nodo.sig
        if self._frente is None:
            self._final = None
        self._n -= 1
        return nodo.valor

    def vacia(self):
        return self._n == 0

    def __len__(self):
        return self._n


# ---------------------------------------------------------- Lista doblemente enlazada
class ListaDoble:
    """Lista doblemente enlazada. Insertar/quitar dado el nodo: O(1)."""

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._n = 0

    def insertar_despues(self, ref, valor):
        """Inserta tras el nodo `ref` (None = al inicio). Devuelve el nodo nuevo."""
        nodo = _Nodo(valor)
        if ref is None:
            nodo.sig = self.cabeza
            if self.cabeza is not None:
                self.cabeza.ant = nodo
            self.cabeza = nodo
            if self.cola is None:
                self.cola = nodo
        else:
            nodo.ant = ref
            nodo.sig = ref.sig
            if ref.sig is not None:
                ref.sig.ant = nodo
            else:
                self.cola = nodo
            ref.sig = nodo
        self._n += 1
        return nodo

    def agregar_al_final(self, valor):
        return self.insertar_despues(self.cola, valor)

    def quitar(self, nodo):
        if nodo.ant is not None:
            nodo.ant.sig = nodo.sig
        else:
            self.cabeza = nodo.sig
        if nodo.sig is not None:
            nodo.sig.ant = nodo.ant
        else:
            self.cola = nodo.ant
        nodo.sig = None
        nodo.ant = None
        self._n -= 1

    def adelante(self):
        nodo = self.cabeza
        while nodo is not None:
            yield nodo.valor
            nodo = nodo.sig

    def atras(self):
        nodo = self.cola
        while nodo is not None:
            yield nodo.valor
            nodo = nodo.ant

    def __len__(self):
        return self._n


# ------------------------------------------------------------------- Arbol AVL
class _NodoAVL:
    __slots__ = ("clave", "valor", "izq", "der", "h")

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None
        self.h = 1


def _alt(n):
    return n.h if n is not None else 0


def _actualizar(n):
    a = _alt(n.izq)
    b = _alt(n.der)
    n.h = (a if a > b else b) + 1


def _rot_der(y):
    x = y.izq
    y.izq = x.der
    x.der = y
    _actualizar(y)
    _actualizar(x)
    return x


def _rot_izq(x):
    y = x.der
    x.der = y.izq
    y.izq = x
    _actualizar(x)
    _actualizar(y)
    return y


def _equilibrar(n):
    _actualizar(n)
    bal = _alt(n.izq) - _alt(n.der)
    if bal > 1:
        if _alt(n.izq.izq) < _alt(n.izq.der):
            n.izq = _rot_izq(n.izq)
        return _rot_der(n)
    if bal < -1:
        if _alt(n.der.der) < _alt(n.der.izq):
            n.der = _rot_der(n.der)
        return _rot_izq(n)
    return n


class AVL:
    """Arbol binario de busqueda balanceado (AVL).

    insertar / eliminar / buscar: O(log n).
    recorrer_desde(clave): primer elemento >= clave en O(log n) y luego
    cada siguiente en O(1) amortizado (recorrido en orden con pila explicita).
    """

    def __init__(self):
        self._raiz = None
        self._n = 0
        self._cambio = False

    def __len__(self):
        return self._n

    def buscar(self, clave):
        n = self._raiz
        while n is not None:
            if clave < n.clave:
                n = n.izq
            elif n.clave < clave:
                n = n.der
            else:
                return n.valor
        return None

    def insertar(self, clave, valor=None):
        self._cambio = False
        self._raiz = self._ins(self._raiz, clave, valor)
        if self._cambio:
            self._n += 1
        return self._cambio

    def _ins(self, n, clave, valor):
        if n is None:
            self._cambio = True
            return _NodoAVL(clave, valor)
        if clave < n.clave:
            n.izq = self._ins(n.izq, clave, valor)
        elif n.clave < clave:
            n.der = self._ins(n.der, clave, valor)
        else:
            n.valor = valor
            return n
        return _equilibrar(n)

    def eliminar(self, clave):
        self._cambio = False
        self._raiz = self._del(self._raiz, clave)
        if self._cambio:
            self._n -= 1
        return self._cambio

    def _del(self, n, clave):
        if n is None:
            return None
        if clave < n.clave:
            n.izq = self._del(n.izq, clave)
        elif n.clave < clave:
            n.der = self._del(n.der, clave)
        else:
            self._cambio = True
            if n.izq is None:
                return n.der
            if n.der is None:
                return n.izq
            suc = n.der
            while suc.izq is not None:
                suc = suc.izq
            n.clave = suc.clave
            n.valor = suc.valor
            ya = self._cambio
            n.der = self._del(n.der, suc.clave)
            self._cambio = ya
        return _equilibrar(n)

    def recorrer_desde(self, clave=None):
        """Genera (clave, valor) en orden ascendente, solo claves >= `clave`."""
        pila = []
        n = self._raiz
        if clave is None:
            while n is not None:
                pila.append(n)
                n = n.izq
        else:
            while n is not None:
                if n.clave < clave:
                    n = n.der
                else:
                    pila.append(n)
                    n = n.izq
        while pila:
            n = pila.pop()
            yield n.clave, n.valor
            m = n.der
            while m is not None:
                pila.append(m)
                m = m.izq
