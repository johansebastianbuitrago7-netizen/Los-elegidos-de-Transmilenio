# Horarios con contexto

## Qué estás consultando

Cada fila de horarios.csv es un evento programado de una ruta en una estación.
Los datos de la presentación corresponden a julio de 2021: no son GPS, tráfico,
predicciones ni disponibilidad de buses actuales. La cabecera no distingue llegada
ni salida. Por eso la interfaz dice **registro**, incluso en una terminal.

## Flujo que funciona en la V2

1. Escribe una estación y confirma la selección con Tab o cambiando de campo.
2. La API consulta sus membresías y ofrece solo rutas que pasan por ella.
3. Cada opción muestra ID y extremos **reales del recorrido ordenado**. Un sufijo
   numérico no determina dirección. Abre «Ver recorrido» si los extremos no bastan.
4. Introduce HH:MM y pulsa «Consultar horarios».
5. Lee hora consultada, próximo registro, diferencia, próximos cinco eventos y escala.

Una estación cerrada no ofrece servicios. Tras editar rutas se usan los índices
actualizados en memoria. Una parada recién agregada puede tener ruta pero ningún
horario: no se crean eventos para completar la visualización.

## La búsqueda binaria

El motor ya tiene un hash ruta→estación→arreglo de minutos ordenado. La consulta
busca el primer minuto **mayor o igual** a la hora pedida. En cada paso compara el
punto medio y elimina la mitad del intervalo. Así cuesta O(log h), h horarios de
esa pareja (con el costo promedio de hashing). Leer después cinco registros cuesta
O(5). El retorno público de proximo_bus no cambió.

Si consultas exactamente un minuto registrado, ese mismo minuto es la respuesta.
Si hay dos filas iguales, ambas permanecen en la lista siguiente; no sabemos que
sean un error ni tenemos identidad de vehículo para deduplicarlas.

## Regresión comprobada directamente contra el CSV

B10-1, sentido **PORTAL 80 → PORTAL NORTE**, consultando en PORTAL NORTE:

| Consulta | Próximo registro |
|---|---|
| 08:00 | 08:18 |
| 08:18 | 08:18 |
| 09:25 | 11:33 |
| 11:33 | 11:33 |
| 11:34 | 11:41 |

09:25 equivale al minuto 565; 11:33 al 693: diferencia 128 minutos, o 2 h 08 min.
Los cinco registros desde 09:25 son 11:33, 11:41, 11:49, 11:57, 12:06.
Eso significa que **el archivo no tiene un evento intermedio de esa pareja**, no
que el TransMilenio actual obligue a esperar dos horas. No se interpolan eventos.

## Hora del día y hora de servicio

25:10 se representa como 1510 minutos desde cero en el servicio. Puede indicar
continuación después de medianoche, pero no se convierte silenciosamente a 01:10
ni se inventa un calendario. Después del último registro se devuelve una lista
vacía, sin reiniciar el día siguiente.

## Interpretar la línea temporal

Las posiciones de los puntos son proporcionales a los minutos desde la consulta
hasta el último registro mostrado. Un hueco de dos horas ocupa más espacio que
uno de ocho minutos. Cada punto tiene información al enfocarlo o pasar el cursor.
La lista inferior contiene todas las horas e intervalos aunque varios puntos se
superpongan. La escala no representa trayectos, geografía ni tiempos de circulación.

## Arquitectura y modificaciones

- Motor: rutas_estacion y siguientes_horarios reutilizan índices y lower bound.
- GET `/api/estacion/rutas?estacion=...`: estado y catálogo dirigido.
- GET `/api/ruta?ruta=...`: extremos y estaciones en orden; permite selección inversa
  (estaciones por ruta) a integraciones futuras, sin agrupar sentidos.
- GET `/api/horarios?estacion=...&ruta=...&hora=...`: `resultado` con eventos y diferencia,
  `presentacion` con metadatos. Nunca devuelve el CSV completo.
- UI: static/js/horarios.js; el cálculo definitivo de diferencia está en Python.

Las pruebas nuevas cubren igualdad, posteriores, vacío, duplicados, horas >24,
cierres, ediciones, rutas inválidas, dirección y las cinco regresiones reales.
