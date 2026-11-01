/* Componentes de representación. No contienen planificación ni asignación FIFO. */
window.PulsoVista = (() => {
  const esc = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const numero = (n) =>
    Number(n).toLocaleString("es-CO", { maximumFractionDigits: 2 });
  const indicador = (valor, texto, unidad = "") =>
    `<div class="metric"><strong>${numero(valor)}<small>${unidad}</small></strong><span>${texto}</span></div>`;
  function grafico(
    titulo,
    filas,
    nombres,
    columnas,
    etiquetas,
    escalonado = false,
  ) {
    if (!filas.length)
      return `<section class="plot"><h3>${titulo}</h3><p class="empty">No hay eventos que representar.</p></section>`;
    const xmax = Math.max(...filas.map((f) => f[0]), 1),
      ymax = Math.max(...filas.flatMap((f) => columnas.map((c) => f[c])), 1);
    const x = (t) => 45 + (t / xmax) * 570,
      y = (v) => 190 - (v / ymax) * 150;
    const colores = ["#196D70", "#D9233F"];
    const series = columnas
      .map((c, j) => {
        if (escalonado && j === 0) return ""; // El valor antes del abordaje es instantáneo, no un nivel sostenido.
        const puntos = filas
          .map(
            (f, i) =>
              `${i && escalonado ? "H" + x(f[0]) + "V" : i ? "L" : "M"}${i && escalonado ? y(f[c]) : x(f[0]) + "," + y(f[c])}`,
          )
          .join(" ");
        return `<path d="${puntos}" fill="none" stroke="${colores[j]}" stroke-width="2.5"/>`;
      })
      .join("");
    const dots = filas
      .map((f) =>
        columnas
          .map(
            (c, j) =>
              `<circle tabindex="0" cx="${x(f[0])}" cy="${y(f[c])}" r="3" fill="${colores[j]}"><title>${esc(etiquetas[0])}: ${numero(f[0])}; ${esc(nombres[j])}: ${numero(f[c])}</title></circle>`,
          )
          .join(""),
      )
      .join("");
    return `<section class="plot"><h3>${titulo}</h3><svg class="chart" viewBox="0 0 650 230" role="img" aria-label="${esc(titulo)}"><path d="M45 25V190H620" fill="none" stroke="#aab6b8"/><text x="4" y="25">${numero(ymax)}</text><text x="26" y="195">0</text><text x="45" y="215">0</text><text x="580" y="215">${numero(xmax)}</text>${series}${dots}</svg><p class="plot-legend">${nombres.map((n, j) => `<span><i style="background:${colores[j]}"></i>${n}</span>`).join("")} · ${etiquetas.join(" / ")}</p><details><summary>Ver datos de la gráfica</summary><div class="table-wrap"><table><thead><tr>${etiquetas.map((t) => `<th>${t}</th>`).join("")}</tr></thead><tbody>${filas.map((f) => `<tr>${[f[0], ...columnas.map((c) => f[c])].map((v) => `<td>${numero(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div></details></section>`;
  }
  function barras(titulo, filas, texto, valor, unidad) {
    const mayor = Math.max(...filas.map((f) => f[valor]), 1);
    return `<section class="plot"><h3>${titulo}</h3><div class="bar-list">${filas.map((f) => `<div class="histogram-row"><span>${esc(texto(f))}</span><meter min="0" max="${mayor}" value="${f[valor]}">${f[valor]}</meter><b>${numero(f[valor])}</b></div>`).join("")}</div><p class="muted">${unidad}</p></section>`;
  }
  return { esc, numero, indicador, grafico, barras };
})();
