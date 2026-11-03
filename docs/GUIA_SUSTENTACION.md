# Guía de sustentación de Atlas

Para estudiantes de segundo semestre. Cada sección dice **dónde está el código**, **qué
responder** y **qué cambio en vivo podrían pedir**.

## Mapa rápido del motor

| Archivo | Qué hay | Líneas clave |
|---|---|---|
| `motor/estructuras.py` | TablaHash, ListaDoble, Pila, Cola | `TablaHash.poner`, `_redimensionar`, `ListaDoble.insertar_despues`, `Cola._crecer` |
| `motor/algoritmos.py` | merge sort estable, búsqueda binaria | `indices_ordenados`, `limite_inferior` |
| `motor/tiempo.py` | HH:MM ↔ minutos | `a_minutos`, `minutos_csv` |
| `motor/carga.py` | lectura de CSV con `csv.reader` | `leer_tabla` |
| `motor/red.py` | clase `Red` (R1–R9) | un bloque comentado por requisito |
| `motor/fila.py` | `simular_fila` (R10) | bucle ENQUEUE/DEQUEUE |

Cómo fluye una consulta: navegador → `static/js/<lámina>.js` → `app.py` (valida y toma el
candado) → `servicios/presentacion.py` (solo formatea) → `motor`.

## Preguntas frecuentes

**¿Por qué una tabla hash y no buscar en la lista de estaciones?** Buscar en una lista es O(n) y
R1 es la consulta más frecuente. La tabla calcula la cubeta con el hash y solo compara con las
pocas claves de esa cubeta: O(1) en promedio. Las colisiones ("Aa" y "BB" tienen el mismo hash)
se resuelven encadenando; `tests/test_estructuras.py` lo prueba.

**¿Qué pasa cuando la tabla se llena?** Al superar 0,75 elementos por cubeta se duplica el arreglo
y se reubica cada entrada (O(n) esa vez). Como ocurre cada vez que el tamaño se duplica, el costo
promedio por inserción sigue siendo O(1) (amortizado).

**¿Por qué no usar la tabla hash para autocompletar?** Porque no guarda orden: para "CAL" habría
que revisar todas las claves. Con el arreglo ordenado, la búsqueda binaria encuentra el primer
candidato en O(log n) y los demás están contiguos.

**¿Qué es n en R4?** Los eventos de la pareja (ruta, estación), no las estaciones. Duplicar la red
copiando rutas no cambia m; por eso en el panel usamos una troncal cuyo m crece con n.

**¿Por qué R5 no es un BFS normal?** El BFS por estaciones no sabe cuántos transbordos lleva ni
respeta "una sola ruta por tramo". Nuestro método combina dos barridos (hacia adelante desde el
origen, hacia atrás desde el destino) y un cruce en los transbordos. En las pruebas lo comparamos
con un 0-1 BFS sobre estados (estación, ruta, transbordos) y con fuerza bruta, en 60 redes
aleatorias con cierres y tras ediciones aleatorias.

**¿Por qué los empates de R5 y R6 son alfabéticos?** Para que dos ejecuciones den el mismo
resultado. En R6 sale "gratis": el merge sort es estable y la entrada ya es alfabética.

**¿Por qué el ranking no se recalcula en cada consulta?** El enunciado dice que se consulta mucho
y cambia poco. Guardamos el arreglo ordenado y solo lo invalidamos al cerrar, reabrir o editar.

**¿Cómo se deshace quitar una parada?** Al quitarla guardamos cuál era la estación anterior. La
inversa es insertar después de esa anterior (o al inicio si era la primera).

**¿Por qué la fila no simula minuto a minuto?** Si el último pasajero llega en el minuto 1.000.000,
simular cada minuto costaría un millón de pasos aunque haya 3 pasajeros. Saltamos al siguiente bus
útil con aritmética: `ceil(llegada / f) * f`.

**¿Qué pasa si las llegadas vienen desordenadas?** Se ordenan los **índices** con merge sort
estable; el resultado se escribe en la posición original de cada pasajero.

**¿La interfaz decide algo?** No. El laboratorio dibuja los pasos que reconstruye
`servicios/laboratorio.py` a partir de los abordajes que devuelve `simular_fila`.

## Ejercicios de cambio en vivo (con pista)

1. **Autocompletar sin distinguir mayúsculas.** Pista: normalizar el prefijo con `.upper()` al
   inicio de `autocompletar`; los nombres ya están en mayúsculas.
2. **R4: si no hay más buses hoy, devolver el primero del día.** Pista: en `_indice_proximo`,
   si `i >= len(eventos)` devolver 0 en lugar de -1 (y documentarlo).
3. **R5 con hasta dos transbordos.** Pista: el método actual no escala; usar BFS por niveles sobre
   (estación, ruta) con el contador de transbordos, como `tests/apoyo.viaje_bfs01`.
4. **R6 con los k menos transitados.** Pista: misma caché, recorrer `_ranking` desde el final.
5. **Agregar `red.paradas_de(ruta)`** que devuelva cuántas paradas tiene. Pista: `len` de la
   `ListaDoble` es O(1).
6. **Cerrar varias estaciones en una sola operación deshacible.** Pista: una operación
   `("cerrar_varias", [nombres])` con su inversa en `_aplicar_inversa`.
7. **R10 devolviendo también el número de buses usados.** Pista: no cambiar el retorno público;
   crear otra función que reutilice `simular_fila`.

Después de cualquier cambio: `python -m unittest discover` y `python herramientas/restricciones.py`.

## Casos límite que conviene saber de memoria

- `estado("portal norte")` → `"inexistente"` (el motor exige nombre exacto; la app normaliza).
- `rango("Z", "A")` → `[]`.
- `proximo_bus` con hora `"24:00"` → `ValueError`.
- `viaje(x, x)` → `[]`; origen o destino cerrados → `None`.
- `agregar_parada` de una estación que ya está en la ruta → `False`.
- `cerrar` de una cerrada → `False` y no entra al historial.
- `simular_fila([5], 5, 1)` → `[5]` (llega justo y sube).
