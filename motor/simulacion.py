from .estructuras import Cola, ordenar
from .modelos import Simulacion


def simular_fila(llegadas, frecuencia, capacidad):
    """Minutos desde cero; buses en 0, f, 2f…; llegadas simultáneas sí abordan."""
    if type(frecuencia) is not int or frecuencia <= 0:
        raise ValueError('Frecuencia debe ser un entero positivo')
    if type(capacidad) is not int or capacidad <= 0:
        raise ValueError('Capacidad debe ser un entero positivo')
    eventos = []
    ordenadas = True
    anterior = 0
    for i, llegada in enumerate(llegadas):
        if type(llegada) is not int or llegada < 0:
            raise ValueError('Llegadas deben ser minutos enteros no negativos')
        if llegada < anterior:
            ordenadas = False
        anterior = llegada
        eventos.append((llegada, i))
    if not ordenadas:
        eventos = ordenar(eventos)
    abordajes, esperas = [0]*len(eventos), [0]*len(eventos)
    cola = Cola()
    i, tiempo, buses = 0, 0, 0
    while i < len(eventos) or cola.cantidad:
        if not cola.cantidad and i < len(eventos) and eventos[i][0] > tiempo:
            tiempo = ((eventos[i][0] + frecuencia - 1) // frecuencia) * frecuencia
        while i < len(eventos) and eventos[i][0] <= tiempo:
            cola.poner(eventos[i])
            i += 1
        cupos = capacidad
        while cupos and cola.cantidad:
            llegada, indice = cola.sacar()
            abordajes[indice] = tiempo
            esperas[indice] = tiempo - llegada
            cupos -= 1
        buses += 1
        tiempo += frecuencia
    return Simulacion(abordajes, esperas, buses)
