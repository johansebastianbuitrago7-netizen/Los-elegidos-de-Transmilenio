# Los Elegidos de TransMilenio · Pulso Urbano V2

Planeador académico de viajes dirigido, con máximo un transbordo, motor Python
sin dependencias externas y aplicación Flask. Datos **históricos/programados**
identificados en la presentación como GTFS de julio de 2021, no llegadas reales.
No hay afiliación oficial ni coordenadas geográficas en los datos suministrados.


## Qué cambia en Pulso Urbano V2

Se conserva el motor y contrato R1–R10, R11 y los CSV de la V1. La consulta de horarios
ahora parte de una estación, ofrece rutas válidas con sentido real y explica el
próximo registro, su diferencia en minutos y los cinco eventos siguientes. Caso real:
B10-1 / PORTAL NORTE / 09:25 → 11:33, diferencia **128 minutos**.

El laboratorio de hora pico tiene modo educativo (hasta 40 pasajeros, reproducción
por eventos y cola visible) y modo avanzado (hasta 300.000, métricas, cuatro gráficas,
semilla y comparación A/B con exactamente las mismas llegadas). Nunca se presenta
como demanda observada de Bogotá. Los resultados avanzados se envían agregados.

Nuevos módulos: `motor/analisis_fila.py` deriva métricas del retorno existente;
`servicios/` genera escenarios y metadatos; `static/js/horarios.js`, `laboratorio.js`,
`producto.js` y `componentes.js` separan los flujos. No hay nuevas dependencias de
aplicación. El análisis extra cuesta O(N log N), aparte del costo original de R10.

- [Guía de horarios](docs/GUIA_HORARIOS.md)
- [Guía del simulador](docs/GUIA_SIMULADOR_HORA_PICO.md)
- [Diseño y experiencia V2](docs/DISENO_Y_EXPERIENCIA_V2.md)
- [Capturas reales](docs/capturas-v2/README.md)

El servidor sigue iniciándose con `python app.py`. Las nuevas rutas de lectura son
`/api/estacion/rutas`, `/api/ruta`, `/api/horarios`; el laboratorio usa POST
`/api/laboratorio`. El endpoint anterior `/api/operacion` se conserva.

## Ejecutar en Windows, Linux o macOS

Python 3.10 o posterior (verificado en 3.12). Desde la raíz del repositorio:

```bash
python -m venv .venv
```

Windows PowerShell: `.venv\Scripts\Activate.ps1`; CMD: `.venv\Scripts\activate.bat`.
Si PowerShell bloquea la activación, usar directamente `.venv\Scripts\python.exe`.
Linux/macOS: `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000` en el navegador. Sin Node, compilación ni servicios
externos para usar la aplicación. Sin virtualenv también es posible instalar las
dependencias con el Python del sistema, aunque se recomienda aislarlas.
Si falta Flask, comprobar que pip y app usan el mismo intérprete. Si el puerto está
ocupado, detener el proceso anterior o usar `python -m flask --app 'app:crear_app()' run --port 5001`.
Las rutas de datos se resuelven desde app.py, no desde una ubicación absoluta cloud.

## Verificar

```bash
python -m unittest discover -v
python herramientas/restricciones.py
```

Las 34 pruebas actuales incluyen datos reales, otras redes, FIFO de 200.000 personas,
588 consultas R5 comparadas con un oráculo 0-1 BFS, 200 ediciones reversibles,
conversión GTFS, API y rendimiento. No se dispone del evaluador del profesor.
Prueba de navegador opcional, con servidor activo: `node tests/navegador.cjs`.
En la V2 ese comando ejecuta `tests/navegador_v2.cjs`: ocho pantallas y cinco anchos, controles FIFO, horarios, A/B y capturas.
Requiere Playwright y Chromium, ajenos a la aplicación. En una instalación de QA
puede instalarse Playwright con npm y proporcionar `CHROMIUM_PATH` con la ruta de
Chromium; el valor predeterminado de esa prueba es `/usr/bin/chromium`.

## Arquitectura y flujo

CSV → `Red` (índices y estructuras propias) → API Flask → HTML/CSS/JavaScript.
La web serializa los resultados; no calcula viajes ni ranking en JavaScript.
`conversion/gtfs.py` prepara CSV y no es importado por el motor.
`herramientas/rendimiento.py` genera redes temporales e invoca el motor real.

La red de la web es compartida por todos los navegadores del servidor; las
modificaciones están protegidas con un candado y viven en memoria. Reiniciar
restaura los CSV. Es una demostración **local**, sin autenticación ni persistencia
multiusuario; no desplegar públicamente como sistema de operación real.

## Contrato público y retornos adoptados

```python
from motor import Red, simular_fila
red = Red('datos')
```

