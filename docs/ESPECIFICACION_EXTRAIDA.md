# Presentación del profesor: transcripción de texto y notas

Fuente: `Proyecto final · Planeador TransMilenio.pptx`. Extracción XML; no reemplaza el original. Los números en notas son pies de página.

## Diapositiva 1

### Contenido

ESTRUCTURAS DE DATOS Y ALGORITMOS · PROYECTO DE ÚLTIMO CORTE

Planeador de viajes TransMilenio

Con la red real. Ustedes deciden cómo.

Grupos de 3 o 4 personas

### Notas

Presentar el proyecto en una frase: van a construir un planeador de viajes con los datos reales de TransMilenio, y lo que se evalúa es cómo deciden resolverlo.

1

## Diapositiva 2

### Contenido

EL PROYECTO

Qué van a construir

Una app donde cualquiera busca una estación, planea un viaje y sabe a qué hora pasa su bus, con la red real de TransMilenio.

La app

Web o de escritorio. La eligen ustedes y solo llama al motor.

El motor

Python, escrito por ustedes. Aquí vive toda la lógica y casi toda la nota.

Los datos

La red real de TransMilenio, convertida a tres archivos CSV.

### Notas

Tres piezas. La app es libre y pesa poco. El motor es donde está el curso: ahí van las estructuras y los algoritmos. Los datos salen del GTFS real.

2

## Diapositiva 3

### Contenido

LA REGLA DEL PROYECTO

Les digo qué tiene que hacer. Nunca cómo.

Qué estructura de datos y qué algoritmo usar en cada requisito lo deciden ustedes. Esa decisión es lo que más pesa en la nota.

### Notas

Este es el punto central. Los requisitos describen necesidades de usuarios y operadores, con pistas de volumen y frecuencia, pero ninguno nombra una estructura. Si algo funciona pero no saben defender por qué lo hicieron así, no está aprendido.

3

## Diapositiva 4

### Contenido

REQUISITOS 1 A 3

Consultar estaciones

R1

Buscar una estación

El usuario escribe un nombre exacto y el sistema dice si la estación existe y si está abierta. Es la consulta que más se usa en la app.

R2

Autocompletar

Mientras el usuario escribe «CAL», mostrar hasta k estaciones abiertas que empiezan por ese texto, en orden alfabético.

R3

Listar un rango

Todas las estaciones abiertas entre dos nombres, en orden alfabético. Por ejemplo, de «CALLE 26» a «CALLE 80».

### Notas

Leerlos como un usuario los vería. Fijarse en las pistas: R1 es la consulta más frecuente, y R2 y R3 piden orden. No decir qué estructura usar.

4

## Diapositiva 5

### Contenido

REQUISITOS 4 A 6

Viajar

R4

Próximo bus

Dada una estación, una ruta y una hora, decir a qué hora pasa el siguiente bus de esa ruta. Las troncales pasan cientos de veces al día.

R5

Planear un viaje

Entre dos estaciones, el viaje directo o con un solo transbordo que pase por menos paradas: qué ruta tomar, dónde bajarse y dónde cambiar.

R6

Ranking

Las k estaciones abiertas por donde pasan más buses al día. Se consulta muy seguido y cambia poco: solo cuando se cierra, se reabre o se edita algo.

### Notas

R5 es el más difícil: no hay un algoritmo del curso que lo resuelva tal cual, tienen que combinar lo que saben. Por eso R5 no se mide en rendimiento.

5

## Diapositiva 6

### Contenido

REQUISITOS 7 A 10

Operar la red

R7

 · Editar rutas

Los operadores agregan una parada entre dos existentes o quitan una, todo el tiempo. También ven el recorrido de una ruta en los dos sentidos.

R8

 · Cerrar y reabrir estaciones

Una estación cerrada no aparece en búsquedas, autocompletado, rangos ni ranking, y nadie sube, baja ni transborda ahí.

R9

 · Deshacer y rehacer

Cualquier cierre, reapertura o edición de ruta se deshace y se rehace en el orden correcto. Un cambio nuevo borra lo que había para rehacer.

R10

 · Fila de abordaje

Simular hora pico: los buses salen cada cierto tiempo con cupo limitado y la gente sube en orden de llegada. Son cientos de miles de pasajeros.

### Notas

Estos son los requisitos de operación. R8 y R9 tocan todo lo anterior: cerrar una estación cambia búsquedas, rangos, ranking y viajes, y todo se puede deshacer.

6

## Diapositiva 7

### Contenido

REQUISITOS 11 Y 12

Demostrar que lo entienden

R11

Panel de rendimiento

Una vista de la app que corre cada operación con redes de tamaño creciente y grafica cómo crece el tiempo, junto a la complejidad que ustedes esperaban. Si la medición no coincide, la explicación va ahí mismo.

R12

README de decisiones

Para cada requisito de R1 a R10: qué estructura y qué algoritmo usaron, qué otra opción consideraron y por qué la descartaron, y la O grande de cada operación, diciendo qué es n.

Estos dos son la evidencia de que cada decisión fue de ustedes.

### Notas

Conectar con el Taller 1: el mismo método de duplicar n y mirar qué pasa, ahora con su propio código. Insistir en que digan qué es n en cada operación.

7

## Diapositiva 8

### Contenido

LOS DATOS

De la red real a tres CSV

GTFS de TransMilenio

Julio de 2021. Un zip de unos 54 MB con paradas, rutas, viajes y horarios.

Su script de conversión

Con cualquier librería. Es parte de la entrega.

estaciones.csv

nombre

rutas.csv

ruta, orden, estacion

horarios.csv

ruta, estacion, hora

El motor

Solo lee estos tres archivos.

Nombres en mayúsculas, sin tildes y sin repetidos. Cada ruta va en un solo sentido.

Horas en formato HH:MM. El GTFS trae horas como 25:10: decidan qué hacer y explíquenlo en el README.

Las pruebas del profesor usan otra red con el mismo formato, mucho más grande.

### Notas

La conversión es trabajo de datos, no del curso, y pueden usar IA y pandas para eso. Lo importante: las pruebas corren con una red distinta y más grande, así que nada puede quedar amarrado a sus datos.

8

## Diapositiva 9

### Contenido

REGLAS DEL MOTOR

Qué pueden usar dentro de motor/

Todo lo que resuelve un requisito vive en el paquete motor/, organizado en los archivos que quieran. Una regla del sistema escrita en el front no cuenta.

Prohibido

dict y set

sorted, .sort(), min y max sobre colecciones

x in lista, .index() y .count() para buscar dentro de una lista

bisect, heapq, collections, functools y cualquier librería externa

Permitido

list como arreglo

str y sus métodos

Recorrer con for x in lista

Los módulos csv, time y random

Fuera del motor, en el front y la conversión: cualquier librería

### Notas

La idea de las prohibiciones: que las estructuras las implementen ellos. Si usan algo prohibido, el requisito no recibe puntos de resultados ni de rendimiento aunque pase las pruebas.

9

## Diapositiva 10

### Contenido

CONTRATO DEL MOTOR

Las llamadas que prueba el script

El script hace from motor import Red, simular_fila y llama exactamente esto. Un nombre o una firma distinta cuenta como requisito no hecho.

Red(carpeta)

carga

red.estado(nombre)

R1

red.autocompletar(prefijo, k)

R2

red.rango(desde, hasta)

R3

red.proximo_bus(estacion, ruta, hora)

R4

red.viaje(origen, destino)

R5

red.ranking(k)

R6

red.agregar_parada(ruta, nueva, despues_de)

R7

red.quitar_parada(ruta, estacion)

R7

red.recorrido(ruta, al_reves=False)

R7

red.cerrar(nombre), red.reabrir(nombre)

R8

red.deshacer(), red.rehacer()

R9

simular_fila(llegadas, frecuencia, capacidad)

R10

Qué devuelve cada una, y sus reglas exactas, está en el enunciado.

### Notas

Las firmas fijas son las que permiten calificar a todos los grupos con el mismo script, sin abrir cada app. Mostrar que simular_fila es una función suelta, fuera de la clase Red.

10

## Diapositiva 11

### Contenido

