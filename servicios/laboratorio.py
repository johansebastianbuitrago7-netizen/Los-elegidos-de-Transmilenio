import hashlib
import json
import random
from motor import simular_fila
from motor.analisis_fila import AnalisisFila

LIMITE_ANIMADO = 40
LIMITE_MASIVO = 300000


def entero(valor, nombre, inferior, superior):
    if type(valor) is not int or not inferior <= valor <= superior:
        raise ValueError(f'{nombre}: use un entero entre {inferior} y {superior}')
    return valor


def generar(cantidad, duracion, escenario, semilla):
    entero(cantidad,'Pasajeros',0,LIMITE_MASIVO)
    entero(duracion,'Duración en minutos',1,1440)
    entero(semilla,'Semilla',0,2**31-1)
    if escenario not in ('baja','media','intensa'):
        raise ValueError('Escenario desconocido')
    rng = random.Random(semilla)
    if escenario == 'intensa':
        # Dos uniformes promediadas: concentración triangular en el centro.
        return sorted((rng.randrange(duracion)+rng.randrange(duracion))//2 for _ in range(cantidad))
    return sorted(rng.randrange(duracion) for _ in range(cantidad))


def reducir(filas, limite=160):
    """Muestra por bloques conservando máximo del segundo componente, primero y último."""
    if len(filas) <= limite:
        return filas
    ancho = (len(filas)+limite-2)//(limite-1)
    salida = [filas[0]]
    for i in range(1,len(filas),ancho):
        salida.append(max(filas[i:i+ancho],key=lambda f:f[1]))
    if salida[-1] != filas[-1]:
        salida.append(filas[-1])
    return salida


def pasos(llegadas, resultado, capacidad):
    """Estados de presentación derivados; NO se decide quién sube aquí."""
    tiempos = sorted(set(llegadas) | set(resultado.abordajes))
    estados = [{'minuto':0,'fase':'inicio','fila':[],'abordando':[],'atendidos':[],
                'llegaron':[],'cupos':capacidad,'explicacion':'Pulsa Siguiente para ver las primeras llegadas.'}]
    atendidos = []
    for t in tiempos:
        fila = sorted((i for i,a in enumerate(llegadas) if a<=t and resultado.abordajes[i]>=t),key=lambda i:(llegadas[i],i))
        nuevos = [i for i,a in enumerate(llegadas) if a==t]
        suben = [i for i in fila if resultado.abordajes[i]==t]
        def agregar(fase,cola,abordando,explicacion):
            estados.append({'minuto':t,'fase':fase,'fila':cola[:], 'abordando':abordando[:],
                            'atendidos':atendidos[:],'llegaron':nuevos,'cupos':capacidad-len(abordando),
                            'explicacion':explicacion})
        if nuevos:
            agregar('llegadas',fila,[], 'Llegan '+', '.join('P'+str(i+1) for i in nuevos)+'. Se incorporan al FINAL; quien llegó antes permanece al FRENTE.')
        if suben:
            agregar('bus',fila,[], f'El bus ofrece {capacidad} cupos. En la fila hay {len(fila)} pasajeros, en orden de llegada.')
            restantes = [i for i in fila if resultado.abordajes[i]>t]
            agregar('abordaje',restantes,suben,'DESENCOLAR: abordan '+', '.join('P'+str(i+1) for i in suben)+
                    ('. '+', '.join('P'+str(i+1) for i in restantes)+' sigue esperando porque los cupos se completaron.' if restantes else '. La fila queda vacía.'))
            atendidos.extend(suben)
            agregar('salida',restantes,[],f'El bus sale con {len(suben)} pasajeros y {capacidad-len(suben)} cupos libres. Permanecen {len(restantes)} en fila.')
    return estados


def ejecutar(llegadas, frecuencia, capacidad, detalle=False):
    entero(frecuencia,'Frecuencia en minutos',1,1440)
    entero(capacidad,'Capacidad',1,10000)
    if not isinstance(llegadas,list) or len(llegadas)>LIMITE_MASIVO:
        raise ValueError('Llegadas: lista de hasta 300.000 pasajeros')
    for l in llegadas:
        entero(l,'Llegada en minutos',0,1000000000)
    if detalle and len(llegadas)>LIMITE_ANIMADO:
        raise ValueError('El modo educativo admite hasta 40 pasajeros; use el modo avanzado')
    resultado=simular_fila(llegadas,frecuencia,capacidad)
    analisis=AnalisisFila(llegadas,resultado,frecuencia,capacidad)
    metricas={k:v for k,v in vars(analisis).items() if k not in ('fila','ocupacion','distribucion','demanda')}
    salida={'metricas':metricas,'series':{'fila':reducir(analisis.fila),
            'ocupacion':reducir(analisis.ocupacion),'distribucion':analisis.distribucion,
            'demanda':reducir(analisis.demanda)},'frecuencia':frecuencia,'capacidad':capacidad,
            'limite_animado':LIMITE_ANIMADO,'resumen_series':len(analisis.fila)>160}
    if detalle:
        salida.update(llegadas=llegadas,abordajes=resultado.abordajes,esperas=resultado.esperas,
                      pasos=pasos(llegadas,resultado,capacidad))
    return salida


def experimento(cuerpo):
    if not isinstance(cuerpo,dict):
        raise ValueError('Se requiere un objeto JSON')
    modo=cuerpo.get('modo')
    if modo=='educativo':
        return ejecutar(cuerpo.get('llegadas'),cuerpo.get('frecuencia'),cuerpo.get('capacidad'),True)
    if modo!='avanzado':
        raise ValueError('Modo desconocido')
    llegadas=generar(cuerpo.get('cantidad'),cuerpo.get('duracion'),cuerpo.get('escenario'),cuerpo.get('semilla',42))
    a=cuerpo.get('a');b=cuerpo.get('b')
    if not isinstance(a,dict) or not isinstance(b,dict):
        raise ValueError('Se requieren configuraciones A y B')
    resultado_a=ejecutar(llegadas,a.get('frecuencia'),a.get('capacidad'))
    resultado_b=ejecutar(llegadas,b.get('frecuencia'),b.get('capacidad'))
    diferencias={}
    for key in ('espera_media','espera_maxima','cola_maxima','buses','ocupacion_media'):
        va=resultado_a['metricas'][key];vb=resultado_b['metricas'][key]
        diferencias[key]={'b_menos_a':vb-va,'porcentaje':(vb-va)/va*100 if va else None}
    return {'a':resultado_a,'b':resultado_b,'diferencias':diferencias,
            'huella_llegadas':hashlib.sha256(json.dumps(llegadas).encode()).hexdigest(),
            'muestra_llegadas':llegadas[:20],'sintetico':True,'semilla':cuerpo.get('semilla',42)}
