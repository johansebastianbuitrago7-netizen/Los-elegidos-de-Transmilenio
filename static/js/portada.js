/* Lámina 00: portada con cifras reales, tablero R6 y una ruta dibujada. */
"use strict";

(() => {
  const { $, el, vaciar, api, num, combobox, registrar, ir, rutas, qs, aviso } = Atlas;

  async function cargarResumen() {
    const r = await api("/api/resumen");
    for (const clave of ["estaciones", "rutas", "paradas", "eventos"]) {
      $(`[data-cifra="${clave}"]`).textContent = num(r[clave]);
    }
    vaciar($("[data-tablero]"), r.top.map(([nombre, buses]) =>
      el("li", {}, el("a", { href: "#estaciones", onclick: (e) => { e.preventDefault(); ir("estaciones", nombre); }, text: nombre }),
        el("span", { class: "valor", text: num(buses) }))));
  }

  /** Tira horizontal esquemática de una ruta: estaciones equiespaciadas. */
  function dibujarRuta(info, paradas) {
    const S = Graficos.s;
    const paso = 46, margen = 24, alto = 190;
    const ancho = margen * 2 + paso * (paradas.length - 1);
    const svg = S("svg", { viewBox: `0 0 ${ancho} ${alto}`, width: ancho, height: alto, role: "img",
      "aria-label": `Recorrido de ${info.etiqueta}: ${paradas.map((p) => p.nombre).join(", ")}` });
    const y = 150;
    svg.append(S("line", { x1: margen, x2: ancho - margen, y1: y, y2: y, stroke: "var(--cerro)", "stroke-width": 8, "stroke-linecap": "round" }));
    paradas.forEach((p, i) => {
      const x = margen + i * paso;
      const extremo = i === 0 || i === paradas.length - 1;
      svg.append(S("circle", { cx: x, cy: y, r: extremo ? 10 : 6, fill: extremo ? "var(--ambar)" : "var(--papel-3)",
        stroke: p.estado === "cerrada" ? "var(--ladrillo)" : "var(--tinta)", "stroke-width": 3 }));
      const t = S("text", { x: x + 4, y: y - 18, transform: `rotate(-50 ${x + 4} ${y - 18})`, "font-size": extremo ? 12 : 11,
        "font-weight": extremo ? 800 : 500, fill: p.estado === "cerrada" ? "var(--tinta-3)" : "var(--tinta)", "font-family": "var(--fuente)" }, p.nombre);
      svg.append(t);
    });
    return svg;
  }

  async function mostrarRuta(ruta) {
    const datos = await api(`/api/recorrido?${qs({ ruta })}`);
    vaciar($("[data-muestra]"), dibujarRuta(datos.ruta, datos.paradas));
  }

  async function iniciar() {
    combobox($("#portada-buscar"));
    $("[data-accion='buscar-portada']").addEventListener("submit", (e) => {
      e.preventDefault();
      const valor = $("#portada-buscar").value.trim();
      if (!valor) { aviso("Escribe el nombre de una estación.", "error"); return; }
      ir("estaciones", valor);
    });
    try {
      await cargarResumen();
      const todas = await rutas();
      const select = $("[data-muestra-ruta]");
      vaciar(select, todas.map((r) => el("option", { value: r.ruta, text: r.etiqueta })));
      const larga = todas.reduce((a, b) => (b.paradas > a.paradas ? b : a), todas[0]);
      select.value = larga.ruta;
      select.addEventListener("change", () => mostrarRuta(select.value));
      await mostrarRuta(larga.ruta);
    } catch (error) {
      aviso(error.message, "error");
    }
  }

  registrar("portada", { iniciar, mostrar: () => { if (document.body.dataset.cambios) { delete document.body.dataset.cambios; cargarResumen(); } } });
})();
