"""Mide el rendimiento por consola y guarda el informe en docs/.

Uso:  python herramientas/medir.py [tamaño_máximo] [repeticiones]
Genera docs/RENDIMIENTO_MEDIDO.md y docs/rendimiento.json con los tiempos
observados en la máquina donde se ejecuta (no son valores inventados).
"""

import json
import os
import platform
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from servicios.rendimiento import medir  # noqa: E402


def micro(seg):
    return f"{seg * 1e6:,.1f} µs" if seg < 1e-2 else f"{seg * 1e3:,.1f} ms"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    maximo = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    repeticiones = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    tamanos = []
    n = 250
    while n <= maximo:
        tamanos.append(n)
        n *= 2
    informe = medir(tuple(tamanos), repeticiones)
    lineas = [
        "# Rendimiento medido (R11)",
        "",
        f"Generado el {informe['generado']} con `python herramientas/medir.py {maximo} {repeticiones}` "
        f"en {platform.system()} / Python {platform.python_version()} ({platform.processor() or 'CPU no reportada'}).",
        "Mediana de las repeticiones; cada repetición cronometra un lote de llamadas. "
        "Razón = t(2n)/t(n) observada (esperada).",
        "",
        "| Req. | Operación | Esperada | " + " | ".join(f"n={p}" for p in tamanos) + " | Razones | Veredicto |",
        "|---|---|---|" + "---|" * len(tamanos) + "---|---|",
    ]
    for op in informe["operaciones"]:
        tiempos = " | ".join(micro(p["mediana"]) for p in op["puntos"])
        razones = ", ".join(
            f"{r['observada']:.2f}" + (f" ({r['esperada']:.2f})" if r.get("esperada") else "") for r in op["razones"])
        lineas.append(f"| {op['requisito']} | {op['clave']} | {op['esperada']} | {tiempos} | {razones} | {op['veredicto']} |")
    lineas += ["", "Para la carga, n es el número de filas leídas (N), no de estaciones; "
               "para R10, p = 40·n pasajeros. R5 no se evalúa en rendimiento según el enunciado.", ""]
    with open(os.path.join(BASE, "docs", "RENDIMIENTO_MEDIDO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    with open(os.path.join(BASE, "docs", "rendimiento.json"), "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=1)
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
