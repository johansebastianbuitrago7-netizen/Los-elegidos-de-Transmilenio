"""Atlas — servidor web del planeador TransMilenio.

Arranque:  python app.py   (http://127.0.0.1:5000)

La aplicación solo traduce HTTP <-> motor. Ninguna regla de planeación
vive aquí: valida parámetros, toma el candado y llama a Red/simular_fila.
"""

import os
import threading

from flask import Flask, jsonify, render_template, request

from motor import Red
from servicios import laboratorio, presentacion, rendimiento
from servicios.presentacion import normalizar

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_DATOS = os.environ.get("ATLAS_DATOS", os.path.join(BASE, "datos"))


class ErrorEntrada(Exception):
    pass


def crear_app(carpeta=CARPETA_DATOS):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    candado = threading.Lock()
    estado = {"red": Red(carpeta), "rendimiento": None}
    candado_rendimiento = threading.Lock()

    def red():
        return estado["red"]

    # ------------------------------------------------------- validación
    def texto(nombre, origen=None, obligatorio=True):
        datos = origen if origen is not None else request.args
        valor = normalizar(datos.get(nombre, ""))
        if obligatorio and not valor:
            raise ErrorEntrada(f"Falta el parámetro '{nombre}'.")
        return valor

    def ruta_param(nombre, origen=None):
        datos = origen if origen is not None else request.args
        valor = str(datos.get(nombre, "")).strip().upper()
        if not valor:
            raise ErrorEntrada(f"Falta el parámetro '{nombre}'.")
        return valor

    def entero(nombre, defecto, minimo, maximo, origen=None):
        datos = origen if origen is not None else request.args
        bruto = datos.get(nombre, defecto)
        try:
            valor = int(bruto)
        except (TypeError, ValueError):
            raise ErrorEntrada(f"'{nombre}' debe ser un número entero.")
        if valor < minimo or valor > maximo:
            raise ErrorEntrada(f"'{nombre}' debe estar entre {minimo} y {maximo}.")
        return valor

    def cuerpo():
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            raise ErrorEntrada("El cuerpo debe ser un objeto JSON.")
        return datos

    @app.errorhandler(ErrorEntrada)
    def error_entrada(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(404)
    def no_encontrado(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Ruta de API inexistente."}), 404
        return render_template("index.html"), 404

    # ------------------------------------------------------------ vistas
    @app.get("/")
    def inicio():
        return render_template("index.html")

    @app.get("/api/resumen")
    def resumen():
        with candado:
            r = red()
            d = r.diagnostico
            return jsonify({
                "estaciones": d.obtener("estaciones"),
                "rutas": d.obtener("rutas"),
                "paradas": d.obtener("paradas"),
                "eventos": d.obtener("eventos"),
                "descartados": d.obtener("eventos_fuera_de_ruta") + d.obtener("horas_invalidas"),
                "cerradas": [e for e in r.estaciones() if r.estado(e) == "cerrada"],
                "top": r.ranking(5),
            })

    @app.get("/api/estaciones")
    def estaciones():
        with candado:
            r = red()
            return jsonify([{"nombre": e, "estado": r.estado(e)} for e in r.estaciones()])

    @app.get("/api/estado")
    def estado_estacion():
        nombre = texto("nombre")
        with candado:
            return jsonify(presentacion.ficha_estacion(red(), nombre))

    @app.get("/api/autocompletar")
    def autocompletar():
        prefijo = texto("prefijo", obligatorio=False)
        k = entero("k", 8, 0, 200)
        with candado:
            return jsonify({"prefijo": prefijo, "k": k, "resultados": red().autocompletar(prefijo, k)})

    @app.get("/api/rango")
    def rango():
        desde, hasta = texto("desde"), texto("hasta")
        with candado:
            return jsonify({"desde": desde, "hasta": hasta, "resultados": red().rango(desde, hasta)})

    @app.get("/api/rutas")
    def rutas():
        with candado:
            r = red()
            return jsonify([presentacion.describir_ruta(r, x) for x in r.rutas()])

    @app.get("/api/estacion/rutas")
    def rutas_estacion():
        nombre = texto("nombre")
        with candado:
            r = red()
            rutas_de = r.rutas_de(nombre)
            if rutas_de is None:
                raise ErrorEntrada(f"La estación {nombre} no existe.")
            return jsonify({"estacion": nombre, "estado": r.estado(nombre),
                            "rutas": [presentacion.describir_ruta(r, x) for x in rutas_de]})

    @app.get("/api/proximo")
    def proximo():
        estacion, ruta = texto("estacion"), ruta_param("ruta")
        hora = request.args.get("hora", "").strip()
        with candado:
            r = red()
            if r.estado(estacion) == "inexistente":
                raise ErrorEntrada(f"La estación {estacion} no existe.")
            if r.recorrido(ruta) is None:
                raise ErrorEntrada(f"La ruta {ruta} no existe.")
            try:
                return jsonify(presentacion.detalle_proximo(r, estacion, ruta, hora))
            except ValueError:
                raise ErrorEntrada("La hora debe tener formato HH:MM entre 00:00 y 23:59.")

    @app.get("/api/viaje")
    def viaje():
        origen, destino = texto("origen"), texto("destino")
        with candado:
            return jsonify(presentacion.detalle_viaje(red(), origen, destino))

    @app.get("/api/ranking")
    def ranking():
        k = entero("k", 10, 0, 1000)
        with candado:
            return jsonify([{"nombre": n, "buses": b} for n, b in red().ranking(k)])

    @app.get("/api/recorrido")
    def recorrido():
        ruta = ruta_param("ruta")
        al_reves = request.args.get("al_reves", "0") in ("1", "true", "si")
        with candado:
            r = red()
            paradas = r.recorrido(ruta, al_reves)
            if paradas is None:
                raise ErrorEntrada(f"La ruta {ruta} no existe.")
            return jsonify({"ruta": presentacion.describir_ruta(r, ruta), "al_reves": al_reves,
                            "paradas": [{"nombre": e, "estado": r.estado(e)} for e in paradas]})

    # ---------------------------------------------------- operación R7–R9
    def respuesta_cambio(ok, mensaje_error):
        r = red()
        return jsonify({"ok": ok, "mensaje": None if ok else mensaje_error,
                        "historial": presentacion.historial(r)})

    @app.post("/api/agregar")
    def agregar():
        datos = cuerpo()
        ruta, nueva = ruta_param("ruta", datos), texto("nueva", datos)
        despues = texto("despues_de", datos, obligatorio=False) or None
        with candado:
            ok = red().agregar_parada(ruta, nueva, despues)
            return respuesta_cambio(ok, "No se pudo agregar: revisa que la ruta y las estaciones "
                                        "existan y que la nueva no esté ya en la ruta.")

    @app.post("/api/quitar")
    def quitar():
        datos = cuerpo()
        ruta, estacion = ruta_param("ruta", datos), texto("estacion", datos)
        with candado:
            ok = red().quitar_parada(ruta, estacion)
            return respuesta_cambio(ok, f"{estacion} no es parada de {ruta}.")

    @app.post("/api/cerrar")
    def cerrar():
        nombre = texto("nombre", cuerpo())
        with candado:
            return respuesta_cambio(red().cerrar(nombre), f"{nombre} no existe o ya estaba cerrada.")

    @app.post("/api/reabrir")
    def reabrir():
        nombre = texto("nombre", cuerpo())
        with candado:
            return respuesta_cambio(red().reabrir(nombre), f"{nombre} no existe o ya estaba abierta.")

    @app.post("/api/deshacer")
    def deshacer():
        with candado:
            return respuesta_cambio(red().deshacer(), "No hay nada para deshacer.")

    @app.post("/api/rehacer")
    def rehacer():
        with candado:
            return respuesta_cambio(red().rehacer(), "No hay nada para rehacer.")

    @app.get("/api/historial")
    def historial():
        with candado:
            return jsonify(presentacion.historial(red()))

    @app.post("/api/reiniciar")
    def reiniciar():
        nueva = Red(carpeta)
        with candado:
            estado["red"] = nueva
            return jsonify({"ok": True, "historial": presentacion.historial(nueva)})

    # ------------------------------------------------------------ R10
    @app.post("/api/fila/educativo")
    def fila_educativa():
        datos = cuerpo()
        llegadas = datos.get("llegadas")
        if not isinstance(llegadas, list) or not llegadas:
            raise ErrorEntrada("Escribe al menos una llegada.")
        if len(llegadas) > laboratorio.LIMITE_EDUCATIVO:
            raise ErrorEntrada(f"El modo educativo admite hasta {laboratorio.LIMITE_EDUCATIVO} personas.")
        if any(not isinstance(x, int) or isinstance(x, bool) or x < 0 or x > 10_000 for x in llegadas):
            raise ErrorEntrada("Cada llegada debe ser un minuto entero entre 0 y 10000.")
        f = entero("frecuencia", None, 1, 240, datos)
        c = entero("capacidad", None, 1, 300, datos)
        return jsonify(laboratorio.traza_educativa(llegadas, f, c))

    def parametros_escenario(datos):
        demanda = datos.get("demanda", "pico")
        if demanda not in laboratorio.DEMANDAS:
            raise ErrorEntrada("Demanda desconocida.")
        return (entero("pasajeros", 20000, 1, laboratorio.LIMITE_AVANZADO, datos),
                entero("duracion", 180, 1, 1440, datos), demanda,
                entero("semilla", 2021, 0, 2**31 - 1, datos))

    @app.post("/api/fila/avanzado")
    def fila_avanzada():
        datos = cuerpo()
        p, d, demanda, semilla = parametros_escenario(datos)
        f = entero("frecuencia", 4, 1, 240, datos)
        c = entero("capacidad", 160, 1, 1000, datos)
        return jsonify(laboratorio.escenario_avanzado(p, d, f, c, demanda, semilla))

    @app.post("/api/fila/comparar")
    def fila_comparar():
        datos = cuerpo()
        p, d, demanda, semilla = parametros_escenario(datos)
        a = datos.get("a") or {}
        b = datos.get("b") or {}
        config_a = (entero("frecuencia", 4, 1, 240, a), entero("capacidad", 160, 1, 1000, a))
        config_b = (entero("frecuencia", 6, 1, 240, b), entero("capacidad", 250, 1, 1000, b))
        return jsonify(laboratorio.comparar(p, d, demanda, semilla, config_a, config_b))

    # ------------------------------------------------------------ R11
    @app.get("/api/rendimiento")
    def rendimiento_ultimo():
        return jsonify(estado["rendimiento"])

    @app.post("/api/rendimiento")
    def rendimiento_medir():
        datos = request.get_json(silent=True) or {}
        maximo = entero("maximo", 2000, 500, 8000, datos)
        tamanos = []
        n = 250
        while n <= maximo:
            tamanos.append(n)
            n *= 2
        repeticiones = entero("repeticiones", 3, 1, 9, datos)
        if not candado_rendimiento.acquire(blocking=False):
            raise ErrorEntrada("Ya hay una medición en curso.")
        try:
            estado["rendimiento"] = rendimiento.medir(tuple(tamanos), repeticiones)
        finally:
            candado_rendimiento.release()
        return jsonify(estado["rendimiento"])

    return app


if __name__ == "__main__":
    crear_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
