"""Revisa motor/ con ast: imports y llamadas prohibidas (R: reglas del motor)."""
import ast
import os
import sys

IMPORTS_OK = {"csv", "time", "random"}
LLAMADAS_NO = {"sorted", "min", "max", "sort", "index", "count"}
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "motor")
errores = 0
for nombre in os.listdir(base):
    if not nombre.endswith(".py"):
        continue
    arbol = ast.parse(open(os.path.join(base, nombre), encoding="utf-8").read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for a in nodo.names:
                if a.name.split(".")[0] not in IMPORTS_OK:
                    print(nombre, nodo.lineno, "import prohibido:", a.name)
                    errores += 1
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0 and nodo.module.split(".")[0] not in IMPORTS_OK:
                print(nombre, nodo.lineno, "import prohibido:", nodo.module)
                errores += 1
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            n = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if n in LLAMADAS_NO:
                print(nombre, nodo.lineno, "llamada prohibida:", n)
                errores += 1
        elif isinstance(nodo, ast.Compare):
            for op, der in zip(nodo.ops, nodo.comparators):
                if isinstance(op, (ast.In, ast.NotIn)):
                    print(nombre, nodo.lineno, "REVISAR 'in':", ast.unparse(nodo))
print("OK" if errores == 0 else "ERRORES: %d" % errores)
sys.exit(1 if errores else 0)
