"""Adaptador web. La red compartida es una sesión de demostración local."""
from pathlib import Path
from threading import RLock
from flask import Flask, jsonify, render_template, request
from motor import Red, simular_fila
from herramientas.rendimiento import medir
from servicios.laboratorio import experimento
from servicios.consultas import horarios, sentido


def serializar(valor):
    if hasattr(valor, '__dict__'):
        return {k:serializar(v) for k,v in vars(valor).items()}
    if isinstance(valor, (list,tuple)):
        return [serializar(x) for x in valor]
    return valor


def crear_app(carpeta=None):
    app=Flask(__name__)
    app.config['MAX_CONTENT_LENGTH']=2*1024*1024
    red=Red(carpeta or Path(__file__).resolve().parent/'datos')
    app.config['RED']=red
    candado=RLock()
    historial=[]
    consultas = {
        'estado': ('nombre',), 'autocompletar': ('prefijo','k'), 'rango': ('desde','hasta'),
        'proximo_bus': ('estacion','ruta','hora'), 'viaje': ('origen','destino'),
        'ranking': ('k',), 'recorrido': ('ruta','al_reves'),
        'cerrar': ('nombre',), 'reabrir': ('nombre',),
        'agregar_parada': ('ruta','nueva','despues_de'), 'quitar_parada': ('ruta','estacion'),
        'deshacer': (), 'rehacer': (),
    }
    cambios={'cerrar','reabrir','agregar_parada','quitar_parada','deshacer','rehacer'}

    @app.get('/')
    def inicio():
        return render_template('index.html')

    @app.get('/api/red')
    def resumen():
        with candado:
            return jsonify(estaciones=red.nombres,estaciones_abiertas=red.autocompletar('',len(red.nombres)),rutas=sorted(r for r,_ in red.rutas.elementos()),
                           abiertas=sum(e.abierta for _,e in red.estaciones.elementos()),
                           horarios=red.eventos,historial=historial[-40:],
                           deshacer=len(red.atras.datos),rehacer=len(red.adelante.datos))

    @app.post('/api/operacion')
    def operacion():
        cuerpo=request.get_json(silent=True)
        if not isinstance(cuerpo,dict):
            return jsonify(error='Se requiere un objeto JSON'),400
        op=cuerpo.get('operacion'); args=cuerpo.get('argumentos',{})
        if not isinstance(args,dict):
            return jsonify(error='Argumentos inválidos'),400
        try:
            with candado:
                if op=='simular_fila':
                    llegadas=args.get('llegadas')
                    if not isinstance(llegadas,list) or len(llegadas)>300000:
                        raise ValueError('Use hasta 300.000 llegadas')
                    resultado=simular_fila(llegadas,args.get('frecuencia'),args.get('capacidad'))
                elif op in consultas:
                    if set(args)!=set(consultas[op]):
                        raise ValueError('Parámetros incorrectos')
                    for k,v in args.items():
                        if k=='k':
                            if type(v) is not int or not 0<=v<=10000:
                                raise ValueError('k debe ser entero entre 0 y 10.000')
                        elif k=='al_reves':
                            if type(v) is not bool: raise ValueError('al_reves debe ser booleano')
                        elif not isinstance(v,str):
                            raise ValueError(k+' debe ser texto')
                    resultado=getattr(red,op)(**args)
                    if op in cambios and resultado:
                        historial.append({'operacion':op,'argumentos':args})
                else:
                    raise ValueError('Operación desconocida')
                return jsonify(resultado=serializar(resultado))
        except (ValueError,TypeError) as error:
            return jsonify(error=str(error)),400

    @app.post('/api/rendimiento')
    def rendimiento():
        cuerpo=request.get_json(silent=True)
        if not isinstance(cuerpo,dict):
            return jsonify(error='Se requiere un objeto JSON'),400
        try:
            return jsonify(medir(cuerpo.get('base',64),cuerpo.get('repeticiones',7)))
        except (ValueError,TypeError) as error:
            return jsonify(error=str(error)),400
    @app.get('/api/estacion/rutas')
    def rutas_estacion():
        try:
            with candado:
                nombre=request.args.get('estacion','')
                return jsonify(estacion=nombre,estado=red.estado(nombre),
                               rutas=[{'ruta':r,'origen':a,'destino':b} for r,a,b in red.rutas_estacion(nombre)])
        except ValueError as error:
            return jsonify(error=str(error)),400

    @app.get('/api/ruta')
    def ruta_detalle():
        try:
            with candado:
                return jsonify(sentido(red,request.args.get('ruta','')))
        except ValueError as error:
            return jsonify(error=str(error)),400

    @app.get('/api/horarios')
    def horarios_detalle():
        try:
            with candado:
                return jsonify(horarios(red,request.args.get('estacion',''),
                                        request.args.get('ruta',''),request.args.get('hora','')))
        except ValueError as error:
            return jsonify(error=str(error)),400

    @app.post('/api/laboratorio')
    def laboratorio():
        try:
            # No usa ni bloquea la red compartida; ambos escenarios usan la misma lista.
            return jsonify(experimento(request.get_json(silent=True)))
        except (ValueError,TypeError) as error:
            return jsonify(error=str(error)),400

    return app

if __name__=='__main__':
    crear_app().run(host='127.0.0.1',port=5000,debug=False)
