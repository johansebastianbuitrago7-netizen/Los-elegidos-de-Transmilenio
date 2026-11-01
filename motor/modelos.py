"""Retornos públicos sin dependencia de web ni serializadores."""

class Estacion:
    def __init__(self, nombre):
        from .estructuras import TablaHash
        self.nombre = nombre
        self.abierta = True
        self.rutas = TablaHash()
        self.buses = 0


class Viaje:
    def __init__(self, rutas, transbordo, estaciones, paradas, tramos):
        self.rutas = rutas
        self.transbordo = transbordo
        self.estaciones = estaciones
        self.paradas = paradas
        self.tramos = tramos


class Simulacion:
    def __init__(self, abordajes, esperas, buses):
        self.abordajes = abordajes
        self.esperas = esperas
        self.buses = buses
        self.pasajeros = len(esperas)
        total, mayor = 0, 0
        for espera in esperas:
            total += espera
            if espera > mayor:
                mayor = espera
        self.espera_media = total / self.pasajeros if self.pasajeros else 0
        self.espera_maxima = mayor


def minutos(hora):
    if not isinstance(hora, str):
        raise ValueError('La hora debe ser HH:MM')
    partes = hora.split(':')
    if len(partes) != 2 or not partes[0].isdigit() or not partes[1].isdigit():
        raise ValueError('La hora debe ser HH:MM (admite horas de servicio >= 24)')
    h, m = int(partes[0]), int(partes[1])
    if m >= 60 or len(partes[1]) != 2 or len(partes[0]) < 2:
        raise ValueError('Hora inválida')
    return h * 60 + m


def hora_texto(valor):
    return str(valor // 60).zfill(2) + ':' + str(valor % 60).zfill(2)