| Firma exacta | Retorno |
|---|---|
| `estado(nombre)` | `'abierta'`, `'cerrada'` o `'inexistente'` |
| `autocompletar(prefijo, k)` | lista de nombres abiertos ordenados |
| `rango(desde, hasta)` | lista de nombres abiertos en rango inclusivo |
| `proximo_bus(estacion, ruta, hora)` | cadena HH:MM o `None` |
| `viaje(origen, destino)` | objeto `Viaje` o `None` |
| `ranking(k)` | lista de tuplas `(nombre, cantidad)` |
| `agregar_parada(ruta, nueva, despues_de)` | `True`; errores: ValueError |
| `quitar_parada(ruta, estacion)` | `True`; errores: ValueError |
| `recorrido(ruta, al_reves=False)` | lista de nombres, incluyendo cerradas |
| `cerrar(nombre)`, `reabrir(nombre)` | bool: si realmente cambió; desconocida: ValueError |
| `deshacer()`, `rehacer()` | bool: si se aplicó operación |
| `simular_fila(llegadas, frecuencia, capacidad)` | objeto `Simulacion` |

`Viaje`: `rutas`, `transbordo`, `estaciones`, `paradas`, `tramos` (una lista por ruta).
`Simulacion`: `abordajes`, `esperas` (orden original de pasajeros), `buses`
(salidas con abordajes), `pasajeros`, `espera_media`, `espera_maxima`.
Estos objetos están en `motor/modelos.py`; JSON es responsabilidad de app.py.

### Suposiciones explícitas (no reglas adicionales del profesor)

La diapositiva 10 remite los retornos a otro enunciado, pero no se suministró otro.
Los anteriores son decisiones del equipo y pueden requerir adaptación si aparece
un contrato adicional. No se afirma compatibilidad con pruebas oficiales desconocidas.

- Comparación alfabética exacta Unicode, sensible a mayúsculas; los originales
  ya están normalizados. No se inventa normalización dentro de las consultas.
- Prefijo vacío devuelve las primeras abiertas; k<=0 devuelve lista vacía.
  Rangos invertidos devuelven vacío, límites no existentes se insertan lógicamente.
- R1 permite diagnosticar una estación cerrada; se excluye de resultados operativos
  en R2, R3, R4, R6 y extremos/transbordos de R5. Esta distinción resuelve la tensión
  entre R1 y R8. Los recorridos de administración conservan las estaciones cerradas.
- R4 incluye el minuto consultado, conserva duplicados y no salta al día siguiente.
  Admite horas de servicio >=24, minutos 00–59, sin segundos.
- R5 cuenta enlaces: A→B→C son 2 paradas recorridas. Origen=destino abierto: 0.
  Desempate: menos enlaces, menos transbordos, ID ruta1, ID ruta2, nombre del cambio.
  No integra tiempos ni garantiza una conexión horaria. Pasar por cerradas es válido.
- Las rutas exigen estaciones únicas dentro de cada sentido, órdenes enteros únicos
  y referencias válidas. Se rechazan con ValueError los CSV mal formados, estaciones
  duplicadas o patrones circulares. No se ignoran silenciosamente.
- Agregar exige una estación existente y una referencia de la ruta. No crea horarios.
  Quitar desactiva los eventos de esa pareja ruta/estación para R4 y R6; se conservan
  para deshacer o reinsertar. Las otras estaciones conservan sus eventos originales;
  no se recalculan tiempos. Puede quitarse incluso la única parada de una ruta.
- R10 acepta minutos enteros >=0. Buses en 0,f,2f… con capacidad entera positiva.
  Las llegadas en el instante de salida pueden abordar. Desordenadas se ordenan de
  forma estable; empates conservan orden de entrada. Se saltan salidas vacías sin
  iterar minuto a minuto. El total de buses reporta solo las salidas con abordajes.

## R12: decisiones implementadas, alternativas y costos

Variables: S estaciones, R rutas, P paradas totales, L longitud de una ruta,
H eventos totales, h eventos de una pareja ruta/estación, c candidatos inspeccionados,
k resultados pedidos, N pasajeros, C ocupación máxima de la cola, U acciones guardadas.
Hash propio polinomial sobre caracteres con encadenamiento, carga máxima 0,75 y
redimensionamiento al doble. Operación promedio/amortizada O(1) para claves de
longitud acotada; peor caso O(S+R+P) según el índice si colisionan todas las claves.
Para nombres de longitud b, sumar O(b) por cálculo hash. No garantiza resistencia a
entradas adversarias, no es un hash criptográfico.

