"""Lectura de los tres CSV (solo modulo csv)."""
import csv

from .algoritmos import esta_ordenada, ordenar


def _ruta_archivo(carpeta, nombre):
    carpeta = str(carpeta)
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + nombre
    return carpeta + "/" + nombre


def _filas(carpeta, nombre):
    with open(_ruta_archivo(carpeta, nombre), newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        next(lector, None)  # encabezado
        for fila in lector:
            if fila:
                yield fila


def minutos(hora):
    """'HH:MM' -> minutos desde el inicio del dia de servicio.
    Horas >= 24 (ej. '25:10') se conservan como 1510: sin envolver al dia siguiente."""
    partes = hora.strip().split(":")
    return int(partes[0]) * 60 + int(partes[1])


def formato(m):
    return str(m // 60).zfill(2) + ":" + str(m % 60).zfill(2)


def leer_estaciones(carpeta):
    vistas = {}
    for fila in _filas(carpeta, "estaciones.csv"):
        nombre = fila[0].strip()
        if nombre != "":
            vistas[nombre] = True  # dict conserva orden y elimina repetidos
    return list(vistas)


def leer_rutas(carpeta):
    """-> dict ruta -> [estaciones en orden]."""
    pares = {}
    for fila in _filas(carpeta, "rutas.csv"):
        try:
            orden = int(fila[1])
        except ValueError:
            continue
        r = fila[0].strip()
        if r not in pares:
            pares[r] = []
        pares[r].append((orden, fila[2].strip()))
    rutas = {}
    for r in pares:
        lista = pares[r]
        if not esta_ordenada(lista):
            lista = ordenar(lista)
        rutas[r] = [e for _, e in lista]
    return rutas


def leer_horarios(carpeta):
    """-> dict (ruta, estacion) -> [minutos ordenados]."""
    h = {}
    for fila in _filas(carpeta, "horarios.csv"):
        try:
            m = minutos(fila[2])
        except (ValueError, IndexError):
            continue
        clave = (fila[0].strip(), fila[1].strip())
        if clave in h:
            h[clave].append(m)
        else:
            h[clave] = [m]
    for clave in h:
        if not esta_ordenada(h[clave]):
            h[clave] = ordenar(h[clave])
    return h
