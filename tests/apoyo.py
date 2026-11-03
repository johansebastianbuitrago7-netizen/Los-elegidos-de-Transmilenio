"""Utilidades de prueba: redes sintéticas en carpetas temporales y
algoritmos de referencia independientes (aquí sí se usan dict/set/sorted,
porque las pruebas están fuera de motor/)."""

import csv
import os
import random
import tempfile
from collections import deque


def escribir_red(estaciones, rutas, horarios=()):
    """rutas: {nombre: [estaciones en orden]}; horarios: [(ruta, est, hora)]."""
    carpeta = tempfile.mkdtemp(prefix="atlas_")
    with open(os.path.join(carpeta, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        for e in estaciones:
            w.writerow([e])
    with open(os.path.join(carpeta, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "orden", "estacion"])
        for ruta, paradas in rutas.items():
            for i, e in enumerate(paradas, 1):
                w.writerow([ruta, i, e])
    with open(os.path.join(carpeta, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "estacion", "hora"])
        for fila in horarios:
            w.writerow(fila)
    return carpeta


def red_aleatoria(semilla, n_est=12, n_rutas=6, largo=(2, 7)):
    rnd = random.Random(semilla)
    estaciones = [f"E{i:02d}" for i in range(n_est)]
    rutas = {}
    for r in range(n_rutas):
        k = rnd.randint(largo[0], min(largo[1], n_est))
        rutas[f"R{r}"] = rnd.sample(estaciones, k)
    return estaciones, rutas


def viaje_referencia(rutas, cerradas, origen, destino):
    """Mejor costo (paradas) con <= 1 transbordo por fuerza bruta.

    Devuelve (costo, transbordos) o None. Enumera toda ruta r1 y todo
    par de posiciones; para transbordo enumera toda ruta r2.
    """
    if origen in cerradas or destino in cerradas:
        return None
    if origen == destino:
        return (0, 0)
    mejor = None
    for r1, p1 in rutas.items():
        if origen not in p1:
            continue
        i = p1.index(origen)
        for j in range(i + 1, len(p1)):
            t = p1[j]
            if t == destino:
                cand = (j - i, 0)
                mejor = cand if mejor is None or cand < mejor else mejor
            if t in cerradas or t == destino:
                continue
            for r2, p2 in rutas.items():
                if r2 == r1 or t not in p2 or destino not in p2:
                    continue
                a, b = p2.index(t), p2.index(destino)
                if b > a:
                    cand = (j - i + b - a, 1)
                    mejor = cand if mejor is None or cand < mejor else mejor
    return mejor


def viaje_bfs01(rutas, cerradas, origen, destino):
    """Referencia alternativa: 0-1 BFS sobre estados (estación, ruta, transbordos).

    Bajarse/subirse cuesta 0 paradas pero consume un transbordo; avanzar
    una parada cuesta 1. Solo se puede subir/bajar en estaciones abiertas.
    """
    if origen in cerradas or destino in cerradas:
        return None
    if origen == destino:
        return 0
    sig = {}
    for r, p in rutas.items():
        for a, b in zip(p, p[1:]):
            sig[(r, a)] = b
    INF = float("inf")
    dist = {}
    dq = deque()
    for r, p in rutas.items():
        if origen in p:
            dist[(origen, r, 0)] = 0
            dq.append((0, origen, r, 0))
    mejor = INF
    while dq:
        d, e, r, t = dq.popleft()
        if d > dist.get((e, r, t), INF):
            continue
        if e == destino and e not in cerradas:
            mejor = min(mejor, d)
        nxt = sig.get((r, e))
        if nxt is not None and dist.get((nxt, r, t), INF) > d + 1:
            dist[(nxt, r, t)] = d + 1
            dq.append((d + 1, nxt, r, t))
        if t == 0 and e not in cerradas and e != origen:
            for r2, p2 in rutas.items():
                if r2 != r and e in p2 and dist.get((e, r2, 1), INF) > d:
                    dist[(e, r2, 1)] = d
                    dq.appendleft((d, e, r2, 1))
    return None if mejor == INF else mejor


def fila_referencia(llegadas, f, c):
    """Simulación directa minuto a minuto de bus en bus (O(n * buses))."""
    pendientes = sorted(range(len(llegadas)), key=lambda i: llegadas[i])
    res = [None] * len(llegadas)
    bus = 0
    while pendientes:
        listos = [i for i in pendientes if llegadas[i] <= bus][:c]
        for i in listos:
            res[i] = bus
        quitar = set(listos)
        pendientes = [i for i in pendientes if i not in quitar]
        bus += f
    return res
