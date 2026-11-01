"""Red dirigida e índices compartidos para R1–R9."""
import csv
from .estructuras import TablaHash, ListaDoble, Pila, ordenar, limite
from .modelos import Estacion, Viaje, minutos, hora_texto


class Red:
    def __init__(self, carpeta):
        self.estaciones = TablaHash()
        self.rutas = TablaHash()
        self.horarios = TablaHash()
        self.atras, self.adelante = Pila(), Pila()
        self.eventos = 0
        self._ranking = None
        carpeta = str(carpeta).rstrip('/\\')
        for nombre, in self._leer(carpeta + '/estaciones.csv', ['nombre']):
            if not nombre or self.estaciones.obtener(nombre) is not None:
                raise ValueError('Estación vacía o repetida: ' + nombre)
            self.estaciones.guardar(nombre, Estacion(nombre))
        self.nombres = ordenar([e for e, _ in self.estaciones.elementos()])
        pendientes = TablaHash()
        for ruta, orden, nombre in self._leer(carpeta + '/rutas.csv', ['ruta', 'orden', 'estacion']):
            self._estacion(nombre)
            if not ruta:
                raise ValueError('Ruta vacía')
            lista = pendientes.obtener(ruta)
            if lista is None:
                lista = []
                pendientes.guardar(ruta, lista)
            lista.append((int(orden), nombre))
        for ruta, lista in pendientes.elementos():
            recorrido = ListaDoble()
            anterior_orden = None
            for orden, nombre in ordenar(lista):
                if anterior_orden == orden:
                    raise ValueError('Orden de ruta repetido')
                anterior_orden = orden
                self._estacion(nombre).rutas.guardar(ruta, recorrido.insertar(nombre, recorrido.ultimo))
            self.rutas.guardar(ruta, recorrido)
        for ruta, nombre, hora in self._leer(carpeta + '/horarios.csv', ['ruta', 'estacion', 'hora']):
            estacion = self._estacion(nombre)
            recorrido = self._ruta(ruta)
            if recorrido.indice.obtener(nombre) is None:
                raise ValueError('Horario de una parada ajena a la ruta')
            grupos = self.horarios.obtener(ruta)
            if grupos is None:
                grupos = TablaHash()
                self.horarios.guardar(ruta, grupos)
            horas = grupos.obtener(nombre)
            if horas is None:
                horas = []
                grupos.guardar(nombre, horas)
            horas.append(minutos(hora))
            estacion.buses += 1
            self.eventos += 1
        for _, grupos in self.horarios.elementos():
            for nombre, horas in grupos.elementos():
                grupos.guardar(nombre, ordenar(horas))

    @staticmethod
    def _leer(archivo, columnas):
        with open(archivo, encoding='utf-8-sig', newline='') as f:
            lector = csv.reader(f, strict=True)
            if next(lector, None) != columnas:
                raise ValueError('Columnas inválidas: ' + archivo)
            for fila in lector:
                if len(fila) != len(columnas):
                    raise ValueError('Fila inválida en ' + archivo)
                yield fila

    def _estacion(self, nombre):
        e = self.estaciones.obtener(nombre)
        if e is None:
            raise ValueError('Estación inexistente: ' + str(nombre))
        return e

    def _ruta(self, nombre):
        ruta = self.rutas.obtener(nombre)
        if ruta is None:
            raise ValueError('Ruta inexistente: ' + str(nombre))
        return ruta

    def estado(self, nombre):
        e = self.estaciones.obtener(nombre)
        if e is None:
            return 'inexistente'
        return 'abierta' if e.abierta else 'cerrada'

    def autocompletar(self, prefijo, k):
        resultado = []
        i = limite(self.nombres, prefijo)
        while i < len(self.nombres) and len(resultado) < k:
            nombre = self.nombres[i]
            if not nombre.startswith(prefijo):
                break
            if self._estacion(nombre).abierta:
                resultado.append(nombre)
            i += 1
        return resultado

    def rango(self, desde, hasta):
        resultado = []
        i = limite(self.nombres, desde)
        while i < len(self.nombres) and self.nombres[i] <= hasta:
            if self._estacion(self.nombres[i]).abierta:
                resultado.append(self.nombres[i])
            i += 1
        return resultado

    def _horas(self, ruta, estacion):
        grupos = self.horarios.obtener(ruta)
        return grupos.obtener(estacion, []) if grupos else []

    def proximo_bus(self, estacion, ruta, hora):
        tiempo = minutos(hora)
        if self.estado(estacion) != 'abierta':
            return None
        recorrido = self.rutas.obtener(ruta)
        if recorrido is None or recorrido.indice.obtener(estacion) is None:
            return None
        horas = self._horas(ruta, estacion)
        i = limite(horas, tiempo)
        return hora_texto(horas[i]) if i < len(horas) else None

    def ranking(self, k):
        if self._ranking is None:
            self._ranking = ordenar([(e.nombre, e.buses) for _, e in self.estaciones.elementos()],
                                    lambda par: (-par[1], par[0]))
        resultado = []
        for nombre, cantidad in self._ranking:
            if len(resultado) >= k:
                break
            if self._estacion(nombre).abierta:
                resultado.append((nombre, cantidad))
        return resultado

    def recorrido(self, ruta, al_reves=False):
        return self._ruta(ruta).valores(al_reves)

    def _registrar(self, operacion):
        self.atras.apilar(operacion)
        self.adelante.vaciar()

    def _estado(self, nombre, abierta):
        e = self._estacion(nombre)
        if e.abierta == abierta:
            return False
        previo = e.abierta
        e.abierta = abierta
        self._registrar(('estado', nombre, previo, abierta))
        return True

    def cerrar(self, nombre):
        return self._estado(nombre, False)

    def reabrir(self, nombre):
        return self._estado(nombre, True)

    def _insertar(self, ruta, nombre, anterior):
        recorrido = self._ruta(ruta)
        nodo = recorrido.insertar(nombre, recorrido.indice.obtener(anterior) if anterior else None)
        e = self._estacion(nombre)
        e.rutas.guardar(ruta, nodo)
        e.buses += len(self._horas(ruta, nombre))
        self._ranking = None

    def _quitar(self, ruta, nombre):
        recorrido = self._ruta(ruta)
        recorrido.quitar(recorrido.indice.obtener(nombre))
        e = self._estacion(nombre)
        e.rutas.borrar(ruta)
        e.buses -= len(self._horas(ruta, nombre))
        self._ranking = None

    def agregar_parada(self, ruta, nueva, despues_de):
        self._estacion(nueva)
        recorrido = self._ruta(ruta)
        if recorrido.indice.obtener(nueva) is not None:
            raise ValueError('La parada ya existe en la ruta')
        if recorrido.indice.obtener(despues_de) is None:
            raise ValueError('Parada de referencia inexistente')
        self._insertar(ruta, nueva, despues_de)
        self._registrar(('insertar', ruta, nueva, despues_de))
        return True

    def quitar_parada(self, ruta, estacion):
        recorrido = self._ruta(ruta)
        nodo = recorrido.indice.obtener(estacion)
        if nodo is None:
            raise ValueError('La parada no pertenece a la ruta')
        anterior = nodo.anterior.valor if nodo.anterior else None
        self._quitar(ruta, estacion)
        self._registrar(('quitar', ruta, estacion, anterior))
        return True

    def _aplicar(self, op, inversa):
        tipo, a, b, c = op
        if tipo == 'estado':
            self._estacion(a).abierta = b if inversa else c
        elif (tipo == 'insertar' and not inversa) or (tipo == 'quitar' and inversa):
            self._insertar(a, b, c)
        else:
            self._quitar(a, b)

    def deshacer(self):
        op = self.atras.sacar()
        if op is None:
            return False
        self._aplicar(op, True)
        self.adelante.apilar(op)
        return True

    def rehacer(self):
        op = self.adelante.sacar()
        if op is None:
            return False
        self._aplicar(op, False)
        self.atras.apilar(op)
        return True

    def viaje(self, origen, destino):
        if self.estado(origen) != 'abierta' or self.estado(destino) != 'abierta':
            return None
        if origen == destino:
            return Viaje([], None, [origen], 0, [])
        mejor = None
        # Cada tramo sigue enlaces hacia adelante: nunca se inventa sentido inverso.
        for ruta1, inicio in self._estacion(origen).rutas.elementos():
            tramo1 = [origen]
            nodo = inicio.siguiente
            while nodo:
                tramo1.append(nodo.valor)
                if nodo.valor == destino:
                    candidato = (len(tramo1)-1, 0, ruta1, '', '', tramo1[:], [tramo1[:]])
                    if mejor is None or candidato[:5] < mejor[:5]:
                        mejor = candidato
                if self._estacion(nodo.valor).abierta:
                    for ruta2, cambio in self._estacion(nodo.valor).rutas.elementos():
                        if ruta1 == ruta2:
                            continue
                        tramo2 = [nodo.valor]
                        fin = cambio.siguiente
                        while fin:
                            tramo2.append(fin.valor)
                            if fin.valor == destino:
                                candidato = (len(tramo1)+len(tramo2)-2, 1, ruta1, ruta2,
                                             nodo.valor, tramo1[:] + tramo2[1:], [tramo1[:], tramo2[:]])
                                if mejor is None or candidato[:5] < mejor[:5]:
                                    mejor = candidato
                                break
                            fin = fin.siguiente
                nodo = nodo.siguiente
        if mejor is None:
            return None
        rutas = [mejor[2], mejor[3]] if mejor[1] else [mejor[2]]
        return Viaje(rutas, mejor[4] if mejor[1] else None, mejor[5], mejor[0], mejor[6])

    def rutas_estacion(self, estacion):
        """Catálogo dirigido (ID, primer extremo, último extremo), solo abiertas."""
        e = self._estacion(estacion)
        if not e.abierta:
            return []
        salida = []
        for nombre, _ in e.rutas.elementos():
            r = self._ruta(nombre)
            salida.append((nombre, r.primero.valor, r.ultimo.valor))
        return ordenar(salida)

    def siguientes_horarios(self, estacion, ruta, hora, cantidad=5):
        """Extensión de lectura; mismo lower bound y semántica inclusiva que R4."""
        tiempo = minutos(hora)
        if type(cantidad) is not int or cantidad < 1 or cantidad > 5:
            raise ValueError('Solicite entre uno y cinco eventos')
        if self.estado(estacion) != 'abierta':
            raise ValueError('La estación no existe o está cerrada')
        recorrido = self._ruta(ruta)
        if recorrido.indice.obtener(estacion) is None:
            raise ValueError('La ruta no pasa por esta estación; seleccione una de sus rutas disponibles')
        horas = self._horas(ruta, estacion)
        i = limite(horas, tiempo)
        return [hora_texto(h) for h in horas[i:i + cantidad]]
