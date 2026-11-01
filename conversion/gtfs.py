"""python -m conversion.gtfs archivo.zip carpeta_salida"""
import argparse
import csv
import io
import unicodedata
import zipfile
from pathlib import Path


def normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', texto.upper())
                            if unicodedata.category(c) != 'Mn').split())


def convertir(archivo, salida):
    """Cada patrón dirigido distinto obtiene un ID; no mezcla servicios divergentes.

    Conserva todas las filas/trips, sin filtrar calendario: oferta programada del
    archivo, no un día calendario real. Segundos se truncan; horas >=24 se conservan.
    """
    with zipfile.ZipFile(archivo) as z:
        def leer(nombre):
            with z.open(nombre) as f:
                return list(csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig')))
        stops = leer('stops.txt'); trips = leer('trips.txt'); times = leer('stop_times.txt')
        routes = {r['route_id'] for r in leer('routes.txt')}
    nombres = {r['stop_id']: normalizar(r['stop_name']) for r in stops}
    if any(not n for n in nombres.values()):
        raise ValueError('Nombre de parada vacío')
    grupos = {}
    for fila in times:
        if fila['stop_id'] not in nombres:
            raise ValueError('stop_id desconocido')
        grupos.setdefault(fila['trip_id'], []).append(fila)
    patrones, rutas, horarios = {}, [], []
    for viaje in sorted(trips, key=lambda t:t['trip_id']):
        if viaje['route_id'] not in routes:
            raise ValueError('route_id desconocido')
        filas = sorted(grupos.pop(viaje['trip_id'], []), key=lambda f:int(f['stop_sequence']))
        if not filas:
            continue
        secuencia = tuple(nombres[f['stop_id']] for f in filas)
        if len(set(secuencia)) != len(secuencia):
            raise ValueError('Patrón circular o nombres colapsados: el motor exige estaciones únicas por ruta')
        if len({int(f['stop_sequence']) for f in filas}) != len(filas):
            raise ValueError('stop_sequence repetido')
        patron = (viaje['route_id'], viaje.get('direction_id', ''), secuencia)
        if patron not in patrones:
            # Codificación por longitud evita colisiones entre IDs arbitrarios.
            base = viaje['route_id']; sentido = viaje.get('direction_id', '')
            identificador = f'{len(base)}:{base}:{len(sentido)}:{sentido}:P{len(patrones)+1}'
            patrones[patron] = identificador
            rutas.extend((identificador, i, nombre) for i,nombre in enumerate(secuencia,1))
        for fila, nombre in zip(filas, secuencia):
            valor = fila.get('departure_time') or fila.get('arrival_time')
            partes = (valor or '').split(':')
            if len(partes) != 3 or not all(x.isdigit() for x in partes):
                raise ValueError('GTFS requiere horario explícito HH:MM:SS')
            h,m,s = map(int, partes)
            if m >= 60 or s >= 60:
                raise ValueError('Hora GTFS inválida')
            horarios.append((patrones[patron], nombre, f'{h:02d}:{m:02d}'))
        if viaje.get('frequencies'):
            raise ValueError('Frecuencias no soportadas')
    if grupos:
        raise ValueError('stop_times con trip_id desconocido')
    with zipfile.ZipFile(archivo) as z:
        if 'frequencies.txt' in z.namelist():
            raise ValueError('frequencies.txt requiere expansión previa explícita')
    salida = Path(salida)
    # No sobrescribir los datos existentes ni producir entregas parciales por validación.
    if any((salida / (n+'.csv')).exists() for n in ('estaciones','rutas','horarios')):
        raise ValueError('La carpeta de salida ya contiene CSV; use una carpeta nueva')
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, columnas, filas in [
        ('estaciones',['nombre'],[(n,) for n in sorted(set(nombres.values()))]),
        ('rutas',['ruta','orden','estacion'],rutas),
        ('horarios',['ruta','estacion','hora'],horarios),
    ]:
        with (salida/(nombre+'.csv')).open('w',encoding='utf8',newline='') as f:
            w=csv.writer(f);w.writerow(columnas);w.writerows(filas)
    return {'estaciones':len(set(nombres.values())), 'rutas':len(patrones), 'horarios':len(horarios)}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip');parser.add_argument('salida')
    args=parser.parse_args()
    print(convertir(args.zip,args.salida))
