"""Laboratorio de hora pico: escenarios, métricas y trazas para R10.

Toda decisión de quién sube y cuándo viene de motor.simular_fila. Este
módulo solo genera llegadas sintéticas y resume/ilustra el resultado.
"""

import math
import random

from motor import simular_fila

LIMITE_EDUCATIVO = 40
LIMITE_AVANZADO = 300_000
DEMANDAS = ("uniforme", "pico", "dos_picos", "oleadas")


def generar_llegadas(pasajeros, duracion, demanda, semilla):
    """Minutos enteros de llegada en [0, duracion). Reproducible con semilla."""
    rnd = random.Random(semilla)
    llegadas = []
    for _ in range(pasajeros):
        if demanda == "uniforme":
            x = rnd.random() * duracion
        elif demanda == "pico":
            x = rnd.gauss(duracion * 0.5, duracion * 0.15)
        elif demanda == "dos_picos":
            centro = 0.3 if rnd.random() < 0.5 else 0.72
            x = rnd.gauss(duracion * centro, duracion * 0.08)
        else:  # oleadas: llegan en grupos cada ~10% de la duración
            ola = rnd.randrange(10)
            x = duracion * (ola / 10) + abs(rnd.gauss(0, duracion * 0.015))
        minuto = int(x)
        if minuto < 0:
            minuto = 0
        if minuto >= duracion:
            minuto = duracion - 1
        llegadas.append(minuto)
    return llegadas


def _percentil(ordenados, p):
    if not ordenados:
        return 0
    k = max(0, math.ceil(p / 100 * len(ordenados)) - 1)
    return ordenados[k]


