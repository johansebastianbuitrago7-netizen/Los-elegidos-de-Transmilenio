"""Lectura de los tres CSV con csv.reader (sin DictReader)."""

import csv


def _ruta(carpeta, archivo):
    if carpeta.endswith("/") or carpeta.endswith("\\"):
        return carpeta + archivo
    return carpeta + "/" + archivo


def leer_tabla(carpeta, archivo, columnas):
    """Devuelve las filas como tuplas con las columnas pedidas, en ese orden.

    Ubica cada columna por nombre en el encabezado, así el orden de las
    columnas en el archivo no importa. Lanza ValueError si falta alguna.
    """
    ruta = _ruta(carpeta, archivo)
    try:
        manejador = open(ruta, newline="", encoding="utf-8-sig")
    except OSError:
        raise ValueError("no se pudo abrir " + ruta)
    filas = []
    with manejador:
        lector = csv.reader(manejador)
        encabezado = None
        for fila in lector:
            encabezado = fila
            break
        if encabezado is None:
            raise ValueError(archivo + " está vacío")
        posiciones = []
        for nombre in columnas:
            encontrada = -1
            i = 0
            while i < len(encabezado):
                if encabezado[i].strip().lower() == nombre:
                    encontrada = i
                i += 1
            if encontrada < 0:
                raise ValueError(archivo + ": falta la columna '" + nombre + "'")
            posiciones.append(encontrada)
        ancho = len(encabezado)
        for fila in lector:
            if len(fila) == 0:
                continue
            if len(fila) < ancho:
                raise ValueError(archivo + ": fila incompleta " + ",".join(fila))
            if len(posiciones) == 1:
                filas.append((fila[posiciones[0]].strip(),))
            elif len(posiciones) == 3:
                filas.append((fila[posiciones[0]].strip(),
                              fila[posiciones[1]].strip(),
                              fila[posiciones[2]].strip()))
            else:
                valores = []
                for p in posiciones:
                    valores.append(fila[p].strip())
                filas.append(tuple(valores))
    return filas
