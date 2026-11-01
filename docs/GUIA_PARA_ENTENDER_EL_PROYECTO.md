# Guía para entender y sustentar el proyecto

## 1. Un recorrido por las tres capas

Imagina la aplicación como una biblioteca: los CSV son los libros, el motor es el
bibliotecario que construye sus catálogos y la web es el mostrador. El mostrador
no debe adivinar una respuesta. Por eso todos los requisitos R1–R10 están en motor/,
y se pueden ejecutar sin Flask. Prueba en una consola:

```python
from motor import Red
red = Red('datos')
print(red.estado('UNIVERSIDADES'))
print(red.viaje('UNIVERSIDADES', 'EL TIEMPO - MALOKA').estaciones)
```

Los nombres del ejemplo son datos reales, no reglas del algoritmo.
En `Red.__init__`, csv.reader entrega arreglos. Primero se crean estaciones; después
se ordenan las paradas por el orden numérico y se enlazan las rutas; finalmente se
agrupan los horarios y se ordena cada grupo. No se confía en el orden de los archivos.
La carga puede costar más que una consulta: ese trabajo se reutiliza miles de veces.

`app.py` convierte JSON en argumentos, valida los tipos, llama al motor y serializa
los resultados. JavaScript usa fetch y dibuja resultados. Si hay un error de viaje,
no se corrige en JavaScript: se reproduce en una red pequeña en tests/.

## 2. Mapa de módulos

- `estructuras.py`: TablaHash, Nodo, ListaDoble, Pila, Cola, mergesort y límite inferior.
- `modelos.py`: datos de estación, resultados y conversión HH:MM↔minutos.
- `red.py`: carga, consultas, edición e historial de la red.
- `simulacion.py`: pasajeros independientes de una red concreta.
- `herramientas/restricciones.py`: auditoría sintáctica conservadora del motor.
- `herramientas/rendimiento.py`: crea CSV temporales, mide operaciones y devuelve muestras.
- `conversion/gtfs.py`: procesa un ZIP sin depender del motor.

Estas dependencias van en una dirección. Los modelos y las estructuras no importan
la aplicación. Así un cambio de interfaz no obliga a reescribir algoritmos.

## 3. Por qué no usar una sola lista

Una lista sirve para recorrer elementos pero buscar un nombre exacto cuesta O(S).
La tabla hash calcula un número desde los caracteres y elige una cubeta. Si dos
nombres chocan, se revisa la lista pequeña de esa cubeta. Al superar 75% de carga,
se duplica el arreglo y se redistribuyen las claves. Se paga ocasionalmente O(S),
pero el costo promedio/amortizado de una serie de inserciones es O(1) por clave
acotada. En el peor caso todas colisionan y la búsqueda es O(S).
No confundir promedio con garantía para cualquier entrada hostil.

Un hash no conserva orden alfabético. Por eso R2/R3 comparten otro índice: un arreglo
ordenado con mergesort propio. La búsqueda binaria descarta la mitad del intervalo
cada vez hasta encontrar el primer nombre >= límite. Después se inspecciona solo
el rango relevante. Las cerradas permanecen en el índice pero se filtran: si hay
muchas cerradas, puede revisarse más de k candidatos. Esa es una decisión consciente
para que cerrar y reabrir sean baratos.

Ejemplo: nombres A, B, D, F. Límite inferior de C es la posición de D. No necesita
existir una estación llamada C. Un rango C–F devuelve D,F si están abiertas.

## 4. R4 y R6: eventos, no buses identificados

La clave de un horario es ruta más estación, mediante dos hashes anidados. Cada
pareja contiene un arreglo de minutos. Para [540,540,600], consultar 09:00 encuentra
540, consultar 09:01 encuentra 600. No se borran los dos 540: no hay identificador
de bus para decidir que sean un error. Pasar a minutos permite comparar 25:10
sin convertirlo erróneamente en 01:10.

