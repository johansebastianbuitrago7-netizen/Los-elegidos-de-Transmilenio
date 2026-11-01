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

# Evolución implementada: Pulso Urbano V2

Rama `codex/pulso-urbano-v2`, basada en V1 `41ebb30` (no en main).
Contrato R1–R10 preservado, verificaciones automáticas de firmas incorporadas.
No se modificaron CSV, PPTX, algoritmos R5, simular_fila ni workflow de CI V1.

## Entrega V2

- Horarios con catálogo dependiente, sentido real, próximos cinco registros,
  diferencia definitiva en Python, escala proporcional y explicación histórica.
- Laboratorio educativo: cola visible, bus/cupos, fichas/estados escritos,
  anterior/siguiente/reproducir/pausar/reiniciar/velocidad; límite visual 40 personas.
- Laboratorio avanzado: presets sintéticos, semillas, hasta 300.000 personas,
  métricas y cuatro gráficas, A/B con la misma lista, diferencias y descarga resumen.
- Inicio, itinerario, estaciones, ranking, administración y R11 con identidad unificada.
- Tres guías nuevas, guías anteriores actualizadas, capturas y evidencia JSON.

## Evidencia V2

- **34 pruebas aprobadas**, cero fallos, errores u omitidas. Incluyen las 23 de V1.
- Auditoría AST sin posibles violaciones; nuevos cálculos de métricas en motor usan
  hash y ordenamiento propios. El análisis no vuelve a decidir abordajes.
- B10-1/PORTAL NORTE verificado contra CSV: 08:00→08:18, 08:18→08:18,
  09:25→11:33 (128 min), 11:33→11:33, 11:34→11:41.
- Caso educativo exacto: [0,0,5,5,5,10,10], esperas [0,0,4,3,0,5,1]; cola máxima4,
  tres buses, espera total13 y media13/7.
- Experimento A/B real de 300.000 personas: ambos atendieron a todos, respuesta
  serializada con json.dumps: 16.296 bytes JSON, aproximadamente 4,04 s observados en esta máquina. El formato HTTP compacto puede ocupar menos.
  Tiempo no garantizado en otros equipos. Registro en docs/VERIFICACION_V2.json.
- Chromium: selectores, resultados, hora exacta/vacío, itinerario con cambio,
  controles completos, descarga A/B, cierres/undo/redo, teclado y reduced motion.
- Ocho pantallas sin desbordamiento del documento en 1440/1024/768/390/320.
- Ocho capturas reales, inspeccionadas; se corrigieron el itinerario recortado,
  avisos tardíos tras navegar y una línea que mantenía indebidamente el valor de
  fila antes del bus. Ahora ese valor se muestra como punto instantáneo.
- Pares principales de contraste medidos: blanco/rojo5,60; papel/asfalto14,78;
  texto secundario/papel5,68; petróleo/superficie6,01. No certifica WCAG integral.
- `python app.py` arrancó en puerto5000; no requiere build ni nuevas dependencias.

## Límites V2

La animación deriva pasos pequeños O(N²), acotados a40; no se ejecuta para grandes.
Métricas adicionales O(N log N), independientes del benchmark de la función R10.
Series masivas muestreadas (~162 puntos) con métricas exactas previas; no se afirma
mostrar cada fluctuación. Demanda/oferta son intervalos sintéticos, no flota real.
No se validó con todos los lectores de pantalla ni se ejecutó Windows localmente.
Persisten las limitaciones de V1 enumeradas arriba.

## Demostración propuesta (cinco minutos)

1. Inicio: consultar una conexión y señalar datos históricos.
2. Horarios: PORTAL NORTE→B10-1→09:25; explicar 128 min y cinco registros.
3. Planeador: 21 ANGELES→AGUAS; sentido de tramos y cambio en HEROES.
4. Laboratorio educativo: avanzar al minuto5, ver P6 esperando; retroceder y reproducir.
5. Comparador: intensa, semilla42, frecuencia5 vs3, cupos30; métricas y gráficas A/B.
6. Rendimiento: medir y distinguir referencia, tiempos y carga. Revisar las guías.
