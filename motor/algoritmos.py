"""Ordenamiento y búsqueda propios: merge sort estable y búsqueda binaria."""


def ordenar(elementos, clave=None):
    """Merge sort ascendente de abajo hacia arriba. Estable. O(n log n).

    `clave` (opcional) transforma cada elemento en el valor a comparar; se
    calcula una sola vez por elemento. Devuelve una lista nueva.
    """
    n = len(elementos)
    if clave is None:
        claves = elementos
    else:
        claves = [None] * n
        i = 0
        while i < n:
            claves[i] = clave(elementos[i])
            i += 1
    orden = indices_ordenados(claves)
    resultado = [None] * n
    i = 0
    while i < n:
        resultado[i] = elementos[orden[i]]
        i += 1
    return resultado


def ya_ordenado(claves):
    """True si claves es no decreciente. O(n)."""
    i = 1
    while i < len(claves):
        if claves[i] < claves[i - 1]:
            return False
        i += 1
    return True


def indices_ordenados(claves):
    """Permutación estable de índices que ordena `claves` ascendentemente.

    Merge sort iterativo sobre índices con un arreglo auxiliar reutilizado.
    Si la entrada ya viene ordenada se detecta en O(n).
    """
    n = len(claves)
    origen = list(range(n))
    if ya_ordenado(claves):
        return origen
    destino = [0] * n
    ancho = 1
    while ancho < n:
        inicio = 0
        while inicio < n:
            medio = inicio + ancho
            if medio > n:
                medio = n
            fin = medio + ancho
            if fin > n:
                fin = n
            i = inicio
            j = medio
            k = inicio
            while i < medio and j < fin:
                # <= conserva el orden original en empates (estabilidad)
                if claves[origen[i]] <= claves[origen[j]]:
                    destino[k] = origen[i]
                    i += 1
                else:
                    destino[k] = origen[j]
                    j += 1
                k += 1
            while i < medio:
                destino[k] = origen[i]
                i += 1
                k += 1
            while j < fin:
                destino[k] = origen[j]
                j += 1
                k += 1
            inicio = fin
        origen, destino = destino, origen
        ancho = ancho * 2
    return origen


def limite_inferior(arreglo, objetivo):
    """Primer índice i con arreglo[i] >= objetivo (len si no hay). O(log n).

    `arreglo` debe estar ordenado ascendentemente.
    """
    bajo = 0
    alto = len(arreglo)
    while bajo < alto:
        medio = (bajo + alto) // 2
        if arreglo[medio] < objetivo:
            bajo = medio + 1
        else:
            alto = medio
    return bajo
