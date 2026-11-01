# Estado verificable de la primera versión integral

Base: main `5ba5f11abbe0325ec00eaf105b3e2110f2575c04`.
Rama: `codex/desarrollo-integral-v1`. Sin merge a main.

## Implementación

| Requisito | Estado y evidencia |
|---|---|
| R1 | Hash propio, estado exacto; tests estado/cierres |
| R2 | Prefijos y límite binario; tests de vacío, cerrado, límite |
| R3 | Rango inclusivo; tests límites ausentes/invertidos/iguales |
| R4 | Hash anidado, minutos ordenados y búsqueda binaria; tests duplicados y >24h |
| R5 | Menos enlaces, directo/un transbordo, dirigido; oráculo 0-1 BFS y datos reales |
| R6 | Conteos activos y caché ordenada; pruebas de edición/cierre |
| R7 | Lista doble + índices; 200 ediciones/historial contra referencia |
| R8 | Estado reversible; exclusión de extremos, transbordo y consultas operativas |
| R9 | Dos pilas, no-op/errores sin historial; extremos vacíos/restauración |
| R10 | Cola FIFO y ordenación estable opcional; 100 referencias y 200.000 pasajeros |
| R11 | Panel con 13 operaciones distintas, 4 tamaños, muestras y curvas interactivas |
| R12 | Tabla de decisiones/costos y suposiciones en README; guías de sustentación |

Motor sin Flask ni dependencias externas. Front conectado a API real: Inicio,
Estaciones, Planeador, Horarios, Ranking, Administración, Simulador y Rendimiento.
Conversor GTFS probado con ZIP sintético; tres CSV originales intactos.
Transcripción de las 16 diapositivas y notas guardada en docs/ESPECIFICACION_EXTRAIDA.md.

## Validación realizada

- `python -m unittest discover -v`: **23 pruebas aprobadas**, sin fallos ni omitidas.
- `python herramientas/restricciones.py`: sin posibles violaciones detectadas;
  revisión manual de imports, ordenamientos y estructuras del motor realizada.
- `node --check static/js/app.js`: correcto.
- Flask arrancó realmente con `python app.py`; Chromium consumió las API vía HTTP.
- `node tests/navegador.cjs`: navegación, consultas, viaje, horarios, ranking,
  cierre/deshacer, simulación, rendimiento y vista móvil; sin errores JS.
- Capturas locales revisadas; la prueba comprueba ausencia de desbordamiento móvil.
- `docs/rendimiento_ejecutado.json`: **52 observaciones agregadas** de 13 operaciones
  × 4 tamaños (64,128,256,512), cada una con siete muestras reales y carga separada.
- `git diff --check`: sin errores de espacios. CSV/PPTX originales sin cambios.

Entorno verificado: Python 3.12 y Flask 3.1.2. requirements fija dependencias exactas.
No se ejecutó Windows; sus comandos usan rutas portables y están documentados.

## Limitaciones explícitas

1. No existe otro enunciado que defina retornos, aunque la diapositiva 10 lo menciona.
   Se documentaron decisiones locales, no compatibilidad con evaluadores desconocidos.
2. R1 diagnostica cerradas por exigencia de existencia/estado; la búsqueda operativa
   las excluye. Interpretación de la tensión R1/R8 documentada.
3. No se suministró el ZIP GTFS de 2021. Conversor sin validación con ese original.
   No expande frequencies, interpola horas faltantes ni filtra calendario diario.
4. Motor/conversor rechazan estaciones repetidas dentro de un patrón de ruta;
   las redes circulares y nombres colapsados requieren ampliación explícita.
5. R5 optimiza enlaces, no duración ni sincronización de transbordos.
6. Ediciones de la web solo en memoria y compartidas por sesión del servidor.
   No hay autenticación, DB ni persistencia. Uso local de demostración.
7. El panel es un experimento reproducible de una familia, no un benchmark completo
   de todas las distribuciones; h es fijo en R4, ranking mide caché caliente.
8. integrantes.md es plantilla; no se inventan autores ni aportes académicos.

## Continuación y revisión recomendada

El equipo debe revisar primero retornos y política de servicio/horarios, reproducir
las pruebas y resolver ejercicios de las guías. Completar integrantes.md con aportes
reales. Para una red circular futura, definir ocurrencia de parada en las firmas de
edición y horarios antes de cambiar índices. Otra instancia debe trabajar en una
rama de revisión, no sobrescribir esta ni fusionarla sin aprobación.

La publicación en GitHub se informa en el mensaje final según resultado real del
push y creación de PR. La configuración/snapshot del entorno cloud no se publica
desde esta tarea. Los procesos locales no son una entrega persistente.

## Publicación observada

La rama `codex/desarrollo-integral-v1` se subió correctamente a origin.
La creación automática del PR quedó bloqueada: tanto GraphQL (`gh pr create`)
como REST de `api.github.com` respondieron `Forbidden` en este entorno. Esto no
impidió el push Git. No se solicita ni se copia ningún token para evitarlo.
El texto listo para revisión quedó en `docs/SOLICITUD_REVISION.md`.
Puede crearse el PR manualmente desde:
https://github.com/johansebastianbuitrago7-netizen/Los-elegidos-de-Transmilenio/compare/main...codex/desarrollo-integral-v1

Se añadió workflow de GitHub Actions para Ubuntu/Windows y Python 3.10/3.12.
Es una configuración preparada, no evidencia de que esos trabajos remotos hayan
terminado ni de que Windows ya haya sido validado. La validación observada en esta
tarea corresponde a Linux/Python 3.12.
