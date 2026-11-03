"""Conversión entre "HH:MM" y minutos desde la medianoche."""

_DIGITOS = "0123456789"


def _entero(texto):
    if len(texto) == 0:
        return -1
    valor = 0
    for c in texto:
        d = _DIGITOS.find(c)
        if d < 0:
            return -1
        valor = valor * 10 + d
    return valor


def a_minutos(hora):
    """Convierte "H:MM" o "HH:MM" (00:00–23:59) a minutos. ValueError si no."""
    if not isinstance(hora, str):
        raise ValueError("la hora debe ser un texto HH:MM")
    texto = hora.strip()
    partes = texto.split(":")
    if len(partes) != 2 or len(partes[1]) != 2 or len(partes[0]) > 2:
        raise ValueError("hora inválida: " + texto)
    h = _entero(partes[0])
    m = _entero(partes[1])
    if h < 0 or m < 0 or h > 23 or m > 59:
        raise ValueError("hora fuera de rango: " + texto)
    return h * 60 + m


def minutos_csv(hora):
    """Lee una hora del CSV. Admite horas GTFS >= 24 (p. ej. 25:10).

    Decisión documentada: una hora >= 24:00 pertenece a la madrugada del
    día de servicio y se pliega a 0–23 (25:10 -> 01:10). Devuelve -1 si el
    texto no es una hora válida.
    """
    partes = hora.strip().split(":")
    if len(partes) < 2 or len(partes[1]) != 2:
        return -1
    h = _entero(partes[0])
    m = _entero(partes[1])
    if h < 0 or m < 0 or m > 59:
        return -1
    return (h % 24) * 60 + m


def a_texto(minutos):
    h = minutos // 60
    m = minutos % 60
    return str(h // 10) + str(h % 10) + ":" + str(m // 10) + str(m % 10)
