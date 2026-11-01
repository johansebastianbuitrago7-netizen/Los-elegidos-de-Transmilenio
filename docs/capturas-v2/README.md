# Capturas reales · Pulso Urbano V2

Generadas con Chromium sobre el servidor Flask ejecutado en este entorno. No son
maquetas ni imágenes generadas. Se inspeccionaron visualmente para ajustar flujo,
contraste, espacio, recortes e interacción. Las de escritorio usan 1440×1000 de
viewport y las móviles 390×900; la captura completa puede tener mayor altura.
El lateral fijo ocupa el alto del viewport, no toda la altura de la página.

| Captura | Escenario |
|---|---|
| [01 · Inicio escritorio](01-inicio-escritorio.png) | Portada y acceso directo al planeador |
| [02 · Horarios](02-horarios-b10.png) | B10-1, PORTAL NORTE, 09:25→11:33, 128 min |
| [03 · Viaje con cambio](03-viaje-transbordo.png) | 21 ANGELES→AGUAS, cambio en HEROES |
| [04 · Fila saturada](04-simulador-saturacion.png) | Minuto 5: abordan P3/P4/P5 y espera P6 |
| [05 · A/B](05-comparador-ab.png) | 1500 llegadas sintéticas, semilla 42, 5 vs 3 min, 30 cupos |
| [06 · Rendimiento](06-rendimiento.png) | Ejecución real de R11, serie simular_fila |
| [07 · Inicio móvil](07-inicio-movil.png) | Menú desplegable y composición vertical |
| [08 · Laboratorio móvil](08-simulador-movil.png) | Escenario educativo, controles, métricas y gráficos |

Reproducir con Flask activo: `node tests/navegador.cjs`. Requiere Playwright y
Chromium; variables APP_URL y CHROMIUM_PATH permiten seleccionar servidor/binario.
La prueba además recorre ocho pantallas en 1440,1024,768,390,320 y verifica que no
exista desbordamiento horizontal del documento. Tablas y listas pueden usar scroll
interno expresamente para conservar legibilidad. Esto no es una auditoría completa
de todos los lectores de pantalla o dispositivos del mercado.
