# Rendimiento medido (R11)

Generado el 2026-11-03 14:07:34 con `python herramientas/medir.py 4000 5` en Windows / Python 3.13.7 (AMD64 Family 23 Model 96 Stepping 1, AuthenticAMD).
Mediana de las repeticiones; cada repetición cronometra un lote de llamadas. Razón = t(2n)/t(n) observada (esperada).

| Req. | Operación | Esperada | n=250 | n=500 | n=1000 | n=2000 | n=4000 | Razones | Veredicto |
|---|---|---|---|---|---|---|---|---|---|
| Carga | carga | O(N log N) | 108.3 ms | 269.6 ms | 413.6 ms | 835.1 ms | 1,890.3 ms | 2.49 (2.14), 1.53 (2.14), 2.02 (2.13), 2.26 (2.13) | coincide |
| R1 | estado | O(1) | 2.3 µs | 2.5 µs | 2.5 µs | 2.2 µs | 2.5 µs | 1.06 (1.00), 1.00 (1.00), 0.90 (1.00), 1.13 (1.00) | coincide |
| R2 | autocompletar | O(log n + k) | 24.6 µs | 23.9 µs | 24.1 µs | 24.5 µs | 24.6 µs | 0.97 (1.13), 1.01 (1.11), 1.01 (1.10), 1.00 (1.09) | coincide |
| R3 | rango | O(log n + m) | 47.6 µs | 48.6 µs | 46.2 µs | 49.6 µs | 48.9 µs | 1.02 (1.13), 0.95 (1.11), 1.07 (1.10), 0.99 (1.09) | coincide |
| R4 | proximo_bus | O(log m) | 15.3 µs | 20.8 µs | 16.0 µs | 16.7 µs | 16.2 µs | 1.36 (1.13), 0.77 (1.11), 1.04 (1.10), 0.97 (1.09) | coincide |
| R5 | viaje | no se evalúa | 24.6 µs | 38.6 µs | 30.8 µs | 26.4 µs | 26.7 µs | 1.57, 0.80, 0.86, 1.01 | sin referencia |
| R6 | ranking | O(k) | 1.0 µs | 1.1 µs | 1.1 µs | 1.1 µs | 1.1 µs | 1.16 (1.00), 0.97 (1.00), 0.98 (1.00), 1.01 (1.00) | coincide |
| R6 | ranking_tras_cambio | O(n log n) | 820.4 µs | 1,766.3 µs | 3,715.2 µs | 7,925.5 µs | 16.0 ms | 2.15 (2.25), 2.10 (2.22), 2.13 (2.20), 2.02 (2.18) | coincide |
| R7 | editar | O(1) | 31.5 µs | 38.6 µs | 32.0 µs | 34.7 µs | 31.0 µs | 1.22 (1.00), 0.83 (1.00), 1.09 (1.00), 0.89 (1.00) | coincide |
| R7 | recorrido | O(L) | 1.8 µs | 2.2 µs | 1.8 µs | 2.1 µs | 1.9 µs | 1.20 (1.00), 0.82 (1.00), 1.17 (1.00), 0.90 (1.00) | coincide |
| R8 | cerrar | O(1) | 5.2 µs | 5.9 µs | 6.3 µs | 5.7 µs | 5.5 µs | 1.13 (1.00), 1.08 (1.00), 0.90 (1.00), 0.97 (1.00) | coincide |
| R9 | deshacer | O(1) | 5.1 µs | 5.4 µs | 5.4 µs | 5.1 µs | 5.2 µs | 1.05 (1.00), 1.01 (1.00), 0.95 (1.00), 1.02 (1.00) | coincide |
| R10 | fila | O(p log p) | 25.5 ms | 58.2 ms | 130.8 ms | 311.3 ms | 729.9 ms | 2.28 (2.15), 2.25 (2.14), 2.38 (2.13), 2.34 (2.12) | coincide |

Para la carga, n es el número de filas leídas (N), no de estaciones; para R10, p = 40·n pasajeros. R5 no se evalúa en rendimiento según el enunciado.
