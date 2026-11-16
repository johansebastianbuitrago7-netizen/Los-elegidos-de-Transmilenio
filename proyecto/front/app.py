"""Front web del planeador. Solo llama al motor (motor/) y lee datos/.
Arrancar:  python front/app.py [puerto]   ->  abre http://127.0.0.1:8000"""
import bisect
import csv
import json
import os
import random
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
from motor import Red, simular_fila  # noqa: E402
import rendimiento  # noqa: E402

DATOS = os.path.join(RAIZ, "datos")
red = Red(DATOS)
cerrojo = threading.Lock()
with open(os.path.join(DATOS, "rutas.csv"), newline="", encoding="utf-8-sig") as f:
    RUTAS = sorted({fila[0] for fila in list(csv.reader(f))[1:] if fila})


def p(q, k, d=""):
    return q.get(k, [d])[0]


def fila(b):
    n, dur = int(b["pasajeros"]), float(b["minutos"])
    fr, cap = float(b["frecuencia"]), int(b["capacidad"])
    ll = sorted(random.uniform(0, dur) for _ in range(n))
    sal = simular_fila(ll, fr, cap)
    serie, abordados = [], 0
    for t, ids in sal:
        abordados += len(ids)
        serie.append([round(t, 2), len(ids), bisect.bisect_right(ll, t) - abordados])
    suma, peor = 0.0, 0.0
    for t, ids in sal:
        for j in ids:
            e = t - ll[j]
            suma += e
            peor = e if e > peor else peor
    return {"buses": len(sal), "ultima_salida": sal[-1][0] if sal else 0,
            "espera_media": suma / n if n else 0, "espera_max": peor,
            "primeros": [[t, len(ids)] for t, ids in sal[:12]], "serie": serie[:600]}


def horarios(ruta, est):
    """Todas las salidas de la ruta en esa parada, preguntando al motor (proximo_bus) una a una."""
    out, m = [], 0
    while True:
        h = red.proximo_bus(est, ruta, m)
        if h is None:
            return out
        out.append(h)
        m = int(h[:2]) * 60 + int(h[3:5]) + 1


def buses():
    res = []
    for r in RUTAS:
        rec = red.recorrido(r)
        hs = []
        for est in rec:
            hs = horarios(r, est)
            if hs:
                break
        if rec:
            res.append({"ruta": r, "origen": rec[0], "destino": rec[-1], "paradas": len(rec),
                        "primero": hs[0] if hs else None, "ultimo": hs[-1] if hs else None,
                        "salidas": len(hs)})
    return res


def wrapped():
    """Datos originales 2016 tal como vienen en datos/ (no cambian con las ediciones del usuario)."""
    def filas(nombre):
        with open(os.path.join(DATOS, nombre), newline="", encoding="utf-8-sig") as f:
            return [x for x in list(csv.reader(f))[1:] if x]
    rutas = {}
    for r in filas("rutas.csv"):
        rutas.setdefault(r[0].strip(), []).append((int(r[1]), r[2].strip()))
    return {"estaciones": [x[0].strip() for x in filas("estaciones.csv")],
            "rutas": {k: [e for _, e in sorted(v)] for k, v in rutas.items()},
            "horarios": len(filas("horarios.csv"))}


WRAPPED = wrapped()
GET = {
    "estado": lambda q: red.estado(p(q, "nombre")),
    "autocompletar": lambda q: red.autocompletar(p(q, "prefijo"), int(p(q, "k", "8"))),
    "rango": lambda q: red.rango(p(q, "desde"), p(q, "hasta")),
    "proximo_bus": lambda q: red.proximo_bus(p(q, "estacion"), p(q, "ruta"), p(q, "hora")),
    "viaje": lambda q: red.viaje(p(q, "origen"), p(q, "destino")),
    "ranking": lambda q: red.ranking(int(p(q, "k", "10"))),
    "recorrido": lambda q: red.recorrido(p(q, "ruta"), p(q, "reves") == "1"),
    "rutas": lambda q: RUTAS,
    "wrapped": lambda q: WRAPPED,
    "buses": lambda q: buses(),
    "horarios": lambda q: horarios(p(q, "ruta"), p(q, "estacion")),
}
POST = {
    "agregar": lambda b: red.agregar_parada(b["ruta"], b["nueva"], b.get("despues") or None),
    "quitar": lambda b: red.quitar_parada(b["ruta"], b["estacion"]),
    "cerrar": lambda b: red.cerrar(b["nombre"]),
    "reabrir": lambda b: red.reabrir(b["nombre"]),
    "deshacer": lambda b: red.deshacer(),
    "rehacer": lambda b: red.rehacer(),
    "fila": fila,
    "crear": lambda b: red.crear_estacion(b["nombre"]),
    "eliminar_estacion": lambda b: red.eliminar_estacion(b["nombre"]),
}


class H(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        cuerpo = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _api(self, nombre, tabla, arg):
        try:
            if nombre == "rendimiento":
                return self._json(rendimiento.correr(arg))
            if nombre == "rendimiento_uno":
                return self._json(rendimiento.medir_uno(arg.get("n")))
            with cerrojo:
                return self._json(tabla[nombre](arg))
        except Exception as e:  # el front muestra el error tal cual
            return self._json({"error": str(e) or e.__class__.__name__}, 400)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.startswith("/api/") and u.path[5:] in GET:
            return self._api(u.path[5:], GET, parse_qs(u.query))
        with open(os.path.join(AQUI, "index.html"), "rb") as f:
            cuerpo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        nombre = urlparse(self.path).path[5:]
        n = int(self.headers.get("Content-Length") or 0)
        cuerpo = json.loads(self.rfile.read(n) or b"{}")
        if nombre in POST or nombre in ("rendimiento", "rendimiento_uno"):
            return self._api(nombre, POST, cuerpo)
        self._json({"error": "no existe"}, 404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    url = "http://127.0.0.1:%d" % puerto
    print("Planeador TransMilenio en", url, "(Ctrl+C para salir)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        ThreadingHTTPServer(("127.0.0.1", puerto), H).serve_forever()
    except KeyboardInterrupt:
        pass
