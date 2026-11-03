"""La clase Red: R1 a R9 sobre las estructuras propias del motor.

Convenciones de retorno (decisiones propias, documentadas en el README):
  estado            -> "abierta" | "cerrada" | "inexistente"
  autocompletar     -> lista de nombres
  rango             -> lista de nombres
  proximo_bus       -> "HH:MM" o None
  viaje             -> lista de tramos (ruta, subir_en, bajar_en); [] si
                       origen == destino; None si no hay viaje posible
  ranking           -> lista de tuplas (nombre, buses_al_dia)
  agregar/quitar/cerrar/reabrir/deshacer/rehacer -> True si hubo cambio
  recorrido         -> lista de nombres o None si la ruta no existe
"""

from .algoritmos import limite_inferior, ordenar
from .carga import leer_tabla
from .estructuras import ListaDoble, Pila, TablaHash
from .tiempo import a_minutos, a_texto, minutos_csv

ABIERTA = "abierta"
CERRADA = "cerrada"
INEXISTENTE = "inexistente"

_SEPARADOR = "\x1f"


def _clave_par(ruta, estacion):
    return ruta + _SEPARADOR + estacion


class Estacion:
    __slots__ = ("nombre", "id", "abierta", "rutas", "buses")

    def __init__(self, nombre, ident):
        self.nombre = nombre
        self.id = ident
        self.abierta = True
        self.rutas = ListaDoble()   # rutas que paran aquí (valores: Ruta)
        self.buses = 0              # eventos de horario de sus rutas activas


class Parada:
    """Valor de cada nodo de una ruta: une estación, ruta e incidencia."""
    __slots__ = ("estacion", "ruta", "nodo_incidencia")

    def __init__(self, estacion, ruta):
        self.estacion = estacion
        self.ruta = ruta
        self.nodo_incidencia = None


class Ruta:
    __slots__ = ("nombre", "paradas", "indice")

    def __init__(self, nombre):
        self.nombre = nombre
        self.paradas = ListaDoble()   # recorrido en el sentido de la ruta
        self.indice = TablaHash()     # nombre de estación -> nodo en paradas


