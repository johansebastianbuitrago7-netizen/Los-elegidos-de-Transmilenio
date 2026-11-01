"""R11: redes aisladas reproducibles, cronómetro real y resultados sin persistir."""
import csv
import statistics
import tempfile
import time
from pathlib import Path
from motor import Red, simular_fila

TEORIA = {
    'estado': 'O(1) promedio; O(n) peor caso hash',
    'autocompletar': 'O(log n + c), c = candidatos inspeccionados',
    'rango': 'O(log n + c); aquí c = n',
    'proximo_bus': 'O(log h); aquí h = 8',
    'ranking': 'O(k) caliente sin cierres; O(n log n) reconstrucción',
    'agregar_parada': 'O(1) amortizado promedio',
    'quitar_parada': 'O(1) promedio',
    'recorrido': 'O(n)',
    'cerrar': 'O(1) amortizado promedio',
    'reabrir': 'O(1) amortizado promedio',
    'deshacer': 'O(1) amortizado promedio',
    'rehacer': 'O(1) amortizado promedio',
    'simular_fila': 'O(n log n) con ordenamiento de entradas',
}


def generar(carpeta, n):
    estaciones = [f'E{i:08d}' for i in range(n + 1)]
    for nombre, columnas, filas in [
        ('estaciones', ['nombre'], [(x,) for x in estaciones]),
        ('rutas', ['ruta', 'orden', 'estacion'], [('R', i, x) for i, x in enumerate(estaciones[:-1])]),
        ('horarios', ['ruta', 'estacion', 'hora'], [('R', x, f'{h:02d}:00') for x in estaciones[:-1] for h in range(8)]),
    ]:
        with (Path(carpeta) / (nombre + '.csv')).open('w', encoding='utf8', newline='') as f:
            w = csv.writer(f); w.writerow(columnas); w.writerows(filas)
    return estaciones


def medir(base=64, repeticiones=7):
    if base not in (32, 64, 128, 256) or not 3 <= repeticiones <= 15:
        raise ValueError('Base permitida: 32, 64, 128, 256; repeticiones: 3–15')
    resultados = []
    for n in [base, base*2, base*4, base*8]:
        with tempfile.TemporaryDirectory() as carpeta:
            nombres = generar(carpeta, n)
            inicio = time.perf_counter_ns()
            red = Red(carpeta)
            carga = (time.perf_counter_ns()-inicio)/1000
            red.ranking(10)  # Calentar explícitamente la caché; carga medida aparte.
            operaciones = {
                'estado': (lambda: None, lambda: red.estado(nombres[0])),
                'autocompletar': (lambda: None, lambda: red.autocompletar('E', 10)),
                'rango': (lambda: None, lambda: red.rango(nombres[0], nombres[-1])),
                'proximo_bus': (lambda: None, lambda: red.proximo_bus(nombres[0], 'R', '03:30')),
                'ranking': (lambda: red.ranking(10), lambda: red.ranking(10)),
                'agregar_parada': (lambda: red.quitar_parada('R', nombres[-1]) if red.rutas.obtener('R').indice.obtener(nombres[-1]) else None,
                                   lambda: red.agregar_parada('R', nombres[-1], nombres[-2])),
                'quitar_parada': (lambda: red.agregar_parada('R', nombres[-1], nombres[-2]) if red.rutas.obtener('R').indice.obtener(nombres[-1]) is None else None,
                                  lambda: red.quitar_parada('R', nombres[-1])),
                'recorrido': (lambda: None, lambda: red.recorrido('R')),
                'cerrar': (lambda: red.reabrir(nombres[0]), lambda: red.cerrar(nombres[0])),
                'reabrir': (lambda: red.cerrar(nombres[0]), lambda: red.reabrir(nombres[0])),
                'deshacer': (lambda: red.cerrar(nombres[0]) if red.estado(nombres[0]) == 'abierta' else red.reabrir(nombres[0]), lambda: red.deshacer()),
                'rehacer': (lambda: (red.cerrar(nombres[0]) if red.estado(nombres[0]) == 'abierta' else red.reabrir(nombres[0]), red.deshacer()), lambda: red.rehacer()),
                'simular_fila': (lambda: None, lambda: simular_fila(list(range(n)), 5, 20)),
            }
            for nombre, (preparar, ejecutar) in operaciones.items():
                muestras = []
                for _ in range(repeticiones):
                    preparar()
                    inicio = time.perf_counter_ns()
                    ejecutar()
                    muestras.append((time.perf_counter_ns()-inicio)/1000)
                resultados.append({'operacion': nombre, 'n': n, 'mediana_us': statistics.median(muestras),
                                   'muestras_us': muestras, 'teoria': TEORIA[nombre], 'carga_us': carga})
    return {'resultados': resultados, 'unidad': 'microsegundos', 'repeticiones': repeticiones,
            'metodologia': 'Mediana de llamadas reales; preparación fuera del cronómetro. n paradas activas, n+1 estaciones, una ruta y 8n horarios. Ranking caliente k=10. Carga separada. R5 excluido.',
            'interpretacion': 'Tiempos pequeños incluyen ruido del reloj, intérprete y sistema. Hashing tiene peor caso lineal. Un n mayor no obliga a una medición mayor. Comparar tendencias, no una muestra. Las redes son sintéticas y no alteran los datos históricos.'}
