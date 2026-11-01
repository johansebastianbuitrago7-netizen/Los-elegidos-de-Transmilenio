# Pulso Urbano V2: horarios contextuales y laboratorio interactivo

Base del PR: **codex/desarrollo-integral-v1**, no main.
Head: **codex/pulso-urbano-v2**.

## Cambios para revisar

- Identidad de señalización urbana, portada editorial, menú móvil, explorador de
  estaciones, ranking de registros, administración diferenciada e itinerarios por tramo.
- Horarios estación→rutas dirigidas válidas→hora: diferencia, cinco eventos, recorrido
  y línea proporcional. Regresión real B10-1/PORTAL NORTE 09:25→11:33, 128 minutos.
- Laboratorio educativo con estados FIFO derivados del motor y controles completos.
- Laboratorio avanzado con semillas, tres presets, cuatro gráficas y A/B sobre las
  mismas llegadas, percentiles y respuesta masiva resumida descargable.
- Documentación de UX, horarios y simulación; ocho capturas reales.

## Validación ejecutada

34 pruebas unittest aprobadas, incluidas todas las V1, contrato de firmas intacto,
regresiones, duplicados, cierres, métricas comparadas con referencia y tamaño de payload.
Auditoría académica sin hallazgos. Chromium ejecutó los flujos y ocho pantallas en
cinco tamaños, sin errores JS ni desbordamiento horizontal. Experimento A/B de
300.000 pasajeros: todos atendidos, JSON resumido ~16 KB; detalles en VERIFICACION_V2.json.
Arranque probado con python app.py. Sin nuevas dependencias de aplicación.
CSV, PPTX y CI Ubuntu/Windows de V1 intactos. Windows no fue ejecutado en esta tarea.

## Límites y decisiones

Datos históricos, no predicciones ni certeza de abordaje en terminal. Escenarios
sintéticos, sin costos reales. Animación hasta 40 personas; motor público sin ese
límite. Análisis adicional de métricas O(N log N); series reducidas identificadas.
Máxima fila incluye llegadas antes del bus del mismo minuto. P95 usa rango próximo.
Persisten las limitaciones GTFS y de red circular documentadas en V1.
Uso local con estado compartido en memoria, sin autenticación ni persistencia.

## Ejecutar y revisar

python -m pip install -r requirements.txt
python app.py
python -m unittest discover -v
python herramientas/restricciones.py

QA opcional con Playwright/Chromium: node tests/navegador.cjs.
Revisar primero el ejemplo 09:25, la saturación de P6 al minuto 5 y A/B con semilla42.
No hacer merge automático. No modificar ni fusionar main desde este PR.