class Red:
    def __init__(self, carpeta):
        self.diagnostico = TablaHash()
        self._estaciones = TablaHash(256)
        self._por_id = []
        self._rutas = TablaHash(256)
        self._horarios = TablaHash(4096)
        self._deshacer = Pila()
        self._rehacer = Pila()
        self._ranking = None
        self._cargar_estaciones(carpeta)
        self._cargar_rutas(carpeta)
        self._cargar_horarios(carpeta)
        n = len(self._por_id)
        # Arreglos de trabajo de R5, reutilizados con marcas de consulta.
        self._marca = [0] * n
        self._dist = [0] * n
        self._ruta_llegada = [None] * n
        self._consulta = 0

    # ------------------------------------------------------------------ carga
    def _cargar_estaciones(self, carpeta):
        repetidas = 0
        nombres = []
        for (nombre,) in leer_tabla(carpeta, "estaciones.csv", ["nombre"]):
            if nombre == "":
                continue
            if self._estaciones.contiene(nombre):
                repetidas += 1
                continue
            estacion = Estacion(nombre, len(self._por_id))
            self._estaciones.poner(nombre, estacion)
            self._por_id.append(estacion)
            nombres.append(nombre)
        self._nombres = ordenar(nombres)
        self.diagnostico.poner("estaciones", len(nombres))
        self.diagnostico.poner("estaciones_repetidas", repetidas)

    def _cargar_rutas(self, carpeta):
        filas = leer_tabla(carpeta, "rutas.csv", ["ruta", "orden", "estacion"])
        convertidas = []
        for ruta, orden, estacion in filas:
            try:
                posicion = int(orden)
            except ValueError:
                raise ValueError("rutas.csv: orden inválido '" + orden + "'")
            convertidas.append((ruta, posicion, estacion))
        convertidas = ordenar(convertidas, lambda f: (f[0], f[1]))
        nombres_rutas = []
        for ruta_nombre, _, estacion_nombre in convertidas:
            estacion = self._estaciones.obtener(estacion_nombre)
            if estacion is None:
                raise ValueError("rutas.csv: la estación '" + estacion_nombre
                                 + "' no está en estaciones.csv")
            ruta = self._rutas.obtener(ruta_nombre)
            if ruta is None:
                ruta = Ruta(ruta_nombre)
                self._rutas.poner(ruta_nombre, ruta)
                nombres_rutas.append(ruta_nombre)
            if ruta.indice.contiene(estacion_nombre):
                raise ValueError("rutas.csv: la ruta " + ruta_nombre
                                 + " repite la estación " + estacion_nombre)
            self._enlazar(ruta, estacion, ruta.paradas.cola)
        self._nombres_rutas = nombres_rutas   # ya en orden alfabético
        self.diagnostico.poner("rutas", len(nombres_rutas))
        self.diagnostico.poner("paradas", len(convertidas))

    def _cargar_horarios(self, carpeta):
        filas = leer_tabla(carpeta, "horarios.csv", ["ruta", "estacion", "hora"])
        fuera_de_ruta = 0
        invalidas = 0
        for ruta, estacion, hora in filas:
            ruta_obj = self._rutas.obtener(ruta)
            if ruta_obj is None or not ruta_obj.indice.contiene(estacion):
                fuera_de_ruta += 1
                continue
            minutos = minutos_csv(hora)
            if minutos < 0:
                invalidas += 1
                continue
            clave = _clave_par(ruta, estacion)
            lista = self._horarios.obtener(clave)
            if lista is None:
                lista = []
                self._horarios.poner(clave, lista)
            lista.append(minutos)
        for clave in self._horarios.claves():
            ordenados = ordenar(self._horarios.obtener(clave))
            self._horarios.poner(clave, ordenados)
            partes = clave.split(_SEPARADOR)
            self._estaciones.obtener(partes[1]).buses += len(ordenados)
        self.diagnostico.poner("eventos", len(filas) - fuera_de_ruta - invalidas)
        self.diagnostico.poner("eventos_fuera_de_ruta", fuera_de_ruta)
        self.diagnostico.poner("horas_invalidas", invalidas)

    # --------------------------------------------------------- utilidades
    def _enlazar(self, ruta, estacion, nodo_previo):
        """Inserta estacion en ruta después de nodo_previo (None = inicio)."""
        parada = Parada(estacion, ruta)
        nodo = ruta.paradas.insertar_despues(nodo_previo, parada)
        ruta.indice.poner(estacion.nombre, nodo)
        parada.nodo_incidencia = estacion.rutas.agregar_final(ruta)
        return nodo

    def _eventos(self, ruta_nombre, estacion_nombre):
        return self._horarios.obtener(_clave_par(ruta_nombre, estacion_nombre))

    def _contar_eventos(self, ruta_nombre, estacion_nombre):
        eventos = self._eventos(ruta_nombre, estacion_nombre)
        if eventos is None:
            return 0
        return len(eventos)

    def _insertar_parada(self, ruta, estacion, despues_de):
        previo = None
        if despues_de is not None:
            previo = ruta.indice.obtener(despues_de)
        self._enlazar(ruta, estacion, previo)
        estacion.buses += self._contar_eventos(ruta.nombre, estacion.nombre)
        self._ranking = None

    def _retirar_parada(self, ruta, estacion):
        """Quita la parada y devuelve el nombre de la anterior (o None)."""
        nodo = ruta.indice.obtener(estacion.nombre)
        previo = None
        if nodo.anterior is not None:
            previo = nodo.anterior.valor.estacion.nombre
        parada = ruta.paradas.eliminar(nodo)
        estacion.rutas.eliminar(parada.nodo_incidencia)
        ruta.indice.eliminar(estacion.nombre)
        estacion.buses -= self._contar_eventos(ruta.nombre, estacion.nombre)
        self._ranking = None
        return previo

    def _registrar(self, operacion):
        self._deshacer.apilar(operacion)
        self._rehacer.vaciar()

    # ---------------------------------------------------------------- R1
    def estado(self, nombre):
        """R1. O(1) promedio (tabla hash)."""
        estacion = self._estaciones.obtener(nombre)
        if estacion is None:
            return INEXISTENTE
        if estacion.abierta:
            return ABIERTA
        return CERRADA

    # ---------------------------------------------------------------- R2
    def autocompletar(self, prefijo, k):
        """R2. Búsqueda binaria del prefijo y avance. O(log n + k + c)."""
        resultado = []
        if k <= 0:
            return resultado
        i = limite_inferior(self._nombres, prefijo)
        while i < len(self._nombres) and len(resultado) < k:
            nombre = self._nombres[i]
            if not nombre.startswith(prefijo):
                break
            if self._estaciones.obtener(nombre).abierta:
                resultado.append(nombre)
            i += 1
        return resultado

    # ---------------------------------------------------------------- R3
    def rango(self, desde, hasta):
        """R3. Inclusivo en ambos extremos. O(log n + m)."""
        resultado = []
        if desde > hasta:
            return resultado
        i = limite_inferior(self._nombres, desde)
        while i < len(self._nombres) and self._nombres[i] <= hasta:
            nombre = self._nombres[i]
            if self._estaciones.obtener(nombre).abierta:
                resultado.append(nombre)
            i += 1
        return resultado

    # ---------------------------------------------------------------- R4
    def proximo_bus(self, estacion, ruta, hora):
        """R4. Primer evento >= hora. O(1) + O(log m) con búsqueda binaria."""
        minutos = a_minutos(hora)
        indice = self._indice_proximo(estacion, ruta, minutos)
        if indice < 0:
            return None
        return a_texto(self._eventos(ruta, estacion)[indice])

    def _indice_proximo(self, estacion, ruta, minutos):
        est = self._estaciones.obtener(estacion)
        ruta_obj = self._rutas.obtener(ruta)
        if est is None or ruta_obj is None or not est.abierta:
            return -1
        if not ruta_obj.indice.contiene(estacion):
            return -1
        eventos = self._eventos(ruta, estacion)
        if eventos is None:
            return -1
        i = limite_inferior(eventos, minutos)
        if i >= len(eventos):
            return -1
        return i

    def proximos_buses(self, estacion, ruta, hora, cantidad):
        """Los `cantidad` eventos desde el próximo bus (apoyo para la app)."""
        indice = self._indice_proximo(estacion, ruta, a_minutos(hora))
        resultado = []
        if indice < 0:
            return resultado
        eventos = self._eventos(ruta, estacion)
        while indice < len(eventos) and len(resultado) < cantidad:
            resultado.append(a_texto(eventos[indice]))
            indice += 1
        return resultado

    # ---------------------------------------------------------------- R5
    def viaje(self, origen, destino):
        """R5. Viaje directo o con un transbordo que pase por menos paradas.

        Paradas = enlaces recorridos (diferencia de posiciones en la ruta).
        1. Desde el origen se avanza por cada ruta que para ahí, guardando
           para cada estación abierta alcanzable la menor distancia y la ruta.
        2. Desde el destino se retrocede por cada ruta que para ahí; cada
           estación abierta alcanzada en ambos barridos es un transbordo.
        Desempate: menos paradas, luego directo antes que transbordo, luego
        orden alfabético de (ruta 1, estación de transbordo, ruta 2).
        Costo O(suma de longitudes de las rutas que tocan origen y destino).
        """
        est_o = self._estaciones.obtener(origen)
        est_d = self._estaciones.obtener(destino)
        if est_o is None or est_d is None:
            return None
        if not est_o.abierta or not est_d.abierta:
            return None
        if est_o is est_d:
            return []
        self._consulta += 1
        marca = self._consulta
        directo_dist = -1
        directo_ruta = None
        incidencia = est_o.rutas.cabeza
        while incidencia is not None:
            ruta = incidencia.valor
            nodo = ruta.indice.obtener(origen).siguiente
            dist = 1
            while nodo is not None:
                est = nodo.valor.estacion
                if est.abierta:
                    if est is est_d:
                        if (directo_dist < 0 or dist < directo_dist
                                or (dist == directo_dist
                                    and ruta.nombre < directo_ruta.nombre)):
                            directo_dist = dist
                            directo_ruta = ruta
                    elif (self._marca[est.id] != marca
                          or dist < self._dist[est.id]
                          or (dist == self._dist[est.id]
                              and ruta.nombre < self._ruta_llegada[est.id].nombre)):
                        self._marca[est.id] = marca
                        self._dist[est.id] = dist
                        self._ruta_llegada[est.id] = ruta
                nodo = nodo.siguiente
                dist += 1
            incidencia = incidencia.siguiente

        mejor = None   # (total, ruta1, transbordo, ruta2)
        incidencia = est_d.rutas.cabeza
        while incidencia is not None:
            ruta = incidencia.valor
            nodo = ruta.indice.obtener(destino).anterior
            dist = 1
            while nodo is not None:
                est = nodo.valor.estacion
                if est is est_o:
                    break   # antes del origen no hay transbordos útiles
                if est.abierta and self._marca[est.id] == marca:
                    candidato = (self._dist[est.id] + dist,
                                 self._ruta_llegada[est.id].nombre,
                                 est.nombre, ruta.nombre)
                    if mejor is None or candidato < mejor:
                        mejor = candidato
                nodo = nodo.anterior
                dist += 1
            incidencia = incidencia.siguiente

        if directo_dist >= 0 and (mejor is None or directo_dist <= mejor[0]):
            return [(directo_ruta.nombre, origen, destino)]
        if mejor is None:
            return None
        return [(mejor[1], origen, mejor[2]), (mejor[3], mejor[2], destino)]

    def paradas_viaje(self, tramos):
        """Total de enlaces recorridos por una lista de tramos de viaje()."""
        total = 0
        for ruta, desde, hasta in tramos:
            total += len(self.tramo(ruta, desde, hasta)) - 1
        return total

    def tramo(self, ruta, desde, hasta):
        """Estaciones de `desde` a `hasta` en el sentido de la ruta (inclusive).

        Devuelve None si alguna no está en la ruta o si hasta va antes.
        """
        ruta_obj = self._rutas.obtener(ruta)
        if ruta_obj is None:
            return None
        nodo = ruta_obj.indice.obtener(desde)
        if nodo is None or not ruta_obj.indice.contiene(hasta):
            return None
        resultado = []
        while nodo is not None:
            nombre = nodo.valor.estacion.nombre
            resultado.append(nombre)
            if nombre == hasta:
                return resultado
            nodo = nodo.siguiente
        return None

    # ---------------------------------------------------------------- R6
    def ranking(self, k):
        """R6. Arreglo ordenado en caché; se reconstruye solo tras cambios.

        Consulta O(k); reconstrucción O(n log n) con merge sort.
        Desempate: orden alfabético.
        """
        if self._ranking is None:
            abiertas = []
            for nombre in self._nombres:
                estacion = self._estaciones.obtener(nombre)
                if estacion.abierta:
                    abiertas.append((nombre, estacion.buses))
            # merge sort estable sobre una entrada alfabética
            self._ranking = ordenar(abiertas, lambda par: -par[1])
        resultado = []
        i = 0
        while i < k and i < len(self._ranking):
            resultado.append(self._ranking[i])
            i += 1
        return resultado

    # ---------------------------------------------------------------- R7
    def agregar_parada(self, ruta, nueva, despues_de):
        """R7. Inserta `nueva` después de `despues_de` (None = al inicio).

        O(1) promedio: tabla hash para ubicar el nodo + lista doble.
        """
        ruta_obj = self._rutas.obtener(ruta)
        estacion = self._estaciones.obtener(nueva)
        if ruta_obj is None or estacion is None:
            return False
        if ruta_obj.indice.contiene(nueva):
            return False
        if despues_de is not None and not ruta_obj.indice.contiene(despues_de):
            return False
        self._insertar_parada(ruta_obj, estacion, despues_de)
        self._registrar(("agregar", ruta, nueva, despues_de))
        return True

    def quitar_parada(self, ruta, estacion):
        """R7. O(1) promedio."""
        ruta_obj = self._rutas.obtener(ruta)
        est = self._estaciones.obtener(estacion)
        if ruta_obj is None or est is None:
            return False
        if not ruta_obj.indice.contiene(estacion):
            return False
        previo = self._retirar_parada(ruta_obj, est)
        self._registrar(("quitar", ruta, estacion, previo))
        return True

    def recorrido(self, ruta, al_reves=False):
        """R7. O(L): recorre la lista doble en el sentido pedido."""
        ruta_obj = self._rutas.obtener(ruta)
        if ruta_obj is None:
            return None
        resultado = []
        for parada in ruta_obj.paradas.valores(al_reves):
            resultado.append(parada.estacion.nombre)
        return resultado

    # ---------------------------------------------------------------- R8
    def cerrar(self, nombre):
        """R8. O(1): solo cambia la bandera; los datos se conservan."""
        if self._cambiar_estado(nombre, False):
            self._registrar(("cerrar", nombre))
            return True
        return False

    def reabrir(self, nombre):
        if self._cambiar_estado(nombre, True):
            self._registrar(("reabrir", nombre))
            return True
        return False

    def _cambiar_estado(self, nombre, abierta):
        estacion = self._estaciones.obtener(nombre)
        if estacion is None or estacion.abierta == abierta:
            return False
        estacion.abierta = abierta
        self._ranking = None
        return True

    # ---------------------------------------------------------------- R9
    def deshacer(self):
        """R9. Saca la última operación, aplica su inversa y la pasa a rehacer."""
        if self._deshacer.vacia():
            return False
        operacion = self._deshacer.desapilar()
        self._aplicar_inversa(operacion)
        self._rehacer.apilar(operacion)
        return True

    def rehacer(self):
        if self._rehacer.vacia():
            return False
        operacion = self._rehacer.desapilar()
        self._aplicar(operacion)
        self._deshacer.apilar(operacion)
        return True

    def _aplicar(self, operacion):
        tipo = operacion[0]
        if tipo == "cerrar":
            self._cambiar_estado(operacion[1], False)
        elif tipo == "reabrir":
            self._cambiar_estado(operacion[1], True)
        elif tipo == "agregar":
            self._insertar_parada(self._rutas.obtener(operacion[1]),
                                  self._estaciones.obtener(operacion[2]),
                                  operacion[3])
        elif tipo == "quitar":
            self._retirar_parada(self._rutas.obtener(operacion[1]),
                                 self._estaciones.obtener(operacion[2]))

    def _aplicar_inversa(self, operacion):
        tipo = operacion[0]
        if tipo == "cerrar":
            self._cambiar_estado(operacion[1], True)
        elif tipo == "reabrir":
            self._cambiar_estado(operacion[1], False)
        elif tipo == "agregar":
            self._retirar_parada(self._rutas.obtener(operacion[1]),
                                 self._estaciones.obtener(operacion[2]))
        elif tipo == "quitar":
            self._insertar_parada(self._rutas.obtener(operacion[1]),
                                  self._estaciones.obtener(operacion[2]),
                                  operacion[3])

    def historial(self):
        """Operaciones (deshacer, rehacer), de la más reciente a la más antigua."""
        return (self._deshacer.valores(), self._rehacer.valores())

    # ------------------------------------------------- consultas de apoyo
    def estaciones(self):
        """Todos los nombres en orden alfabético (abiertas y cerradas)."""
        return list(self._nombres)

    def rutas(self):
        return list(self._nombres_rutas)

    def rutas_de(self, estacion):
        """Rutas que hoy paran en la estación, en orden alfabético."""
        est = self._estaciones.obtener(estacion)
        if est is None:
            return None
        nombres = []
        for ruta in est.rutas.valores():
            nombres.append(ruta.nombre)
        return ordenar(nombres)

    def horarios(self, estacion, ruta):
        """Todos los eventos (ordenados) del par, o [] si no hay."""
        resultado = []
        ruta_obj = self._rutas.obtener(ruta)
        if ruta_obj is None or not ruta_obj.indice.contiene(estacion):
            return resultado
        eventos = self._eventos(ruta, estacion)
        if eventos is None:
            return resultado
        for minutos in eventos:
            resultado.append(a_texto(minutos))
        return resultado

    def buses(self, estacion):
        est = self._estaciones.obtener(estacion)
        if est is None:
            return None
        return est.buses
