"""Clase Red: contrato del motor (R1-R9)."""
from .estructuras import AVL, ListaDoble, Pila
from .algoritmos import primero_mayor_o_igual
from . import carga


class _Ruta:
    __slots__ = ("id", "lista", "nodos")

    def __init__(self, id_):
        self.id = id_
        self.lista = ListaDoble()       # paradas en orden (R7)
        self.nodos = {}                 # estacion -> nodo de la lista (acceso O(1))


class Red:
    def __init__(self, carpeta):
        nombres = carga.leer_estaciones(carpeta)
        rutas = carga.leer_rutas(carpeta)
        self._horarios = carga.leer_horarios(carpeta)

        self._abierta = {}              # R1: tabla hash nombre -> bool
        self._buses = {}                # nombre -> buses al dia
        self._rutas_de = {}             # estacion -> {ruta: True} (rutas que pasan)
        self._arbol_nombres = AVL()     # R2/R3: estaciones abiertas por nombre
        self._arbol_ranking = AVL()     # R6: estaciones abiertas por (-buses, nombre)
        self._rutas = {}
        self._deshacer = Pila()         # R9
        self._rehacer = Pila()
        self._nuevas = set()            # estaciones añadidas en runtime (las unicas que se pueden eliminar)

        for nombre in nombres:
            self._abierta[nombre] = True
            self._buses[nombre] = 0
            self._rutas_de[nombre] = {}

        for id_ in rutas:
            ruta = _Ruta(id_)
            for est in rutas[id_]:
                if est not in self._abierta or est in ruta.nodos:
                    continue  # estacion desconocida o repetida en la ruta
                ruta.nodos[est] = ruta.lista.agregar_al_final(est)
                self._rutas_de[est][id_] = True
                self._buses[est] += self._pasan(id_, est)
            self._rutas[id_] = ruta

        for nombre in nombres:
            self._arbol_nombres.insertar(nombre, True)
            self._arbol_ranking.insertar((-self._buses[nombre], nombre), True)

    # ------------------------------------------------------------ auxiliares
    def _pasan(self, ruta, estacion):
        h = self._horarios.get((ruta, estacion))
        return len(h) if h is not None else 0

    def _ajustar_buses(self, estacion, delta):
        antes = self._buses[estacion]
        self._buses[estacion] = antes + delta
        if self._abierta[estacion]:
            self._arbol_ranking.eliminar((-antes, estacion))
            self._arbol_ranking.insertar((-(antes + delta), estacion), True)

    def crear_estacion(self, nombre):
        """Extra (fuera del contrato): registra una estacion nueva, abierta y sin rutas. O(log n)."""
        if nombre == "" or nombre in self._abierta:
            return False
        self._abierta[nombre] = True
        self._buses[nombre] = 0
        self._rutas_de[nombre] = {}
        self._arbol_nombres.insertar(nombre, True)
        self._arbol_ranking.insertar((0, nombre), True)
        self._nuevas.add(nombre)
        return True

    def eliminar_estacion(self, nombre):
        """Extra: elimina SOLO una estacion creada con crear_estacion (la base original no se toca).
        La saca de todas sus rutas y de los arboles; vacia el historial de deshacer/rehacer. O(r log n)."""
        if nombre not in self._nuevas:
            return False
        for ruta in list(self._rutas_de[nombre]):
            self._quitar(ruta, nombre)
        if self._abierta[nombre]:
            self._arbol_nombres.eliminar(nombre)
            self._arbol_ranking.eliminar((-self._buses[nombre], nombre))
        del self._abierta[nombre]
        del self._buses[nombre]
        del self._rutas_de[nombre]
        self._nuevas.discard(nombre)
        self._deshacer.vaciar()
        self._rehacer.vaciar()
        return True

    # ------------------------------------------------------------ R1
    def estado(self, nombre):
        """'abierta', 'cerrada' o 'no existe'. O(1)."""
        a = self._abierta.get(nombre)
        if a is None:
            return "no existe"
        return "abierta" if a else "cerrada"

    # ------------------------------------------------------------ R2
    def autocompletar(self, prefijo, k):
        """Hasta k estaciones abiertas que empiezan por prefijo, en orden. O(log n + k)."""
        res = []
        if k <= 0:
            return res
        for nombre, _ in self._arbol_nombres.recorrer_desde(prefijo):
            if not nombre.startswith(prefijo):
                break
            res.append(nombre)
            if len(res) >= k:
                break
        return res

    # ------------------------------------------------------------ R3
    def rango(self, desde, hasta):
        """Abiertas con desde <= nombre <= hasta, en orden. O(log n + m)."""
        res = []
        if hasta < desde:
            return res
        for nombre, _ in self._arbol_nombres.recorrer_desde(desde):
            if hasta < nombre:
                break
            res.append(nombre)
        return res

    # ------------------------------------------------------------ R4
    def proximo_bus(self, estacion, ruta, hora):
        """Primera hora de paso >= hora ('HH:MM'), como 'HH:MM', o None. O(log h)."""
        if self._abierta.get(estacion) is not True:
            return None
        r = self._rutas.get(ruta)
        if r is None or estacion not in r.nodos:
            return None
        horas = self._horarios.get((ruta, estacion))
        if horas is None:
            return None
        m = hora if isinstance(hora, int) else carga.minutos(hora)
        i = primero_mayor_o_igual(horas, m)
        if i >= len(horas):
            return None
        return carga.formato(horas[i])

    # ------------------------------------------------------------ R5
    def viaje(self, origen, destino):
        """Ruta con cualquier cantidad de transbordos. Prioridad:
        1) menos transbordos, 2) no cruzar estaciones cerradas, 3) menos paradas.
        Solo se sube, baja o transborda en estaciones abiertas. Devuelve dict o None (no hay ruta).
        Busqueda por niveles de transbordo (BFS): el primer nivel con destino da el minimo de transbordos."""
        if self._abierta.get(origen) is not True or self._abierta.get(destino) is not True:
            return None
        if origen == destino:
            return {"tipo": "directo", "tramos": [], "paradas": 0, "transbordo": None,
                    "transbordos": [], "cruza_cerrada": False}
        info = {}        # (ruta, estacion_subida) -> [cruza, paradas, clave_padre, estacion_subida]
        visto = set()
        nivel = []
        for ra in self._rutas_de[origen]:
            k = (ra, origen)
            info[k] = [False, 0, None, origen]
            visto.add(k)
            nivel.append(k)
        while nivel:
            fin = None
            sig = []
            for k in nivel:
                ruta, sube = k
                cruza, paradas = info[k][0], info[k][1]
                nodo = self._rutas[ruta].nodos[sube].sig
                while nodo is not None:
                    est = nodo.valor
                    nodo = nodo.sig
                    if not self._abierta[est]:
                        cruza = True
                        continue
                    paradas += 1
                    if est == destino:
                        if fin is None or (cruza, paradas) < (fin[0], fin[1]):
                            fin = (cruza, paradas, k)
                        break
                    for rb in self._rutas_de[est]:
                        if rb == ruta:
                            continue
                        nk = (rb, est)
                        if nk in visto:
                            continue
                        previo = info.get(nk)
                        if previo is None or (cruza, paradas) < (previo[0], previo[1]):
                            if previo is None:
                                sig.append(nk)
                            info[nk] = [cruza, paradas, k, est]
            if fin is not None:
                cruza, paradas, k = fin
                cadena = []
                while k is not None:
                    cadena.append(k)
                    k = info[k][2]
                cadena.reverse()
                tramos = []
                for n, (ruta, sube) in enumerate(cadena):
                    hasta = cadena[n + 1][1] if n + 1 < len(cadena) else destino
                    tramos.append((ruta, sube, hasta))
                trans = [sube for _, sube in cadena[1:]]
                return {"tipo": "directo" if not trans else "transbordo", "tramos": tramos,
                        "paradas": paradas, "transbordo": trans[0] if trans else None,
                        "transbordos": trans, "cruza_cerrada": cruza}
            for nk in sig:
                visto.add(nk)
            nivel = sig
        return None

    # ------------------------------------------------------------ R6
    def ranking(self, k):
        """k estaciones abiertas con mas buses al dia: [(nombre, buses)]. O(log n + k)."""
        res = []
        if k <= 0:
            return res
        for (neg, nombre), _ in self._arbol_ranking.recorrer_desde(None):
            res.append((nombre, -neg))
            if len(res) >= k:
                break
        return res

    # ------------------------------------------------------------ R7
    def recorrido(self, ruta, al_reves=False):
        """Paradas de la ruta (incluye cerradas), en un sentido o en el otro. O(L)."""
        r = self._rutas.get(ruta)
        if r is None:
            return []
        return list(r.lista.atras() if al_reves else r.lista.adelante())

    def _agregar(self, ruta, nueva, despues_de):
        r = self._rutas.get(ruta)
        if r is None or nueva not in self._abierta or nueva in r.nodos:
            return False
        ref = None
        if despues_de is not None:
            ref = r.nodos.get(despues_de)
            if ref is None:
                return False
        r.nodos[nueva] = r.lista.insertar_despues(ref, nueva)
        self._rutas_de[nueva][ruta] = True
        self._ajustar_buses(nueva, self._pasan(ruta, nueva))
        return True

    def _quitar(self, ruta, estacion):
        """-> (ok, estacion anterior en la ruta o None)."""
        r = self._rutas.get(ruta)
        if r is None:
            return False, None
        nodo = r.nodos.get(estacion)
        if nodo is None:
            return False, None
        anterior = nodo.ant.valor if nodo.ant is not None else None
        r.lista.quitar(nodo)
        del r.nodos[estacion]
        del self._rutas_de[estacion][ruta]
        self._ajustar_buses(estacion, -self._pasan(ruta, estacion))
        return True, anterior

    def agregar_parada(self, ruta, nueva, despues_de):
        """Inserta `nueva` justo despues de `despues_de` (None = al inicio). O(1)."""
        if self._agregar(ruta, nueva, despues_de):
            self._registrar(("agregar", ruta, nueva, despues_de))
            return True
        return False

    def quitar_parada(self, ruta, estacion):
        """O(1)."""
        ok, anterior = self._quitar(ruta, estacion)
        if ok:
            self._registrar(("quitar", ruta, estacion, anterior))
        return ok

    # ------------------------------------------------------------ R8
    def _cerrar(self, nombre):
        if self._abierta.get(nombre) is not True:
            return False
        self._abierta[nombre] = False
        self._arbol_nombres.eliminar(nombre)
        self._arbol_ranking.eliminar((-self._buses[nombre], nombre))
        return True

    def _reabrir(self, nombre):
        if self._abierta.get(nombre) is not False:
            return False
        self._abierta[nombre] = True
        self._arbol_nombres.insertar(nombre, True)
        self._arbol_ranking.insertar((-self._buses[nombre], nombre), True)
        return True

    def cerrar(self, nombre):
        """O(log n)."""
        if self._cerrar(nombre):
            self._registrar(("cerrar", nombre))
            return True
        return False

    def reabrir(self, nombre):
        """O(log n)."""
        if self._reabrir(nombre):
            self._registrar(("reabrir", nombre))
            return True
        return False

    # ------------------------------------------------------------ R9
    def _registrar(self, cambio):
        self._deshacer.apilar(cambio)
        self._rehacer.vaciar()  # un cambio nuevo borra lo que habia para rehacer

    def deshacer(self):
        c = self._deshacer.desapilar()
        if c is None:
            return False
        tipo = c[0]
        if tipo == "cerrar":
            self._reabrir(c[1])
        elif tipo == "reabrir":
            self._cerrar(c[1])
        elif tipo == "agregar":
            self._quitar(c[1], c[2])
        else:  # quitar
            self._agregar(c[1], c[2], c[3])
        self._rehacer.apilar(c)
        return True

    def rehacer(self):
        c = self._rehacer.desapilar()
        if c is None:
            return False
        tipo = c[0]
        if tipo == "cerrar":
            self._cerrar(c[1])
        elif tipo == "reabrir":
            self._reabrir(c[1])
        elif tipo == "agregar":
            self._agregar(c[1], c[2], c[3])
        else:  # quitar
            self._quitar(c[1], c[2])
        self._deshacer.apilar(c)
        return True
