import bisect
import random
import unittest

from motor.algoritmos import indices_ordenados, limite_inferior, ordenar
from motor.estructuras import Cola, ListaDoble, Pila, TablaHash, hash_texto
from motor.tiempo import a_minutos, a_texto, minutos_csv


class TestTablaHash(unittest.TestCase):
    def test_colisiones_reales(self):
        # "Aa" y "BB" tienen el mismo hash polinomial base 31
        self.assertEqual(hash_texto("Aa"), hash_texto("BB"))
        t = TablaHash()
        t.poner("Aa", 1)
        t.poner("BB", 2)
        self.assertEqual(t.obtener("Aa"), 1)
        self.assertEqual(t.obtener("BB"), 2)
        self.assertTrue(t.eliminar("Aa"))
        self.assertIsNone(t.obtener("Aa"))
        self.assertEqual(t.obtener("BB"), 2)

    def test_redimensiona_y_conserva(self):
        t = TablaHash()
        capacidad_inicial = t.capacidad()
        for i in range(5000):
            t.poner(f"clave{i}", i)
        self.assertGreater(t.capacidad(), capacidad_inicial)
        self.assertEqual(len(t), 5000)
        self.assertLessEqual(len(t) / t.capacidad(), TablaHash.CARGA_MAXIMA)
        for i in range(5000):
            self.assertEqual(t.obtener(f"clave{i}"), i)
        self.assertLess(t.cubeta_mas_larga(), 12)

    def test_reemplazo_y_eliminacion(self):
        t = TablaHash()
        self.assertTrue(t.poner("a", 1))
        self.assertFalse(t.poner("a", 3))
        self.assertEqual(len(t), 1)
        self.assertEqual(t.obtener("a"), 3)
        self.assertFalse(t.eliminar("zzz"))
        self.assertEqual(t.obtener("zzz", "def"), "def")
        self.assertEqual(sorted(t.claves()), ["a"])


class TestListas(unittest.TestCase):
    def test_lista_doble(self):
        l = ListaDoble()
        a = l.agregar_final("A")
        c = l.agregar_final("C")
        b = l.insertar_despues(a, "B")
        l.insertar_despues(None, "0")
        l.insertar_despues(c, "D")
        self.assertEqual(l.valores(), ["0", "A", "B", "C", "D"])
        self.assertEqual(l.valores(True), ["D", "C", "B", "A", "0"])
        l.eliminar(b)
        l.eliminar(l.cabeza)
        l.eliminar(l.cola)
        self.assertEqual(l.valores(), ["A", "C"])
        self.assertEqual(len(l), 2)
        l.eliminar(a)
        l.eliminar(c)
        self.assertIsNone(l.cabeza)
        self.assertIsNone(l.cola)

    def test_pila(self):
        p = Pila()
        self.assertTrue(p.vacia())
        for i in range(5):
            p.apilar(i)
        self.assertEqual(p.cima(), 4)
        self.assertEqual(p.valores(), [4, 3, 2, 1, 0])
        self.assertEqual(p.desapilar(), 4)
        p.vaciar()
        self.assertRaises(IndexError, p.desapilar)

    def test_cola_circular_crece(self):
        c = Cola(4)
        esperado = []
        rnd = random.Random(3)
        siguiente = 0
        for _ in range(3000):
            if rnd.random() < 0.6:
                c.encolar(siguiente)
                esperado.append(siguiente)
                siguiente += 1
            elif esperado:
                self.assertEqual(c.frente(), esperado[0])
                self.assertEqual(c.desencolar(), esperado.pop(0))
            self.assertEqual(len(c), len(esperado))
        while esperado:
            self.assertEqual(c.desencolar(), esperado.pop(0))
        self.assertRaises(IndexError, c.desencolar)


class TestAlgoritmos(unittest.TestCase):
    def test_merge_sort_contra_sorted(self):
        rnd = random.Random(7)
        for n in (0, 1, 2, 3, 10, 17, 100, 1000):
            datos = [rnd.randint(-20, 20) for _ in range(n)]
            self.assertEqual(ordenar(datos), sorted(datos))

    def test_estabilidad(self):
        pares = [(3, "a"), (1, "b"), (3, "c"), (1, "d"), (2, "e")]
        self.assertEqual(ordenar(pares, lambda p: p[0]),
                         [(1, "b"), (1, "d"), (2, "e"), (3, "a"), (3, "c")])
        self.assertEqual(indices_ordenados([5, 5, 5]), [0, 1, 2])

    def test_busqueda_binaria_contra_bisect(self):
        rnd = random.Random(11)
        for _ in range(200):
            arr = sorted(rnd.randint(0, 50) for _ in range(rnd.randint(0, 30)))
            x = rnd.randint(-5, 55)
            self.assertEqual(limite_inferior(arr, x), bisect.bisect_left(arr, x))


class TestTiempo(unittest.TestCase):
    def test_conversiones(self):
        self.assertEqual(a_minutos("09:25"), 565)
        self.assertEqual(a_minutos("9:25"), 565)
        self.assertEqual(a_texto(693), "11:33")
        for invalida in ("24:00", "12:60", "abc", "", "1:2", "-1:00", None):
            self.assertRaises(ValueError, a_minutos, invalida)

    def test_horas_gtfs_mayores_a_23(self):
        self.assertEqual(minutos_csv("25:10"), 70)
        self.assertEqual(minutos_csv("24:00"), 0)
        self.assertEqual(minutos_csv("xx"), -1)


if __name__ == "__main__":
    unittest.main()
