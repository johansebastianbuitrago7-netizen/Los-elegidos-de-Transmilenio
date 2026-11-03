"""Adaptación de resultados del motor a estructuras JSON para la interfaz.

Aquí no se decide nada de la planeación: solo se describe lo que devolvió
el motor (extremos de ruta, estaciones de cada tramo, intervalos).
"""

import unicodedata

from motor.tiempo import a_minutos

INTERVALO_LARGO = 30   # minutos; umbral para explicar huecos en horarios


def normalizar(texto):
    """Mayúsculas, sin tildes y sin espacios repetidos (formato del CSV)."""
    if texto is None:
        return ""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", str(texto))
                         if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.upper().split())


def describir_ruta(red, ruta):
    recorrido = red.recorrido(ruta)
    if not recorrido:
        return None
    return {
        "ruta": ruta,
        "desde": recorrido[0],
        "hasta": recorrido[-1],
        "paradas": len(recorrido),
        "etiqueta": f"{ruta} · {recorrido[0]} → {recorrido[-1]}",
    }


def ficha_estacion(red, nombre):
    estado = red.estado(nombre)
    ficha = {"nombre": nombre, "estado": estado}
    if estado == "inexistente":
        ficha["sugerencias"] = red.autocompletar(nombre[:3], 5) if nombre else []
        return ficha
    rutas = []
    for ruta in red.rutas_de(nombre):
        info = describir_ruta(red, ruta)
        recorrido = red.recorrido(ruta)
        info["posicion"] = recorrido.index(nombre) + 1
        info["eventos"] = len(red.horarios(nombre, ruta))
        rutas.append(info)
    ficha["rutas"] = rutas
    ficha["buses"] = red.buses(nombre)
    return ficha


def detalle_proximo(red, estacion, ruta, hora, siguientes=5):
    minutos = a_minutos(hora)
    proximo = red.proximo_bus(estacion, ruta, hora)
    todos = red.horarios(estacion, ruta)
    detalle = {
        "estacion": estacion,
        "ruta": describir_ruta(red, ruta),
        "estado": red.estado(estacion),
        "hora": hora,
        "proximo": proximo,
        "diferencia": None,
        "siguientes": red.proximos_buses(estacion, ruta, hora, siguientes + 1)[1:],
        "eventos_dia": todos,
        "total_dia": len(todos),
        "intervalo": None,
    }
    if proximo is not None:
        detalle["diferencia"] = a_minutos(proximo) - minutos
        anterior = None
        for h in todos:
            if a_minutos(h) < minutos:
                anterior = h
        if detalle["diferencia"] >= INTERVALO_LARGO:
            detalle["intervalo"] = {
                "anterior": anterior,
                "siguiente": proximo,
                "minutos": a_minutos(proximo) - (a_minutos(anterior) if anterior else 0),
            }
    return detalle


def detalle_viaje(red, origen, destino):
    tramos = red.viaje(origen, destino)
    respuesta = {"origen": origen, "destino": destino,
                 "estado_origen": red.estado(origen),
                 "estado_destino": red.estado(destino),
                 "encontrado": tramos is not None, "tramos": [], "paradas": 0}
    if not tramos:
        return respuesta
    for ruta, desde, hasta in tramos:
        estaciones = red.tramo(ruta, desde, hasta)
        respuesta["tramos"].append({
            "ruta": describir_ruta(red, ruta),
            "subir": desde,
            "bajar": hasta,
            "estaciones": [{"nombre": e, "estado": red.estado(e)} for e in estaciones],
            "paradas": len(estaciones) - 1,
        })
    respuesta["paradas"] = red.paradas_viaje(tramos)
    respuesta["transbordo"] = tramos[0][2] if len(tramos) == 2 else None
    return respuesta


def describir_operacion(op):
    tipo = op[0]
    if tipo == "cerrar":
        return {"tipo": tipo, "texto": f"Cerrar {op[1]}"}
    if tipo == "reabrir":
        return {"tipo": tipo, "texto": f"Reabrir {op[1]}"}
    if tipo == "agregar":
        lugar = f"después de {op[3]}" if op[3] else "al inicio"
        return {"tipo": tipo, "texto": f"{op[1]}: agregar {op[2]} {lugar}"}
    lugar = f"(seguía a {op[3]})" if op[3] else "(era la primera)"
    return {"tipo": tipo, "texto": f"{op[1]}: quitar {op[2]} {lugar}"}


def historial(red):
    deshacer, rehacer = red.historial()
    return {"deshacer": [describir_operacion(o) for o in deshacer],
            "rehacer": [describir_operacion(o) for o in rehacer]}
