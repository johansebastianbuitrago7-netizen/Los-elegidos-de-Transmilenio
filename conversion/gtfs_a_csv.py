"""Conversión del GTFS de TransMilenio a los tres CSV del motor.

Uso:
    python conversion/gtfs_a_csv.py ruta/al/gtfs.zip datos_salida/

Fuera de motor/ se permite cualquier librería; aquí basta la estándar.

Decisiones:
- Estación = parada padre (parent_station) si existe; si no, la parada misma.
  Nombre en MAYÚSCULAS, sin tildes, sin espacios repetidos.
- Una "ruta" del motor es un sentido de servicio: los viajes (trips) se
  agrupan por route_short_name + direction_id + secuencia exacta de
  estaciones. Cada patrón distinto recibe un sufijo -1, -2, ... en orden de
  frecuencia (el patrón con más viajes primero). Así "cada ruta va en un
  solo sentido", como pide el enunciado.
- Si un patrón visita dos veces la misma estación consecutiva (andenes de
  la misma estación), se colapsa en una sola parada.
- horarios.csv: una fila por (ruta, estación, hora) de cada viaje, con la
  hora de llegada (o salida si falta). Horas >= 24 se pliegan restando 24
  (25:10 -> 01:10): son la madrugada del mismo día de servicio.

Limitación: verificado con un GTFS sintético en tests/test_conversion.py;
el GTFS real de julio de 2021 (~54 MB) no está en el repositorio.
"""

import csv
import io
import os
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict


def normalizar(nombre):
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.upper().split())


def plegar_hora(hora):
    h, m = hora.strip().split(":")[:2]
    return f"{int(h) % 24:02d}:{int(m):02d}"


class FuenteGTFS:
    """Lee archivos de un .zip o de una carpeta descomprimida."""

    def __init__(self, ruta):
        self.ruta = ruta
        self.zip = zipfile.ZipFile(ruta) if zipfile.is_zipfile(ruta) else None

    def filas(self, nombre):
        if self.zip:
            interno = next((n for n in self.zip.namelist() if n.split("/")[-1] == nombre), None)
            if interno is None:
                raise FileNotFoundError(nombre)
            texto = io.TextIOWrapper(self.zip.open(interno), encoding="utf-8-sig")
        else:
            texto = open(os.path.join(self.ruta, nombre), encoding="utf-8-sig", newline="")
        with texto:
            yield from csv.DictReader(texto)


def convertir(origen, destino):
    gtfs = FuenteGTFS(origen)
    paradas = {}
    padre = {}
    for s in gtfs.filas("stops.txt"):
        paradas[s["stop_id"]] = s["stop_name"]
        padre[s["stop_id"]] = s.get("parent_station") or ""

    def estacion(stop_id):
        raiz = padre.get(stop_id) or stop_id
        return normalizar(paradas.get(raiz, paradas.get(stop_id, stop_id)))

    nombre_ruta = {r["route_id"]: (r.get("route_short_name") or r["route_id"]).strip() for r in gtfs.filas("routes.txt")}
    viajes = {t["trip_id"]: (nombre_ruta.get(t["route_id"], t["route_id"]), t.get("direction_id") or "0")
              for t in gtfs.filas("trips.txt")}

    por_viaje = defaultdict(list)
    for st in gtfs.filas("stop_times.txt"):
        if st["trip_id"] not in viajes:
            continue
        hora = st.get("arrival_time") or st.get("departure_time")
        if not hora:
            continue
        por_viaje[st["trip_id"]].append((int(st["stop_sequence"]), estacion(st["stop_id"]), hora))

    patrones = defaultdict(list)  # (ruta, sentido, secuencia) -> [viajes]
    for trip, filas in por_viaje.items():
        filas.sort()
        secuencia, horas = [], []
        for _, est, hora in filas:
            if secuencia and secuencia[-1] == est:
                continue
            secuencia.append(est)
            horas.append(hora)
        if len(secuencia) < 2 or len(set(secuencia)) != len(secuencia):
            continue  # circulares o de una sola parada: no son un sentido simple
        ruta, sentido = viajes[trip]
        patrones[(ruta, sentido, tuple(secuencia))].append(horas)

    conteo = Counter()
    nombres = {}
    for (ruta, sentido, secuencia), lista in sorted(patrones.items(), key=lambda kv: (kv[0][0], kv[0][1], -len(kv[1]), kv[0][2])):
        conteo[ruta] += 1
        nombres[(ruta, sentido, secuencia)] = f"{ruta}-{conteo[ruta]}"

    os.makedirs(destino, exist_ok=True)
    estaciones = set()
    with open(os.path.join(destino, "rutas.csv"), "w", newline="", encoding="utf-8") as fr, \
            open(os.path.join(destino, "horarios.csv"), "w", newline="", encoding="utf-8") as fh:
        wr, wh = csv.writer(fr), csv.writer(fh)
        wr.writerow(["ruta", "orden", "estacion"])
        wh.writerow(["ruta", "estacion", "hora"])
        for clave in sorted(nombres, key=lambda k: nombres[k]):
            nombre = nombres[clave]
            for i, est in enumerate(clave[2], 1):
                wr.writerow([nombre, i, est])
                estaciones.add(est)
            for horas in patrones[clave]:
                for est, hora in zip(clave[2], horas):
                    wh.writerow([nombre, est, plegar_hora(hora)])
    with open(os.path.join(destino, "estaciones.csv"), "w", newline="", encoding="utf-8") as fe:
        w = csv.writer(fe)
        w.writerow(["nombre"])
        for e in sorted(estaciones):
            w.writerow([e])
    return {"estaciones": len(estaciones), "rutas": len(nombres),
            "viajes": sum(len(v) for v in patrones.values())}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    print(convertir(sys.argv[1], sys.argv[2]))
