/* Lámina 03: R5. Diagrama de itinerario esquemático (sin coordenadas inventadas). */
"use strict";

(() => {
  const { $, el, vaciar, api, qs, mensaje, combobox, registrar, conCarga, codigoRuta, sello } = Atlas;

  function parada(nombre, estado, clases, nota) {
    return el("li", { class: `parada ${clases} ${estado === "cerrada" ? "parada--cerrada" : ""}` },
      el("span", { class: "parada__punto", "aria-hidden": "true" }),
      el("span", { text: nombre }),
      nota ? el("span", { class: "parada__nota", text: nota }) : el("span"));
  }

  function diagrama(v) {
    const filas = [];
    v.tramos.forEach((t, i) => {
      const variante = i === 1 ? "parada--tramo-b" : "";
      const internas = t.estaciones.slice(1, -1);
      if (i === 0) filas.push(parada(t.subir, "abierta", `parada--extremo parada--origen`, "Origen"));
      filas.push(el("li", { class: `parada ${variante}` }, el("span"),
        el("div", { class: "tramo-rotulo" }, codigoRuta(t.ruta.ruta, i === 1 ? "b" : null),
          el("span", { text: `hacia ${t.ruta.hasta} · ${t.paradas} ${t.paradas === 1 ? "parada" : "paradas"}` })), el("span")));
      const items = internas.map((e) => parada(e.nombre, e.estado, variante, e.estado === "cerrada" ? "cerrada · no se detiene" : ""));
      if (items.length > 6) {
        const det = el("details", { class: "colapso" }, el("summary", { text: `${items.length} estaciones intermedias` }), el("ol", {}, items));
        filas.push(el("li", { class: `parada ${variante}` }, el("span"), det, el("span")));
      } else filas.push(...items);
      if (i < v.tramos.length - 1) filas.push(parada(t.bajar, "abierta", "parada--transbordo", "Transbordo"));
      else filas.push(parada(t.bajar, "abierta", `parada--extremo parada--destino ${variante}`, "Destino"));
    });
    return el("div", { class: "diagrama" }, el("ol", { "aria-label": "Diagrama del itinerario" }, filas),
      el("p", { class: "pie", text: "Diagrama esquemático: el espaciado es uniforme y no representa distancias ni tiempos." }));
  }

  function pintar(v) {
    const destino = $("[data-viaje]");
    if (!v.encontrado) {
      const motivos = [];
      if (v.estado_origen !== "abierta") motivos.push(`El origen ${v.origen} ${v.estado_origen === "cerrada" ? "está cerrado" : "no existe"}.`);
      if (v.estado_destino !== "abierta") motivos.push(`El destino ${v.destino} ${v.estado_destino === "cerrada" ? "está cerrado" : "no existe"}.`);
      if (!motivos.length) motivos.push("Ninguna combinación de una o dos rutas une estas estaciones en ese sentido sin pasar por un transbordo cerrado.");
      vaciar(destino, mensaje("error", "No hay viaje posible", motivos.join(" ")));
      return;
    }
    if (!v.tramos.length) {
      vaciar(destino, mensaje("info", "Ya estás ahí", "Origen y destino son la misma estación: 0 paradas."));
      return;
    }
    const pasos = v.tramos.map((t, i) => el("li", {}, el("span", {},
      i === 0 ? "En " : "Cambia en ", el("strong", { text: t.subir }), " toma ", codigoRuta(t.ruta.ruta, i === 1 ? "b" : null),
      ` (sentido ${t.ruta.desde} → ${t.ruta.hasta}) y bájate en `, el("strong", { text: t.bajar }),
      ` tras ${t.paradas} ${t.paradas === 1 ? "parada" : "paradas"}.`)));
    vaciar(destino, el("div", { class: "itinerario" },
      el("div", { class: "resumen-viaje" },
        el("p", { class: "resumen-viaje__cifra" }, String(v.paradas), el("small", { text: v.paradas === 1 ? "parada" : "paradas" })),
        el("p", {}, v.tramos.length === 1 ? "Viaje directo, sin transbordos." : `Un transbordo en ${v.transbordo}.`),
        el("ol", { class: "instrucciones" }, pasos),
        el("p", { class: "pie", text: "Se cuentan enlaces entre paradas consecutivas de cada ruta; no se estiman tiempos de viaje." })),
      el("div", { class: "tarjeta" }, diagrama(v))));
  }

  async function trazar(boton) {
    const origen = $("#via-origen").value, destino = $("#via-destino").value;
    if (!origen || !destino) { vaciar($("[data-viaje]"), mensaje("error", "Faltan estaciones", "Escribe origen y destino.")); return; }
    try {
      pintar(await conCarga(boton, () => api(`/api/viaje?${qs({ origen, destino })}`)));
    } catch (error) {
      vaciar($("[data-viaje]"), mensaje("error", "No se pudo planear", error.message));
    }
  }

  function iniciar() {
    combobox($("#via-origen"));
    combobox($("#via-destino"));
    $("[data-intercambiar]").addEventListener("click", () => {
      const a = $("#via-origen"), b = $("#via-destino");
      [a.value, b.value] = [b.value, a.value];
    });
    $("[data-accion='viaje']").addEventListener("submit", (e) => { e.preventDefault(); trazar(e.submitter); });
    $("#via-origen").value = "PORTAL 80";
    $("#via-destino").value = "PORTAL USME";
    trazar();
  }

  registrar("viaje", { iniciar });
})();
