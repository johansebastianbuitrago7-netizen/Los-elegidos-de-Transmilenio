"""Pruebas de 'crear nueva estación' del lado del motor y del servidor (API real)."""
import json, os, sys, threading, unittest, urllib.request
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "front"))
from motor import Red  # noqa: E402


def foto(r):
    nombres = r.autocompletar("", 100000)
    return (nombres, r.ranking(100000), [tuple(r.recorrido(x)) for x in ("1-1", "K43-2", "G11-1")], r.viaje("UNIVERSIDADES", "PORTAL ELDORADO"))


class Motor(unittest.TestCase):
    def setUp(self):
        self.r = Red(os.path.join(RAIZ, "datos"))
        self.base = foto(self.r)

    def test_entre_dos_estaciones_y_origen_destino(self):
        rec = self.r.recorrido("1-1"); a, b = rec[0], rec[1]
        self.assertTrue(self.r.crear_estacion("NUEVA UNO"))
        self.assertTrue(self.r.agregar_parada("1-1", "NUEVA UNO", a))
        self.assertEqual(self.r.recorrido("1-1")[:3], [a, "NUEVA UNO", b])
        self.assertEqual(self.r.estado("NUEVA UNO"), "abierta")
        self.assertIn("NUEVA UNO", self.r.autocompletar("NUEVA", 5))
        v = self.r.viaje("NUEVA UNO", rec[3])            # como origen
        self.assertIsNotNone(v); self.assertEqual(v["tramos"][0][1], "NUEVA UNO")
        v = self.r.viaje(a, "NUEVA UNO")                  # como destino
        self.assertIsNotNone(v); self.assertEqual(v["paradas"], 1)

    def test_consecutivas_y_dos_rutas(self):
        rec = self.r.recorrido("1-1"); a = rec[0]
        for n in ("N1", "N2", "N3"):
            self.assertTrue(self.r.crear_estacion(n))
        self.assertTrue(self.r.agregar_parada("1-1", "N1", a))
        self.assertTrue(self.r.agregar_parada("1-1", "N2", "N1"))
        self.assertTrue(self.r.agregar_parada("1-1", "N3", "N2"))
        self.assertEqual(self.r.recorrido("1-1")[:4], [a, "N1", "N2", "N3"])
        # el mismo tramo en otra ruta que lo comparta
        for x in ("1-2", "K43-2", "G11-1"):
            rr = self.r.recorrido(x)
            if a in rr and rr.index(a) + 1 < len(rr):
                self.assertTrue(self.r.agregar_parada(x, "N1", a)); break
        self.assertFalse(self.r.agregar_parada("1-1", "NO EXISTE", a))   # no se inventan estaciones

    def test_eliminar_restaura_y_protege_la_base(self):
        a = self.r.recorrido("1-1")[0]
        self.r.crear_estacion("TEMP"); self.r.agregar_parada("1-1", "TEMP", a); self.r.cerrar(a); self.r.reabrir(a)
        self.assertTrue(self.r.eliminar_estacion("TEMP"))
        self.assertEqual(foto(self.r), self.base)
        self.assertEqual(self.r.estado("TEMP"), "no existe")
        self.assertFalse(self.r.eliminar_estacion(a))                    # estación original: protegida
        self.assertEqual(self.r.estado(a), "abierta")


class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        from http.server import ThreadingHTTPServer
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 8765), app.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def call(self, p, body=None):
        u = "http://127.0.0.1:8765/api/" + p
        rq = urllib.request.Request(u, data=json.dumps(body).encode() if body is not None else None)
        return json.loads(urllib.request.urlopen(rq).read())

    def test_flujo_completo(self):
        rec = self.call("recorrido?ruta=1-1"); a = rec[0]
        self.assertTrue(self.call("crear", {"nombre": "API NUEVA"}))
        self.assertFalse(self.call("crear", {"nombre": "API NUEVA"}))
        self.assertTrue(self.call("agregar", {"ruta": "1-1", "nueva": "API NUEVA", "despues": a}))
        self.assertEqual(self.call("recorrido?ruta=1-1")[1], "API NUEVA")
        self.assertIn("API NUEVA", self.call("autocompletar?prefijo=API&k=5"))
        self.assertIsNotNone(self.call("viaje?origen=API+NUEVA&destino=" + rec[2].replace(" ", "+")))
        self.assertTrue(self.call("eliminar_estacion", {"nombre": "API NUEVA"}))
        self.assertEqual(self.call("recorrido?ruta=1-1"), rec)
        self.assertEqual(self.call("estado?nombre=API+NUEVA"), "no existe")

    def test_buses_y_horarios(self):
        b = self.call("buses")
        self.assertGreater(len(b), 100)
        g = [x for x in b if x["ruta"].startswith("G11")]
        self.assertTrue(g and g[0]["primero"] and g[0]["ultimo"])
        rec = self.call("recorrido?ruta=" + g[0]["ruta"])
        hs = self.call("horarios?ruta=%s&estacion=%s" % (g[0]["ruta"], rec[0].replace(" ", "+")))
        self.assertEqual(hs, sorted(hs)); self.assertGreater(len(hs), 5)


if __name__ == "__main__":
    unittest.main()
