/* Lámina 02: R4. Estación → ruta válida (con extremos reales) → hora. */
"use strict";

(() => {
  const { $, el, vaciar, api, qs, duracion, mensaje, combobox, registrar, tomar, conCarga, codigoRuta } = Atlas;
  const S = Graficos.s;
  const aMin = (h) => { const [a, b] = h.split(":").map(Number); return a * 60 + b; };

  async function cargarRutas(estacion, preferida) {
    const select = $("#hor-ruta");
    select.disabled = true;
    vaciar(select, el("option", { value: "", text: "Cargando rutas…" }));
    try {
      const r = await api(`/api/estacion/rutas?${qs({ nombre: estacion })}`);
      if (!r.rutas.length) {
        vaciar(select, el("option", { value: "", text: "Ninguna ruta para aquí" }));
        return;
      }
      vaciar(select, r.rutas.map((x) => el("option", { value: x.ruta, text: x.etiqueta })));
      if (preferida) select.value = preferida;
      select.disabled = false;
    } catch (error) {
      vaciar(select, el("option", { value: "", text: "Estación no encontrada" }));
    }
  }

  /** Línea de 00:00 a 24:00 con un trazo por registro, la hora pedida y el próximo. */
  function cronologia(d) {
    const ancho = 760, alto = 120, m = 24;
    const fx = (min) => m + (min / 1440) * (ancho - 2 * m);
    const svg = S("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img",
      "aria-label": `Línea del día con ${d.total_dia} registros de ${d.ruta.ruta} en ${d.estacion}` });
    // histograma por hora (contexto) + ticks individuales
    const porHora = new Array(24).fill(0);
    for (const h of d.eventos_dia) porHora[Math.floor(aMin(h) / 60)]++;
    const maxH = Math.max(1, ...porHora);
    porHora.forEach((c, h) => {
      const alto_b = (c / maxH) * 44;
      const barra = S("rect", { class: "barra-svg--suave", x: fx(h * 60) + 1, width: fx(60) - fx(0) - 2, y: 66 - alto_b, height: alto_b });
      barra.append(S("title", {}, `${String(h).padStart(2, "0")}:00 – ${c} registros`));
      svg.append(barra);
    });
    for (const h of d.eventos_dia) {
      const x = fx(aMin(h));
      svg.append(S("line", { class: "evento-tick", x1: x, x2: x, y1: 70, y2: 84 }));
    }
    svg.append(S("line", { class: "eje", x1: m, x2: ancho - m, y1: 84, y2: 84 }));
    for (let h = 0; h <= 24; h += 3) {
      svg.append(S("text", { class: "texto-eje", x: fx(h * 60), y: 100, "text-anchor": "middle" }, `${String(h).padStart(2, "0")}h`));
    }
    const xq = fx(aMin(d.hora));
    svg.append(S("line", { class: "marca-consulta", x1: xq, x2: xq, y1: 14, y2: 90 }));
    svg.append(S("text", { class: "texto-eje", x: xq + 4, y: 14 }, `consulta ${d.hora}`));
    if (d.proximo) {
      const xp = fx(aMin(d.proximo));
      if (d.intervalo) {
        svg.append(S("rect", { x: Math.min(xq, xp), width: Math.abs(xp - xq), y: 70, height: 14, fill: "var(--ladrillo)", opacity: .18 }));
      }
      svg.append(S("path", { class: "marca-proximo", d: `M${xp},84 l-7,-14 h14 z` }));
      svg.append(S("text", { class: "texto-eje", x: xp + 4, y: 30, "font-weight": 700 }, `próximo ${d.proximo}`));
    }
    return el("div", { class: "cronologia" }, svg);
  }

  function pintar(d) {
    const destino = $("[data-horario]");
    const cerrada = d.estado === "cerrada";
    const marquesina = el("dl", { class: "marquesina" },
      el("div", { class: "marquesina__ruta" }, codigoRuta(d.ruta.ruta),
        el("span", { class: "marquesina__sentido", text: `${d.ruta.desde} → ${d.ruta.hasta}` }),
        el("span", { text: `· en ${d.estacion}` })),
      el("div", {}, el("dt", { text: "Hora consultada" }), el("dd", { text: d.hora })),
      el("div", {}, el("dt", { text: "Próximo registro" }), el("dd", { class: "destacado", text: d.proximo || "—" })),
      el("div", {}, el("dt", { text: "Espera" }), el("dd", { text: d.diferencia === null ? "—" : duracion(d.diferencia) })),
      el("div", {}, el("dt", { text: "Registros del día" }), el("dd", { text: d.total_dia })));

    const avisos = [];
    if (cerrada) avisos.push(mensaje("error", "La estación está cerrada", "Mientras esté cerrada ningún bus la atiende, así que no hay próximo bus."));
    else if (!d.proximo && d.total_dia) avisos.push(mensaje("info", "No hay más registros ese día",
      `El último registro de ${d.ruta.ruta} en ${d.estacion} es a las ${d.eventos_dia[d.eventos_dia.length - 1]}. El motor no pasa al día siguiente.`));
    else if (!d.total_dia) avisos.push(mensaje("info", "Sin registros programados", "El CSV no tiene horarios para esta ruta en esta estación (puede ser una parada agregada en Operación)."));
    if (d.intervalo) avisos.push(mensaje("info", `Intervalo largo: ${duracion(d.intervalo.minutos)} sin registros`,
      d.intervalo.anterior
        ? `Entre ${d.intervalo.anterior} y ${d.intervalo.siguiente} el horario programado no registra pasos de esta ruta aquí. Es común en rutas que solo operan en franjas pico.`
        : `Antes de ${d.intervalo.siguiente} no hay registros programados de esta ruta en este punto.`));

    vaciar(destino, marquesina, ...avisos.map((a) => el("div", { style: "margin-top:14px" }, a)),
      el("div", { class: "horario-detalle" },
        el("div", { class: "tarjeta" }, el("h3", { class: "tarjeta__titulo", text: "Siguientes registros" }),
          d.siguientes.length
            ? el("ol", { class: "siguientes" }, d.siguientes.map((h) => el("li", {}, el("span", { text: h }), el("span", { text: `+${duracion(aMin(h) - aMin(d.hora))}` }))))
            : el("p", { class: "vacio-estado", text: "No hay más registros después del próximo." })),
        el("div", { class: "tarjeta" }, el("h3", { class: "tarjeta__titulo", text: "El día completo" }),
          d.total_dia ? cronologia(d) : el("p", { class: "vacio-estado", text: "Sin registros." }),
          el("p", { class: "pie", text: "Barras: registros por hora. Trazos: cada registro. Línea roja: tu consulta; triángulo: el próximo." }))));
  }

  async function consultar(boton) {
    const estacion = $("#hor-estacion").value, ruta = $("#hor-ruta").value, hora = $("#hor-hora").value;
    const destino = $("[data-horario]");
    if (!estacion || !ruta) { vaciar(destino, mensaje("error", "Faltan datos", "Elige una estación y una de sus rutas.")); return; }
    if (!hora) { vaciar(destino, mensaje("error", "Falta la hora", "Escribe una hora entre 00:00 y 23:59.")); return; }
    try {
      pintar(await conCarga(boton, () => api(`/api/proximo?${qs({ estacion, ruta, hora })}`)));
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo consultar", error.message));
    }
  }

  function iniciar() {
    const input = $("#hor-estacion");
    combobox(input, { alElegir: (v) => cargarRutas(v) });
    input.addEventListener("change", () => { if (input.value) cargarRutas(input.value); });
    $("[data-accion='horario']").addEventListener("submit", (e) => { e.preventDefault(); consultar(e.submitter); });
  }

  async function mostrar() {
    const datos = tomar("horarios");
    if (datos) {
      $("#hor-estacion").value = datos.estacion;
      await cargarRutas(datos.estacion, datos.ruta);
      consultar();
    } else if (!$("#hor-estacion").value) {
      $("#hor-estacion").value = "PORTAL NORTE";
      await cargarRutas("PORTAL NORTE", "B10-1");
    }
  }

  registrar("horarios", { iniciar, mostrar });
})();
