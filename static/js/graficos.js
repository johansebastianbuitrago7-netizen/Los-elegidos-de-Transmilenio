/* Gráficos SVG mínimos hechos a mano: líneas, áreas y barras.
   Solo dibujan lo que reciben; no calculan nada del dominio. */
"use strict";

const Graficos = (() => {
  const NS = "http://www.w3.org/2000/svg";
  function s(etiqueta, attrs = {}, texto) {
    const n = document.createElementNS(NS, etiqueta);
    for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) n.setAttribute(k, v);
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  function escala(d0, d1, r0, r1) {
    const ancho = d1 - d0 || 1;
    return (v) => r0 + (v - d0) / ancho * (r1 - r0);
  }

  function marcasBonitas(maximo, cantidad = 4) {
    if (maximo <= 0) return [0];
    const bruto = maximo / cantidad;
    const mag = Math.pow(10, Math.floor(Math.log10(bruto)));
    const paso = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= bruto) || bruto;
    const marcas = [];
    for (let v = 0; v <= maximo + paso * 0.001; v += paso) marcas.push(+v.toFixed(6));
    return marcas;
  }

  const corto = (v) => {
    const a = Math.abs(v);
    if (a >= 1e6) return (v / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
    if (a >= 1e3) return (v / 1e3).toFixed(1).replace(/\.0$/, "") + "k";
    if (a > 0 && a < 1) return v.toFixed(2);
    return String(Math.round(v * 100) / 100);
  };

  /** series: [{valores:[y...], xs?:[x...], clase, area?}] */
  function lineas(series, { alto = 220, ancho = 560, etiquetaX = "", etiquetaY = "", formatoX = corto, formatoY = corto, xLog = false, marcasX = null, titulo = "" } = {}) {
    const m = { i: 46, d: 12, a: 12, b: 34 };
    const svg = s("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": titulo || etiquetaY });
    let xmin = Infinity, xmax = -Infinity, ymax = 0;
    for (const serie of series) {
      serie.valores.forEach((y, i) => {
        const x = serie.xs ? serie.xs[i] : i;
        xmin = Math.min(xmin, x); xmax = Math.max(xmax, x);
        if (y !== null && y !== undefined) ymax = Math.max(ymax, y);
      });
    }
    const tx = xLog ? (v) => Math.log2(v) : (v) => v;
    const fx = escala(tx(xmin), tx(xmax), m.i, ancho - m.d);
    const marcasY = marcasBonitas(ymax || 1);
    const fy = escala(0, marcasY[marcasY.length - 1], alto - m.b, m.a);
    for (const v of marcasY) {
      svg.append(s("line", { class: "rejilla-svg", x1: m.i, x2: ancho - m.d, y1: fy(v), y2: fy(v) }));
      svg.append(s("text", { class: "texto-eje", x: m.i - 6, y: fy(v) + 3, "text-anchor": "end" }, formatoY(v)));
    }
    svg.append(s("line", { class: "eje", x1: m.i, x2: ancho - m.d, y1: alto - m.b, y2: alto - m.b }));
    const xs = marcasX || marcasBonitas(xmax - xmin, 5).map((v) => v + xmin);
    for (const v of xs) {
      if (v > xmax + 1e-9) continue;
      svg.append(s("text", { class: "texto-eje", x: fx(tx(v)), y: alto - m.b + 14, "text-anchor": "middle" }, formatoX(v)));
    }
    if (etiquetaX) svg.append(s("text", { class: "texto-eje", x: ancho - m.d, y: alto - 4, "text-anchor": "end" }, etiquetaX));
    if (etiquetaY) svg.append(s("text", { class: "texto-eje", x: 4, y: m.a - 2 }, etiquetaY));
    for (const serie of series) {
      const pts = serie.valores.map((y, i) => [fx(tx(serie.xs ? serie.xs[i] : i)), y === null ? null : fy(y)]).filter((p) => p[1] !== null);
      if (!pts.length) continue;
      const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
      if (serie.area) svg.append(s("path", { class: serie.area, d: `${d}L${pts[pts.length - 1][0]},${alto - m.b}L${pts[0][0]},${alto - m.b}Z` }));
      svg.append(s("path", { class: `serie ${serie.clase || "serie--a"}`, d }));
      if (serie.puntos) for (const p of pts) svg.append(s("circle", { class: "punto", cx: p[0], cy: p[1], r: 4, style: serie.colorPunto ? `stroke:${serie.colorPunto}` : null }));
    }
    return svg;
  }

  /** Barras verticales simples. */
  function barras(valores, { alto = 200, ancho = 560, clase = "barra-svg", etiquetaX = "", formatoX = (i) => i, titulo = "" } = {}) {
    const m = { i: 46, d: 8, a: 12, b: 30 };
    const svg = s("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": titulo });
    const ymax = Math.max(1, ...valores);
    const marcas = marcasBonitas(ymax);
    const fy = escala(0, marcas[marcas.length - 1], alto - m.b, m.a);
    for (const v of marcas) {
      svg.append(s("line", { class: "rejilla-svg", x1: m.i, x2: ancho - m.d, y1: fy(v), y2: fy(v) }));
      svg.append(s("text", { class: "texto-eje", x: m.i - 6, y: fy(v) + 3, "text-anchor": "end" }, corto(v)));
    }
    const w = (ancho - m.i - m.d) / Math.max(1, valores.length);
    valores.forEach((v, i) => {
      const r = s("rect", { class: clase, x: m.i + i * w + w * 0.1, width: Math.max(1, w * 0.8), y: fy(v), height: Math.max(0, alto - m.b - fy(v)) });
      r.append(s("title", {}, `${formatoX(i)}: ${v}`));
      svg.append(r);
    });
    const salto = Math.ceil(valores.length / 8);
    for (let i = 0; i < valores.length; i += salto) {
      svg.append(s("text", { class: "texto-eje", x: m.i + i * w + w / 2, y: alto - m.b + 14, "text-anchor": "middle" }, formatoX(i)));
    }
    svg.append(s("line", { class: "eje", x1: m.i, x2: ancho - m.d, y1: alto - m.b, y2: alto - m.b }));
    if (etiquetaX) svg.append(s("text", { class: "texto-eje", x: ancho - m.d, y: alto - 2, "text-anchor": "end" }, etiquetaX));
    return svg;
  }

  return { s, lineas, barras, escala, corto };
})();
