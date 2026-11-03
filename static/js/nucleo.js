/* Núcleo de la interfaz Atlas: utilidades DOM, API, avisos, combobox y
   navegación por láminas. Sin dependencias ni compilación. */
"use strict";

const Atlas = (() => {
  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => Array.from(raiz.querySelectorAll(sel));

  /** Crea un elemento. attrs: class, text, data-*, aria-*, on<evento>, y atributos. */
  function el(etiqueta, attrs = {}, ...hijos) {
    const nodo = document.createElement(etiqueta);
    for (const [clave, valor] of Object.entries(attrs)) {
      if (valor === null || valor === undefined || valor === false) continue;
      if (clave === "class") nodo.className = valor;
      else if (clave === "text") nodo.textContent = valor;
      else if (clave.startsWith("on")) nodo.addEventListener(clave.slice(2), valor);
      else nodo.setAttribute(clave, valor === true ? "" : valor);
    }
    for (const hijo of hijos.flat()) {
      if (hijo === null || hijo === undefined || hijo === false) continue;
      nodo.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
    }
    return nodo;
  }

  function vaciar(nodo, ...hijos) { nodo.replaceChildren(...hijos.flat().filter(Boolean)); return nodo; }

  async function api(ruta, { metodo = "GET", cuerpo } = {}) {
    const opciones = { method: metodo, headers: {} };
    if (cuerpo !== undefined) {
      opciones.headers["Content-Type"] = "application/json";
      opciones.body = JSON.stringify(cuerpo);
    }
    let respuesta;
    try {
      respuesta = await fetch(ruta, opciones);
    } catch (e) {
      throw new Error("No hay conexión con el servidor. ¿Está corriendo python app.py?");
    }
    const datos = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) throw new Error(datos.error || `Error ${respuesta.status}`);
    return datos;
  }

  const qs = (obj) => new URLSearchParams(obj).toString();

  let temporizadorAviso;
  function aviso(texto, tipo = "info") {
    const caja = $("[data-aviso]");
    caja.textContent = texto;
    caja.className = "aviso" + (tipo === "error" ? " aviso--error" : "");
    caja.hidden = false;
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => { caja.hidden = true; }, 3800);
  }

  function mensaje(tipo, titulo, texto) {
    return el("div", { class: `mensaje mensaje--${tipo}`, role: tipo === "error" ? "alert" : null },
      el("strong", { text: titulo }), texto ? el("span", { text: texto }) : null);
  }

  /** Ejecuta una promesa mostrando el botón en estado de carga. */
  async function conCarga(boton, tarea) {
    if (boton) { boton.classList.add("cargando"); boton.disabled = true; }
    try { return await tarea(); }
    finally { if (boton) { boton.classList.remove("cargando"); boton.disabled = false; } }
  }

  const formato = new Intl.NumberFormat("es-CO");
  const num = (n, decimales = 0) => (n === null || n === undefined) ? "—"
    : new Intl.NumberFormat("es-CO", { maximumFractionDigits: decimales, minimumFractionDigits: decimales }).format(n);

  function duracion(minutos) {
    if (minutos < 60) return `${minutos} min`;
    const h = Math.floor(minutos / 60), m = minutos % 60;
    return m ? `${h} h ${m} min` : `${h} h`;
  }

  function sello(estado) {
    const textos = { abierta: "Abierta", cerrada: "Cerrada", inexistente: "No existe" };
    return el("span", { class: `sello sello--${estado}`, text: textos[estado] || estado });
  }

  function codigoRuta(ruta, variante) {
    return el("span", { class: "codigo-ruta" + (variante ? ` codigo-ruta--${variante}` : ""), text: ruta });
  }

  /* ------------------------------------------------------------ combobox
     Usa R2 (autocompletar del motor) como fuente de sugerencias. */
  let idCombo = 0;
  function combobox(input, { fuente, alElegir, k = 8 } = {}) {
    const lista = el("ul", { class: "combo-lista", role: "listbox", id: `combo-${++idCombo}`, hidden: true });
    input.after(lista);
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-controls", lista.id);
    let opciones = [], activa = -1, espera, pedido = 0;
    const obtener = fuente || (async (prefijo) =>
      (await api(`/api/autocompletar?${qs({ prefijo, k })}`)).resultados);

    function cerrar() { lista.hidden = true; input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant"); activa = -1; }
    function marcar(i) {
      activa = i;
      $$("li", lista).forEach((li, j) => li.setAttribute("aria-selected", String(j === i)));
      if (i >= 0 && lista.children[i]) {
        input.setAttribute("aria-activedescendant", lista.children[i].id);
        lista.children[i].scrollIntoView({ block: "nearest" });
      }
    }
    function elegir(valor) {
      input.value = valor;
      cerrar();
      input.dispatchEvent(new Event("change"));
      if (alElegir) alElegir(valor);
    }
    async function actualizar() {
      const prefijo = input.value.toUpperCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
      const n = ++pedido;
      let resultado;
      try { resultado = await obtener(prefijo.trimStart()); } catch { return; }
      if (n !== pedido) return;
      opciones = resultado;
      vaciar(lista, opciones.length ? opciones.map((nombre, i) => {
        const largo = prefijo.trimStart().length;
        return el("li", { role: "option", id: `${lista.id}-${i}`, "aria-selected": "false",
          onmousedown: (e) => { e.preventDefault(); elegir(nombre); } },
          el("span", {}, el("mark", { text: nombre.slice(0, largo) }), nombre.slice(largo)));
      }) : [el("li", { class: "vacio", text: "Sin estaciones abiertas con ese inicio" })]);
      lista.hidden = false;
      input.setAttribute("aria-expanded", "true");
      activa = -1;
    }
    input.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(actualizar, 110); });
    input.addEventListener("focus", () => { if (!input.value) actualizar(); });
    input.addEventListener("blur", () => setTimeout(cerrar, 120));
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); if (lista.hidden) actualizar(); else marcar(Math.min(activa + 1, opciones.length - 1)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); marcar(Math.max(activa - 1, 0)); }
      else if (e.key === "Enter" && !lista.hidden && activa >= 0) { e.preventDefault(); elegir(opciones[activa]); }
      else if (e.key === "Escape") cerrar();
    });
    return { cerrar };
  }

  /* -------------------------------------------------------- navegación */
  const laminas = {};
  const iniciadas = new Set();
  function registrar(nombre, modulo) { laminas[nombre] = modulo; }

  function mostrar(nombre, { enfocar = true } = {}) {
    if (!$(`[data-lamina="${nombre}"]`)) nombre = "portada";
    $$("[data-lamina]").forEach((s) => { s.hidden = s.dataset.lamina !== nombre; });
    $$("[data-ir]").forEach((a) => {
      if (a.dataset.ir === nombre) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    const enlace = $(`[data-ir="${nombre}"]`);
    if (enlace) enlace.scrollIntoView({ inline: "center", block: "nearest" });
    const modulo = laminas[nombre];
    if (modulo) {
      if (!iniciadas.has(nombre)) { iniciadas.add(nombre); modulo.iniciar && modulo.iniciar(); }
      modulo.mostrar && modulo.mostrar();
    }
    document.title = `${enlace ? enlace.querySelector(".linea__nombre").textContent + " · " : ""}Atlas`;
    if (enfocar) { window.scrollTo({ top: 0 }); $("#contenido").focus({ preventScroll: true }); }
  }

  /** Navega a una lámina pasando datos (p. ej. una estación a consultar). */
  function ir(nombre, datos) {
    pendiente[nombre] = datos;
    if (location.hash === `#${nombre}`) mostrar(nombre); else location.hash = nombre;
  }
  const pendiente = {};
  function tomar(nombre) { const d = pendiente[nombre]; delete pendiente[nombre]; return d; }

  window.addEventListener("hashchange", () => mostrar(location.hash.slice(1)));
  document.addEventListener("DOMContentLoaded", () => mostrar(location.hash.slice(1) || "portada", { enfocar: false }));

  /* rutas: caché de etiquetas con extremos reales (se invalida al editar) */
  let cacheRutas = null;
  async function rutas(forzar = false) {
    if (!cacheRutas || forzar) cacheRutas = await api("/api/rutas");
    return cacheRutas;
  }
  function invalidarRutas() { cacheRutas = null; }

  return { $, $$, el, vaciar, api, qs, aviso, mensaje, conCarga, num, formato, duracion, sello, codigoRuta,
    combobox, registrar, mostrar, ir, tomar, rutas, invalidarRutas };
})();
