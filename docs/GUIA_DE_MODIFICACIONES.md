# Cambios pequeños y sustentación práctica

## Rutina segura

1. `git status` y crear rama propia desde la versión revisada. No editar main.
2. Definir un ejemplo con respuesta conocida y escribir prueba en tests/.
3. Implementar la regla en motor/, respetando AGENTS.md y el contrato público.
4. Revisar índices, conteos, cachés y operación inversa si se modifica estado.
5. Ejecutar unittest y auditoría; luego probar API y vista afectada.
6. Actualizar decisiones y hacer commit que explique el comportamiento resultante.

Trabajar en el checkout existente de la tarea cloud; no hacen falta worktrees.
No tocar CSV para hacer pasar una prueba. El fixture se escribe en TemporaryDirectory.

## Agregar una consulta

Ejemplo de práctica: listar rutas de una estación. Implementar un método adicional
en Red que lea `self._estacion(nombre).rutas.elementos()`, filtre si se requiere
abierta y ordene con `ordenar`. Complejidad O(d log d), d rutas de esa estación.
No cambiar las firmas obligatorias; un método nuevo no rompe el contrato existente.
Agregar prueba de estación con dos rutas y una inexistente. El retorno debe ser
un arreglo, no un dict dentro del motor.

## Cambiar el ranking

El criterio está en la función clave de `ranking`: (-cantidad,nombre). Si se desea
otro criterio, definir primero cómo resolver empates. Si solo cambia el orden, ajustar
esa clave y sus tests. Si cambia qué cuenta como evento, revisar carga y _insertar/
_quitar juntos, además de deshacer/rehacer. Un cambio solo en el gráfico sería un
error: el ranking debe ser el del motor. Invalidar caché cuando cambie información
que determine su clave.

## Extender una estructura

Para añadir `contiene` a TablaHash, reutilizar `obtener` con un objeto centinela si
los valores pueden ser None; no confundir None con ausencia. Escribir prueba con
colisiones, clave actualizada, borrado y redimensionamiento. Para cambiar ListaDoble,
comprobar extremos vacíos, único nodo y recorrido inverso. No sustituir silenciosamente
la implementación por dict o collections.

## Añadir un endpoint

En `app.py`, registrar firma en `consultas` si se trata de una operación simple.
Los nombres deben coincidir exactamente con argumentos del método. Adaptar validación
de tipos, serializador si hay un nuevo objeto y tests Web. Si muta estado, incluirlo
en `cambios`, proteger con el candado y decidir su historial. No exponer getattr sin
lista de operaciones permitidas ni permitir al usuario acceder a métodos internos.

Ejemplo HTTP actual:

```json
{"operacion":"viaje","argumentos":{"origen":"A","destino":"E"}}
```

La API responde `{"resultado": ...}` o `{"error": ...}` con HTTP 400 para entradas
inválidas. No mezclar la estructura JSON con los retornos Python del profesor.

## Modificar la interfaz

`templates/index.html` define el marco. `static/js/app.js` contiene las secciones,
formularios y representación; `static/css/app.css` define superficies y responsive.
Usar `esc` al insertar texto variable en HTML, etiquetas para todos los campos y
mensajes visibles de error/carga. Formularios deben invocar el motor a través de API.
No introducir coordenadas ficticias: el itinerario es esquemático. Los datalist de
consultas excluyen cerradas; administración tiene lista completa para reabrirlas.

Después de cambiar UI: `node --check static/js/app.js`, arrancar Flask, probar teclado
y móvil. La prueba opcional `tests/navegador.cjs` usa Playwright; configurar Chromium
mediante CHROMIUM_PATH si no está en /usr/bin/chromium. No instalar Node para ejecutar
la aplicación Python: solo es herramienta opcional de QA.

## Agregar pruebas

Reutilizar `escribir` para generar una red alternativa. No depender del orden del
archivo: invertir las filas de rutas/horarios. Incluir positivo, vacío, inválido y
cambio reversible. Un error debe dejar el estado e historial anteriores intactos.
Para R5, ampliar el oráculo 0-1 BFS antes de optimizar; comparar enlaces y probar
sentidos y cambios en estaciones cerradas. Una implementación de referencia puede
usar librerías estándar y dict en tests, nunca en motor/.

## Preparar una modificación de 45 minutos

No se conoce el requisito sorpresa. Practicar esta secuencia: cinco minutos para
leer/definir retorno y ejemplo; diez para prueba y diseño; quince para implementación;
diez para integración/regresión; cinco para explicar complejidad y registrar commit.
Es una propuesta de organización, no una instrucción del profesor.

Ejercicios propuestos por el equipo:
- Consulta adicional de rutas por estación sin alterar la API obligatoria.
- Criterio alternativo de desempate documentado en ranking.
- Mostrar primera y última salida de una pareja usando el índice ordenado existente.
- Detectar una edición fallida sin borrar rehacer.
- Añadir a la gráfica otra familia de tamaños de horarios h con estaciones S fijas.

## Revisión por otra instancia de Codex

Crear una rama de revisión distinta, leer AGENTS.md y ESTADO_PROYECTO.md, instalar
requirements y ejecutar las pruebas independientemente. Revisar principalmente
suposiciones de retorno y limitaciones GTFS. Proponer PR acotado; no simular autores
y no fusionar cambios sin autorización del grupo. Repartir módulos (motor, UI,
conversión, pruebas/docs) evita editar todos el mismo archivo.

## V2: puntos de extensión concretos

- Para cambiar un preset, editar servicios/laboratorio.py (distribución) y los valores
  iniciales del formulario en laboratorio.js; mantener semilla y misma lista A/B.
- Para añadir una métrica, calcularla en motor/analisis_fila.py con estructuras
  permitidas, probar contra una referencia y serializarla en el servicio. No volver
  a implementar FIFO para obtenerla. Actualizar definiciones y unidades en la guía.
- Para cambiar los pasos visuales, editar pasos() del servicio. Los IDs deben seguir
  representando posiciones del arreglo original y respetar resultado.abordajes.
- Para ampliar horarios, mantener proximo_bus intacto y extender consultas auxiliares
  sobre _horas y limite; probar cierres y edición de rutas junto con los casos reales.
- Para cambiar la escena o controles, usar laboratorio.js; componentes.js centraliza
  indicadores/gráficas. producto.js tiene portada e itinerario; horarios.js la consulta.
- QA visual: `node tests/navegador_v2.cjs` con servidor activo. `APP_URL` permite puerto
  alternativo y CHROMIUM_PATH selecciona el ejecutable de Chromium. La prueba regenera
  docs/capturas-v2, así que revisar sus cambios antes de hacer commit.
