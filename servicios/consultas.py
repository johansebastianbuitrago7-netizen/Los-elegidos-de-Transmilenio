from motor.modelos import minutos


def sentido(red, ruta):
    recorrido=red.recorrido(ruta)
    return {'ruta':ruta,'origen':recorrido[0] if recorrido else None,
            'destino':recorrido[-1] if recorrido else None,'estaciones':recorrido}


def horarios(red, estacion, ruta, hora):
    eventos=red.siguientes_horarios(estacion,ruta,hora)
    delta=minutos(eventos[0])-minutos(hora) if eventos else None
    return {'resultado':{'eventos':eventos,'diferencia_minutos':delta},
            'presentacion':{'estacion':estacion,'consulta':hora,**sentido(red,ruta),
                           'tipo':'Registro histórico/programado; no distingue llegada y salida'}}
