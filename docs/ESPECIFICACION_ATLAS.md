# Especificación de Atlas

Fuente: `docs/Proyecto final · Planeador TransMilenio.pptx` (16 diapositivas, leídas con sus
notas del orador). Cuando este documento y la presentación difieren, manda la presentación.

## 1. Requisitos explícitos del profesor

**Proyecto** (diap. 2–3, 13): app web o de escritorio que solo llama al motor; motor en Python
con "toda la lógica y casi toda la nota"; datos = red real convertida a tres CSV. Qué estructura
y algoritmo usar lo decide el grupo y "es lo que más pesa".

**Requisitos** (diap. 4–7):

| | Enunciado (resumido) |
|---|---|
| R1 | Nombre exacto → ¿existe? ¿está abierta? Es la consulta más usada. |
| R2 | Hasta k estaciones **abiertas** que empiezan por el texto, en orden alfabético. |
| R3 | Todas las **abiertas** entre dos nombres, en orden alfabético (ej. CALLE 26 a CALLE 80). |
| R4 | Estación + ruta + hora → hora del siguiente bus. Las troncales pasan cientos de veces al día. |
| R5 | Viaje directo o con **un solo transbordo** que pase por **menos paradas**: qué ruta, dónde bajarse, dónde cambiar. |
| R6 | Las k estaciones **abiertas** con más buses al día. Se consulta seguido, cambia solo al cerrar/reabrir/editar. |
| R7 | Agregar una parada entre dos existentes o quitar una; ver el recorrido en los dos sentidos. |
| R8 | Una cerrada no aparece en búsquedas, autocompletado, rangos ni ranking; nadie sube, baja ni transborda ahí. |
| R9 | Cierres, reaperturas y ediciones se deshacen/rehacen en orden; un cambio nuevo borra lo de rehacer. |
| R10 | Buses cada cierto tiempo con cupo limitado; la gente sube en orden de llegada; cientos de miles de pasajeros. |
| R11 | Vista que corre cada operación con redes crecientes, grafica el tiempo junto a la complejidad esperada y explica si no coincide. |
| R12 | README con, para R1–R10: estructura y algoritmo, alternativa considerada y por qué se descartó, O grande diciendo qué es n. |

**Datos** (diap. 8): `estaciones.csv(nombre)`, `rutas.csv(ruta, orden, estacion)`,
`horarios.csv(ruta, estacion, hora)`. Nombres en mayúsculas, sin tildes, sin repetidos; cada ruta
va en un solo sentido; horas HH:MM; el GTFS trae horas como 25:10 y hay que decidir y explicar.
El script de conversión es entregable. **Las pruebas usan otra red, mucho más grande.**

**Reglas del motor** (diap. 9): prohibidos `dict`, `set`, `sorted`, `.sort()`, `min`/`max` sobre
colecciones, `x in lista`, `.index()`, `.count()`, `bisect`, `heapq`, `collections`,
`functools` y librerías externas. Permitidos `list` como arreglo, `str` y sus métodos, `for x in
lista`, `csv`, `time`, `random`. Una regla escrita en el front no cuenta.

**Contrato** (diap. 10): `from motor import Red, simular_fila` con las firmas exactas; un nombre
o firma distinta cuenta como requisito no hecho. `simular_fila` es función suelta.

**Rendimiento** (diap. 11): el script duplica la red y mide; cada operación **menos R5** debe
crecer como la mejor opción vista en el curso.

**Entregables y evaluación** (diap. 13–15): repo con motor, front, conversión + CSV, README
(decisiones y comando único), `integrantes.md`, historial de Git con commits de todos. Cambio
sorpresa de 45 min y sustentación individual sobre un requisito que no hizo. Usar algo prohibido
anula puntos de resultados y rendimiento de ese requisito.

## 2. Ambigüedades y decisiones propias

| Tema | Decisión de Atlas | Por qué |
|---|---|---|
| Retornos de cada llamada | Ver tabla en el README | El enunciado los remite a un documento que no está en el repo. |
| `estado` de un nombre inexistente | `"inexistente"` | Texto explícito, distinto de cerrada. |
| Normalizar entrada en el motor | No (nombre exacto) | R1 dice "nombre exacto". La app sí normaliza (mayúsculas, sin tildes). |
| Horas ≥ 24 | Se pliegan (25:10 → 01:10) | Pertenecen a la madrugada del mismo día de servicio. |
| R4 sin más registros ese día | `None` | No inventamos el servicio del día siguiente. |
| Filas de horario duplicadas | Se conservan | El CSV tiene 1.580 duplicados exactos; pueden ser viajes distintos a la misma hora. |
| Qué es "paradas" en R5 | Enlaces recorridos | Diferencia de posiciones en la ruta. |
| Estación cerrada en medio de un tramo | El bus pasa sin detenerse | R8 prohíbe subir, bajar o transbordar, no atravesar. |
| Empates en R5 | Menos paradas → directo → orden alfabético (ruta1, transbordo, ruta2) | Determinista y explicable. |
| Origen = destino | `[]` | Viaje vacío de 0 paradas. |
| "Buses al día" (R6) | Filas de horarios de las rutas que hoy paran en la estación | Es lo que registra el CSV; una parada nueva sin horarios aporta 0. |
| Empates en R6 | Alfabético | Merge sort estable sobre entrada alfabética. |
| `agregar_parada` con estación nueva | Debe existir en `estaciones.csv` | "Entre dos existentes"; evitamos crear estaciones sin nombre normalizado. |
| `despues_de=None` | Inserta al inicio | Permite agregar antes de la primera. |
| Recorrido incluye cerradas | Sí (la app las marca) | Es la definición de la ruta; cerrar no la destruye. |
| Operaciones sin efecto | Devuelven `False` y no entran al historial | Deshacer debe revertir cambios reales. |
| `simular_fila` | Devuelve abordajes alineados con la entrada | Las esperas se derivan (abordaje − llegada). |
| Llegadas desordenadas | Merge sort estable y resultado en el orden original | Empates conservan el orden de la lista. |
| Llegadas negativas | Abordan el bus del minuto 0 | Los buses empiezan en 0. |

## 3. Mejoras propuestas (no exigidas)

Laboratorio educativo paso a paso con pseudocódigo, escenarios masivos sintéticos (hasta 300.000
personas) con percentiles y gráficas agregadas, comparador A/B con las mismas llegadas, horarios
con cronología del día y explicación de intervalos largos, diagrama de itinerario, ficha de
estación, visualización de las pilas de deshacer/rehacer, modo oscuro y diseño adaptable.

## 4. Inspección de los CSV originales

Recalculado con `csv` estándar (no codificado en el motor):

| Archivo | Filas | Observaciones |
|---|---|---|
| `estaciones.csv` | 147 | Únicas, ya en orden alfabético, todas usadas por alguna ruta. |
| `rutas.csv` | 1.927 | 181 rutas; orden consecutivo desde 1; ninguna repite estación; largo 3–33; todas las estaciones existen. |
| `horarios.csv` | 140.492 | Todas las parejas (ruta, estación) existen en rutas; 1.580 filas duplicadas exactas; 447 de 1.927 grupos no vienen ordenados; horas 00–23 (71 en la hora 00, ya plegadas); ninguna ≥ 24. |

Estación con más registros: RICAURTE (4.446). Caso de control: `B10-1` (PORTAL 80 → PORTAL NORTE)
en PORTAL NORTE a las 09:25 → próximo 11:33 (128 min; el anterior es 08:18).

Los datos son un conjunto histórico/programado de 2021 y no reflejan la operación actual.
