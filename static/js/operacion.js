/* Lámina 05: R7 (editar rutas), R8 (cerrar/reabrir) y R9 (deshacer/rehacer). */
"use strict";

(() => {
  const { $, $$, el, vaciar, api, qs, aviso, mensaje, combobox, registrar, conCarga, rutas, invalidarRutas, codigoRuta } = Atlas;
  let alReves = false;
  let resaltar = null;

  function pintarPilas(h) {
    const pila = (titulo, ops, vacio) => el("div", { class: "pila" }, el("h3", { text: titulo }),
      el("ol", { "aria-label": titulo }, ops.length ? ops.map((o) => el("li", { "data-tipo": o.tipo, text: o.texto }))
        : [el("li", { class: "vacio-estado", text: vacio, style: "background:none;border:0" })]));
    vaciar($("[data-pilas]"), pila(`Pila deshacer (${h.deshacer.length})`, h.deshacer, "vacía"),
      pila(`Pila rehacer (${h.rehacer.length})`, h.rehacer, "vacía"));
    $("[data-deshacer]").disabled = !h.deshacer.length;
    $("[data-rehacer]").disabled = !h.rehacer.length;
  }

  async function pintarCerradas() {
    const r = await api("/api/resumen");
    vaciar($("[data-cerradas]"), r.cerradas.length
      ? el("div", { class: "cerradas" }, el("p", { class: "rotulo", text: `Cerradas (${r.cerradas.length})` }),
        el("div", { class: "chips" }, r.cerradas.map((n) => el("button", { type: "button", class: "chip", "aria-label": `Reabrir ${n}`,
          onclick: () => cambiar("/api/reabrir", { nombre: n }, `${n} reabierta.`) }, `↺ ${n}`))))
      : el("p", { class: "pie", text: "No hay estaciones cerradas." }));
  }

  async function pintarRuta() {
    const ruta = $("#ope-ruta").value;
    if (!ruta) return;
    const datos = await api(`/api/recorrido?${qs({ ruta, al_reves: alReves ? 1 : 0 })}`);
    vaciar($("[data-tira]"), datos.paradas.map((p) =>
      el("li", { class: `${p.estado === "cerrada" ? "cerrada" : ""} ${p.nombre === resaltar ? "nueva" : ""}` },
        el("span", { class: "nudo", "aria-hidden": "true" }),
        el("span", { class: "tira__nombre", text: p.nombre + (p.estado === "cerrada" ? " (cerrada)" : "") }),
        el("button", { type: "button", class: "tira__quitar", "aria-label": `Quitar ${p.nombre} de ${ruta}`, text: "Quitar",
          onclick: () => cambiar("/api/quitar", { ruta, estacion: p.nombre }, `${p.nombre} salió de ${ruta}.`) }))));
    resaltar = null;
    // "después de" siempre en el sentido de la ruta
    const ida = alReves ? datos.paradas.slice().reverse() : datos.paradas;
    const select = $("#ope-despues");
    const previo = select.value;
    vaciar(select, el("option", { value: "", text: "(al inicio)" }), ida.map((p) => el("option", { value: p.nombre, text: p.nombre })));
    if (previo && ida.some((p) => p.nombre === previo)) select.value = previo;
  }

  async function cargarRutas(forzar) {
    const select = $("#ope-ruta");
    const actual = select.value;
    const todas = await rutas(forzar);
    vaciar(select, todas.map((r) => el("option", { value: r.ruta, text: r.etiqueta })));
    select.value = actual || "B10-1";
    if (!select.value) select.selectedIndex = 0;
  }

  async function cambiar(url, cuerpo, exito, boton) {
    try {
      const r = await conCarga(boton, () => api(url, { metodo: "POST", cuerpo }));
      if (!r.ok) { aviso(r.mensaje, "error"); return false; }
      aviso(exito);
      pintarPilas(r.historial);
      document.body.dataset.cambios = "1";
      invalidarRutas();
      await Promise.all([cargarRutas(true), pintarCerradas()]);
      await pintarRuta();
      return true;
    } catch (error) {
      aviso(error.message, "error");
      return false;
    }
  }

  function iniciar() {
    combobox($("#ope-nueva"));
    combobox($("#ope-cerrar"));
    $("#ope-ruta").addEventListener("change", pintarRuta);
    $$("[data-sentido]").forEach((b) => b.addEventListener("click", () => {
      alReves = b.dataset.sentido === "1";
      $$("[data-sentido]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      pintarRuta();
    }));
    $("[data-accion='agregar']").addEventListener("submit", async (e) => {
      e.preventDefault();
      const ruta = $("#ope-ruta").value, nueva = $("#ope-nueva").value.trim(), despues_de = $("#ope-despues").value;
      if (!nueva) { aviso("Escribe la estación que quieres agregar.", "error"); return; }
      resaltar = nueva.toUpperCase();
      if (await cambiar("/api/agregar", { ruta, nueva, despues_de }, `${nueva.toUpperCase()} agregada a ${ruta}.`, e.submitter)) $("#ope-nueva").value = "";
    });
    $("[data-accion='cerrar']").addEventListener("submit", async (e) => {
      e.preventDefault();
      const nombre = $("#ope-cerrar").value.trim();
      if (!nombre) { aviso("Escribe la estación que quieres cerrar.", "error"); return; }
      if (await cambiar("/api/cerrar", { nombre }, `${nombre.toUpperCase()} cerrada.`, e.submitter)) $("#ope-cerrar").value = "";
    });
    $("[data-deshacer]").addEventListener("click", (e) => cambiar("/api/deshacer", {}, "Se deshizo la última operación.", e.currentTarget));
    $("[data-rehacer]").addEventListener("click", (e) => cambiar("/api/rehacer", {}, "Se rehízo la operación.", e.currentTarget));
    $("[data-reiniciar]").addEventListener("click", async (e) => {
      if (!confirm("¿Recargar la red desde los CSV? Se pierden los cambios y el historial.")) return;
      await cambiar("/api/reiniciar", {}, "Red recargada desde los CSV.", e.currentTarget);
    });
  }

  async function mostrar() {
    try {
      await cargarRutas();
      await Promise.all([pintarRuta(), pintarCerradas(), api("/api/historial").then(pintarPilas)]);
    } catch (error) {
      vaciar($("[data-tira]"), mensaje("error", "No se pudo cargar", error.message));
    }
  }

  registrar("operacion", { iniciar, mostrar });
})();
