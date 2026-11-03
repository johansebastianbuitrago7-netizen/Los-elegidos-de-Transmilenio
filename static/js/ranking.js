/* Lámina 04: R6. Barras horizontales del ranking que devuelve el motor. */
"use strict";

(() => {
  const { $, el, vaciar, api, qs, num, mensaje, registrar, conCarga, ir } = Atlas;

  async function cargar(boton) {
    const destino = $("[data-ranking]");
    const k = $("#ran-k").value;
    try {
      const filas = await conCarga(boton, () => api(`/api/ranking?${qs({ k })}`));
      if (!filas.length) { vaciar(destino, mensaje("info", "Ranking vacío", "No hay estaciones abiertas o k es 0.")); return; }
      const maximo = filas[0].buses || 1;
      vaciar(destino, el("ol", { class: "barras", "aria-label": "Ranking de estaciones por buses al día" }, filas.map((f, i) =>
        el("li", {},
          el("span", { class: "pos", text: i + 1 }),
          el("button", { type: "button", class: "enlace nombre", text: f.nombre, title: f.nombre, onclick: () => ir("estaciones", f.nombre) }),
          el("span", { class: "pista", role: "img", "aria-label": `${num(f.buses)} buses` },
            el("span", { class: "relleno", style: `width:${(f.buses / maximo) * 100}%; animation-delay:${i * 25}ms` }),
            el("span", { class: "cuenta", text: num(f.buses) }))))),
      el("p", { class: "pie", text: "Cuenta = filas de horarios.csv de las rutas que hoy paran en la estación. Empates: orden alfabético." }));
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo calcular", error.message));
    }
  }

  function iniciar() {
    $("[data-accion='ranking']").addEventListener("submit", (e) => { e.preventDefault(); cargar(e.submitter); });
  }

  registrar("ranking", { iniciar, mostrar: () => cargar() });
})();
