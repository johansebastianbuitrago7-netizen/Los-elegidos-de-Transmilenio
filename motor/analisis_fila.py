"""Métricas derivadas del resultado público, sin volver a asignar abordajes FIFO."""
from .estructuras import TablaHash, ordenar


class AnalisisFila:
    def __init__(self, llegadas, resultado, frecuencia, capacidad):
        self.pasajeros = resultado.pasajeros
        self.abordados = resultado.pasajeros
        self.espera_media = resultado.espera_media
        self.espera_maxima = resultado.espera_maxima
        self.buses = resultado.buses
        self.espera_total = 0
        self.espera_mediana = 0
        self.espera_p95 = 0
        self.ocupacion_media = 0
        self.cola_maxima = 0
        self.ultimo_abordaje = 0
        self.fila = []
        self.ocupacion = []
        self.distribucion = []
        self.demanda = []
        n = resultado.pasajeros
        if n == 0:
            return
        esperas = ordenar(resultado.esperas)
        for espera in esperas:
            self.espera_total += espera
        self.espera_mediana = (esperas[(n-1)//2] + esperas[n//2])/2
        self.espera_p95 = esperas[(95*n+99)//100-1]
        self.ocupacion_media = n / (resultado.buses * capacidad)
        # Por minuto: llegadas y abordajes provistos por el motor, no otra cola.
        eventos = TablaHash()
        for llegada, abordaje in zip(llegadas, resultado.abordajes):
            for tiempo, tipo in [(llegada, 0), (abordaje, 1)]:
                par = eventos.obtener(str(tiempo))
                if par is None:
                    par = [0, 0]
                    eventos.guardar(str(tiempo), par)
                par[tipo] += 1
        pendiente = 0
        for tiempo, par in ordenar([(int(t), p) for t, p in eventos.elementos()]):
            antes = pendiente + par[0]
            if antes > self.cola_maxima:
                self.cola_maxima = antes
            pendiente = antes - par[1]
            self.fila.append((tiempo, antes, pendiente))
            if par[1]:
                self.ocupacion.append((tiempo, par[1], capacidad-par[1]))
                self.ultimo_abordaje = tiempo
        # Histograma de hasta 20 intervalos, extremos inclusivos.
        ancho = self.espera_maxima // 20 + 1
        bins = [0] * (self.espera_maxima // ancho + 1)
        for espera in esperas:
            bins[espera // ancho] += 1
        for i, conteo in enumerate(bins):
            self.distribucion.append((i*ancho, (i+1)*ancho-1, conteo))
        # Intervalos de ancho f: llegadas en [inicio,fin), oferta en ese inicio.
        demanda = TablaHash()
        for llegada in llegadas:
            inicio = (llegada // frecuencia)*frecuencia
            demanda.guardar(str(inicio), demanda.obtener(str(inicio), 0)+1)
        # No iterar miles de millones de intervalos vacíos: solo bloques con demanda.
        for inicio, cantidad in ordenar([(int(t), c) for t, c in demanda.elementos()]):
            self.demanda.append((inicio, inicio+frecuencia, cantidad, capacidad))