El ranking cuenta filas de horarios de parejas activas, no rutas ni vehículos
identificados. Los conteos se mantienen por estación. La primera consulta ordena
por (-conteo,nombre); luego reutiliza la caché. Cerrar no cambia el conteo, solo
filtra. Quitar/agregar paradas ajusta el conteo y anula el orden en caché.
Recalcular todo H en cada consulta sería más simple pero desperdiciaría el patrón
de muchas lecturas y pocas ediciones. Un heap no aporta aquí una salida completa
estable y también está prohibido usar heapq.

## 5. R5 explicado paso a paso

Red de ejemplo: R=A→B→C y S=B→D→E. Para ir de A a E:

1. Buscar A y E en el hash; deben estar abiertas.
2. A conoce las rutas en las que tiene un nodo, aquí R.
3. Desde el nodo A, seguir los enlaces **siguientes** de R, nunca los anteriores.
4. En B, que está abierta, revisar las otras rutas que pasan por B, aquí S.
5. Desde el nodo B de S avanzar hacia E: el candidato es A,B,D,E, tres enlaces.
6. Comparar con todos los demás candidatos, incluidos los directos.

El algoritmo no se detiene en el primer transbordo que encuentra. Dos rutas que
comparten una estación no garantizan que el destino quede después de ella. Por
eso se recorre cada segundo tramo hacia adelante hasta destino o fin de ruta.
B cerrada impediría el cambio, pero A→C por R sigue siendo posible: atravesarla no
es abordar ni descender. Si origen=destino abierto, el resultado tiene cero enlaces.

### Argumento de corrección

Todo viaje permitido tiene una ruta inicial que contiene origen. El bucle externo
la examina. Si es directo, encontrará destino avanzando. Si tiene un cambio, ese
cambio es una estación posterior abierta de la primera ruta; el recorrido la visita
y examina su ruta final. Si destino está después del cambio, se registra ese
candidato. No hay un tercer tramo. Por tanto se enumeran todos los itinerarios
permitidos por el modelo. Escoger el menor número de enlaces da el óptimo. El
desempate adicional solo elige entre óptimos y hace reproducible el resultado.

La cota conservadora O(P²) es admisible aquí: R5 está excluido de la comparación
académica de rendimiento. Su corrección importa más que complicarlo con estados
temporales inexistentes en los datos. El test de referencia usa otro enfoque:
0-1 BFS con estado (ruta,posición,cambios), transición de parada costo 1 y cambio
costo 0. Contrasta 12 redes pequeñas reproducibles, 49 pares por red.

## 6. R7–R9: consistencia e inversas

Una lista doble permite enlazar una parada entre dos nodos en O(1) una vez localizado
el predecesor. Un hash por ruta evita recorrer L para localizarlo. Hay además una
membresía por estación con el nodo de cada ruta. R5 usa esa misma membresía.
Quitar actualiza los vecinos, los extremos, el índice de la ruta y las membresías.
El listado inverso comienza en ultimo y sigue anterior; no cambia el sentido real.

Los comandos de historial son tuplas pequeñas:
- estado: nombre, estado anterior, estado nuevo;
- insertar/quitar: ruta, estación, nombre del predecesor (None para el extremo).

Una pila representa acciones aplicadas, la otra acciones deshechas. Deshacer saca
la última de atrás, ejecuta su inversa sin volver a registrarla, y la apila adelante.
Rehacer hace lo contrario. Un cambio nuevo borra adelante. Un error o cerrar una
estación ya cerrada no genera acción. La estructura LIFO preserva predecesores:
antes de deshacer una edición antigua se deshacen las más recientes que la afectan.

No se copian 140.492 eventos por cada cierre. Los eventos desactivados se conservan
y se reactivan al restaurar la pareja. Ninguna edición escribe los CSV originales.
Prueba el siguiente ejercicio: quitar primera parada, agregar otra, cerrar, deshacer
3 veces y rehacer 3. Inspecciona recorrido, estado y ranking en cada paso.

## 7. La fila FIFO

