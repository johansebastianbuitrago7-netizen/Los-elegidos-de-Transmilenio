"""R11: panel de rendimiento. Corre cada operacion del motor con redes de tamano creciente."""
import gc
import random
import time

from medir import generar
from motor import Red, simular_fila

MAX_N = 256000  # tamano maximo por medicion

ESPERADO = {
    "R1 estado": "O(1)", "R2 autocompletar": "O(log n + k)", "R3 rango": "O(log n + m)",
    "R4 proximo_bus": "O(log h)", "R6 ranking": "O(log n + k)",
    "R7 agregar+quitar": "O(1)", "R8 cerrar+reabrir": "O(log n)",
    "R9 deshacer+rehacer": "O(log n)", "R10 simular_fila": "O(P + B)",
}


def tiempo(fn, reps):
    """Mejor de 3 tandas, en microsegundos por llamada."""
    for _ in range(reps // 5):
        fn()
    mejor = None
    for _ in range(3):
        gc.collect()
        gc.disable()
        t = time.perf_counter()
        for _ in range(reps):
            fn()
        dt = (time.perf_counter() - t) / reps
        gc.enable()
        mejor = dt if mejor is None or dt < mejor else mejor
    return mejor * 1e6


def operaciones(red, nombres, nr):
    n = len(nombres)
    rnd = random.Random(5)
    est = [rnd.choice(nombres) for _ in range(500)]
    ruta = ["R%d" % rnd.randrange(nr) for _ in range(500)]
    c = [0]

    def s():
        c[0] = (c[0] + 1) % 500
        return c[0]

    def r3():
        a = (s() * 7) % n
        red.rango(nombres[a], nombres[a + 40 if a + 40 < n else n - 1])

    def r4():
        j = s()
        red.proximo_bus(est[j], ruta[j], "12:00")

    def r7():
        j = s()
        x = ruta[j]
        nuevo = nombres[(j * 7919) % n]
        if red.agregar_parada(x, nuevo, red.recorrido(x)[3]):
            red.quitar_parada(x, nuevo)

    def r8():
        e = est[s()]
        red.cerrar(e)
        red.reabrir(e)

    def r9():
        red.cerrar(est[s()])
        red.deshacer()
        red.rehacer()
        red.deshacer()

    return [("R1 estado", lambda: red.estado(est[s()]), 5000),
            ("R2 autocompletar", lambda: red.autocompletar("ESTACION 00%d" % (s() % 10), 10), 2000),
            ("R3 rango", r3, 1000), ("R4 proximo_bus", r4, 5000),
            ("R6 ranking", lambda: red.ranking(10), 2000), ("R7 agregar+quitar", r7, 2000),
            ("R8 cerrar+reabrir", r8, 2000), ("R9 deshacer+rehacer", r9, 2000)]


def veredicto(esp, razones):
    if not razones:
        return "Pon al menos dos tamanos para comparar."
    lineal = esp.startswith("O(P")
    ok = all(1.6 <= r <= 2.6 for r in razones) if lineal else all(r < 1.6 for r in razones)
    media = sum(razones) / len(razones)
    if ok:
        return "Coincide: al duplicar n el tiempo se multiplica por %.2f en promedio." % media
    return ("No coincide del todo (media x%.2f al duplicar). Suele ser la memoria cache y el "
            "recolector de basura al crecer las estructuras; prueba con tamanos mayores." % media)


def medir_uno(n):
    """Mide todas las operaciones para UN tamano. Asi el panel dibuja cada punto en cuanto llega."""
    n = int(n)
    if n < 2:
        raise ValueError("el tamano debe ser al menos 2")
    if n > MAX_N:
        raise ValueError("el tamano maximo es %d" % MAX_N)
    d, nombres, nr = generar(n)
    red = Red(d)
    tiempos = {}
    for nom, fn, reps in operaciones(red, nombres, nr):
        tiempos[nom] = tiempo(fn, reps)
    rnd = random.Random(3)
    t, ll = 0, []
    for _ in range(n * 50):
        t += rnd.randint(0, 2)
        ll.append(t)
    tiempos["R10 simular_fila"] = tiempo(lambda: simular_fila(ll, 30, 160), 1)
    return {"n": n, "tiempos": tiempos, "esperado": ESPERADO}


def correr(b):
    tam = [int(x) for x in (b.get("tamanos") or [500, 1000, 2000, 4000])]
    res = {k: [] for k in ESPERADO}
    for n in tam:
        d, nombres, nr = generar(n)
        red = Red(d)
        for nom, fn, reps in operaciones(red, nombres, nr):
            res[nom].append(tiempo(fn, reps))
        rnd = random.Random(3)
        t, ll = 0, []
        for _ in range(n * 50):
            t += rnd.randint(0, 2)
            ll.append(t)
        res["R10 simular_fila"].append(tiempo(lambda: simular_fila(ll, 30, 160), 1))
    ops = []
    for k, v in res.items():
        razones = [v[i + 1] / v[i] for i in range(len(v) - 1)]
        ops.append({"op": k, "esperado": ESPERADO[k], "tiempos": v, "razones": razones,
                    "veredicto": veredicto(ESPERADO[k], razones)})
    return {"tamanos": tam, "ops": ops}