RENDIMIENTO

El script duplica la red y mide

Cada operación, menos R5, tiene que crecer como la mejor opción vista en el curso para ese problema. Cuál es esa opción, lo deciden ustedes.

Red de tamaño n

Corre cada operación y mide.

Red de tamaño 2n

Corre lo mismo y vuelve a medir.

¿Creció como debía?

Si no, pierde los puntos de rendimiento.

Es el mismo método del Taller 1: duplicar n y mirar qué pasa.

### Notas

R5 no se mide porque no hay una opción vista en el curso para compararlo. Recordar el Taller 1: si al duplicar se duplica, es lineal; si se multiplica por 4, es cuadrático. No decir qué esperar de cada requisito.

11

## Diapositiva 12

### Contenido

SOBRE LA IA

Usar IA es lo esperado.

Lo que se evalúa es que cada decisión sea de ustedes. En la sustentación la defienden, aunque la haya propuesto la IA.

### Notas

Decirlo sin rodeos: la IA es una herramienta permitida en todo el proyecto, incluido el cambio sorpresa. Lo que no reemplaza es entender: la sustentación es individual y sobre un requisito que no hicieron.

12

## Diapositiva 13

### Contenido

ENTREGABLES

Un solo link: el repositorio del grupo

El paquete motor/

Con el contrato completo.

El front

Web o de escritorio, el que hayan elegido.

La conversión

El script del GTFS a los tres CSV, y los CSV ya generados.

README.md

Las decisiones (R12) y el comando único para arrancar la app.

integrantes.md

Los nombres y qué requisitos hizo cada uno.

Git desde la primera semana

El historial cuenta: tienen que verse commits de todos los integrantes a lo largo del proyecto, no un solo commit al final.

### Notas

GitLab o GitHub, con acceso para el profesor. integrantes.md importa: de ahí sale sobre qué requisito sustenta cada persona.

13

## Diapositiva 14

### Contenido

EL DÍA DE LA ENTREGA

Una sola sesión, en clase

45 min

Cambio sorpresa

Todos los grupos a la vez. Cada grupo recibe un requisito nuevo y lo agrega a su motor, con las mismas herramientas del proyecto, IA incluida. El script lo verifica al terminar.

10 min

Sustentación individual

Por persona. Cada uno responde sobre un requisito que no hizo, según integrantes.md, y hace un cambio en vivo sobre el código. La nota es individual.

Un motor que entienden recibe el requisito nuevo en minutos. Uno que no entienden, no alcanza.

### Notas

El cambio sorpresa no se anuncia antes. La sustentación sobre un requisito que no hicieron obliga a que el grupo se explique el código entre ellos.

14

## Diapositiva 15

### Contenido

RÚBRICA

100 puntos: 75 del grupo, 25 individuales

Criterio

Cómo se mide

Puntos

Resultados del motor

R1 a R10 correctos con una red que no conocen, bordes incluidos

20

Rendimiento

Al duplicar la red, cada operación menos R5 crece como debe

10

Decisiones y panel

R11 y R12: decisiones justificadas y mediciones coherentes

20

Cambio sorpresa

Lo verifica el script al terminar los 45 minutos

15

App y datos

Arranca con un comando y la conversión del GTFS funciona

5

Historial de Git

Commits de todos a lo largo del proyecto

5

Sustentación

Individual, sobre un requisito que no hizo

25

Un requisito que pasa las pruebas usando algo prohibido dentro de motor/ no recibe puntos de resultados ni de rendimiento.

### Notas

Lo grupal suma 75 y la sustentación 25. Las decisiones pesan lo mismo que los resultados: un motor que funciona pero no se sabe defender no saca la nota completa.

15

## Diapositiva 16

### Contenido

GRUPOS Y FECHAS

Grupos de 3 o 4 personas

No se aceptan grupos de 2 ni de 5.

Publicación del enunciado

[fecha]

Entrega del link del repositorio

[fecha]

Cambio sorpresa y sustentaciones, en clase

[fecha]

¿Preguntas?

### Notas

Llenar las fechas antes de presentar. Recordar que el repositorio se crea desde la primera semana.

16
