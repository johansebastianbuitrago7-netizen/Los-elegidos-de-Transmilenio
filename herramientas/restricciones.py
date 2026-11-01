"""Auditor AST conservador. Toda pertenencia se marca para revisión manual."""
import ast
from pathlib import Path

PROHIBIDAS = {'dict', 'set', 'sorted', 'min', 'max', 'DictReader'}
MODULOS = {'csv', 'time', 'random'}


def auditar(carpeta):
    errores = []
    for archivo in Path(carpeta).glob('*.py'):
        for n in ast.walk(ast.parse(archivo.read_text(encoding='utf8'))):
            motivo = None
            if isinstance(n, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)):
                motivo = 'diccionario/conjunto'
            elif isinstance(n, ast.Call):
                nombre = n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else ''
                if nombre in PROHIBIDAS or nombre in {'sort', 'index', 'count'}:
                    motivo = 'llamada prohibida: ' + nombre
            elif isinstance(n, ast.Compare) and any(isinstance(x, (ast.In, ast.NotIn)) for x in n.ops):
                motivo = 'pertenencia: revisar tipo manualmente'
            elif isinstance(n, ast.Import):
                if any(a.name not in MODULOS for a in n.names):
                    motivo = 'importación no permitida'
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module not in MODULOS:
                motivo = 'importación no permitida'
            if motivo:
                errores.append(f'{archivo}:{n.lineno}: {motivo}')
    return errores

if __name__ == '__main__':
    errores = auditar(Path(__file__).resolve().parents[1] / 'motor')
    print('\n'.join(errores) if errores else 'Sin posibles violaciones académicas')
    raise SystemExit(bool(errores))