FIFO significa que entra primero quien llegó primero. La cola tiene cabeza y cola:
poner al final y sacar de la cabeza modifican un número constante de enlaces. Con
pop(0) cada salida desplazaría las personas restantes y podría volverse cuadrática.

Llegadas [0,0,1,5], frecuencia=5, capacidad=2: el bus 0 lleva los dos primeros; el bus
5 lleva al tercero y cuarto. Esperas [0,0,4,0]. Con llegadas desordenadas, un mergesort
estable ordena por minuto e índice original; los retornos vuelven al orden de entrada.
Si el próximo pasajero llega al minuto mil millones, se calcula la próxima salida
con división entera: no se simula cada minuto vacío.

N pasajeros ordenados cuestan O(N), desordenados O(N log N). Los resultados y eventos
usan O(N), la cola hasta O(C), C pasajeros simultáneamente pendientes.

## 8. Rendimiento: qué demuestra y qué no

Un cronómetro mide observaciones, no prueba O grande. El panel muestra mediana y
todas las muestras de operaciones reales, con carga separada. Los nombres sintéticos
son E00000000, E00000001…: evita errores como nombres duplicados al multiplicar una
red. Cada experimento usa un directorio temporal, no la red que consulta el usuario.
El gráfico deja seleccionar la operación y explorar puntos con ratón/teclado.

La red de prueba tiene ocho horarios por parada: R4 mantiene h fijo. Para investigar
log h, cambiar el generador y variar h dejando S fijo. Ranking muestra el caso caliente;
para estudiar reconstrucción, invalidar antes y medir aparte. No convertir ruido de
microsegundos en una promesa de rendimiento en otros equipos.

## 9. Extender sin romper

Para una nueva consulta, definir su contrato y un ejemplo pequeño primero. Reutilizar
los índices disponibles antes de crear otro. Si se crea uno, describir qué operaciones
lo invalidan y comprobar undo/redo. Añadir el adaptador Flask y después una vista;
no poner búsquedas ni cálculos del dominio en JavaScript. Ver guía de modificaciones.

## 10. Errores frecuentes y diagnóstico

- CSV desconocido: comprobar cabeceras exactas, nombres referenciados y UTF-8.
- Resultado en sentido imposible: revisar enlaces siguientes y no usar recorrido inverso.
- Ranking incorrecto después de edición: revisar conteo activo y anulación de caché.
- Undo cambia horarios: el historial no debe generar horarios nuevos.
- Misma ruta aparece con dos patrones GTFS: deben tener IDs distintos por patrón dirigido.
- API funciona pero la web no: inspeccionar consola, estado HTTP y serialización.
- Página vacía: arrancar desde Python correcto y verificar /api/red antes de CSS.

## 11. Preguntas de práctica (no preguntas atribuidas al profesor)

1. ¿Por qué dos índices para estaciones? Hash resuelve igualdad; arreglo resuelve orden.
2. ¿Cómo puede fallar O(1)? Colisiones y redimensionamientos; distinguir peor y amortizado.
3. ¿Por qué no eliminar cerradas? Se perderían referencias, historial y horarios reutilizables.
4. ¿Qué cambia al quitar B de A→B→C? El enlace pasa A→C; se desactivan eventos de B en
   esa ruta, sin modificar eventos históricos de A/C. Esa política está documentada.
5. ¿Por qué compartir estación no basta? El destino debe quedar después en el sentido elegido.
6. ¿Qué significa 25:10? Minuto 1510 del mismo servicio, no el día siguiente inferido.
7. ¿Cómo probar FIFO? Comparar orden de llegadas y asignación de cupos, incluidos empates.
8. ¿Por qué una mediana baja no prueba optimalidad? Depende de entradas, escala y sistema.

Ejercicios: dibujar una colisión, seguir un mergesort de ocho nombres, agregar un
caso de empate R5, probar undo tras borrar el primer nodo y explicar la caché de
ranking con cierres. Cada integrante debe resolver ejemplos de requisitos ajenos.
