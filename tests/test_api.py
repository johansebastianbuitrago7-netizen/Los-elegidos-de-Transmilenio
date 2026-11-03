"""API Flask con el cliente de pruebas (sin abrir puertos)."""

import unittest

try:
    from app import crear_app
except ImportError:  # Flask no instalado
    crear_app = None


@unittest.skipIf(crear_app is None, "Flask no está instalado")
class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = crear_app()
        cls.c = cls.app.test_client()

    def setUp(self):
        self.c.post("/api/reiniciar")

    def test_pagina(self):
        r = self.c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"ATLAS", r.data)

    def test_resumen(self):
        d = self.c.get("/api/resumen").get_json()
        self.assertEqual(d["estaciones"], 147)
        self.assertEqual(len(d["top"]), 5)

    def test_estado_normaliza_entrada(self):
        d = self.c.get("/api/estado?nombre=portal%20nórte").get_json()
        self.assertEqual(d["nombre"], "PORTAL NORTE")
        self.assertEqual(d["estado"], "abierta")
        self.assertTrue(any(r["ruta"] == "B10-1" for r in d["rutas"]))
        d = self.c.get("/api/estado?nombre=NOEXISTE").get_json()
        self.assertEqual(d["estado"], "inexistente")

    def test_validaciones(self):
        self.assertEqual(self.c.get("/api/estado").status_code, 400)
        self.assertEqual(self.c.get("/api/autocompletar?prefijo=A&k=x").status_code, 400)
        self.assertEqual(self.c.get("/api/proximo?estacion=PORTAL NORTE&ruta=B10-1&hora=25:00").status_code, 400)
        self.assertEqual(self.c.get("/api/proximo?estacion=PORTAL NORTE&ruta=ZZ&hora=09:00").status_code, 400)
        self.assertEqual(self.c.post("/api/cerrar", data="x").status_code, 400)
        self.assertEqual(self.c.post("/api/fila/educativo", json={"llegadas": list(range(41)), "frecuencia": 5, "capacidad": 3}).status_code, 400)
        self.assertEqual(self.c.post("/api/fila/avanzado", json={"pasajeros": 300001}).status_code, 400)
        self.assertEqual(self.c.get("/api/inexistente").status_code, 404)

    def test_horario_b10(self):
        d = self.c.get("/api/proximo?estacion=PORTAL NORTE&ruta=B10-1&hora=09:25").get_json()
        self.assertEqual(d["proximo"], "11:33")
        self.assertEqual(d["diferencia"], 128)
        self.assertEqual(d["ruta"]["etiqueta"], "B10-1 · PORTAL 80 → PORTAL NORTE")
        self.assertEqual(len(d["siguientes"]), 5)
        self.assertEqual(d["intervalo"]["anterior"], "08:18")

    def test_rutas_de_estacion(self):
        d = self.c.get("/api/estacion/rutas?nombre=PORTAL NORTE").get_json()
        self.assertIn("B10-1 · PORTAL 80 → PORTAL NORTE", [r["etiqueta"] for r in d["rutas"]])

    def test_viaje_y_cierre(self):
        d = self.c.get("/api/viaje?origen=PORTAL 80&destino=PORTAL USME").get_json()
        self.assertTrue(d["encontrado"])
        self.assertEqual(d["paradas"], sum(t["paradas"] for t in d["tramos"]))
        self.assertTrue(self.c.post("/api/cerrar", json={"nombre": "PORTAL USME"}).get_json()["ok"])
        d = self.c.get("/api/viaje?origen=PORTAL 80&destino=PORTAL USME").get_json()
        self.assertFalse(d["encontrado"])
        self.assertEqual(d["estado_destino"], "cerrada")

    def test_operacion_e_historial(self):
        r = self.c.post("/api/agregar", json={"ruta": "B10-1", "nueva": "RICAURTE", "despues_de": "ALCALA"}).get_json()
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["historial"]["deshacer"]), 1)
        rec = self.c.get("/api/recorrido?ruta=B10-1").get_json()
        self.assertEqual([p["nombre"] for p in rec["paradas"]][-2], "RICAURTE")
        self.assertFalse(self.c.post("/api/agregar", json={"ruta": "B10-1", "nueva": "RICAURTE"}).get_json()["ok"])
        r = self.c.post("/api/deshacer").get_json()
        self.assertEqual(len(r["historial"]["rehacer"]), 1)
        self.assertTrue(self.c.post("/api/rehacer").get_json()["ok"])
        self.assertTrue(self.c.post("/api/quitar", json={"ruta": "B10-1", "estacion": "RICAURTE"}).get_json()["ok"])
        self.assertFalse(self.c.post("/api/rehacer").get_json()["ok"])

    def test_fila_educativa(self):
        d = self.c.post("/api/fila/educativo", json={"llegadas": [0, 0, 1, 2, 5, 5, 9], "frecuencia": 5, "capacidad": 3}).get_json()
        self.assertEqual(d["abordajes"], [0, 0, 5, 5, 5, 10, 10])
        self.assertAlmostEqual(d["metricas"]["espera_media"], 13 / 7)
        self.assertEqual(d["metricas"]["buses_con_abordajes"], 3)
        # después del abordaje del minuto 5, P6 (índice 5) sigue en la fila
        paso = next(p for p in d["pasos"] if p["tipo"] == "dequeue" and p["minuto"] == 5)
        self.assertEqual(paso["fila"], [5])
        self.assertEqual(paso["pasajeros"], [2, 3, 4])

    def test_fila_avanzada_y_ab(self):
        d = self.c.post("/api/fila/avanzado", json={"pasajeros": 5000, "duracion": 120, "frecuencia": 3,
                                                     "capacidad": 100, "demanda": "pico", "semilla": 1}).get_json()
        m = d["metricas"]
        self.assertEqual(m["pasajeros"], 5000)
        self.assertLessEqual(m["espera_mediana"], m["p90"])
        self.assertLessEqual(m["p95"], m["espera_maxima"])
        self.assertLessEqual(len(d["series"]["cola"]), 240)
        ab = self.c.post("/api/fila/comparar", json={"pasajeros": 3000, "duracion": 60, "demanda": "uniforme", "semilla": 3,
                                                     "a": {"frecuencia": 2, "capacidad": 100}, "b": {"frecuencia": 6, "capacidad": 100}}).get_json()
        self.assertEqual(ab["a"]["metricas"]["pasajeros"], ab["b"]["metricas"]["pasajeros"])
        self.assertLess(ab["a"]["metricas"]["espera_media"], ab["b"]["metricas"]["espera_media"])


if __name__ == "__main__":
    unittest.main()
