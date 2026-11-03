"""R11: mediciones reales de cada operación con redes de tamaño creciente.

Método (el mismo del enunciado): se genera una red sintética de tamaño n,
se mide, se duplica n y se vuelve a medir. Cada red vive en una carpeta
temporal propia: nunca se toca la red compartida de la aplicación, y la
carga se mide aparte de las consultas.

Para cada operación se reporta la mediana de varias repeticiones (cada
repetición cronometra un lote de llamadas para superar la resolución del
reloj), el rango observado y la razón t(2n)/t(n) frente a la esperada.
"""

import csv
import math
import os
import random
import shutil
import statistics
import tempfile
import time

from motor import Red, simular_fila

LARGO_RUTA = 12
EVENTOS_POR_PARADA = 6

# clave: (nombre, requisito, complejidad esperada, qué es n, función de costo)
OPERACIONES = [
    ("carga", "Carga", "O(N log N)", "N = filas de los CSV", lambda n: n * math.log2(n)),
    ("estado", "R1", "O(1)", "n = estaciones", lambda n: 1),
    ("autocompletar", "R2", "O(log n + k)", "n = estaciones, k = 10", lambda n: math.log2(n)),
    ("rango", "R3", "O(log n + m)", "n = estaciones, m = 20 resultados", lambda n: math.log2(n)),
    ("proximo_bus", "R4", "O(log m)", "m = eventos de la pareja ruta-estación (m ∝ n)", lambda n: math.log2(n)),
    ("viaje", "R5", "no se evalúa", "suma de largos de rutas en origen y destino", None),
    ("ranking", "R6", "O(k)", "consulta en caché, k = 10", lambda n: 1),
    ("ranking_tras_cambio", "R6", "O(n log n)", "reconstrucción tras un cierre", lambda n: n * math.log2(n)),
    ("editar", "R7", "O(1)", "agregar + quitar una parada", lambda n: 1),
    ("recorrido", "R7", "O(L)", "L = paradas de la ruta (fijo = 12)", lambda n: 1),
    ("cerrar", "R8", "O(1)", "cerrar + reabrir", lambda n: 1),
    ("deshacer", "R9", "O(1)", "deshacer + rehacer", lambda n: 1),
    ("fila", "R10", "O(p log p)", "p = pasajeros = 40·n (llegadas desordenadas)", lambda n: n * math.log2(n)),
]


