# Instrucciones para tareas futuras

Trabajar en este checkout; cada tarea cloud está aislada, no crear worktrees sin petición.
No editar main ni hacer merge sin autorización. Crear rama propia y preservar cambios ajenos.

## Arquitectura
- `motor/`: Python estándar, R1–R10 y estructuras propias.
- `app.py`: adaptación JSON, validación HTTP, candado para estado compartido.
- `templates/`, `static/`: interfaz sin reglas de planificación duplicadas.
- `conversion/`: GTFS, independiente de la aplicación.
- `herramientas/`: auditoría AST y mediciones sintéticas aisladas.
- `tests/`: unittest, oráculos, pruebas web y navegador opcional.

## Reglas obligatorias del motor
Prohibidos dict/set, literales/comprensiones de esos tipos, sorted, .sort(), min/max
sobre colecciones, pertenencia para buscar en listas, .index(), .count(), bisect,
heapq, collections, functools y dependencias externas. Módulos permitidos csv,
time, random y módulos propios relativos. Listas como arreglos, tuplas, ciclos y
clases propias. No usar DictReader. Ejecutar la auditoría tras cualquier cambio.

Contrato: `from motor import Red, simular_fila`. Preservar las firmas publicadas
en README (incluyendo nombres de parámetros). No cambiar retornos sin revisar
motor/modelos.py, documentación, API, frontend y pruebas.

## Validación
Python >=3.10. `python -m pip install -r requirements.txt` (preferir .venv).
`python -m unittest discover -v`
`python herramientas/restricciones.py`
`python app.py` inicia en 127.0.0.1:5000 sin debug.
Opcional Playwright: con servidor activo `node tests/navegador.cjs`;
requiere Playwright y Chromium (`CHROMIUM_PATH` portable).

## Cómo cambiar
No tocar los CSV originales para ajustar algoritmos ni inventar eventos.
Actualizar índices, conteos y operaciones inversas juntos. Agregar una prueba
con red mínima y resultado conocido. R5 se compara además con 0-1 BFS de referencia.
Medir rendimiento fuera de la red compartida y sin incluir carga en consultas.
Leer las dos guías de docs antes de ampliar funcionalidades.
