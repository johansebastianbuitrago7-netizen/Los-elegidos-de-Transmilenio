"""R10: simulacion de la fila de abordaje (cola enlazada)."""
from .estructuras import Cola
from .algoritmos import ordenar, esta_ordenada


def simular_fila(llegadas, frecuencia, capacidad):
    """llegadas: tiempos de llegada de cada pasajero (la posicion en la lista
    es su identificador). Los buses salen en frecuencia, 2*frecuencia, ...
    Un pasajero que llega en el instante exacto de una salida alcanza a subir.
    Sube en orden de llegada hasta llenar `capacidad`.

    Devuelve [(hora_salida, [ids de pasajeros que abordaron en orden]), ...]
    desde el primer bus hasta el que sube al ultimo pasajero.
    Complejidad: O(P + B), P = pasajeros, B = buses (+ O(P log P) solo si
    las llegadas vienen desordenadas).
    """
    n = len(llegadas)
    if n == 0:
        return []
    if frecuencia <= 0 or capacidad <= 0:
        raise ValueError("frecuencia y capacidad deben ser positivas")

    if esta_ordenada(llegadas):
        orden = None
    else:
        orden = [j for _, j in ordenar([(llegadas[j], j) for j in range(n)])]

    cola = Cola()
    salidas = []
    i = 0
    k = 1
    while i < n or not cola.vacia():
        t = k * frecuencia
        while i < n:
            j = i if orden is None else orden[i]
            if llegadas[j] <= t:
                cola.encolar(j)
                i += 1
            else:
                break
        subieron = []
        while len(subieron) < capacidad and not cola.vacia():
            subieron.append(cola.desencolar())
        salidas.append((t, subieron))
        k += 1
    return salidas
