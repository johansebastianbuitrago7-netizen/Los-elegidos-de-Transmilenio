"""Pruebas del motor. Correr:  python -m unittest discover -s tests -v
(Aqui si se puede usar sorted, min, etc.: es codigo de prueba, no del motor.)"""
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from motor import Red, simular_fila  # noqa: E402
from motor.algoritmos import ordenar, primero_mayor_o_igual  # noqa: E402
from motor.estructuras import AVL, Cola, ListaDoble, Pila  # noqa: E402

DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")


def red_pequena():
    d = tempfile.mkdtemp()
    with open(d + "/estaciones.csv", "w", newline="") as f:
        f.write("nombre\r\nA\r\nB\r\nC\r\nD\r\nE\r\nF\r\n")
    with open(d + "/rutas.csv", "w", newline="") as f:
        f.write("ruta,orden,estacion\r\n"
                "R1,1,A\r\nR1,2,B\r\nR1,3,C\r\n"
                "R2,1,C\r\nR2,2,D\r\nR2,3,E\r\n"
                "R3,1,A\r\nR3,2,E\r\n")
    with open(d + "/horarios.csv", "w", newline="") as f:
        f.write("ruta,estacion,hora\r\n"
                "R1,A,10:30\r\nR1,A,08:00\r\nR1,A,09:15\r\nR1,B,08:10\r\n"
                "R2,C,25:10\r\nR2,C,06:00\r\nR3,A,07:00\r\nR3,E,07:20\r\n")
    return d


class Estructuras(unittest.TestCase):
    def test_pila_cola(self):
        p = Pila()
        self.assertIsNone(p.desapilar())
        for i in range(5):
            p.apilar(i)
        self.assertEqual([p.desapilar() for _ in range(5)], [4, 3, 2, 1, 0])
        c = Cola()
        self.assertIsNone(c.desencolar())
        for i in range(5):
            c.encolar(i)
        self.assertEqual([c.desencolar() for _ in range(5)], [0, 1, 2, 3, 4])
        c.encolar(9)
        self.assertEqual(c.desencolar(), 9)

    def test_lista_doble(self):
        l = ListaDoble()
        a = l.agregar_al_final("a")
        c = l.agregar_al_final("c")
        b = l.insertar_despues(a, "b")
        z = l.insertar_despues(None, "z")
        self.assertEqual(list(l.adelante()), ["z", "a", "b", "c"])
        self.assertEqual(list(l.atras()), ["c", "b", "a", "z"])
        l.quitar(z)
        l.quitar(c)
        l.quitar(b)
        self.assertEqual(list(l.adelante()), ["a"])
        l.quitar(a)
        self.assertEqual(len(l), 0)

    def test_ordenar_y_busqueda(self):
        rnd = random.Random(1)
        for n in (0, 1, 2, 3, 7, 100, 1001):
            a = [rnd.randint(0, 50) for _ in range(n)]
            self.assertEqual(ordenar(a), sorted(a))
            s = sorted(a)
            for x in range(-1, 52):
                esperado = len([v for v in s if v < x])
                self.assertEqual(primero_mayor_o_igual(s, x), esperado)

    def test_avl_aleatorio(self):
        rnd = random.Random(2)
        t = AVL()
        ref = set()
        for _ in range(4000):
            x = rnd.randint(0, 600)
            if rnd.random() < 0.55:
                self.assertEqual(t.insertar(x, x), x not in ref)
                ref.add(x)
            else:
                self.assertEqual(t.eliminar(x), x in ref)
                ref.discard(x)
            self.assertEqual(len(t), len(ref))
        self.assertEqual([k for k, _ in t.recorrer_desde(None)], sorted(ref))
        self.assertEqual([k for k, _ in t.recorrer_desde(300)], sorted(v for v in ref if v >= 300))

    def test_avl_altura(self):
        t = AVL()
        for i in range(100000):
            t.insertar(i, i)
        self.assertLessEqual(t._raiz.h, 24)  # 1.44*log2(1e5) ~ 24