def generar_red(n, semilla=7):
    """Red sintética con n estaciones, n/3 rutas de 12 paradas y una troncal
    cuyo número de eventos en su primera parada crece con n (para R4)."""
    rnd = random.Random(semilla)
    carpeta = tempfile.mkdtemp(prefix=f"atlas_rend_{n}_")
    nombres = [f"ESTACION {i:06d}" for i in range(n)]
    rutas = []
    for r in range(max(1, n // 3)):
        rutas.append((f"S{r}-1", rnd.sample(nombres, LARGO_RUTA)))
    troncal = ("TRONCAL-1", nombres[:LARGO_RUTA])
    rutas.append(troncal)
    with open(os.path.join(carpeta, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        for e in rnd.sample(nombres, n):          # desordenadas a propósito
            w.writerow([e])
    filas = 0
    with open(os.path.join(carpeta, "rutas.csv"), "w", newline="", encoding="utf-8") as f, \
            open(os.path.join(carpeta, "horarios.csv"), "w", newline="", encoding="utf-8") as g:
        wr, wh = csv.writer(f), csv.writer(g)
        wr.writerow(["ruta", "orden", "estacion"])
        wh.writerow(["ruta", "estacion", "hora"])
        for nombre, paradas in rutas:
            for i, e in enumerate(paradas, 1):
                wr.writerow([nombre, i, e])
                eventos = 2 * n if nombre == "TRONCAL-1" and i == 1 else EVENTOS_POR_PARADA
                for _ in range(eventos):
                    m = rnd.randrange(4 * 60, 24 * 60)
                    wh.writerow([nombre, e, f"{m // 60:02d}:{m % 60:02d}"])
                    filas += 1
    return carpeta, nombres, rutas, filas + n + len(rutas) * LARGO_RUTA


def _cronometrar(funcion, lote, repeticiones):
    muestras = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion(lote)
        muestras.append((time.perf_counter() - inicio) / lote)
    return muestras


def medir(tamanos=(250, 500, 1000, 2000, 4000), repeticiones=5, semilla=7):
    resultados = {clave: [] for clave, *_ in OPERACIONES}
    for n in tamanos:
        carpeta, nombres, rutas, filas = generar_red(n, semilla)
        try:
            cargas = []
            red = None
            for _ in range(max(2, repeticiones // 2)):
                inicio = time.perf_counter()
                red = Red(carpeta)
                cargas.append(time.perf_counter() - inicio)
            resultados["carga"].append(_fila(n, cargas, filas))
            rnd = random.Random(semilla + n)
            ordenados = sorted(nombres)
            consultas = [rnd.choice(nombres) for _ in range(512)]
            pares = [(rnd.choice(nombres), rnd.choice(nombres)) for _ in range(64)]
            horas = [f"{h:02d}:{m:02d}" for h, m in ((rnd.randrange(24), rnd.randrange(60)) for _ in range(512))]
            ruta_editable, paradas = rutas[0]
            fuera = next(e for e in nombres if e not in set(paradas))

            def estado(lote):
                for i in range(lote):
                    red.estado(consultas[i % 512])

            def autocompletar(lote):
                for i in range(lote):
                    red.autocompletar(consultas[i % 512][:12], 10)

            def rango(lote):
                for i in range(lote):
                    j = (i * 37) % (n - 20)
                    red.rango(ordenados[j], ordenados[j + 19])

            def proximo(lote):
                for i in range(lote):
                    red.proximo_bus(nombres[0], "TRONCAL-1", horas[i % 512])

            def viaje(lote):
                for i in range(lote):
                    o, d = pares[i % 64]
                    red.viaje(o, d)

            def ranking(lote):
                for _ in range(lote):
                    red.ranking(10)

            def ranking_cambio(lote):
                for i in range(lote):
                    e = consultas[i % 512]
                    red.cerrar(e)
                    red.ranking(10)
                    red.reabrir(e)

            def editar(lote):
                for _ in range(lote):
                    red.agregar_parada(ruta_editable, fuera, paradas[5])
                    red.quitar_parada(ruta_editable, fuera)

            def recorrido(lote):
                for _ in range(lote):
                    red.recorrido(ruta_editable, True)

            def cerrar(lote):
                for i in range(lote):
                    e = consultas[i % 512]
                    red.cerrar(e)
                    red.reabrir(e)

            def deshacer(lote):
                for _ in range(lote):
                    red.deshacer()
                    red.rehacer()

            pasajeros = 40 * n
            llegadas = [rnd.randrange(0, 600) for _ in range(pasajeros)]

            def fila(lote):
                for _ in range(lote):
                    simular_fila(llegadas, 3, 150)

            plan = [("estado", estado, 4000), ("autocompletar", autocompletar, 2000),
                    ("rango", rango, 1000), ("proximo_bus", proximo, 4000),
                    ("viaje", viaje, 64), ("ranking", ranking, 4000),
                    ("ranking_tras_cambio", ranking_cambio, 3), ("editar", editar, 2000),
                    ("recorrido", recorrido, 2000), ("cerrar", cerrar, 4000),
                    ("deshacer", deshacer, 2000), ("fila", fila, 1)]
            for clave, funcion, lote in plan:
                funcion(min(lote, 50))   # calentamiento
                tamano = pasajeros if clave == "fila" else n
                resultados[clave].append(_fila(tamano, _cronometrar(funcion, lote, repeticiones), None))
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)
    return _informe(resultados, tamanos, repeticiones)


def _fila(n, muestras, filas):
    return {"n": n, "filas": filas, "mediana": statistics.median(muestras),
            "minimo": min(muestras), "maximo": max(muestras)}


def _informe(resultados, tamanos, repeticiones):
    operaciones = []
    for clave, requisito, esperada, que_es_n, costo in OPERACIONES:
        puntos = resultados[clave]
        if clave == "carga":
            for p in puntos:
                p["n"] = p["filas"]
        base = puntos[0]
        teoria = None
        if costo is not None:
            teoria = [base["mediana"] * costo(p["n"]) / costo(base["n"]) for p in puntos]
        razones = []
        for a, b in zip(puntos, puntos[1:]):
            razon = {"observada": b["mediana"] / a["mediana"] if a["mediana"] else None}
            if costo is not None:
                razon["esperada"] = costo(b["n"]) / costo(a["n"])
            razones.append(razon)
        operaciones.append({"clave": clave, "requisito": requisito, "esperada": esperada,
                            "n": que_es_n, "puntos": puntos, "teoria": teoria,
                            "razones": razones, "veredicto": _veredicto(razones)})
    return {"tamanos": list(tamanos), "repeticiones": repeticiones,
            "generado": time.strftime("%Y-%m-%d %H:%M:%S"), "operaciones": operaciones}


def _veredicto(razones):
    """Compara razones observadas con las esperadas, con tolerancia por ruido."""
    validas = [r for r in razones if r.get("esperada") and r["observada"]]
    if not validas:
        return "sin referencia"
    desvio = statistics.median(r["observada"] / r["esperada"] for r in validas)
    if desvio < 1.35:
        return "coincide"
    if desvio < 1.8:
        return "ruido o efecto de caché"
    return "crece más de lo esperado"
