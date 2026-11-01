## Resultado

Implementa una primera versión integral del Planeador TransMilenio sobre los tres CSV suministrados: estaciones, horarios programados históricos, viajes dirigidos con máximo un transbordo, ranking, edición de rutas, cierres, historial reversible y simulación FIFO. Incluye ocho vistas responsive y un panel de rendimiento con mediciones reales.

## Arquitectura y decisiones

- Motor Python independiente de Flask con hash, lista doble, pilas, cola, mergesort y búsqueda binaria propios; contrato público preservado.
- Adaptador Flask/JSON y frontend HTML/CSS/JS sin algoritmos de dominio duplicados.
- Conversor GTFS independiente con pruebas sintéticas; datos originales sin cambios.
- README R12, transcripción de 16 diapositivas/notas, guías de comprensión/modificación, AGENTS y estado verificable.

## Validación ejecutada

- 23 pruebas unittest aprobadas, sin omitidas: redes alternativas, CSV reales, 588 comparaciones de viajes contra oráculo 0-1 BFS, 200 ediciones reversibles, 100 referencias FIFO y simulación de 200.000 pasajeros, conversión, API y rendimiento.
- Auditor AST sin posibles violaciones; revisión manual del motor.
- Arranque Flask real y prueba Chromium: navegación, consultas, viaje, horarios, ranking, cierre/deshacer, simulación, rendimiento y móvil, sin errores JS ni desbordamiento móvil.
- 52 observaciones de rendimiento guardadas, cada una con siete muestras; carga separada de consultas, R5 excluido.

## Ejecutar

Python >=3.10 (verificado en 3.12):

```bash
python -m pip install -r requirements.txt
python app.py
python -m unittest discover -v
python herramientas/restricciones.py
```

Se recomienda virtualenv; instrucciones para Windows en README.

## Revisar antes de aprobar

- Retornos adoptados y tensión R1/R8: no se suministró el enunciado adicional mencionado por la presentación.
- Criterio de enlaces/desempate de R5; horarios no sincronizan transbordos.
- Ediciones compartidas en memoria, uso local sin autenticación ni persistencia.
- Motor exige estaciones únicas por ruta; patrones circulares requieren ampliación.
- Conversor probado con ZIP sintético; sin ZIP histórico original, expansión frequencies, interpolación ni filtrado diario de calendario.
- Panel usa h fijo y ranking caliente; no pretende medir todos los peores casos.
- integrantes.md debe completarse con aportes reales; no se inventaron contribuciones de estudiantes.

No fusionar automáticamente. No se publicó ni cambió la configuración del entorno cloud.
