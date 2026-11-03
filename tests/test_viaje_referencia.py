"""R5 contra dos referencias independientes: fuerza bruta y 0-1 BFS."""

import random
import shutil
import unittest

from motor import Red
from tests.apoyo import escribir_red, red_aleatoria, viaje_bfs01, viaje_referencia


def validar_itinerario(prueba, red, rutas, cerradas, origen, destino, tramos):
    """Comprueba que lo devuelto sea un viaje real y factible."""
    prueba.assertGreaterEqual(len(tramos), 1)
    prueba.assertLessEqual(len(tramos), 2)
    prueba.assertEqual(tramos[0][1], origen)
    prueba.assertEqual(tramos[-1][2], destino)
    if len(tramos) == 2:
        prueba.assertEqual(tramos[0][2], tramos[1][1])
        prueba.assertNotIn(tramos[0][2], cerradas)
        prueba.assertNotEqual(tramos[0][0], tramos[1][0])
    total = 0
    for ruta, desde, hasta in tramos:
        p = rutas[ruta]
        prueba.assertLess(p.index(desde), p.index(hasta), "sentido incorrecto")
        total += p.index(hasta) - p.index(desde)
    prueba.assertEqual(total, red.paradas_viaje(tramos))
    return total


class TestViajeContraReferencia(unittest.TestCase):
    def test_redes_aleatorias(self):
        casos = 0
        for semilla in range(60):
            estaciones, rutas = red_aleatoria(semilla)
            carpeta = escribir_red(estaciones, rutas)
            red = Red(carpeta)
            rnd = random.Random(semilla)
            cerradas = set(rnd.sample(estaciones, rnd.randint(0, 3)))
            for e in cerradas:
                red.cerrar(e)
            for o in estaciones:
                for d in estaciones:
                    esperado = viaje_referencia(rutas, cerradas, o, d)
                    bfs = viaje_bfs01(rutas, cerradas, o, d)
                    obtenido = red.viaje(o, d)
                    casos += 1
                    if esperado is None:
                        self.assertIsNone(obtenido, (semilla, o, d))
                        self.assertIsNone(bfs)
                        continue
                    self.assertEqual(esperado[0], bfs)
                    if o == d:
                        self.assertEqual(obtenido, [])
                        continue
                    self.assertIsNotNone(obtenido, (semilla, o, d))
                    total = validar_itinerario(self, red, rutas, cerradas, o, d, obtenido)
                    self.assertEqual(total, esperado[0], (semilla, o, d, obtenido))
                    # a igual costo se prefiere el viaje directo
                    self.assertEqual(len(obtenido) - 1, esperado[1], (semilla, o, d))
            shutil.rmtree(carpeta)
        self.assertGreater(casos, 5000)

    def test_tras_ediciones_aleatorias(self):
        for semilla in range(15):
            estaciones, rutas = red_aleatoria(100 + semilla, n_est=10, n_rutas=5)
            carpeta = escribir_red(estaciones, rutas)
            red = Red(carpeta)
            rnd = random.Random(semilla)
            for _ in range(8):
                ruta = rnd.choice(list(rutas))
                if rnd.random() < 0.5 and len(rutas[ruta]) > 2:
                    e = rnd.choice(rutas[ruta])
                    self.assertTrue(red.quitar_parada(ruta, e))
                    rutas[ruta].remove(e)
                else:
                    fuera = [e for e in estaciones if e not in rutas[ruta]]
                    if not fuera:
                        continue
                    e = rnd.choice(fuera)
                    despues = rnd.choice(rutas[ruta])
                    self.assertTrue(red.agregar_parada(ruta, e, despues))
                    rutas[ruta].insert(rutas[ruta].index(despues) + 1, e)
                self.assertEqual(red.recorrido(ruta), rutas[ruta])
            for o in estaciones:
                for d in estaciones:
                    esperado = viaje_referencia(rutas, set(), o, d)
                    obtenido = red.viaje(o, d)
                    if esperado is None:
                        self.assertIsNone(obtenido)
                    elif o != d:
                        self.assertEqual(validar_itinerario(self, red, rutas, set(), o, d, obtenido),
                                         esperado[0])
            shutil.rmtree(carpeta)

    def test_desempate_determinista(self):
        # dos rutas directas con igual costo: gana la de nombre menor
        carpeta = escribir_red(["A", "B", "C"], {"Z-1": ["A", "B", "C"], "M-1": ["A", "C"], "K-1": ["A", "B", "C"]})
        red = Red(carpeta)
        self.assertEqual(red.viaje("A", "C"), [("M-1", "A", "C")])
        self.assertEqual(red.viaje("A", "B"), [("K-1", "A", "B")])
        shutil.rmtree(carpeta)

    def test_directo_preferido_en_empate(self):
        carpeta = escribir_red(["A", "B", "C"], {"Z": ["A", "B", "C"], "B1": ["A", "B"], "B2": ["B", "C"]})
        red = Red(carpeta)
        self.assertEqual(red.viaje("A", "C"), [("Z", "A", "C")])
        shutil.rmtree(carpeta)


class TestViajeDatosReales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import csv
        cls.red = Red("datos")
        rutas = {}
        with open("datos/rutas.csv", encoding="utf-8") as f:
            filas = list(csv.reader(f))[1:]
        for r, o, e in sorted(filas, key=lambda x: (x[0], int(x[1]))):
            rutas.setdefault(r, []).append(e)
        cls.rutas = rutas
        with open("datos/estaciones.csv", encoding="utf-8") as f:
            cls.estaciones = [x[0] for x in list(csv.reader(f))[1:]]

    def test_muestra_de_pares_reales(self):
        rnd = random.Random(2021)
        for _ in range(400):
            o, d = rnd.choice(self.estaciones), rnd.choice(self.estaciones)
            esperado = viaje_referencia(self.rutas, set(), o, d)
            obtenido = self.red.viaje(o, d)
            if esperado is None:
                self.assertIsNone(obtenido, (o, d))
            elif o == d:
                self.assertEqual(obtenido, [])
            else:
                total = validar_itinerario(self, self.red, self.rutas, set(), o, d, obtenido)
                self.assertEqual(total, esperado[0], (o, d))


if __name__ == "__main__":
    unittest.main()
