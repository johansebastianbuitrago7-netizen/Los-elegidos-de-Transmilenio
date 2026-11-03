"""R10: simulación de la fila de abordaje en hora pico."""

from .algoritmos import indices_ordenados
from .estructuras import Cola


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def simular_fila(llegadas, frecuencia, capacidad):
    """Simula una fila FIFO frente a buses que salen en 0, f, 2f, ...

    llegadas[i] es el minuto (entero) en que llega el pasajero i. Cada bus
    lleva hasta `capacidad` personas; quien llega exactamente en el minuto
    del bus alcanza a subir. Los empates conservan el orden de la lista.

    Devuelve una lista `abordajes` alineada con `llegadas`: abordajes[i] es
    el minuto en que sube el pasajero i (su espera es abordajes[i] - llegadas[i]).

    Costo: O(n log n) para ordenar las llegadas con merge sort estable
    (O(n) si ya vienen ordenadas) + O(n) para la simulación, porque los
    buses vacíos se saltan en lugar de recorrerse uno por uno.
    Memoria O(n).
    """
    if not _es_entero(frecuencia) or frecuencia <= 0:
        raise ValueError("la frecuencia debe ser un entero positivo")
    if not _es_entero(capacidad) or capacidad <= 0:
        raise ValueError("la capacidad debe ser un entero positivo")
    n = len(llegadas)
    for minuto in llegadas:
        if not _es_entero(minuto):
            raise ValueError("cada llegada debe ser un minuto entero")
    abordajes = [0] * n
    if n == 0:
        return abordajes

    orden = indices_ordenados(llegadas)
    fila = Cola(1024)
    siguiente = 0          # próximo pasajero (en orden de llegada) por encolar
    bus = 0                # minuto del bus que está por salir
    while siguiente < n or not fila.vacia():
        if fila.vacia():
            llegada = llegadas[orden[siguiente]]
            if llegada > bus:
                # salta al primer bus en o después de esa llegada
                bus = ((llegada + frecuencia - 1) // frecuencia) * frecuencia
        # ENQUEUE: todos los que llegaron hasta el minuto del bus
        while siguiente < n and llegadas[orden[siguiente]] <= bus:
            fila.encolar(orden[siguiente])
            siguiente += 1
        # DEQUEUE: suben hasta llenar el cupo, en orden de llegada
        cupos = capacidad
        while cupos > 0 and not fila.vacia():
            abordajes[fila.desencolar()] = bus
            cupos -= 1
        bus += frecuencia
    return abordajes
