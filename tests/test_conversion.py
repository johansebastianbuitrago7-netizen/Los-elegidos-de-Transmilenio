"""Conversión GTFS -> CSV con un GTFS sintético mínimo."""

import os
import shutil
import tempfile
import unittest

from conversion.gtfs_a_csv import convertir
from motor import Red

GTFS = {
    "stops.txt": "stop_id,stop_name,parent_station\nP1,Portal Ñ,\nP1a,Portal Ñ andén,P1\nP2,Calle  Única,\nP3,Héroes,\n",
    "routes.txt": "route_id,route_short_name\nR,B1\n",
    "trips.txt": "route_id,trip_id,direction_id\nR,T1,0\nR,T2,0\nR,T3,1\n",
    "stop_times.txt": (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "T1,06:00:00,06:00:00,P1a,1\nT1,06:05:00,06:05:00,P2,2\nT1,06:09:00,06:09:00,P3,3\n"
        "T2,24:50:00,24:50:00,P1,1\nT2,24:55:00,24:55:00,P2,2\nT2,25:01:00,25:01:00,P3,3\n"
        "T3,07:00:00,07:00:00,P3,1\nT3,07:06:00,07:06:00,P1,2\n"
    ),
}


class TestConversion(unittest.TestCase):
    def test_gtfs_minimo(self):
        origen = tempfile.mkdtemp()
        destino = tempfile.mkdtemp()
        try:
            for nombre, texto in GTFS.items():
                with open(os.path.join(origen, nombre), "w", encoding="utf-8") as f:
                    f.write(texto)
            resumen = convertir(origen, destino)
            self.assertEqual(resumen, {"estaciones": 3, "rutas": 2, "viajes": 3})
            red = Red(destino)
            self.assertEqual(red.recorrido("B1-1"), ["PORTAL N", "CALLE UNICA", "HEROES"])
            self.assertEqual(red.recorrido("B1-2"), ["HEROES", "PORTAL N"])
            self.assertEqual(red.horarios("HEROES", "B1-1"), ["01:01", "06:09"])
            self.assertEqual(red.viaje("PORTAL N", "HEROES"), [("B1-1", "PORTAL N", "HEROES")])
        finally:
            shutil.rmtree(origen)
            shutil.rmtree(destino)


if __name__ == "__main__":
    unittest.main()
