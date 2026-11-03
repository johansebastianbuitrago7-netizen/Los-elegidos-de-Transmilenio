"""Auditoría AST de las reglas del motor (diapositiva 9 del enunciado).

Uso:  python herramientas/restricciones.py [carpeta_motor]
Sale con código 1 si encuentra algo prohibido dentro de motor/.

Limitación honesta: el análisis es estático. `x in y` se reporta siempre
que y no sea un literal de texto, porque sin tipos no se puede saber si y
es una lista; por eso el motor evita el operador `in` como búsqueda.
"""

import ast
import os
import sys

NOMBRES_PROHIBIDOS = {"dict", "set", "frozenset", "sorted", "min", "max"}
METODOS_PROHIBIDOS = {"sort", "index", "count"}
MODULOS_PERMITIDOS = {"csv", "time", "random"}


class Auditor(ast.NodeVisitor):
    def __init__(self, archivo):
        self.archivo = archivo
        self.hallazgos = []

    def _reportar(self, nodo, mensaje):
        self.hallazgos.append((self.archivo, nodo.lineno, mensaje))

    def visit_Dict(self, nodo):
        self._reportar(nodo, "literal de diccionario")
        self.generic_visit(nodo)

    def visit_Set(self, nodo):
        self._reportar(nodo, "literal de conjunto")
        self.generic_visit(nodo)

    def visit_DictComp(self, nodo):
        self._reportar(nodo, "comprensión de diccionario")
        self.generic_visit(nodo)

    def visit_SetComp(self, nodo):
        self._reportar(nodo, "comprensión de conjunto")
        self.generic_visit(nodo)

    def visit_Name(self, nodo):
        if nodo.id in NOMBRES_PROHIBIDOS:
            self._reportar(nodo, "uso de " + nodo.id)
        if nodo.id in ("__dict__", "vars", "globals", "locals"):
            self._reportar(nodo, "acceso a diccionarios internos: " + nodo.id)

    def visit_Attribute(self, nodo):
        if nodo.attr in METODOS_PROHIBIDOS:
            self._reportar(nodo, "método ." + nodo.attr + "()")
        if nodo.attr in ("DictReader", "DictWriter", "__dict__"):
            self._reportar(nodo, "uso de " + nodo.attr)
        self.generic_visit(nodo)

    def visit_Call(self, nodo):
        for palabra in nodo.keywords:
            if palabra.arg is None:
                self._reportar(nodo, "desempaquetado **kwargs (crea dict)")
        self.generic_visit(nodo)

    def visit_FunctionDef(self, nodo):
        if nodo.args.kwarg is not None:
            self._reportar(nodo, "parámetro **kwargs (crea dict)")
        self.generic_visit(nodo)

    def visit_Compare(self, nodo):
        for operador, derecho in zip(nodo.ops, nodo.comparators):
            if isinstance(operador, (ast.In, ast.NotIn)):
                es_texto = isinstance(derecho, ast.Constant) and isinstance(derecho.value, str)
                if not es_texto:
                    self._reportar(nodo, "operador 'in' para buscar en una colección")
        self.generic_visit(nodo)

    def visit_Import(self, nodo):
        for alias in nodo.names:
            if alias.name.split(".")[0] not in MODULOS_PERMITIDOS:
                self._reportar(nodo, "import no permitido: " + alias.name)

    def visit_ImportFrom(self, nodo):
        if nodo.level == 0 and (nodo.module or "").split(".")[0] not in MODULOS_PERMITIDOS:
            self._reportar(nodo, "import no permitido: " + str(nodo.module))


def auditar(carpeta):
    hallazgos = []
    archivos = 0
    for raiz, _, nombres in os.walk(carpeta):
        for nombre in nombres:
            if not nombre.endswith(".py"):
                continue
            ruta = os.path.join(raiz, nombre)
            archivos += 1
            with open(ruta, encoding="utf-8") as f:
                arbol = ast.parse(f.read(), filename=ruta)
            auditor = Auditor(ruta)
            auditor.visit(arbol)
            hallazgos.extend(auditor.hallazgos)
    return archivos, hallazgos


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, "motor")
    archivos, hallazgos = auditar(carpeta)
    for archivo, linea, mensaje in hallazgos:
        print(f"{archivo}:{linea}: {mensaje}")
    if hallazgos:
        print(f"\n{len(hallazgos)} hallazgo(s) en {archivos} archivo(s).")
        return 1
    print(f"Auditoría limpia: {archivos} archivo(s) de motor/ sin construcciones prohibidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
