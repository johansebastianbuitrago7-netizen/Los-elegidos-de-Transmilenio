/* Lámina 01: R1 (ficha), R2 (autocompletar) y R3 (índice por rango). */
"use strict";

(() => {
  const { $, el, vaciar, api, qs, num, sello, codigoRuta, mensaje, combobox, registrar, tomar, conCarga, ir } = Atlas;

  async function consultar(nombre, boton) {
    const destino = $("[data-ficha]");
    if (!nombre.trim()) { vaciar(destino, mensaje("error", "Falta el nombre", "Escribe una estación para consultarla.")); return; }
    try {
      const f = await conCarga(boton, () => api(`/api/estado?${qs({ nombre })}`));
      $("#est-nombre").value = f.nombre;
      if (f.estado === "inexistente") {
        vaciar(destino, el("div", { class: "ficha" },
          el("div", { class: "ficha__cabeza" }, el("p", { class: "ficha__nombre", text: f.nombre }), sello(f.estado)),
          el("p", { text: "No hay una estación con ese nombre exacto." }),
          f.sugerencias.length ? el("div", {}, el("p", { class: "rotulo", text: "¿Quisiste decir?" }),
            el("div", { class: "chips" }, f.sugerencias.map((s) => el("button", { type: "button", class: "chip", text: s, onclick: () => consultar(s) })))) : null));
        return;
      }
      vaciar(destino, el("div", { class: "ficha" },
        el("div", { class: "ficha__cabeza" }, el("h3", { class: "ficha__nombre", text: f.nombre }), sello(f.estado)),
        el("p", { class: "ficha__dato" }, `${num(f.buses)} registros de paso al día · ${f.rutas.length} rutas`),
        f.estado === "cerrada" ? mensaje("error", "Estación cerrada", "No aparece en búsquedas, rangos ni ranking, y nadie sube, baja ni transborda aquí.") : null,
        el("ul", { class: "lista-rutas", "aria-label": "Rutas que paran aquí" }, f.rutas.map((r) =>
          el("li", {}, codigoRuta(r.ruta), el("span", {}, `${r.desde} → ${r.hasta}`),
            el("button", { type: "button", class: "enlace", text: "horarios", "aria-label": `Ver horarios de ${r.ruta} en ${f.nombre}`,
              onclick: () => ir("horarios", { estacion: f.nombre, ruta: r.ruta }) }))))));
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo consultar", error.message));
    }
  }

  async function listarRango(boton) {
    const destino = $("[data-rango]");
    const desde = $("#rango-desde").value, hasta = $("#rango-hasta").value;
    try {
      const r = await conCarga(boton, () => api(`/api/rango?${qs({ desde, hasta })}`));
      if (!r.resultados.length) {
        vaciar(destino, mensaje("info", "Sin estaciones abiertas en ese rango",
          r.desde > r.hasta ? "El inicio va después del final en orden alfabético." : "Prueba con un rango más amplio."));
        return;
      }
      vaciar(destino, el("p", { class: "contador", text: `${r.resultados.length} estaciones abiertas de «${r.desde}» a «${r.hasta}»` }),
        el("ol", { class: "indice" }, r.resultados.map((n) =>
          el("li", {}, el("span", { class: "letra", text: n[0] }),
            el("button", { type: "button", class: "enlace", text: n, onclick: () => consultar(n) })))));
    } catch (error) {
      vaciar(destino, mensaje("error", "Rango inválido", error.message));
    }
  }

  function iniciar() {
    combobox($("#est-nombre"), { alElegir: (v) => consultar(v) });
    $("[data-accion='ficha']").addEventListener("submit", (e) => { e.preventDefault(); consultar($("#est-nombre").value, e.submitter); });
    $("[data-accion='rango']").addEventListener("submit", (e) => { e.preventDefault(); listarRango(e.submitter); });
    listarRango();
  }

  function mostrar() {
    const nombre = tomar("estaciones");
    if (nombre) { $("#est-nombre").value = nombre; consultar(nombre); }
  }

  registrar("estaciones", { iniciar, mostrar });
})();
