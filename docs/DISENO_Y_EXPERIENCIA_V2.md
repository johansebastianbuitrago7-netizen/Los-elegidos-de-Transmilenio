# Pulso Urbano: diseño y experiencia implementados

## Concepto y problemas resueltos

Señalización, tablero de estación y trazos de recorrido inspiran la composición.
La V1 tenía formularios independientes, un resultado de horario sin contexto y
una tabla FIFO que no mostraba por qué alguien quedaba esperando. La V2 conserva
las operaciones y hace visibles selección, sentido, diferencia y decisiones.

Inicio usa una portada editorial con consulta de viaje integrada y un tablero
oscuro de conexiones. Las estadísticas forman una franja, no otra cuadrícula de
tarjetas. El diagrama original está rotulado como esquemático, sin coordenadas.
No se usan logos oficiales ni se depende de fuentes, imágenes o CDNs remotos.

## Tokens reales

En :root de static/css/app.css: asfalto #14232B, papel #F7F5F1, superficie #FFFEFA,
rojo #C9203A (ligeramente más oscuro que la propuesta para contraste), infraestructura
#D6DADD, petróleo #196D70, ámbar #E8AD4F. El rojo identifica acción y próximo evento;
el petróleo estructura explicaciones y análisis; ámbar señala operación o advertencia.
Los estados tienen texto además de color. La tipografía es system-ui para lectura y
ui-monospace/Consolas para señalización, horas, códigos y cifras tabulares.
No se requiere instalar una fuente para comprender la interfaz.

## Componentes y módulos

- componentes.js: escape de texto, cifras, indicadores, gráficos SVG y barras.
- producto.js: portada e itinerario por tramos, origen/cambio/destino.
- horarios.js: selector dependiente, tablero, escala y lista cronológica.
- laboratorio.js: modos, controles, escena, métricas y comparador.
- app.js: navegación y formularios conservados de V1, administración y benchmark.

No hay framework, empaquetador ni dependencia nueva en requirements. Los scripts
locales se cargan defer en orden. Prettier se usó como herramienta temporal para
formatear JS/CSS legibles; no es requisito para instalar ni ejecutar la aplicación.

## Horarios

Estación→rutas válidas→hora→resultado. Servicios deshabilitados hasta confirmar la
estación; cada etiqueta explica sus extremos reales. El tablero contrasta consulta
y próximo registro con cifras grandes. El hueco de 128 min se muestra explícitamente
y ocupa espacio proporcional en la escala. No se afirma una espera operativa actual.
Los eventos repetidos pueden superponerse en SVG; todos permanecen en la lista.

## Laboratorio

Modo educativo con escena, FRENTE/FINAL, fichas Pn y estados escritos; pasos y reloj
son navegación sobre un resultado estable. El bus es un diagrama, no una animación
que asigne pasajeros por su cuenta. El modo avanzado compara cifras lado a lado,
permite explorar gráficas A/B y descarga un resumen reproducible. Una nota identifica
si la serie está reducida; los percentiles siempre usan todos los pasajeros.

## Resto del producto

Estaciones reúne las tres operaciones en una superficie de exploración. Ranking
conserva barras proporcionales e identifica registros, no demanda u ocupación real.
Administración tiene una banda de advertencia, confirmaciones y el historial con
controles reales. Los cambios son compartidos y solo en memoria. Rendimiento mantiene
las trece operaciones, muestras, referencia teórica y costo de carga separados.
El itinerario separa tramos y sentido, destaca el cambio y cuenta enlaces, no minutos.

## Accesibilidad y adaptación

Etiquetas explícitas, skip link, navegación actual con aria-current y foco visible.
Selectores anuncian disponibilidad; las respuestas usan aria-live y carga usa aria-busy.
Los formularios relacionan campos y resultados/errores con aria-describedby. Gráficas
incluyen valores enfocables y detalles/tablas textuales. Reproducción es optativa y
se detiene al salir de la sección. prefers-reduced-motion elimina transiciones.
En móvil la navegación se abre con un botón aria-expanded; no es una tira que exige
arrastrar un escritorio comprimido. Controles principales tienen al menos 44 px.

Breakpoints reorganizan portada, formulario/resultado, métricas y A/B. Se comprueban
1440,1024,768,390,320 en ocho pantallas; las tablas tienen scroll interno cuando su
estructura lo necesita. Esto no equivale a una certificación completa WCAG ni prueba
con todos los lectores de pantalla. El color de las barras <meter> puede depender
del navegador, manteniendo cifras y etiquetas como soporte.

## Cómo cambiar estilos

Modificar primero tokens :root, después el componente, al final media queries.
Mantener foco y estados no cromáticos. Probar contenido largo, vista móvil y
prefers-reduced-motion. No transformar una línea proporcional en puntos equidistantes
sin cambiar su explicación. Los selectores CSS conservan nombres de módulos legibles.

## Evidencia

Capturas reales del servidor en docs/capturas-v2; el índice describe cada escenario.
No son imágenes generadas ni mockups. Ver pruebas/navegador en tests/navegador_v2.cjs
para reproducir flujos, capturas y detección de desbordamiento.
