/* Lámina 06: R10. Laboratorio de hora pico.
   El orden de abordaje lo decide simular_fila en Python; aquí solo se
   reproduce la traza que devuelve el servidor (pasos ENQUEUE/DEQUEUE). */
"use strict";

(() => {
  const { $, $$, el, vaciar, api, num, mensaje, registrar, conCarga, duracion } = Atlas;
  const ANCHO_PERSONA = 50, INICIO_FILA = 196;

  /* ================================================== modo educativo */
  let traza = null, paso = -1, reproduciendo = null;

  const CODIGO = [
    "para cada minuto con eventos:",
    "    para cada persona que llega en este minuto:",
    "        fila.encolar(persona)            # ENQUEUE al final",
    "    si minuto % frecuencia == 0:          # sale un bus",
    "        cupos = capacidad",
    "        mientras cupos > 0 y no fila.vacia():",
    "            p = fila.desencolar()          # DEQUEUE del frente",
    "            abordaje[p] = minuto",
  ];

  function leerLlegadas() {
    const texto = $("#edu-llegadas").value.trim();
    if (!texto) throw new Error("Escribe al menos una llegada.");
    const partes = texto.split(/[\s,;]+/).filter(Boolean);
    const valores = partes.map(Number);
    if (valores.some((v) => !Number.isInteger(v) || v < 0)) throw new Error("Cada llegada debe ser un minuto entero no negativo.");
    return valores;
  }

  async function simularEducativo(boton) {
    detener();
    const destino = $("[data-edu]");
    try {
      const cuerpo = { llegadas: leerLlegadas(), frecuencia: Number($("#edu-f").value), capacidad: Number($("#edu-c").value) };
      traza = await conCarga(boton, () => api("/api/fila/educativo", { metodo: "POST", cuerpo }));
      construirEscenario();
      irA(-1);
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo simular", error.message));
    }
  }

  function construirEscenario() {
    const n = traza.llegadas.length;
    const anchoAnden = INICIO_FILA + n * ANCHO_PERSONA + 40;
    const personas = traza.llegadas.map((l, i) => el("div", { class: "persona fuera", "data-p": i, "aria-hidden": "true" },
      el("span", { class: "persona__cuerpo", text: `P${i + 1}` }), el("span", { class: "persona__min", text: `m${l}` })));
    const cupos = Array.from({ length: traza.capacidad }, () => el("span", { class: "cupo" }));
    const m = traza.metricas;
    vaciar($("[data-edu]"),
      el("div", { class: "escenario" },
        el("div", { class: "escenario__cabeza" },
          el("p", { class: "reloj", "aria-live": "polite" }, el("small", { text: "MINUTO" }), el("span", { "data-reloj": true, text: "—" })),
          el("div", { class: "controles", role: "group", "aria-label": "Controles de reproducción" },
            el("button", { type: "button", class: "boton", "data-ctl": "reiniciar", "aria-label": "Reiniciar", text: "⏮" }),
            el("button", { type: "button", class: "boton", "data-ctl": "anterior", "aria-label": "Paso anterior", text: "◀ Anterior" }),
            el("button", { type: "button", class: "boton", "data-ctl": "play", "aria-label": "Reproducir", text: "▶ Reproducir" }),
            el("button", { type: "button", class: "boton", "data-ctl": "siguiente", "aria-label": "Paso siguiente", text: "Siguiente ▶" }),
            el("label", {}, "Velocidad", el("select", { "data-velocidad": true },
              el("option", { value: "1800", text: "0.5×" }), el("option", { value: "1100", text: "1×", selected: true }), el("option", { value: "550", text: "2×" }))),
            el("span", { "data-contador": true, style: "font-family:var(--mono);font-size:12px;color:#B8B4AA" }))),
        el("div", { class: "anden", tabindex: "0", "aria-label": "Andén: usa las flechas para avanzar o retroceder",
          style: `--ancho:${anchoAnden}px` },
          el("div", { style: `position:relative;width:${anchoAnden}px;min-width:100%;height:100%` },
            el("div", { class: "anden__piso" }),
            el("div", { class: "bus ausente", "data-bus": true },
              el("div", { class: "bus__cabeza" }, el("span", { "data-bus-min": true, text: "BUS" }), el("span", { text: `cap ${traza.capacidad}` })),
              el("div", { class: "bus__cupos" }, cupos)),
            el("span", { class: "anden__rotulo", style: `left:${INICIO_FILA}px`, "data-frente": true, text: "▲ frente" }),
            el("span", { class: "anden__rotulo", "data-final": true, text: "final ▲" }),
            personas)),
        el("div", { class: "explicacion" },
          el("div", { "data-explica": true, "aria-live": "polite" }),
          el("div", {}, el("p", { class: "rotulo", text: "Pseudocódigo de simular_fila" }),
            el("ol", { class: "codigo", "data-codigo": true }, CODIGO.map((l) => el("li", { text: l })))))),
      el("dl", { class: "metricas" },
        dato("Espera media", `${num(m.espera_media, 2)} min`, `${traza.esperas.reduce((a, b) => a + b, 0)}/${m.pasajeros}`),
        dato("Espera máxima", `${m.espera_maxima} min`),
        dato("Buses con abordajes", m.buses_con_abordajes),
        dato("Cola máxima", m.cola_maxima, `en el minuto ${m.minuto_cola_maxima}`),
        dato("Último abordaje", `min ${m.ultimo_abordaje}`)),
      el("div", { class: "tabla-wrap" }, el("table", { class: "tabla" },
        el("caption", { class: "sr", text: "Resultado por pasajero, en el orden de entrada" }),
        el("thead", {}, el("tr", {}, ["Pasajero", "Llegada", "Abordaje", "Espera"].map((t) => el("th", { scope: "col", text: t })))),
        el("tbody", { "data-tabla": true }, traza.llegadas.map((l, i) => el("tr", { "data-fila": i },
          el("td", { text: `P${i + 1}` }), el("td", { text: l }), el("td", { "data-celda-abordaje": true, text: "·" }), el("td", { "data-celda-espera": true, text: "·" })))))));

    $$("[data-ctl]").forEach((b) => b.addEventListener("click", () => {
      const accion = b.dataset.ctl;
      if (accion === "reiniciar") { detener(); irA(-1); }
      else if (accion === "anterior") { detener(); irA(paso - 1); }
      else if (accion === "siguiente") { detener(); irA(paso + 1); }
      else if (accion === "play") reproduciendo ? detener() : reproducir();
    }));
    $(".anden").addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { e.preventDefault(); detener(); irA(paso + 1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); detener(); irA(paso - 1); }
      if (e.key === " ") { e.preventDefault(); reproduciendo ? detener() : reproducir(); }
    });
  }

  function dato(titulo, valor, sub) {
    return el("div", {}, el("dt", { text: titulo }), el("dd", {}, String(valor), sub ? el("small", { text: ` ${sub}` }) : null));
  }

  function reproducir() {
    if (paso >= traza.pasos.length - 1) irA(-1);
    const boton = $("[data-ctl='play']");
    boton.textContent = "❚❚ Pausar"; boton.setAttribute("aria-label", "Pausar");
    const tic = () => {
      if (paso >= traza.pasos.length - 1) { detener(); return; }
      irA(paso + 1);
      reproduciendo = setTimeout(tic, Number($("[data-velocidad]").value));
    };
    reproduciendo = setTimeout(tic, 250);
  }

  function detener() {
    clearTimeout(reproduciendo);
    reproduciendo = null;
    const boton = $("[data-ctl='play']");
    if (boton) { boton.textContent = "▶ Reproducir"; boton.setAttribute("aria-label", "Reproducir"); }
  }

  function irA(i) {
    if (!traza) return;
    paso = Math.max(-1, Math.min(i, traza.pasos.length - 1));
    const p = paso >= 0 ? traza.pasos[paso] : null;
    const fila = p ? p.fila : [];
    const subidos = new Set(p ? p.subidos : []);
    const subenAhora = new Set(p && p.tipo === "dequeue" ? p.pasajeros : []);
    const nuevos = new Set(p && p.tipo === "enqueue" ? p.pasajeros : []);
    const posicion = new Map(fila.map((id, k) => [id, k]));

    $$(".persona").forEach((nodo) => {
      const id = Number(nodo.dataset.p);
      nodo.classList.remove("nueva", "frente", "sube", "fuera");
      if (posicion.has(id)) {
        nodo.style.left = `${INICIO_FILA + posicion.get(id) * ANCHO_PERSONA}px`;
        nodo.style.bottom = "46px";
        if (nuevos.has(id)) nodo.classList.add("nueva");
        if (posicion.get(id) === 0) nodo.classList.add("frente");
      } else if (subenAhora.has(id)) {
        nodo.style.left = "60px"; nodo.style.bottom = "80px"; nodo.classList.add("sube");
      } else {
        nodo.classList.add("fuera");
        if (!subidos.has(id)) { nodo.style.left = `${INICIO_FILA + (fila.length + 2) * ANCHO_PERSONA}px`; nodo.style.bottom = "46px"; }
      }
    });
    $("[data-final]").style.left = `${INICIO_FILA + Math.max(0, fila.length - 1) * ANCHO_PERSONA + 4}px`;
    $("[data-final]").hidden = fila.length < 2;
    $("[data-frente]").hidden = fila.length === 0;

    const bus = $("[data-bus]");
    bus.classList.toggle("ausente", !(p && p.tipo === "dequeue"));
    $$(".cupo", bus).forEach((c, k) => c.classList.toggle("ocupado", p && p.tipo === "dequeue" && k < p.pasajeros.length));
    const proximoBus = p ? (p.tipo === "dequeue" ? p.minuto : Math.ceil(p.minuto / traza.frecuencia) * traza.frecuencia) : 0;
    $("[data-bus-min]").textContent = p && p.tipo === "dequeue" ? `BUS m${p.minuto}` : `próx. m${proximoBus}`;

    $("[data-reloj]").textContent = p ? String(p.minuto).padStart(2, "0") : "—";
    $("[data-contador]").textContent = `paso ${paso + 1}/${traza.pasos.length}`;
    $("[data-ctl='anterior']").disabled = paso < 0;
    $("[data-ctl='siguiente']").disabled = paso >= traza.pasos.length - 1;

    explicar(p, fila);
    const lineas = $$("[data-codigo] li");
    const activas = !p ? [] : p.tipo === "enqueue" ? [0, 1, 2] : [3, 4, 5, 6, 7];
    lineas.forEach((li, k) => li.classList.toggle("activa", activas.includes(k)));

    $$("[data-fila]").forEach((tr) => {
      const id = Number(tr.dataset.fila);
      const ya = subidos.has(id);
      tr.classList.toggle("pendiente", !ya);
      tr.classList.toggle("actual", subenAhora.has(id) || nuevos.has(id));
      $("[data-celda-abordaje]", tr).textContent = ya ? traza.abordajes[id] : "·";
      $("[data-celda-espera]", tr).textContent = ya ? traza.esperas[id] : "·";
    });
  }

  function explicar(p, fila) {
    const caja = $("[data-explica]");
    const nombres = (ids) => ids.map((x) => `P${x + 1}`).join(", ");
    if (!p) {
      vaciar(caja, el("p", { class: "operacion-badge", text: "INICIO" }),
        el("p", { text: `La fila está vacía. Llegan ${traza.llegadas.length} personas; los buses salen en los minutos 0, ${traza.frecuencia}, ${2 * traza.frecuencia}… con ${traza.capacidad} cupos.` }),
        el("p", { class: "pie", text: "Avanza con «Siguiente» o con las flechas del teclado sobre el andén." }));
      return;
    }
    if (p.tipo === "enqueue") {
      vaciar(caja, el("span", { class: "operacion-badge operacion-badge--enqueue", text: `ENQUEUE ×${p.pasajeros.length}` }),
        el("p", {}, `Minuto ${p.minuto}: llega${p.pasajeros.length > 1 ? "n" : ""} `, el("strong", { text: nombres(p.pasajeros) }),
          ". Cada uno se encola al ", el("strong", { text: "final" }), " de la fila, en O(1)."),
        el("p", { text: fila.length ? `Fila (frente → final): ${nombres(fila)}.` : "" }),
        p.pasajeros.length > 1 ? el("p", { class: "pie", text: "Llegaron en el mismo minuto: conservan el orden en que aparecen en la lista (orden estable)." }) : null);
      return;
    }
    const sobran = fila.length;
    vaciar(caja, el("span", { class: "operacion-badge operacion-badge--dequeue", text: `DEQUEUE ×${p.pasajeros.length}` }),
      el("p", {}, `Minuto ${p.minuto}: sale un bus con ${traza.capacidad} cupos. Se desencola desde el `, el("strong", { text: "frente" }), ": ",
        el("strong", { text: nombres(p.pasajeros) }), "."),
      el("p", { text: p.cupos_libres > 0 ? `El bus sale con ${p.cupos_libres} cupo(s) libre(s): la fila quedó vacía.`
        : sobran ? `El bus se llenó. Siguen esperando ${sobran}: ${nombres(fila)} — subirán en un bus posterior.` : "El bus se llenó justo con la fila." }),
      el("p", { class: "pie", text: "Quien llega exactamente en el minuto del bus alcanza a subir, si hay cupo." }));
  }

  /* ================================================== modo masivo */
  function leerNumero(id) { return Number($(id).value); }

  function tarjetasMetricas(m, comparar) {
    const fila = (titulo, clave, sufijo = "", dec = 0, menorEsMejor = true) => {
      const v = m[clave];
      let dif = null;
      if (comparar && comparar[clave] !== undefined) {
        const d = v - comparar[clave];
        if (Math.abs(d) > 1e-9) {
          const mejor = menorEsMejor ? d < 0 : d > 0;
          dif = el("span", { class: `dif ${mejor ? "dif--mejor" : "dif--peor"}`, text: `${d > 0 ? "+" : ""}${num(d, dec)}` });
        }
      }
      return el("div", {}, el("dt", { text: titulo }), el("dd", {}, `${num(v, dec)}${sufijo}`, dif));
    };
    return el("dl", { class: "metricas" },
      fila("Pasajeros", "pasajeros"),
      fila("Espera media", "espera_media", " min", 2),
      fila("Mediana", "espera_mediana", " min"),
      fila("Percentil 90", "p90", " min"),
      fila("Percentil 95", "p95", " min"),
      fila("Espera máxima", "espera_maxima", " min"),
      fila("Cola máxima", "cola_maxima"),
      fila("Ocupación media", "ocupacion_media", "", 2, false),
      fila("Buses con abordajes", "buses_con_abordajes"),
      fila("Buses llenos", "buses_llenos", "", 0, false),
      fila("Último abordaje", "ultimo_abordaje", " min"));
  }

  function minutosEje(paso) { return (i) => `${i * paso}`; }

  function graficosEscenario(series, clase = "a") {
    const xs = series.cola.map((_, i) => i * series.paso);
    return el("div", { class: "graficos" },
      el("figure", { class: "grafico grafico--ancho", style: "margin:0" },
        el("h3", { text: "Personas en la fila" }),
        el("p", { text: `Al final de cada intervalo de ${series.paso} min, después de los abordajes.` }),
        Graficos.lineas([{ valores: series.cola, xs, clase: `serie--${clase}`, area: `area--${clase}` }],
          { etiquetaX: "minuto", titulo: "Personas en la fila a lo largo del tiempo", ancho: 1100, alto: 280 })),
      el("figure", { class: "grafico", style: "margin:0" },
        el("h3", { text: "Ocupación de cada bus" }),
        el("p", { text: "Abordajes ÷ capacidad (1 = lleno)." }),
        Graficos.lineas([{ valores: series.ocupacion.map((o) => o.ocupacion), xs: series.ocupacion.map((o) => o.minuto), clase: `serie--${clase}` }],
          { etiquetaX: "minuto de salida", titulo: "Ocupación por bus", formatoY: (v) => v.toFixed(1) })),
      el("figure", { class: "grafico", style: "margin:0" },
        el("h3", { text: "Distribución de esperas" }),
        el("p", { text: `Personas por rango de ${series.histograma.ancho} min.` }),
        Graficos.barras(series.histograma.conteos, { clase: clase === "b" ? "barra-svg barra-svg--b" : "barra-svg",
          formatoX: (i) => `${i * series.histograma.ancho}`, etiquetaX: "min de espera", titulo: "Histograma de esperas" })));
  }

  async function simularAvanzado(boton) {
    const destino = $("[data-ava]");
    const cuerpo = { pasajeros: leerNumero("#ava-p"), duracion: leerNumero("#ava-d"), frecuencia: leerNumero("#ava-f"),
      capacidad: leerNumero("#ava-c"), demanda: $("#ava-dem").value, semilla: leerNumero("#ava-s") };
    try {
      const inicio = performance.now();
      const r = await conCarga(boton, () => api("/api/fila/avanzado", { metodo: "POST", cuerpo }));
      const ms = performance.now() - inicio;
      vaciar(destino, tarjetasMetricas(r.metricas), graficosEscenario(r.series),
        el("p", { class: "pie", text: `${num(r.metricas.pasajeros)} pasajeros simulados por el motor en Python; respuesta en ${num(ms)} ms (incluye red y resumen). Las gráficas usan agregados; las métricas usan cada pasajero.` }));
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo simular", error.message));
    }
  }

  async function comparar(boton) {
    const destino = $("[data-ab]");
    const cuerpo = { pasajeros: leerNumero("#ab-p"), duracion: leerNumero("#ab-d"), demanda: $("#ab-dem").value, semilla: leerNumero("#ab-s"),
      a: { frecuencia: leerNumero("#ab-fa"), capacidad: leerNumero("#ab-ca") },
      b: { frecuencia: leerNumero("#ab-fb"), capacidad: leerNumero("#ab-cb") } };
    try {
      const r = await conCarga(boton, () => api("/api/fila/comparar", { metodo: "POST", cuerpo }));
      const sa = r.a.series, sb = r.b.series;
      const ofertaA = (60 / r.a.frecuencia) * r.a.capacidad, ofertaB = (60 / r.b.frecuencia) * r.b.capacidad;
      vaciar(destino,
        el("div", { class: "rejilla rejilla--2", style: "margin-top:18px" },
          el("div", {}, el("h3", { class: "tarjeta__titulo" }, el("span", {}, "A · ", `cada ${r.a.frecuencia} min, ${r.a.capacidad} cupos`)),
            el("p", { class: "pie", text: `Oferta nominal: ${num(ofertaA)} cupos por hora.` }), tarjetasMetricas(r.a.metricas)),
          el("div", {}, el("h3", { class: "tarjeta__titulo" }, el("span", {}, "B · ", `cada ${r.b.frecuencia} min, ${r.b.capacidad} cupos`)),
            el("p", { class: "pie", text: `Oferta nominal: ${num(ofertaB)} cupos por hora. Diferencias respecto a A (verde = mejor).` }), tarjetasMetricas(r.b.metricas, r.a.metricas))),
        el("figure", { class: "grafico grafico--ancho", style: "margin:0 0 24px" },
          el("h3", { text: "Personas en la fila: A frente a B" }),
          el("p", { text: "Mismas llegadas para ambas configuraciones." }),
          Graficos.lineas([
            { valores: sa.cola, xs: sa.cola.map((_, i) => i * sa.paso), clase: "serie--a", area: "area--a" },
            { valores: sb.cola, xs: sb.cola.map((_, i) => i * sb.paso), clase: "serie--b", area: "area--b" }],
          { etiquetaX: "minuto", titulo: "Fila de A y B a lo largo del tiempo", ancho: 1100, alto: 280 }),
          el("div", { class: "leyenda" }, el("span", {}, el("i", { style: "background:var(--cerro)" }), "A"), el("span", {}, el("i", { style: "background:var(--andino)" }), "B"))),
        el("div", { class: "graficos" },
          el("figure", { class: "grafico", style: "margin:0" }, el("h3", { text: "Esperas en A" }),
            Graficos.barras(sa.histograma.conteos, { formatoX: (i) => `${i * sa.histograma.ancho}`, etiquetaX: "min", titulo: "Histograma A" })),
          el("figure", { class: "grafico", style: "margin:0" }, el("h3", { text: "Esperas en B" }),
            Graficos.barras(sb.histograma.conteos, { clase: "barra-svg barra-svg--b", formatoX: (i) => `${i * sb.histograma.ancho}`, etiquetaX: "min", titulo: "Histograma B" }))),
        el("p", { class: "pie", text: "Escenario sintético. No es una predicción de la operación real ni incluye costos." }));
    } catch (error) {
      vaciar(destino, mensaje("error", "No se pudo comparar", error.message));
    }
  }

  /* ================================================== pestañas */
  function activarPestana(boton) {
    $$("[role='tab']").forEach((t) => {
      const activa = t === boton;
      t.setAttribute("aria-selected", String(activa));
      t.tabIndex = activa ? 0 : -1;
      $(`#${t.getAttribute("aria-controls")}`).hidden = !activa;
    });
    if (boton.dataset.tab !== "edu") detener();
  }

  function iniciar() {
    const tabs = $$("[role='tab']");
    tabs.forEach((t, i) => {
      t.addEventListener("click", () => activarPestana(t));
      t.addEventListener("keydown", (e) => {
        const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        const otro = tabs[(i + d + tabs.length) % tabs.length];
        otro.focus(); activarPestana(otro);
      });
    });
    $("[data-accion='fila-edu']").addEventListener("submit", (e) => { e.preventDefault(); simularEducativo(e.submitter); });
    $("[data-accion='fila-ava']").addEventListener("submit", (e) => { e.preventDefault(); simularAvanzado(e.submitter); });
    $("[data-accion='fila-ab']").addEventListener("submit", (e) => { e.preventDefault(); comparar(e.submitter); });
    $$("[data-ejemplo]").forEach((b) => b.addEventListener("click", () => {
      const [ll, f, c] = b.dataset.ejemplo.split("|");
      $("#edu-llegadas").value = ll.split(",").join(", ");
      $("#edu-f").value = f; $("#edu-c").value = c;
      simularEducativo();
    }));
    simularEducativo();
  }

  registrar("fila", { iniciar, mostrar: () => {} });
  window.addEventListener("hashchange", () => { if (location.hash !== "#fila") detener(); });
})();