| Req. | Estructura y algoritmo reales | Alternativa descartada / motivo | Tiempo y memoria adicionales |
|---|---|---|---|
| R1 | Tabla hash de estaciones | Recorrer arreglo: O(S) por consulta frecuente | promedio O(1), peor O(S); índice O(S) |
| R2 | Arreglo alfabético; límite inferior binario y escaneo de prefijo | Trie: más nodos y mantenimiento; aquí el índice comparte R3 | O(log S+c), c incluye cerradas; salida O(k) |
| R3 | Mismo arreglo, límite binario e iteración inclusiva | Recorrer toda la red ignora el límite inferior | O(log S+c); salida O(c) |
| R4 | Hash anidado ruta→estación→arreglo ordenado, lower bound propio | Escaneo de H eventos por consulta | promedio O(log h), peor O(R+L+log h); salida O(1) |
| R5 | Membresías estación→ruta/nodo y exploración dirigida de directos y un cambio | BFS solo por estación pierde el límite de cambios; Dijkstra temporal resuelve otro problema | O(P²) cota conservadora con estaciones únicas por ruta, espacio auxiliar O(P) por tramos |
| R6 | Conteos incrementales y caché ordenada por (-buses,nombre) con mergesort | Reordenar cada consulta desperdicia frecuencia de lecturas | frío O(S log S), caliente O(c), sin cierres O(k); memoria O(S) |
| R7 | Lista doble y hash nombre→nodo por ruta | Arreglo exige desplazar O(L) al insertar | editar O(1) promedio amortizado; peor hash O(S+R+L), recorrido O(L); salida O(L) |
| R8 | Bandera abierta y filtrado en consultas | Eliminar estación perdería referencias para restaurarla | O(1) promedio/amortizado; no reconstruye índices, puede aumentar c en R2/R3/R6 |
| R9 | Dos pilas de comandos inversos compactos | Copiar toda la red por acción consume O(P+H) | aplicar O(1) promedio/amortizado; historial O(U), sin copias de horarios |
| R10 | Cola enlazada FIFO, detector de orden y mergesort estable si hace falta | pop(0) desplaza la lista; simulación minuto a minuto desperdicia huecos | ordenadas O(N), desordenadas O(N log N); espacio O(N+C) |

Carga: O(S log S + suma L log L + suma h log h + H + P), esperada con hashing;
memoria O(S+R+P+H). Todos los ordenamientos son mergesort estable manual, O(n log n)
y O(n) auxiliar. Los horarios repetidos nunca se deduplican.

R7 actualiza enlaces, membresías, conteos de la estación y anula la caché de ranking.
No recorre todos los horarios: usa la longitud del grupo. R8 no modifica conteos.
R9 conserva exactamente el predecesor y estado previo para restaurar el orden;
una edición exitosa vacía rehacer, un error/no-op no lo vacía.
El descarte de la pila de rehacer puede liberar O(U) referencias en Python, de modo
que el costo total se analiza amortizado, no como latencia constante garantizada.

### R11: medir con sentido

En Rendimiento, elegir base 32/64/128/256 y 3–15 repeticiones. n,2n,4n,8n paradas,
n+1 estaciones, una ruta, ocho horarios por parada. Se mide cada operación pública
salvo R5, incluyendo recorrido, ambas ediciones, cierre/reapertura y undo/redo.
Preparación y carga fuera del cronómetro de consultas. Se muestran las muestras,
mediana en microsegundos, carga separada y curva teórica normalizada, no inventada
como una segunda medición. La simulación usa llegadas ordenadas, por eso su curva
es lineal. Hashing se compara con referencia constante, no con su peor caso.
Ranking caliente k=10; al invalidarse hay reconstrucción O(S log S), no se oculta
que ese costo no forma parte de la curva caliente. El dataset mantiene h=8:
esta prueba no demuestra la curva log h de R4 ni todos los peores casos.
Ruido del sistema, cachés y resolución del reloj afectan especialmente consultas
muy pequeñas. Ver las muestras en lugar de exigir cocientes exactos de dos.

## Conversión GTFS

```bash
python -m conversion.gtfs archivo.zip datos_convertidos
```

Salida nueva: tres CSV con cabeceras exigidas; nunca sobrescribe los originales.
Lee stops, routes, trips y stop_times; mayúsculas, sin tildes y espacios compactados.
Ordena stop_sequence numéricamente. Cada combinación de route_id, direction_id y
patrón de paradas recibe ID distinto; no mezcla variantes con el mismo sentido.
Los IDs codifican longitud del original para evitar colisiones por separadores.
Conserva eventos de todos los trips sin filtrar calendar/service_id: no afirma que
todos circulan el mismo día. Segundos truncados, 25:10:30→25:10 (sin módulo 24).
Esto puede producir minutos repetidos, que se conservan.
Rechaza horarios interpolables vacíos, rutas con estaciones repetidas/nombres
colapsados, referencias desconocidas y frequencies.txt sin expansión previa.
No implementa esos casos GTFS opcionales. El ZIP histórico original no se suministró:
la conversión fue probada con ZIP sintético, no con ese archivo real.

## Documentación y colaboración

- [Guía de comprensión](docs/GUIA_PARA_ENTENDER_EL_PROYECTO.md)
- [Guía de modificaciones](docs/GUIA_DE_MODIFICACIONES.md)
- [Presentación extraída con notas](docs/ESPECIFICACION_EXTRAIDA.md)
- [Estado y evidencia](ESTADO_PROYECTO.md)
- [Integrantes por completar](integrantes.md)

No atribuir commits de esta implementación asistida a estudiantes. Completar la
plantilla con aportes reales y revisar cada algoritmo antes de sustentarlo.
