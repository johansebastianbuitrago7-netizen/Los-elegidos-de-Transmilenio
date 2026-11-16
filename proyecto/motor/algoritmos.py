"""Ordenamiento y busqueda propios."""


def esta_ordenada(a):
    for i in range(1, len(a)):
        if a[i] < a[i - 1]:
            return False
    return True


def ordenar(a):
    """Merge sort iterativo (de abajo hacia arriba), estable. O(n log n).
    Devuelve una lista nueva; no modifica la original."""
    n = len(a)
    src = a[:]
    if n < 2:
        return src
    dst = [None] * n
    ancho = 1
    while ancho < n:
        i = 0
        while i < n:
            medio = i + ancho
            if medio > n:
                medio = n
            fin = i + 2 * ancho
            if fin > n:
                fin = n
            l = i
            r = medio
            k = i
            while l < medio and r < fin:
                if src[r] < src[l]:
                    dst[k] = src[r]
                    r += 1
                else:
                    dst[k] = src[l]
                    l += 1
                k += 1
            while l < medio:
                dst[k] = src[l]
                l += 1
                k += 1
            while r < fin:
                dst[k] = src[r]
                r += 1
                k += 1
            i += 2 * ancho
        src, dst = dst, src
        ancho *= 2
    return src


def primero_mayor_o_igual(a, x):
    """Busqueda binaria en lista ordenada: indice del primer elemento >= x
    (len(a) si no hay). O(log n)."""
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo
