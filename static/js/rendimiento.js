/* Lámina 07: R11. Grafica mediciones reales frente a la curva esperada. */
"use strict";

(() => {
  const { $, el, vaciar, api, num, mensaje, registrar, conCarga } = Atlas;

  const unidad = (seg) => seg >= 1 ? `${num(seg, 2)} s` : seg >= 1e-3 ? `${num(seg * 1e3, 2)} ms` : `${num(seg * 1e6, 1)} µs`;
  const clasesVeredicto = { "coincide": "coincide", "ruido o efecto de caché": "ruido", "crece más de lo esperado": "mal" };

  const EXPLICACIONES = {
    estado: "Tabla hash: el costo no depende de cuántas estaciones haya. Pequeñas subidas vienen de la caché del procesador al crecer la tabla.",
    autocompletar: "Búsqueda binaria del prefijo y luego k pasos. Duplicar n solo agrega una comparación a la búsqueda.",
    rango: "Búsqueda binaria del inicio y recorrido de los m resultados (fijo en 20).",
    proximo_bus: "Búsqueda binaria entre los m eventos de la pareja; en la red sintética m crece con n en la troncal.",
    viaje: "R5 no se evalúa en rendimiento (lo dice el enunciado). Depende del largo y número de rutas que tocan origen y destino.",
    ranking: "Consulta sobre el arreglo ordenado en caché: solo copia k elementos.",
    ranking_tras_cambio: "Cerrar invalida la caché; la siguiente consulta reordena con merge sort.",
    editar: "Tabla hash ubica el nodo; la lista doble enlaza o desenlaza en O(1).",
    recorrido: "Recorre la lista doble de una ruta de largo fijo: no depende de n.",
    cerrar: "Cambiar una bandera y apilar la operación.",
    deshacer: "Desapilar, aplicar la inversa y apilar en la otra pila.",
    fila: "Merge sort de las llegadas + una pasada con la cola FIFO.",
    carga: "Leer los CSV, ordenar nombres y horarios por pareja. N = filas leídas.",
  };

  function tarjeta(op) {
    const xs = op.puntos.map((p) => p.n);
    const series = [{ valores: op.puntos.map((p) => p.mediana), xs, clase: "serie--a", puntos: true }];
    if (op.teoria) series.unshift({ valores: op.teoria, xs, clase: "serie--teoria" });
    const svg = Graficos.lineas(series, { alto: 190, ancho: 380, xLog: true, marcasX: xs, formatoY: (v) => unidad(v).replace(" ", ""),
      formatoX: Graficos.corto, etiquetaX: op.clave === "carga" ? "N (log₂)" : "n (log₂)", titulo: `Tiempo de ${op.clave}` });
    const clase = clasesVeredicto[op.veredicto] || "neutro";
    return el("figure", { class: "grafico", style: "margin:0" },
      el("header", {}, el("div", {}, el("h3", {}, `${op.requisito} · ${op.clave.replace(/_/g, " ")}`),
        el("p", {}, `Esperada ${op.esperada} · ${op.n}`)), el("span", { class: `veredicto veredicto--${clase}`, text: op.veredicto })),
      svg,
      el("div", { class: "razones" }, `t(2n)/t(n) observada: ${op.razones.map((r) => r.observada ? r.observada.toFixed(2) : "—").join(" · ")}`,
        op.razones[0] && op.razones[0].esperada ? el("br") : null,
        op.razones[0] && op.razones[0].esperada ? `esperada: ${op.razones.map((r) => r.esperada.toFixed(2)).join(" · ")}` : null),
      el("p", { style: "margin-top:6px", text: EXPLICACIONES[op.clave] || "" }),
      el("details", {}, el("summary", { class: "pie", text: "Datos medidos" }),
        el("table", { class: "tabla" }, el("thead", {}, el("tr", {}, ["n", "mediana", "mín", "máx"].map((t) => el("th", { text: t })))),
          el("tbody", {}, op.puntos.map((p) => el("tr", {}, el("td", { text: num(p.n) }), el("td", { text: unidad(p.mediana) }),
            el("td", { text: unidad(p.minimo) }), el("td", { text: unidad(p.maximo) })))))));
  }

  function pintar(r) {
    vaciar($("[data-rendimiento]"),
      el("div", { class: "mensaje mensaje--info" }, el("strong", { text: `Medición del ${r.generado}` }),
        el("span", { text: ` Tamaños n = ${r.tamanos.map((n) => num(n)).join(", ")} estaciones · ${r.repeticiones} repeticiones por punto (se grafica la mediana). Línea punteada: curva teórica anclada al primer punto; línea continua: tiempo medido en esta máquina.` })),
      el("div", { class: "leyenda", style: "margin-top:10px" },
        el("span", {}, el("i", { style: "background:var(--cerro)" }), "medido (mediana por operación)"),
        el("span", {}, el("i", { style: "background:var(--tinta-3)" }), "teoría esperada")),
      el("div", { class: "rend" }, r.operaciones.map(tarjeta)));
  }

  async function medir(boton) {
    const destino = $("[data-rendimiento]");
    try {
      vaciar(destino, mensaje("info", "Midiendo…", "Generando redes sintéticas y cronometrando. Puede tardar entre 5 y 40 segundos."));
      pintar(await conCarga(boton, () => api("/api/rendimiento", { metodo: "POST",
        cuerpo: { maximo: Number($("#ren-max").value), repeticiones: Number($("#ren-rep").value) } })));
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo medir", error.message));
    }
  }

  function iniciar() {
    $("[data-accion='rendimiento']").addEventListener("submit", (e) => { e.preventDefault(); medir(e.submitter); });
  }

  async function mostrar() {
    const ultimo = await api("/api/rendimiento").catch(() => null);
    if (ultimo) pintar(ultimo);
    else if (!$("[data-rendimiento]").children.length) {
      vaciar($("[data-rendimiento]"), mensaje("info", "Aún no hay mediciones en esta sesión", "Pulsa «Medir ahora»: los resultados son de tu máquina, no valores precargados."));
    }
  }

  registrar("rendimiento", { iniciar, mostrar });
})();
