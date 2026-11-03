"""R1–R9 sobre redes mínimas con resultado conocido."""

import os
import shutil
import unittest

from motor import Red
from tests.apoyo import escribir_red

ESTACIONES = ["ALFA", "BETA", "CALLE 10", "CALLE 20", "CALLE 30", "DELTA", "EPSILON"]
RUTAS = {
    "A-1": ["ALFA", "BETA", "CALLE 10", "DELTA"],
    "A-2": ["DELTA", "CALLE 10", "BETA", "ALFA"],
    "B-1": ["CALLE 10", "CALLE 20", "CALLE 30", "EPSILON"],
}
HORARIOS = [
    ("A-1", "BETA", "06:10"), ("A-1", "BETA", "05:50"), ("A-1", "BETA", "06:10"),
    ("A-1", "BETA", "25:05"), ("A-1", "ALFA", "05:40"),
    ("B-1", "CALLE 10", "07:00"), ("B-1", "CALLE 10", "07:30"),
    ("B-1", "CALLE 20", "07:05"),
    ("A-2", "BETA", "08:00"),
    ("X-9", "BETA", "08:00"),          # ruta inexistente: se descarta
    ("B-1", "ALFA", "08:00"),          # par fuera de ruta: se descarta
]


class TestRedMinima(unittest.TestCase):
    def setUp(self):
        self.carpeta = escribir_red(ESTACIONES, RUTAS, HORARIOS)
        self.red = Red(self.carpeta)

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    # R1
    def test_estado(self):
        self.assertEqual(self.red.estado("ALFA"), "abierta")
        self.assertEqual(self.red.estado("alfa"), "inexistente")
        self.assertEqual(self.red.estado("ZETA"), "inexistente")
        self.red.cerrar("ALFA")
        self.assertEqual(self.red.estado("ALFA"), "cerrada")

    # R2
    def test_autocompletar(self):
        self.assertEqual(self.red.autocompletar("CALLE", 2), ["CALLE 10", "CALLE 20"])
        self.assertEqual(self.red.autocompletar("CALLE", 10), ["CALLE 10", "CALLE 20", "CALLE 30"])
        self.assertEqual(self.red.autocompletar("Z", 5), [])
        self.assertEqual(self.red.autocompletar("CALLE", 0), [])
        self.assertEqual(self.red.autocompletar("", 2), ["ALFA", "BETA"])
        self.red.cerrar("CALLE 10")
        self.assertEqual(self.red.autocompletar("CALLE", 2), ["CALLE 20", "CALLE 30"])

    # R3
    def test_rango(self):
        self.assertEqual(self.red.rango("BETA", "CALLE 20"), ["BETA", "CALLE 10", "CALLE 20"])
        self.assertEqual(self.red.rango("B", "CALLE 15"), ["BETA", "CALLE 10"])
        self.assertEqual(self.red.rango("Z", "A"), [])
        self.red.cerrar("BETA")
        self.assertEqual(self.red.rango("BETA", "CALLE 10"), ["CALLE 10"])

    # R4
    def test_proximo_bus(self):
        self.assertEqual(self.red.proximo_bus("BETA", "A-1", "06:00"), "06:10")
        self.assertEqual(self.red.proximo_bus("BETA", "A-1", "06:10"), "06:10")
        self.assertEqual(self.red.proximo_bus("BETA", "A-1", "00:00"), "01:05")  # 25:05 plegada
        self.assertIsNone(self.red.proximo_bus("BETA", "A-1", "06:11"))
        self.assertIsNone(self.red.proximo_bus("BETA", "X-9", "06:00"))
        self.assertIsNone(self.red.proximo_bus("ZETA", "A-1", "06:00"))
        self.assertIsNone(self.red.proximo_bus("DELTA", "A-1", "06:00"))  # sin eventos
        self.assertRaises(ValueError, self.red.proximo_bus, "BETA", "A-1", "25:00")
        self.assertEqual(self.red.horarios("BETA", "A-1"), ["01:05", "05:50", "06:10", "06:10"])
        self.red.cerrar("BETA")
        self.assertIsNone(self.red.proximo_bus("BETA", "A-1", "06:00"))
        self.red.reabrir("BETA")
        self.red.quitar_parada("A-1", "BETA")
        self.assertIsNone(self.red.proximo_bus("BETA", "A-1", "06:00"))
        self.red.deshacer()
        self.assertEqual(self.red.proximo_bus("BETA", "A-1", "06:00"), "06:10")

    def test_diagnostico(self):
        self.assertEqual(self.red.diagnostico.obtener("eventos_fuera_de_ruta"), 2)
        self.assertEqual(self.red.diagnostico.obtener("estaciones"), 7)

    # R5
    def test_viaje_directo_y_sentido(self):
        self.assertEqual(self.red.viaje("ALFA", "DELTA"), [("A-1", "ALFA", "DELTA")])
        self.assertEqual(self.red.viaje("DELTA", "ALFA"), [("A-2", "DELTA", "ALFA")])
        self.assertEqual(self.red.viaje("ALFA", "ALFA"), [])
        self.assertIsNone(self.red.viaje("ALFA", "ZETA"))

    def test_viaje_transbordo(self):
        tramos = self.red.viaje("ALFA", "EPSILON")
        self.assertEqual(tramos, [("A-1", "ALFA", "CALLE 10"), ("B-1", "CALLE 10", "EPSILON")])
        self.assertEqual(self.red.paradas_viaje(tramos), 5)
        # sin camino en sentido contrario de B-1
        self.assertIsNone(self.red.viaje("EPSILON", "ALFA"))

    def test_viaje_con_cierres(self):
        self.red.cerrar("CALLE 10")    # no se puede transbordar ahí
        self.assertIsNone(self.red.viaje("ALFA", "EPSILON"))
        # pero el bus pasa por la estación cerrada sin detenerse
        self.assertEqual(self.red.viaje("ALFA", "DELTA"), [("A-1", "ALFA", "DELTA")])
        self.red.cerrar("DELTA")
        self.assertIsNone(self.red.viaje("ALFA", "DELTA"))
        self.red.deshacer()
        self.red.deshacer()
        self.assertEqual(len(self.red.viaje("ALFA", "EPSILON")), 2)

    def test_viaje_tras_modificar_ruta(self):
        self.assertTrue(self.red.agregar_parada("A-1", "EPSILON", "BETA"))
        self.assertEqual(self.red.viaje("ALFA", "EPSILON"), [("A-1", "ALFA", "EPSILON")])
        self.red.deshacer()
        self.assertEqual(len(self.red.viaje("ALFA", "EPSILON")), 2)

    # R6
    def test_ranking(self):
        self.assertEqual(self.red.ranking(3), [("BETA", 5), ("CALLE 10", 2), ("ALFA", 1)])
        self.red.cerrar("BETA")
        self.assertEqual(self.red.ranking(1), [("CALLE 10", 2)])
        self.red.deshacer()
        self.red.quitar_parada("A-1", "BETA")   # BETA pierde los 4 eventos de A-1
        self.assertEqual(self.red.ranking(2), [("CALLE 10", 2), ("ALFA", 1)])
        self.assertEqual(self.red.buses("BETA"), 1)
        self.red.deshacer()
        self.assertEqual(self.red.ranking(1), [("BETA", 5)])
        self.assertEqual(self.red.ranking(0), [])
        self.assertEqual(len(self.red.ranking(100)), 7)
        # empates en 0 se resuelven alfabéticamente
        ceros = [n for n, b in self.red.ranking(100) if b == 0]
        self.assertEqual(ceros, sorted(ceros))

    # R7
    def test_agregar_y_quitar(self):
        self.assertTrue(self.red.agregar_parada("B-1", "DELTA", "CALLE 20"))
        self.assertEqual(self.red.recorrido("B-1"),
                         ["CALLE 10", "CALLE 20", "DELTA", "CALLE 30", "EPSILON"])
        self.assertEqual(self.red.recorrido("B-1", al_reves=True),
                         ["EPSILON", "CALLE 30", "DELTA", "CALLE 20", "CALLE 10"])
        self.assertTrue(self.red.agregar_parada("B-1", "ALFA", None))
        self.assertEqual(self.red.recorrido("B-1")[0], "ALFA")
        self.assertTrue(self.red.agregar_parada("B-1", "BETA", "EPSILON"))
        self.assertEqual(self.red.recorrido("B-1")[-1], "BETA")
        self.assertFalse(self.red.agregar_parada("B-1", "DELTA", "ALFA"))   # repetida
        self.assertFalse(self.red.agregar_parada("B-1", "ZETA", "ALFA"))    # no existe
        self.assertFalse(self.red.agregar_parada("B-1", "EPSILON", "ZETA"))
        self.assertFalse(self.red.agregar_parada("X-9", "ALFA", None))
        self.assertTrue(self.red.quitar_parada("B-1", "CALLE 20"))
        self.assertFalse(self.red.quitar_parada("B-1", "CALLE 20"))
        self.assertFalse(self.red.quitar_parada("X-9", "ALFA"))
        self.assertIsNone(self.red.recorrido("X-9"))
        self.assertNotIn("B-1", self.red.rutas_de("CALLE 20"))
        self.assertIn("B-1", self.red.rutas_de("DELTA"))

    # R8 + R9
    def test_cerrar_reabrir_idempotente(self):
        self.assertTrue(self.red.cerrar("ALFA"))
        self.assertFalse(self.red.cerrar("ALFA"))
        self.assertFalse(self.red.cerrar("ZETA"))
        self.assertTrue(self.red.reabrir("ALFA"))
        self.assertFalse(self.red.reabrir("ALFA"))
        deshacer, _ = self.red.historial()
        self.assertEqual(len(deshacer), 2)

    def test_deshacer_rehacer_orden(self):
        original = self.red.recorrido("A-1")
        self.red.quitar_parada("A-1", "ALFA")       # quitar la primera
        self.red.quitar_parada("A-1", "CALLE 10")
        self.red.cerrar("BETA")
        self.assertEqual(self.red.recorrido("A-1"), ["BETA", "DELTA"])
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.estado("BETA"), "abierta")
        self.assertTrue(self.red.deshacer())
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("A-1"), original)
        self.assertFalse(self.red.deshacer())
        self.assertTrue(self.red.rehacer())
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.recorrido("A-1"), ["BETA", "DELTA"])
        # un cambio nuevo borra lo que había para rehacer
        self.red.cerrar("EPSILON")
        self.assertFalse(self.red.rehacer())
        self.assertEqual(self.red.estado("BETA"), "abierta")

    def test_deshacer_en_cadena_larga(self):
        estados = [self.red.recorrido("B-1")]
        for nueva, despues in (("ALFA", "CALLE 10"), ("BETA", "ALFA"), ("DELTA", None)):
            self.red.agregar_parada("B-1", nueva, despues)
            estados.append(self.red.recorrido("B-1"))
        self.red.quitar_parada("B-1", "ALFA")
        estados.append(self.red.recorrido("B-1"))
        for esperado in reversed(estados[:-1]):
            self.red.deshacer()
            self.assertEqual(self.red.recorrido("B-1"), esperado)
        for esperado in estados[1:]:
            self.red.rehacer()
            self.assertEqual(self.red.recorrido("B-1"), esperado)


