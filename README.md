# Atlas · Los Elegidos de TransMilenio

Planeador de viajes sobre la red programada de TransMilenio (GTFS de julio de 2021),
con un motor de estructuras de datos escrito a mano en Python y una interfaz web
editorial organizada como las láminas de un atlas.

> Los horarios son **programados de 2021**, no información en tiempo real.

## Arranque (un solo comando)

```bash
python -m pip install -r requirements.txt && python app.py
```

Abre <http://127.0.0.1:5000>. Si el puerto está ocupado: `set PORT=5051` (Windows cmd)
o `$env:PORT=5051` (PowerShell) antes de `python app.py`.

En Windows, con entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Pruebas y auditoría:

```bash
python -m unittest discover -v
python herramientas/restricciones.py
python herramientas/medir.py 4000 5
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `motor/` | El motor académico: solo `csv`, `time`, `random` y módulos propios. |
| `servicios/` | Presentación (etiquetas de ruta, detalle de viaje), laboratorio FIFO y mediciones R11. |
| `app.py` | Flask: valida HTTP, toma un candado y llama al motor. Sin reglas de negocio. |
| `templates/`, `static/` | Interfaz (HTML, CSS y un archivo JS por lámina, sin compilación). |
| `conversion/` | `gtfs_a_csv.py`: GTFS → tres CSV. |
| `herramientas/` | Auditoría AST de prohibiciones y medición de rendimiento por consola. |
| `tests/` | `unittest`: estructuras, R1–R10, referencias independientes, API y conversión. |
| `docs/` | Enunciado, especificación, guía de sustentación, rendimiento medido y capturas. |

## Contrato del motor

```python
from motor import Red, simular_fila
red = Red("datos")
```

El enunciado dice que el detalle de los retornos está "en el enunciado", que no está en el
repositorio. Estas son **nuestras** convenciones (ver `docs/ESPECIFICACION_ATLAS.md`):

| Llamada | Devuelve |
|---|---|
| `red.estado(nombre)` | `"abierta"`, `"cerrada"` o `"inexistente"` (nombre exacto) |
| `red.autocompletar(prefijo, k)` | lista de hasta k nombres abiertos con ese prefijo, alfabética |
| `red.rango(desde, hasta)` | lista alfabética de abiertas con `desde <= nombre <= hasta` |
| `red.proximo_bus(estacion, ruta, hora)` | `"HH:MM"` del primer registro `>= hora`, o `None` |
| `red.viaje(origen, destino)` | `[(ruta, subir, bajar)]` o `[(r1, origen, t), (r2, t, destino)]`; `[]` si son la misma; `None` si no hay |
| `red.ranking(k)` | `[(nombre, buses_al_dia), ...]` de mayor a menor |
| `red.agregar_parada(ruta, nueva, despues_de)` | `True`/`False` (`despues_de=None` inserta al inicio) |
| `red.quitar_parada(ruta, estacion)` | `True`/`False` |
| `red.recorrido(ruta, al_reves=False)` | lista de nombres, o `None` si la ruta no existe |
| `red.cerrar(nombre)`, `red.reabrir(nombre)` | `True` si cambió el estado |
| `red.deshacer()`, `red.rehacer()` | `True` si había algo que deshacer/rehacer |
| `simular_fila(llegadas, frecuencia, capacidad)` | lista de minutos de abordaje alineada con `llegadas` |

`proximo_bus` lanza `ValueError` si la hora no es `HH:MM` válida; `simular_fila` lo hace si
frecuencia o capacidad no son enteros positivos o si una llegada no es entera.

## R12 · Decisiones por requisito

Notación: **n** = estaciones, **R** = rutas, **L** = paradas de una ruta, **m** = eventos de
horario de una pareja (ruta, estación), **k** = resultados pedidos, **c** = estaciones cerradas
saltadas, **p** = pasajeros. "Promedio" se refiere a la tabla hash.

### Estructuras propias (`motor/estructuras.py`, `motor/algoritmos.py`)

- **TablaHash**: encadenamiento separado, hash polinomial base 31 sobre el texto, capacidad
  potencia de 2, se duplica al superar factor de carga 0,75. poner/obtener/eliminar O(1) promedio.
- **ListaDoble**: nodos con `anterior`/`siguiente`; insertar después de un nodo conocido y
  eliminar un nodo conocido en O(1); recorrer en ambos sentidos en O(L).
- **Pila** enlazada (O(1)), **Cola** sobre arreglo circular que se duplica (O(1) amortizado).
- **Merge sort** iterativo, estable, sobre índices (O(n log n), O(n) si ya viene ordenado).
- **Búsqueda binaria** `limite_inferior` (O(log n)).

### R1 · Buscar una estación
- **Estructura**: tabla hash nombre → objeto `Estacion` (bandera `abierta`).
- **Costo**: O(1) promedio (más O(|nombre|) del hash).
- **Descartada**: arreglo ordenado + búsqueda binaria (O(log n)). R1 es la consulta más
  frecuente, así que preferimos O(1) aunque la tabla no guarde orden.

### R2 · Autocompletar
- **Estructura**: arreglo de nombres ordenado con merge sort al cargar; búsqueda binaria del
  primer nombre `>= prefijo`, y avance mientras empiece por el prefijo, saltando cerradas.
- **Costo**: O(log n + k + c).
- **Descartada**: trie (O(|prefijo| + k), pero más memoria y más código para cerrar/reabrir);
  recorrer todo el arreglo (O(n)).

### R3 · Rango
- **Estructura**: el mismo arreglo ordenado: búsqueda binaria de `desde` y avance hasta `hasta`.
- **Costo**: O(log n + m) con m = nombres en el rango (incluye cerradas saltadas).
- **Descartada**: árbol AVL de abiertas: O(log n) por cierre en vez de O(1), y la red de
  nombres es fija (agregar paradas no crea estaciones nuevas).

### R4 · Próximo bus
- **Estructura**: tabla hash `ruta␟estación` → arreglo de minutos ordenado (merge sort al cargar);
  búsqueda binaria del primer minuto `>= hora`.
- **Costo**: O(1) + O(log m). Carga O(E log m) para E eventos.
- **Descartada**: recorrido lineal del arreglo (O(m); las troncales tienen cientos de eventos).
- **Bordes**: estación cerrada, ruta inexistente o estación que ya no está en la ruta → `None`;
  sin registros posteriores ese día → `None` (no pasamos al día siguiente).
  Horas GTFS ≥ 24 (25:10) se pliegan a 01:10 al cargar: son madrugada del mismo día de servicio.

### R5 · Planear un viaje
- **Algoritmo**: dos barridos sobre listas dobles.
  1. Desde el origen, por cada ruta que para ahí, avanzar hacia adelante guardando para cada
     estación **abierta** la menor distancia (en paradas) y su ruta (arreglos por id de estación
     con "marca de consulta" para no reiniciarlos).
  2. Desde el destino, por cada ruta que para ahí, retroceder; cada estación abierta alcanzada
     en ambos barridos es un transbordo candidato con costo d1 + d2.
  3. Se compara con el mejor directo. Desempate: menos paradas → directo antes que transbordo →
     orden alfabético de (ruta 1, transbordo, ruta 2).
- **Costo**: O(Σ largo de las rutas que tocan origen y destino). No se mide (lo dice el enunciado).
- **Descartada**: BFS sobre un grafo de estados (estación, ruta, transbordos): correcto y lo
  usamos como **referencia en las pruebas** (0-1 BFS), pero recorre toda la red.
- **Paradas** = enlaces recorridos. El bus atraviesa estaciones cerradas sin detenerse (cuentan
  como enlace), pero no se puede subir, bajar ni transbordar en ellas.

### R6 · Ranking
- **Estructura**: cada estación guarda `buses` = filas de `horarios.csv` de las rutas que hoy
  paran en ella (se actualiza en O(1) al agregar/quitar parada). Arreglo ordenado en **caché**
  (merge sort estable por buses descendente sobre entrada alfabética); cerrar, reabrir o editar
  solo lo invalida.
- **Costo**: consulta O(k); reconstrucción O(n log n) solo tras un cambio.
- **Descartada**: montículo (O(k log n) por consulta, peor para "se consulta muy seguido");
  reordenar en cada consulta (O(n log n) siempre).

### R7 · Editar rutas
- **Estructura**: cada ruta es una lista doble + tabla hash estación → nodo. Cada estación tiene
  una lista doble de rutas que paran en ella (para R5) y cada parada guarda su nodo ahí.
- **Costo**: agregar/quitar O(1) promedio; recorrido O(L) en cualquier sentido.
- **Descartada**: lista de Python (insertar/quitar en medio es O(L)).
- **Reglas**: la nueva debe ser una estación existente que no esté ya en la ruta;
  `despues_de` debe estar en la ruta (`None` = al inicio).

### R8 · Cerrar y reabrir
- Bandera en la estación: O(1). No se borra nada: rutas, horarios y conteos se conservan.
  R2, R3, R6 la saltan; R4 y R5 no la usan para subir, bajar ni transbordar.

### R9 · Deshacer y rehacer
- **Estructura**: dos pilas enlazadas de operaciones (tuplas). Deshacer aplica la inversa y pasa
  la operación a rehacer; un cambio nuevo vacía rehacer. Quitar parada guarda la anterior para
  reinsertarla en el mismo lugar.
- **Costo**: O(1) promedio por operación.
- Solo entran al historial las operaciones que cambiaron algo (cerrar una ya cerrada no).

### R10 · Fila de abordaje
- **Algoritmo**: ordenar índices por llegada con merge sort **estable** (O(p) si ya vienen
  ordenadas), luego simular con la **Cola** propia: en cada bus se encola a todos los que llegaron
  hasta su minuto y se desencola hasta la capacidad. Los buses sin nadie esperando se saltan
  calculando el siguiente múltiplo de f, así el costo no depende de la duración.
- **Costo**: O(p log p) tiempo, O(p) memoria (no se guarda una fila por pasajero y bus).
- **Descartada**: simular minuto a minuto (O(T + p), con T potencialmente enorme) y conteo por
  minuto (memoria O(T)).
- **Escenario del enunciado**: `simular_fila([0,0,1,2,5,5,9], 5, 3)` → `[0,0,5,5,5,10,10]`;
  esperas `[0,0,4,3,0,5,1]`, media 13/7, máxima 5, 3 buses con abordajes.

## R11 · Panel de rendimiento

Lámina 07 de la app y `herramientas/medir.py`. Redes sintéticas de n = 250, 500, 1000, 2000,
4000 estaciones en carpetas temporales (nunca la red compartida), carga medida aparte, mediana de
varias repeticiones y comparación de t(2n)/t(n) contra la razón esperada. Resultado más reciente:
[`docs/RENDIMIENTO_MEDIDO.md`](docs/RENDIMIENTO_MEDIDO.md).

## Datos

- `datos/`: los CSV originales, sin modificar (147 estaciones, 181 rutas dirigidas, 1.927
  paradas, 140.492 registros). El motor no codifica ninguna de estas cifras.
- `conversion/gtfs_a_csv.py`: script de conversión (probado con un GTFS sintético; el zip real
  de 54 MB no está en el repositorio).

## Documentación adicional

- [`docs/ESPECIFICACION_ATLAS.md`](docs/ESPECIFICACION_ATLAS.md): requisitos del profesor vs.
  decisiones propias vs. mejoras.
- [`docs/GUIA_SUSTENTACION.md`](docs/GUIA_SUSTENTACION.md): cómo defender cada decisión,
  preguntas frecuentes y ejercicios de cambio.
- [`ESTADO_ATLAS.md`](ESTADO_ATLAS.md): estado de avance.
- [`integrantes.md`](integrantes.md): a completar por el grupo.
