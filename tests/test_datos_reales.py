"""Verificaciones sobre los CSV originales, recalculadas con csv estándar."""

import csv
import unittest
from collections import Counter

from motor import Red


class TestDatosReales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.red = Red("datos")
        with open("datos/horarios.csv", encoding="utf-8") as f:
            cls.horarios = list(csv.reader(f))[1:]
        with open("datos/estaciones.csv", encoding="utf-8") as f:
            cls.estaciones = [x[0] for x in list(csv.reader(f))[1:]]

    def test_conteos_no_codificados(self):
        self.assertEqual(len(self.red.estaciones()), len(self.estaciones))
        self.assertEqual(self.red.diagnostico.obtener("eventos"), len(self.horarios))

    def test_caso_b10_portal_norte(self):
        self.assertEqual(self.red.proximo_bus("PORTAL NORTE", "B10-1", "09:25"), "11:33")
        horas = sorted(h for r, e, h in self.horarios if r == "B10-1" and e == "PORTAL NORTE")
        siguiente = next(h for h in horas if h >= "09:25")
        self.assertEqual(siguiente, "11:33")
        self.assertEqual(self.red.recorrido("B10-1")[0], "PORTAL 80")
        self.assertEqual(self.red.recorrido("B10-1")[-1], "PORTAL NORTE")

    def test_proximo_bus_contra_csv(self):
        grupos = {}
        for r, e, h in self.horarios:
            grupos.setdefault((r, e), []).append(h)
        for i, ((r, e), horas) in enumerate(sorted(grupos.items())):
            if i % 7:
                continue
            horas.sort()
            for consulta in ("00:00", "05:30", "09:25", "17:45", "23:59"):
                esperado = next((h for h in horas if h >= consulta), None)
                self.assertEqual(self.red.proximo_bus(e, r, consulta), esperado, (r, e, consulta))

    def test_ranking_contra_csv(self):
        conteo = Counter(e for _, e, _ in self.horarios)
        esperado = sorted(conteo.items(), key=lambda p: (-p[1], p[0]))[:10]
        self.assertEqual(self.red.ranking(10), esperado)

    def test_autocompletar_y_rango_contra_sorted(self):
        todas = sorted(self.estaciones)
        for prefijo in ("CAL", "PORTAL", "A", "Z", ""):
            esperado = [e for e in todas if e.startswith(prefijo)][:6]
            self.assertEqual(self.red.autocompletar(prefijo, 6), esperado)
        self.assertEqual(self.red.rango("CALLE 26", "CALLE 80"),
                         [e for e in todas if "CALLE 26" <= e <= "CALLE 80"])


if __name__ == "__main__":
    unittest.main()
