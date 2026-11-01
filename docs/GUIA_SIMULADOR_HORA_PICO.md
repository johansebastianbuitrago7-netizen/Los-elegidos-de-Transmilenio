# Laboratorio de hora pico

## Un modelo académico, no una operación real

Llegadas es una lista de minutos enteros desde cero, uno por persona. Frecuencia f
significa un bus en 0,f,2f…; capacidad c es el número de cupos por bus. Todos los
pasajeros terminarán siendo atendidos. No se modelan viajes de buses, costos,
abandono, GPS, demanda observada de Bogotá ni restricciones de estaciones reales.

Los dos modos llaman a **la misma función pública simular_fila**. Su retorno no se
modificó. La V2 deriva métricas en motor/analisis_fila.py y estados visuales en
servicios/laboratorio.py. No hay otro algoritmo FIFO en JavaScript.

## Modo 01: aprende con una fila

Por defecto: llegadas [0,0,1,2,5,5,9], frecuencia 5 min, capacidad 3.

| Persona | Llegada | Abordaje | Espera |
|---|---:|---:|---:|
| P1 | 0 | 0 | 0 |
| P2 | 0 | 0 | 0 |
| P3 | 1 | 5 | 4 |
| P4 | 2 | 5 | 3 |
| P5 | 5 | 5 | 0 |
| P6 | 5 | 10 | 5 |
| P7 | 9 | 10 | 1 |

Minuto 0: P1/P2 abordan, queda un cupo. Minuto 1: P3 entra. Minuto 2: P4 entra.
Minuto 5: antes del bus se incorporan P5/P6: FRENTE→P3→P4→P5→P6←FINAL.
Abordan P3/P4/P5; P6 queda esperando. Minuto 9: P7 va detrás de P6. Minuto 10:
ambos abordan y la fila termina vacía.

Resultados: espera total 13, media 13/7≈1,86 min, mediana 1, máxima 5, P95 5,
tres buses con pasajeros, ocupación media 7/(3×3)=77,78%, máxima fila 4 personas
justo antes de abordar y último abordaje en minuto 10.

Los pasos distinguen llegada, bus, abordaje y salida. Llegar exactamente con el bus
permite abordar; los empates usan el orden de entrada. En desorden, el motor ordena
establemente por minuto e índice de pasajero, devolviendo arreglos en el orden original.

### Controles

Anterior/Siguiente navegan eventos calculados, sin cambiar el motor ni llamar a
red.deshacer. Reproducir avanza con un reloj visual; Pausar lo detiene, Reiniciar
vuelve al estado inicial; Velocidad cambia solo el intervalo visual. Salir de la
sección cancela reproducción. Los resultados finales permanecen iguales.
La escena y los controles tienen etiquetas además de colores; el foco de controles
se conserva al cambiar de paso. No hay movimiento automático al abrir la página.

### Cola enlazada real

ENQUEUE agrega al FINAL. DEQUEUE saca del FRENTE. La implementación mantiene ambos
extremos para hacer cada operación en O(1). pop(0) en un arreglo tendría que desplazar
los elementos. Esta diferencia importa con cientos de miles de pasajeros.

## Modo 02: experimenta y compara

Presets editables: baja (60 personas/60 min), media (300/60), intensa (1500/60).
Baja y media distribuyen uniformemente minutos enteros del periodo [0,duración).
Intensa concentra llegadas en el centro promediando dos uniformes: distribución
triangular discreta. Son escenarios **sintéticos**. El nombre no garantiza una cola
concreta: la congestión depende también de frecuencia y cupos que el usuario elija.

La semilla predeterminada 42 permite repetir. Se genera una lista una sola vez y
se entrega esa misma lista a A y B; la respuesta incluye su huella SHA-256 y veinte
llegadas de muestra. No se generan dos demandas aleatorias independientes.

Se permiten hasta 300.000 personas, periodos de 1–1440 min, frecuencias 1–1440 min
y capacidades 1–10.000. Es un límite de la capa web, no del contrato del motor.
El modo animado admite 40 personas. La vista masiva no recibe arreglos completos
de esperas/abordajes, ni crea un elemento por pasajero.

## Métricas: definiciones exactas

- Pasajeros: cantidad de entradas; abordados: misma cantidad al terminar el modelo.
- Espera individual: minuto de abordaje − minuto de llegada.
- Media: suma de esperas/N; mediana: valor central o promedio de los dos centrales.
- P95: método de rango más próximo, índice ceil(0,95N)-1 en esperas ordenadas.
- Buses: solo horarios con al menos un abordaje, igual que el retorno público V1.
- Ocupación media: N/(buses utilizados × capacidad), no media incluyendo vacíos.
- Máxima cola: mayor cantidad que ya llegó y aún no ha abordado, **incluyendo las
  llegadas del mismo minuto antes de procesar el bus**.
- Último abordaje: máximo minuto de abordaje contado desde cero (no desde la primera llegada).
- Lista vacía: todas las métricas se definen como cero, sin porcentajes A=0.

El comparador muestra B−A y (B−A)/A×100. Si A es cero, el porcentaje relativo se
marca no definido; no se divide entre cero ni se inventa una mejora porcentual.
Menor espera no equivale a menor costo: el modelo no contiene costos operativos.

## Las cuatro gráficas

1. **Fila**: la línea escalonada roja indica personas restantes después del evento,
   hasta el siguiente. Los puntos petróleo indican el máximo instantáneo antes del
   abordaje, sin mantenerlo como si fuera una espera sostenida.
2. **Ocupación**: una barra por bus mostrado; relleno=ocupados, trama=libres. Incluye
   tabla con minutos y conteos; no muestra salidas vacías como buses utilizados.
3. **Histograma**: hasta veinte intervalos inclusivos de espera, usando a todos los
   pasajeros; cada barra dice cuántos tienen una espera en ese intervalo.
4. **Llegadas/cupos**: bloques [t,t+f), cupos de un bus en t y llegadas durante el bloque.
   Solo bloques con demanda. No significa que llegadas posteriores a t puedan usar
   el bus de t; permite comparar volúmenes, no decidir abordajes.

Las series grandes se muestrean por bloques con un máximo aproximado de 162 filas.
Para fila se preservan máximos locales previos y extremos; las métricas exactas se
calculan **antes** de reducir. Las líneas reducidas no muestran cada variación.
La ocupación y demanda muestran una muestra, no sumas del total. El histograma no
se muestrea. El resumen descargable contiene métricas y las series mostradas, no
un CSV individual de todos los pasajeros. Los detalles textuales son alternativa
a puntos estrechos en pantallas táctiles.

## Complejidad y separación de responsabilidades

Simular_fila conserva O(N) si las llegadas están ordenadas y O(N log N) si debe
ordenarlas; salida y eventos O(N). El análisis adicional usa mergesort propio para
percentiles y tiempos distintos: O(N log N) esperado con hashing y O(N) memoria.
No se incluye este análisis extra en el benchmark de la función pública R10.
Los pasos educativos filtran pasajeros por evento (hasta 40), O(N²) acotado en la
capa de presentación; jamás se ejecuta esta expansión para escenarios grandes.

Servicios genera escenarios y serializa; motor calcula asignaciones y métricas;
JavaScript representa los estados del servidor y maneja el reloj de reproducción.
Para cambiar la semántica, empezar por pruebas del motor, no por la animación.
