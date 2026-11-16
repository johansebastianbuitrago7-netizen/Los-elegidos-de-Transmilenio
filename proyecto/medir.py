"""R11: mide cada operacion con redes de tamano creciente (n, 2n, 4n...).
Uso: python medir.py   -> imprime tabla y guarda rendimiento.png / rendimiento.csv
Aqui si se puede usar cualquier libreria (esto no es motor/)."""
import gc
import random
import sys
import tempfile
import time

from motor import Red, simular_fila

TAMANOS = [1000, 2000, 4000, 8000, 16000]   # n = estaciones
PASAJEROS = [100000, 200000, 400000, 800000]
ESPERADO = {
    "R1 estado": "O(1)", "R2 autocompletar": "O(log n + k)", "R3 rango": "O(log n + m)",
    "R4 proximo_bus": "O(log h)", "R6 ranking": "O(log n + k)",
    "R7 agregar+quitar": "O(1)", "R8 cerrar+reabrir": "O(log n)",
    "R9 deshacer+rehacer": "O(log n)", "R10 simular_fila": "O(P + B)",
}


def generar(n, semilla=1):
    rnd = random.Random(semilla)
    d = tempfile.mkdtemp()
    nombres = ["ESTACION %06d" % i for i in range(n)]
    with open(d + "/estaciones.csv", "w") as f:
        f.write("nombre\n" + "\n".join(nombres) + "\n")
    rutas = n // 8
    with open(d + "/rutas.csv", "w") as fr, open(d + "/horarios.csv", "w") as fh:
        fr.write("ruta,orden,estacion\n")
        fh.write("ruta,estacion,hora\n")
        for r in range(rutas):
            paradas = rnd.sample(nombres, 20)
            horas = sorted(rnd.randint(300, 1400) for _ in range(30))
            for o, e in enumerate(paradas, 1):
                fr.write("R%d,%d,%s\n" % (r, o, e))
                for h in horas:
                    fh.write("R%d,%s,%02d:%02d\n" % (r, e, (h + o) // 60, (h + o) % 60))
    return d, nombres, rutas


def medir(fn, reps):
    """Mejor de 5 tandas (descarta ruido del sistema) con el recolector de basura apagado."""
    for _ in range(reps // 5):
        fn()  # calentamiento
    mejor = None
    for _ in range(5):
        gc.collect()
        gc.disable()
        t = time.perf_counter()
        for _ in range(reps):
            fn()
        dt = (time.perf_counter() - t) / reps
        gc.enable()
        if mejor is None or dt < mejor:
            mejor = dt
    return mejor


def main():
    filas = {k: [] for k in ESPERADO}
    for n in TAMANOS:
        d, nombres, nr = generar(n)
        t0 = time.perf_counter()
        red = Red(d)
        carga = time.perf_counter() - t0
        rnd = random.Random(5)
        est = [rnd.choice(nombres) for _ in range(2000)]
        ruta = ["R%d" % rnd.randrange(nr) for _ in range(2000)]
        i = [0]

        def sig():
            i[0] = (i[0] + 1) % 2000
            return i[0]

        def r1():
            red.estado(est[sig()])

        def r2():
            red.autocompletar("ESTACION 00%d" % (sig() % 10), 10)

        def r3():
            a = sig() % n
            red.rango(nombres[a], nombres[a + 50] if a + 50 < n else nombres[-1])

        def r4():
            j = sig()
            red.proximo_bus(est[j], ruta[j], "12:00")

        def r6():
            red.ranking(10)

        def r7():
            x = ruta[sig()]
            rec = red.recorrido(x)
            nuevo = nombres[(i[0] * 7919) % n]
            if red.agregar_parada(x, nuevo, rec[3]):
                red.quitar_parada(x, nuevo)

        def r8():
            e = est[sig()]
            red.cerrar(e)
            red.reabrir(e)

        def r9():
            red.cerrar(est[sig()])
            red.deshacer()
            red.rehacer()
            red.deshacer()

        pruebas = [("R1 estado", r1, 20000), ("R2 autocompletar", r2, 5000),
                   ("R3 rango", r3, 3000), ("R4 proximo_bus", r4, 20000),
                   ("R6 ranking", r6, 5000), ("R7 agregar+quitar", r7, 5000),
                   ("R8 cerrar+reabrir", r8, 5000), ("R9 deshacer+rehacer", r9, 5000)]
        for nombre, fn, reps in pruebas:
            filas[nombre].append(medir(fn, reps))
        print("n=%d carga=%.2fs" % (n, carga), file=sys.stderr)
    for p in PASAJEROS:
        rnd = random.Random(3)
        t = 0
        ll = []
        for _ in range(p):
            t += rnd.randint(0, 2)
            ll.append(t)
        filas["R10 simular_fila"].append(medir(lambda: simular_fila(ll, 30, 160), 1))

    lineas = ["operacion,esperado," + ",".join(str(x) for x in TAMANOS)]
    print("\n%-22s %-14s %s" % ("operacion", "esperado", "tiempo al duplicar n (x veces)"))
    for k, v in filas.items():
        razones = ["%.2f" % (v[j + 1] / v[j]) for j in range(len(v) - 1)]
        print("%-22s %-14s %s" % (k, ESPERADO[k], "  ".join(razones)))
        lineas.append(k + "," + ESPERADO[k] + "," + ",".join("%.3e" % x for x in v))
    open("rendimiento.csv", "w").write("\n".join(lineas) + "\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ejes = plt.subplots(3, 3, figsize=(12, 9))
        for ax, (k, v) in zip(ejes.flat, filas.items()):
            xs = PASAJEROS if k.startswith("R10") else TAMANOS
            ax.plot(xs, [x * 1e6 for x in v], marker="o")
            ax.set_title("%s  (%s)" % (k, ESPERADO[k]), fontsize=9)
            ax.set_xlabel("pasajeros P" if k.startswith("R10") else "estaciones n")
            ax.set_ylabel("microsegundos" if not k.startswith("R10") else "us (total)")
            ax.set_ylim(bottom=0)
        fig.tight_layout()
        fig.savefig("rendimiento.png", dpi=110)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