class RedPequena(unittest.TestCase):
    def setUp(self):
        self.r = Red(red_pequena())

    def test_r1(self):
        self.assertEqual(self.r.estado("A"), "abierta")
        self.assertEqual(self.r.estado("ZZZ"), "no existe")
        self.assertEqual(self.r.estado(""), "no existe")
        self.r.cerrar("A")
        self.assertEqual(self.r.estado("A"), "cerrada")

    def test_r2_r3(self):
        self.assertEqual(self.r.autocompletar("", 3), ["A", "B", "C"])
        self.assertEqual(self.r.autocompletar("Q", 3), [])
        self.assertEqual(self.r.autocompletar("A", 0), [])
        self.assertEqual(self.r.rango("B", "D"), ["B", "C", "D"])
        self.assertEqual(self.r.rango("D", "B"), [])
        self.assertEqual(self.r.rango("B", "B"), ["B"])
        self.r.cerrar("C")
        self.assertEqual(self.r.rango("B", "D"), ["B", "D"])
        self.assertEqual(self.r.autocompletar("", 10), ["A", "B", "D", "E", "F"])

    def test_r4(self):
        self.assertEqual(self.r.proximo_bus("A", "R1", "08:00"), "08:00")
        self.assertEqual(self.r.proximo_bus("A", "R1", "08:01"), "09:15")
        self.assertEqual(self.r.proximo_bus("A", "R1", "10:31"), None)
        self.assertEqual(self.r.proximo_bus("A", "R1", "00:00"), "08:00")
        self.assertEqual(self.r.proximo_bus("C", "R2", "07:00"), "25:10")
        self.assertEqual(self.r.proximo_bus("A", "R9", "08:00"), None)
        self.assertEqual(self.r.proximo_bus("D", "R1", "08:00"), None)
        self.r.cerrar("A")
        self.assertEqual(self.r.proximo_bus("A", "R1", "08:00"), None)

    def test_r5(self):
        v = self.r.viaje("A", "E")
        self.assertEqual(v["paradas"], 1)  # R3 directo
        self.assertEqual(v["tipo"], "directo")
        v = self.r.viaje("B", "E")
        self.assertEqual(v["tipo"], "transbordo")
        self.assertEqual(v["transbordo"], "C")
        self.assertEqual(v["paradas"], 3)
        self.assertIsNone(self.r.viaje("E", "A"))      # sentido contrario
        self.assertIsNone(self.r.viaje("A", "F"))      # F sin rutas
        self.assertIsNone(self.r.viaje("A", "NOEXISTE"))
        self.assertEqual(self.r.viaje("A", "A")["paradas"], 0)
        self.r.cerrar("C")
        self.assertIsNone(self.r.viaje("B", "E"))      # no se puede transbordar en C
        self.assertIsNone(self.r.viaje("A", "C"))
        self.assertEqual(self.r.viaje("A", "E")["paradas"], 1)

    def test_r6(self):
        self.assertEqual(self.r.ranking(2), [("A", 4), ("C", 2)])
        self.r.cerrar("A")
        self.assertEqual(self.r.ranking(2), [("C", 2), ("B", 1)])
        self.assertEqual(len(self.r.ranking(100)), 5)
        self.assertEqual(self.r.ranking(0), [])

    def test_r7(self):
        self.assertEqual(self.r.recorrido("R1"), ["A", "B", "C"])
        self.assertEqual(self.r.recorrido("R1", al_reves=True), ["C", "B", "A"])
        self.assertTrue(self.r.agregar_parada("R1", "F", "A"))
        self.assertEqual(self.r.recorrido("R1"), ["A", "F", "B", "C"])
        self.assertFalse(self.r.agregar_parada("R1", "F", "A"))       # ya esta
        self.assertFalse(self.r.agregar_parada("R1", "X", "A"))       # no existe
        self.assertFalse(self.r.agregar_parada("R1", "D", "ZZ"))      # referencia invalida
        self.assertFalse(self.r.agregar_parada("RX", "D", "A"))
        self.assertTrue(self.r.quitar_parada("R1", "A"))
        self.assertEqual(self.r.recorrido("R1"), ["F", "B", "C"])
        self.assertFalse(self.r.quitar_parada("R1", "A"))
        self.assertEqual(self.r.recorrido("R1", al_reves=True), ["C", "B", "F"])
        self.assertEqual(self.r.recorrido("NOHAY"), [])
        # quitar A de R1 resta sus buses del ranking
        self.assertIn(("A", 1), self.r.ranking(10))   # perdio los 3 buses de R1
        self.assertIsNone(self.r.proximo_bus("A", "R1", "00:00"))

    def test_r9(self):
        base = (self.r.ranking(10), self.r.recorrido("R1"), self.r.autocompletar("", 10))
        self.assertFalse(self.r.deshacer())
        self.assertFalse(self.r.rehacer())
        self.r.cerrar("B")
        self.r.agregar_parada("R1", "F", "C")
        self.r.quitar_parada("R1", "A")
        self.r.reabrir("B")
        self.r.cerrar("A")
        for _ in range(5):
            self.assertTrue(self.r.deshacer())
        self.assertFalse(self.r.deshacer())
        self.assertEqual(base, (self.r.ranking(10), self.r.recorrido("R1"), self.r.autocompletar("", 10)))
        self.assertTrue(self.r.rehacer())
        self.assertEqual(self.r.estado("B"), "cerrada")
        self.r.cerrar("D")                 # cambio nuevo borra lo rehacible
        self.assertFalse(self.r.rehacer())
        self.assertTrue(self.r.deshacer())
        self.assertEqual(self.r.estado("D"), "abierta")
        self.assertTrue(self.r.rehacer())
        self.assertEqual(self.r.estado("D"), "cerrada")
        # operaciones fallidas no entran al historial
        n = len(self.r._deshacer)
        self.r.cerrar("D")
        self.r.reabrir("A")
        self.r.quitar_parada("R1", "E")
        self.assertEqual(len(self.r._deshacer), n)

    def test_r10(self):
        self.assertEqual(simular_fila([], 5, 3), [])
        self.assertEqual(simular_fila([0, 0, 0, 0, 0], 10, 2),
                         [(10, [0, 1]), (20, [2, 3]), (30, [4])])
        self.assertEqual(simular_fila([10], 10, 5), [(10, [0])])
        self.assertEqual(simular_fila([3, 1], 5, 5), [(5, [1, 0])])   # desordenadas
        with self.assertRaises(ValueError):
            simular_fila([1], 5, 0)


class RedReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = Red(DATOS)
        cls.nombres = sorted(cls.r._abierta)

    def test_contra_fuerza_bruta(self):
        r = self.r
        rnd = random.Random(7)
        for pref in ["", "C", "CAL", "CALLE 1", "PORTAL", "ZZ", "AV."]:
            for k in (1, 5, 1000):
                esp = [n for n in self.nombres if n.startswith(pref)][:k]
                self.assertEqual(r.autocompletar(pref, k), esp)
        for _ in range(100):
            a, b = rnd.choice(self.nombres), rnd.choice(self.nombres)
            self.assertEqual(r.rango(a, b), [n for n in self.nombres if a <= n <= b])
        esp = sorted(((-r._buses[n], n) for n in self.nombres))
        self.assertEqual(r.ranking(20), [(n, -b) for b, n in esp[:20]])

    def test_proximo_bus_fuerza_bruta(self):
        r = self.r
        rnd = random.Random(8)
        claves = list(r._horarios)
        for _ in range(300):
            ruta, est = rnd.choice(claves)
            h = rnd.randint(0, 24 * 60)
            horas = sorted(r._horarios[(ruta, est)])
            cand = [x for x in horas if x >= h]
            esp = None if not cand else str(cand[0] // 60).zfill(2) + ":" + str(cand[0] % 60).zfill(2)
            self.assertEqual(r.proximo_bus(est, ruta, h), esp)

    def test_viaje_fuerza_bruta(self):
        """Compara con busqueda exhaustiva de 0 y 1 transbordo (prioridad: transbordos, luego paradas)."""
        r = self.r
        rnd = random.Random(9)

        def brute(o, d):
            mejor = None
            seqs = {k: r.recorrido(k) for k in r._rutas}
            for a, sa in seqs.items():
                if o not in sa:
                    continue
                ia = sa.index(o)
                for i in range(ia + 1, len(sa)):
                    if sa[i] == d:
                        c = (0, i - ia)
                        mejor = c if mejor is None or c < mejor else mejor
                    for b, sb in seqs.items():
                        if b == a or sa[i] not in sb or d not in sb:
                            continue
                        ib, idd = sb.index(sa[i]), sb.index(d)
                        if idd > ib:
                            c = (1, i - ia + idd - ib)
                            mejor = c if mejor is None or c < mejor else mejor
            return mejor
        hechos = 0
        for _ in range(60):
            o, d = rnd.choice(self.nombres), rnd.choice(self.nombres)
            if o == d:
                continue
            esp = brute(o, d)
            v = r.viaje(o, d)
            if esp is not None:
                self.assertIsNotNone(v)
                self.assertEqual((len(v["transbordos"]), v["paradas"]), esp)
                hechos += 1
            elif v is not None:
                self.assertGreaterEqual(len(v["transbordos"]), 2)
        self.assertGreater(hechos, 10)

    def test_deshacer_aleatorio(self):
        r = Red(DATOS)
        rnd = random.Random(10)
        rutas = list(r._rutas)

        def foto():
            return (r.ranking(500), r.autocompletar("", 500),
                    [tuple(r.recorrido(x)) for x in rutas],
                    [r.estado(n) for n in self.nombres])
        fotos = [foto()]
        for _ in range(300):
            op = rnd.randint(0, 3)
            if op == 0:
                r.cerrar(rnd.choice(self.nombres))
            elif op == 1:
                r.reabrir(rnd.choice(self.nombres))
            elif op == 2:
                x = rnd.choice(rutas)
                rec = r.recorrido(x)
                if rec:
                    r.quitar_parada(x, rnd.choice(rec))
            else:
                x = rnd.choice(rutas)
                rec = r.recorrido(x)
                if rec:
                    r.agregar_parada(x, rnd.choice(self.nombres), rnd.choice(rec))
            fotos.append(foto())
        # el historial solo guarda cambios efectivos: comparamos contra el estado tras cada deshacer
        final = foto()
        pasos = 0
        while r.deshacer():
            pasos += 1
        self.assertEqual(foto(), fotos[0])
        for _ in range(pasos):
            self.assertTrue(r.rehacer())
        self.assertEqual(foto(), final)

    def test_r10_grande(self):
        rnd = random.Random(11)
        t = 0
        ll = []
        for _ in range(300000):
            t += rnd.randint(0, 2)
            ll.append(t)
        res = simular_fila(ll, 30, 160)
        total = 0
        for hora, ids in res:
            self.assertLessEqual(len(ids), 160)
            for j in ids:
                self.assertLessEqual(ll[j], hora)
            total += len(ids)
        self.assertEqual(total, len(ll))
        orden = [j for _, ids in res for j in ids]
        self.assertEqual(orden, list(range(len(ll))))  # orden de llegada


def red_con(rutas):
    d = tempfile.mkdtemp()
    est = sorted({e for lista in rutas.values() for e in lista})
    with open(d + "/estaciones.csv", "w", newline="") as f:
        f.write("nombre\r\n" + "".join(e + "\r\n" for e in est))
    with open(d + "/rutas.csv", "w", newline="") as f:
        f.write("ruta,orden,estacion\r\n")
        for r, lista in rutas.items():
            for o, e in enumerate(lista, 1):
                f.write("%s,%d,%s\r\n" % (r, o, e))
    with open(d + "/horarios.csv", "w", newline="") as f:
        f.write("ruta,estacion,hora\r\n")
    return Red(d)


class Cerradas(unittest.TestCase):
    def test_transbordo_en_cerrada_pasa_a_otra_estacion(self):
        # Como Modelia: el transbordo natural es M; si M esta cerrada, debe usar N.
        r = red_con({"R1": ["O", "M", "N"], "R2": ["M", "D"], "R3": ["N", "P", "D"]})
        v = r.viaje("O", "D")
        self.assertEqual((v["transbordo"], v["paradas"], v["cruza_cerrada"]), ("M", 2, False))
        r.cerrar("M")
        v = r.viaje("O", "D")
        self.assertEqual(v["tipo"], "transbordo")
        self.assertEqual((v["transbordo"], v["paradas"]), ("N", 3))
        self.assertTrue(v["cruza_cerrada"])          # el bus pasa por M, pero no se puede bajar ni transbordar

    def test_prefiere_no_cruzar_cerrada(self):
        # X es mas corta pero pasa por Q; Y no pasa por ninguna cerrada.
        r = red_con({"X": ["P", "Q", "S"], "Y": ["P", "T", "U", "S"]})
        self.assertEqual(r.viaje("P", "S")["tramos"][0][0], "X")
        r.cerrar("Q")
        v = r.viaje("P", "S")
        self.assertEqual(v["tramos"][0][0], "Y")
        self.assertFalse(v["cruza_cerrada"])

    def test_muchos_transbordos(self):
        r = red_con({"A": ["P", "Q"], "B": ["Q", "R"], "C": ["R", "S"], "D": ["S", "T"]})
        v = r.viaje("P", "T")
        self.assertEqual(v["transbordos"], ["Q", "R", "S"])
        self.assertEqual([t[0] for t in v["tramos"]], ["A", "B", "C", "D"])
        self.assertEqual(v["paradas"], 4)  # Q, R, S, T: una parada por estacion visitada

    def test_menos_transbordos_antes_que_menos_paradas(self):
        r = red_con({"L1": ["P", "A", "B", "C", "T"], "L2": ["P", "X"], "L3": ["X", "T"]})
        v = r.viaje("P", "T")
        self.assertEqual(v["transbordos"], [])
        self.assertEqual(v["paradas"], 4)

    def test_sin_ruta_es_none_aunque_haya_muchos_transbordos(self):
        r = red_con({"A": ["P", "Q"], "B": ["Q", "R"], "C": ["Z", "Y"]})
        self.assertIsNone(r.viaje("P", "Y"))

    def test_sin_alternativa_devuelve_none(self):
        r = red_con({"R1": ["O", "M", "N"], "R2": ["M", "D"], "R3": ["N", "P", "D"]})
        r.cerrar("M")
        r.cerrar("N")
        self.assertIsNone(r.viaje("O", "D"))


if __name__ == "__main__":
    unittest.main()