class TestCSVInvalidos(unittest.TestCase):
    def test_carpeta_inexistente(self):
        self.assertRaises(ValueError, Red, "no/existe/carpeta")

    def test_estacion_desconocida_en_ruta(self):
        carpeta = escribir_red(["A", "B"], {"R": ["A", "C"]})
        self.assertRaises(ValueError, Red, carpeta)
        shutil.rmtree(carpeta)

    def test_columna_faltante(self):
        carpeta = escribir_red(["A", "B"], {"R": ["A", "B"]})
        with open(os.path.join(carpeta, "horarios.csv"), "w", encoding="utf-8") as f:
            f.write("ruta,estacion\nR,A\n")
        self.assertRaises(ValueError, Red, carpeta)
        shutil.rmtree(carpeta)

    def test_columnas_en_otro_orden_y_repetidos(self):
        carpeta = escribir_red(["A", "B", "A"], {"R": ["A", "B"]}, [("R", "A", "05:00")] * 3)
        with open(os.path.join(carpeta, "rutas.csv"), "w", encoding="utf-8") as f:
            f.write("estacion,ruta,orden\nB,R,2\nA,R,1\n")
        red = Red(carpeta)
        self.assertEqual(red.recorrido("R"), ["A", "B"])
        self.assertEqual(red.diagnostico.obtener("estaciones_repetidas"), 1)
        self.assertEqual(red.horarios("A", "R"), ["05:00"] * 3)
        shutil.rmtree(carpeta)

    def test_hora_invalida_se_descarta(self):
        carpeta = escribir_red(["A", "B"], {"R": ["A", "B"]}, [("R", "A", "xx:yy"), ("R", "A", "05:00")])
        red = Red(carpeta)
        self.assertEqual(red.diagnostico.obtener("horas_invalidas"), 1)
        self.assertEqual(red.proximo_bus("A", "R", "00:00"), "05:00")
        shutil.rmtree(carpeta)


if __name__ == "__main__":
    unittest.main()
