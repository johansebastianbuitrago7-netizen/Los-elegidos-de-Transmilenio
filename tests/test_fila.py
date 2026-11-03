"""R10: simulación FIFO."""

import random
import time
import unittest

from motor import simular_fila
from tests.apoyo import fila_referencia


class TestFila(unittest.TestCase):
    def test_escenario_del_enunciado(self):
        llegadas = [0, 0, 1, 2, 5, 5, 9]
        abordajes = simular_fila(llegadas, 5, 3)
        esperas = [a - l for a, l in zip(abordajes, llegadas)]
        self.assertEqual(abordajes, [0, 0, 5, 5, 5, 10, 10])
        self.assertEqual(esperas, [0, 0, 4, 3, 0, 5, 1])
        self.assertEqual(sum(esperas), 13)
        self.assertEqual(max(esperas), 5)
        self.assertEqual(len(set(abordajes)), 3)
        # P6 (índice 5) llegó en el minuto 5 pero no cupo en ese bus
        self.assertEqual(abordajes[5], 10)

    def test_llegada_en_el_minuto_del_bus_aborda(self):
        self.assertEqual(simular_fila([5], 5, 1), [5])
        self.assertEqual(simular_fila([6], 5, 1), [10])

    def test_simultaneas_respetan_orden_de_la_lista(self):
        self.assertEqual(simular_fila([3, 3, 3, 3], 5, 2), [5, 5, 10, 10])

    def test_desordenadas_alineadas_al_orden_original(self):
        llegadas = [9, 0, 5, 1, 0, 5, 2]
        abordajes = simular_fila(llegadas, 5, 3)
        self.assertEqual(abordajes, fila_referencia(llegadas, 5, 3))
        # mismo resultado por pasajero que el escenario ordenado
        self.assertEqual(abordajes, [10, 0, 5, 5, 0, 10, 5])

    def test_salto_de_buses_vacios(self):
        self.assertEqual(simular_fila([1000000], 7, 1), [1000006])
        self.assertEqual(simular_fila([-3], 5, 1), [0])

    def test_entradas_invalidas(self):
        self.assertEqual(simular_fila([], 5, 3), [])
        self.assertRaises(ValueError, simular_fila, [1], 0, 3)
        self.assertRaises(ValueError, simular_fila, [1], 5, 0)
        self.assertRaises(ValueError, simular_fila, [1.5], 5, 3)
        self.assertRaises(ValueError, simular_fila, [1], 5, True)

    def test_aleatorio_contra_referencia(self):
        rnd = random.Random(5)
        for _ in range(300):
            n = rnd.randint(0, 40)
            llegadas = [rnd.randint(0, 30) for _ in range(n)]
            f, c = rnd.randint(1, 8), rnd.randint(1, 5)
            self.assertEqual(simular_fila(llegadas, f, c), fila_referencia(llegadas, f, c))

    def test_invariantes_fifo(self):
        rnd = random.Random(9)
        llegadas = [rnd.randint(0, 600) for _ in range(5000)]
        f, c = 4, 30
        ab = simular_fila(llegadas, f, c)
        conteo = {}
        for a, l in zip(ab, llegadas):
            self.assertGreaterEqual(a, l)
            self.assertEqual(a % f, 0)
            conteo[a] = conteo.get(a, 0) + 1
        self.assertLessEqual(max(conteo.values()), c)
        # FIFO: si i llegó antes que j (o igual y antes en la lista), sube antes o igual
        orden = sorted(range(len(llegadas)), key=lambda i: llegadas[i])
        for x, y in zip(orden, orden[1:]):
            self.assertLessEqual(ab[x], ab[y])

    def test_escenario_grande(self):
        rnd = random.Random(1)
        llegadas = [rnd.randint(0, 240) for _ in range(300000)]
        inicio = time.perf_counter()
        ab = simular_fila(llegadas, 3, 120)
        self.assertEqual(len(ab), 300000)
        self.assertLess(time.perf_counter() - inicio, 20)
        self.assertTrue(all(a >= l for a, l in zip(ab, llegadas)))


if __name__ == "__main__":
    unittest.main()
