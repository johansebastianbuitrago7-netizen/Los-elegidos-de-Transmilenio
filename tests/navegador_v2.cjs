// Prueba funcional y capturas de la aplicación real. Node es solo herramienta de QA.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
    args: ["--no-sandbox"],
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("dialog", (d) => d.accept());
    const base = process.env.APP_URL || "http://127.0.0.1:5000";
    const dir = path.resolve(__dirname, "../docs/capturas-v2");
    fs.mkdirSync(dir, { recursive: true });
    async function section(id) {
      await page.goto(base + "/#" + id);
      await page.locator("nav a.active").waitFor({ state: "attached" });
      await page.waitForFunction(
        () => !document.querySelector("#pagina .loading"),
      );
    }
    async function shot(name) {
      await page.evaluate(() => scrollTo(0, 0));
      await page.waitForTimeout(100);
      if ((await page.locator("#aviso").innerText()).includes("Cannot"))
        throw Error("Error capturado en la interfaz");
      await page.screenshot({
        path: path.join(dir, name + ".png"),
        fullPage: true,
      });
    }
    async function submit(form) {
      await form.locator("button").click();
      await page
        .locator(`#${await form.getAttribute("data-operation")}-resultado`)
        .locator("p,ol,h2,h3,table")
        .first()
        .waitFor();
      if (
        await page
          .locator(`#${await form.getAttribute("data-operation")}-resultado`)
          .locator(".error")
          .count()
      )
        throw Error("Error de formulario");
    }
    await section("inicio");
    await page.getByRole("heading", { name: /¿De dónde sales/ }).waitFor();
    await shot("01-inicio-escritorio");
    // Dependencias, sentido real y regresión B10-1.
    await section("horarios");
    const f = page.locator("#horario-form");
    if (!(await f.locator("[name=ruta]").isDisabled()))
      throw Error("Ruta habilitada sin estación");
    await f.locator("[name=estacion]").fill("PORTAL NORTE");
    await f.locator("[name=estacion]").press("Tab");
    await f
      .locator('[name=ruta] option[value="B10-1"]')
      .waitFor({ state: "attached" });
    await f.locator("[name=ruta]").selectOption("B10-1");
    await f.locator("button").click();
    await page.locator(".time-gap").waitFor();
    if (
      !(await page.locator("#horario-resultado").innerText()).includes(
        "128 minutos",
      )
    )
      throw Error("Regresión 128 minutos");
    if (
      !(await page.locator("#horario-resultado").innerText()).includes(
        "PORTAL 80 → PORTAL NORTE",
      )
    )
      throw Error("Sentido incorrecto");
    if ((await page.locator(".event-list li").count()) !== 5)
      throw Error("Faltan cinco eventos");
    await shot("02-horarios-b10");
    await f.locator("[name=hora]").fill("08:18");
    await f.locator("button").click();
    await page
      .getByText("Hay un registro programado justo a la hora consultada.", {
        exact: false,
      })
      .waitFor();
    await f.locator("[name=hora]").fill("99:00");
    await f.locator("button").click();
    await page
      .getByText("No hay más horarios registrados", { exact: false })
      .waitFor();
    // Itinerario real con transbordo.
    await section("planeador");
    let form = page.locator("form[data-operation=viaje]");
    await form.locator("[name=origen]").fill("21 ANGELES");
    await form.locator("[name=destino]").fill("AGUAS");
    await submit(form);
    await page.locator(".itinerary .transfer").first().waitFor();
    await shot("03-viaje-transbordo");
    // Escena, anterior/siguiente, play/pause, reset y validación.
    await section("simulador");
    await page.locator("#siguiente").waitFor();
    for (let i = 0; i < 9; i++) await page.locator("#siguiente").click();
    if (
      !(await page.locator(".step-explanation").innerText()).includes(
        "P6 sigue esperando",
      )
    )
      throw Error("No se representa la saturación de P6");
    await shot("04-simulador-saturacion");
    const texto = await page.locator(".step-explanation").innerText();
    await page.locator("#anterior").click();
    await page.locator("#siguiente").click();
    if ((await page.locator(".step-explanation").innerText()) !== texto)
      throw Error("Anterior/siguiente cambió datos");
    await page.locator("#reiniciar").click();
    await page.locator("#velocidad").selectOption("350");
    await page.locator("#reproducir").click();
    await page.waitForTimeout(450);
    await page.locator("#pausar").click();
    const pausa = await page.locator(".playback-meta").innerText();
    await page.waitForTimeout(450);
    if ((await page.locator(".playback-meta").innerText()) !== pausa)
      throw Error("Pausar no detuvo la reproducción");
    await page.locator("#reiniciar").click();
    if (
      !(await page.locator(".playback-meta").innerText()).includes("Paso 1 de")
    )
      throw Error("Reiniciar falló");
    await page.locator("#educativo textarea").fill("-1");
    await page.locator("#educativo button").click();
    await page
      .locator("#lab-error")
      .getByText("Escribe minutos", { exact: false })
      .waitFor();
    // Comparador real con las mismas llegadas, gráficos y descarga.
    await page.locator("#modo-avanzado").click();
    await page.locator("#avanzado [name=escenario]").selectOption("intensa");
    await page.locator("#avanzado button").click();
    await page.locator("#descargar").waitFor();
    await shot("05-comparador-ab");
    await page.locator("[data-graficas=b]").click();
    await page.locator("#graficas-avanzadas .chart").first().waitFor();
    const downloadPromise = page.waitForEvent("download");
    await page.locator("#descargar").click();
    await downloadPromise;
    // Administración con confirmación, cierre real, selector dependiente y undo/redo.
    await section("administracion");
    form = page.locator("form[data-operation=cerrar]");
    await form.locator("input").fill("PORTAL NORTE");
    await submit(form);
    await section("horarios");
    await page.locator("#horario-form [name=estacion]").fill("PORTAL NORTE");
    await page.locator("#horario-form [name=estacion]").press("Tab");
    await page
      .getByText("Esta estación está cerrada", { exact: false })
      .waitFor();
    await section("administracion");
    await page.locator("[data-history=deshacer]").click();
    await page.getByRole("button", { name: /Rehacer \(1\)/ }).waitFor();
    await page.locator("[data-history=rehacer]").click();
    await page.getByRole("button", { name: /Deshacer \(1\)/ }).waitFor();
    await page.locator("[data-history=deshacer]").click();
    await section("ranking");
    await page.locator("form button").click();
    await page.locator(".bar-row").first().waitFor();
    await section("estaciones");
    form = page.locator("form[data-operation=autocompletar]");
    await form.locator("[name=prefijo]").fill("CAL");
    await submit(form);
    await section("rendimiento");
    await page.locator("#benchmark button").click();
    await page.locator("#serie").waitFor();
    await page.locator("#serie").selectOption("simular_fila");
    await shot("06-rendimiento");
    // Cinco tamaños en todas las pantallas, con navegación y reduced motion.
    for (const width of [1440, 1024, 768, 390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      for (const id of [
        "inicio",
        "estaciones",
        "planeador",
        "horarios",
        "ranking",
        "administracion",
        "simulador",
        "rendimiento",
      ]) {
        await section(id);
        if (
          await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth + 1,
          )
        )
          throw Error("Desbordamiento " + id + " " + width);
      }
      if (width === 390) {
        await section("inicio");
        await shot("07-inicio-movil");
        await section("simulador");
        await page.locator("#siguiente").waitFor();
        await shot("08-simulador-movil");
      }
    }
    await page.emulateMedia({ reducedMotion: "reduce" });
    await section("simulador");
    await page.locator("#siguiente").waitFor();
    await page.locator("#menu-toggle").click();
    await page
      .getByRole("navigation")
      .getByRole("link", { name: "Horarios" })
      .click();
    await page.locator("#horario-form").waitFor();
    await page.locator("#horario-form [name=estacion]").focus();
    await page.keyboard.press("Tab");
    if (errors.length) throw Error(errors.join("\n"));
    console.log(
      "V2 OK: horarios, itinerario, FIFO/control completo, A/B, descarga, cierres/undo/redo, ranking, estaciones, benchmark, teclado y 8 pantallas × 5 anchos. Sin errores JS. Capturas en docs/capturas-v2.",
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
