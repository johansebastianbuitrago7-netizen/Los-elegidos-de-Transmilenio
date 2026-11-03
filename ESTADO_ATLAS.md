# Estado de Atlas

Rama: `claude/atlas-independiente-v1`, creada desde `main` (5ba5f11). No toca `main` ni las ramas
`codex/*`. No se copió código ni documentación de las ramas de Codex.

## Requisitos

| Req. | Implementado | Probado | Evidencia |
|---|---|---|---|
| R1 | Sí | Sí | `tests/test_red.py`, `test_datos_reales.py`, lámina 01 |
| R2 | Sí | Sí (contra `sorted`) | combobox de toda la app usa R2 |
| R3 | Sí | Sí | lámina 01 |
| R4 | Sí | Sí (contra el CSV) | B10-1 · PORTAL NORTE · 09:25 → 11:33, lámina 02 |
| R5 | Sí | Sí (fuerza bruta + 0-1 BFS, >8.000 pares sintéticos, 400 reales) | lámina 03 |
| R6 | Sí | Sí (contra `Counter`) | láminas 00 y 04 |
| R7 | Sí | Sí | lámina 05 |
| R8 | Sí | Sí | lámina 05 |
| R9 | Sí | Sí | lámina 05 (pilas visibles) |
| R10 | Sí | Sí (contra simulación directa, 300.000 pasajeros) | lámina 06 |
| R11 | Sí | Medido | lámina 07, `docs/RENDIMIENTO_MEDIDO.md` |
| R12 | Sí | — | `README.md`, `docs/GUIA_SUSTENTACION.md` |
| Conversión GTFS | Sí | Solo con GTFS sintético | `conversion/gtfs_a_csv.py`, `tests/test_conversion.py` |

## Pruebas ejecutadas (3 de noviembre de 2026)

- `python -m unittest discover`: 60 pruebas, todas OK (Python 3.13, Flask 3.1).
- `python herramientas/restricciones.py`: auditoría limpia (7 archivos de `motor/`).
- `python herramientas/medir.py 4000 5`: todas las operaciones evaluadas "coinciden".
- Navegador (panel integrado de la app de escritorio): portada, estaciones, horarios, viaje
  directo y con transbordo, laboratorio educativo paso a paso, escenario masivo, A/B, operación
  (agregar, cerrar, deshacer), rendimiento; 375 px sin desplazamiento horizontal; modo claro y
  oscuro. Capturas en `docs/capturas/` (Edge sin interfaz).

## Problemas detectados y corregidos

- Paréntesis sobrante en `rendimiento.js` (error de sintaxis).
- Choque de atributos `data-ab` entre la tabla educativa y el panel A/B.
- Selector de ruta de la portada desbordaba a 375 px.
- Plantillas en caché del servidor: reiniciar `app.py` tras cambiar HTML.

## Pendiente / decisiones del grupo

- Completar `integrantes.md` (no se inventaron aportes).
- Probar `conversion/gtfs_a_csv.py` con el GTFS real (no está en el repositorio).
- Las fuentes se cargan de Google Fonts; sin internet se usan fuentes del sistema.
- No hay prueba automática de navegador (no hay Node/Playwright en esta máquina); la
  verificación visual fue manual con el navegador integrado.
- El ZIP `los-elegidos-claude-parcial.zip` no estaba disponible; no se usó. En Descargas existe
  `proyecto_transmilenio.zip`, que no se revisó ni se usó.

## Próxima tarea sugerida

Revisión humana del PR, completar `integrantes.md` y ensayar la sustentación con
`docs/GUIA_SUSTENTACION.md`.