def metricas(llegadas, abordajes, frecuencia, capacidad):
    n = len(llegadas)
    if n == 0:
        return {"pasajeros": 0}
    esperas = sorted(a - l for a, l in zip(abordajes, llegadas))
    por_bus = {}
    for a in abordajes:
        por_bus[a] = por_bus.get(a, 0) + 1
    primera = min(llegadas)
    primero = -(-primera // frecuencia) * frecuencia if primera > 0 else 0
    ultimo = max(abordajes)
    buses_ofrecidos = (ultimo - primero) // frecuencia + 1
    cola_max, minuto_cola_max = _cola_maxima(llegadas, abordajes)
    return {
        "pasajeros": n,
        "espera_media": sum(esperas) / n,
        "espera_mediana": _percentil(esperas, 50),
        "p90": _percentil(esperas, 90),
        "p95": _percentil(esperas, 95),
        "espera_maxima": esperas[-1],
        "sin_espera": sum(1 for e in esperas if e == 0),
        "buses_con_abordajes": len(por_bus),
        "buses_ofrecidos": buses_ofrecidos,
        "ocupacion_media": n / (len(por_bus) * capacidad),
        "buses_llenos": sum(1 for v in por_bus.values() if v == capacidad),
        "cola_maxima": cola_max,
        "minuto_cola_maxima": minuto_cola_max,
        "ultimo_abordaje": ultimo,
    }


def _cola_maxima(llegadas, abordajes):
    """Personas esperando justo antes de que salga cada bus (pico de la fila)."""
    cambios = {}
    for l in llegadas:
        cambios[l] = cambios.get(l, 0) + 1
    salidas = {}
    for a in abordajes:
        salidas[a] = salidas.get(a, 0) + 1
    tiempos = sorted(set(cambios) | set(salidas))
    actual, mayor, cuando = 0, 0, 0
    for t in tiempos:
        actual += cambios.get(t, 0)
        if actual > mayor:
            mayor, cuando = actual, t
        actual -= salidas.get(t, 0)
    return mayor, cuando


def series(llegadas, abordajes, capacidad, puntos=240):
    """Agregados para graficar sin enviar cada pasajero."""
    fin = max(abordajes) + 1
    paso = max(1, math.ceil(fin / puntos))
    nb = math.ceil(fin / paso)
    llegan = [0] * nb
    suben = [0] * nb
    for l in llegadas:
        llegan[max(0, l) // paso] += 1
    for a in abordajes:
        suben[a // paso] += 1
    cola = []
    acumulado = 0
    # fila al final de cada intervalo (después de los abordajes del intervalo)
    for i in range(nb):
        acumulado += llegan[i] - suben[i]
        cola.append(acumulado)
    por_bus = {}
    for a in abordajes:
        por_bus[a] = por_bus.get(a, 0) + 1
    buses = sorted(por_bus.items())
    if len(buses) > puntos:
        grupo = math.ceil(len(buses) / puntos)
        buses = [(buses[i][0], sum(v for _, v in buses[i:i + grupo]) / len(buses[i:i + grupo]))
                 for i in range(0, len(buses), grupo)]
    esperas = [a - l for a, l in zip(abordajes, llegadas)]
    emax = max(esperas)
    ancho = max(1, math.ceil((emax + 1) / 30))
    hist = [0] * (emax // ancho + 1)
    for e in esperas:
        hist[e // ancho] += 1
    return {
        "paso": paso,
        "llegadas": llegan,
        "abordajes": suben,
        "cola": cola,
        "ocupacion": [{"minuto": m, "ocupacion": v / capacidad} for m, v in buses],
        "histograma": {"ancho": ancho, "conteos": hist},
    }


def traza_educativa(llegadas, frecuencia, capacidad):
    """Pasos ENQUEUE/DEQUEUE reconstruidos a partir de los abordajes del motor."""
    abordajes = simular_fila(llegadas, frecuencia, capacidad)
    n = len(llegadas)
    orden = sorted(range(n), key=lambda i: llegadas[i])   # orden FIFO estable
    pasos = []
    eventos = sorted(set(llegadas) | set(abordajes))
    fila = []
    subidos = []
    for t in eventos:
        nuevos = [i for i in orden if llegadas[i] == t]
        if nuevos:
            fila.extend(nuevos)
            pasos.append({"tipo": "enqueue", "minuto": t, "pasajeros": nuevos,
                          "fila": list(fila), "subidos": list(subidos)})
        if t % frecuencia == 0 and t in set(abordajes):
            suben = [i for i in fila if abordajes[i] == t]
            fila = [i for i in fila if abordajes[i] != t]
            subidos.extend(suben)
            pasos.append({"tipo": "dequeue", "minuto": t, "pasajeros": suben,
                          "fila": list(fila), "subidos": list(subidos),
                          "cupos_libres": capacidad - len(suben)})
    return {
        "llegadas": llegadas,
        "abordajes": abordajes,
        "esperas": [a - l for a, l in zip(abordajes, llegadas)],
        "frecuencia": frecuencia,
        "capacidad": capacidad,
        "pasos": pasos,
        "metricas": metricas(llegadas, abordajes, frecuencia, capacidad),
    }


def escenario_avanzado(pasajeros, duracion, frecuencia, capacidad, demanda, semilla):
    llegadas = generar_llegadas(pasajeros, duracion, demanda, semilla)
    abordajes = simular_fila(llegadas, frecuencia, capacidad)
    return {
        "parametros": {"pasajeros": pasajeros, "duracion": duracion, "frecuencia": frecuencia,
                       "capacidad": capacidad, "demanda": demanda, "semilla": semilla},
        "metricas": metricas(llegadas, abordajes, frecuencia, capacidad),
        "series": series(llegadas, abordajes, capacidad),
    }


def comparar(pasajeros, duracion, demanda, semilla, config_a, config_b):
    """Mismas llegadas, dos configuraciones (frecuencia, capacidad)."""
    llegadas = generar_llegadas(pasajeros, duracion, demanda, semilla)
    resultado = {"parametros": {"pasajeros": pasajeros, "duracion": duracion,
                                "demanda": demanda, "semilla": semilla}}
    for nombre, (f, c) in (("a", config_a), ("b", config_b)):
        abordajes = simular_fila(llegadas, f, c)
        resultado[nombre] = {"frecuencia": f, "capacidad": c,
                             "metricas": metricas(llegadas, abordajes, f, c),
                             "series": series(llegadas, abordajes, c)}
    return resultado
