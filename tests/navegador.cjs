// Opcional: requiere Playwright y Chromium; el proyecto no usa Node en ejecución.
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('dialog',d=>d.accept());
 const base=process.env.APP_URL||'http://127.0.0.1:5000';
 await page.goto(base);await page.getByRole('heading',{name:/Tu próximo viaje/}).waitFor();
 await page.screenshot({path:'/tmp/transmilenio-inicio.png',fullPage:true});
 async function section(hash,heading){await page.goto(base+'/#'+hash);await page.getByRole('heading',{name:heading,exact:true}).waitFor();}
 async function submit(form){await form.locator('button').click();await form.locator('xpath=following-sibling::div').locator('p,ol,h3,table').first().waitFor();if(await form.locator('xpath=following-sibling::div').locator('.error').count())throw Error(await form.locator('xpath=following-sibling::div').innerText());}
 await section('estaciones','Cada estación, una conexión');
 let f=page.locator('form[data-operation="estado"]');await f.locator('[name=nombre]').fill('UNIVERSIDADES');await submit(f);
 f=page.locator('form[data-operation="autocompletar"]');await f.locator('[name=prefijo]').fill('CAL');await submit(f);
 await section('planeador','¿A dónde quieres llegar?');f=page.locator('form');await f.locator('[name=origen]').fill('UNIVERSIDADES');await f.locator('[name=destino]').fill('EL TIEMPO - MALOKA');await submit(f);await page.getByText('2 paradas entre estaciones',{exact:false}).waitFor();
 await section('horarios','Tu próxima salida programada');f=page.locator('form');await f.locator('[name=ruta]').fill('1-1');await f.locator('[name=estacion]').fill('UNIVERSIDADES');await submit(f);
 await section('ranking','Las estaciones que más conectan');f=page.locator('form');await f.locator('button').click();await page.locator('.bar-row').first().waitFor();
 await section('administracion','Operación de la red');f=page.locator('form[data-operation="cerrar"]');await f.locator('input').fill('UNIVERSIDADES');await submit(f);await page.getByRole('button',{name:/Deshacer \(1\)/}).click();await page.getByRole('button',{name:/Rehacer \(1\)/}).waitFor();
 await section('simulador','Una fila, muchas historias');await submit(page.locator('form'));await page.locator('.result table').waitFor();
 await section('rendimiento','De la teoría al cronómetro');await page.getByRole('button',{name:'Medir operaciones'}).click();await page.locator('#serie').waitFor();await page.selectOption('#serie','simular_fila');await page.locator('.chart').waitFor();
 await page.setViewportSize({width:390,height:844});await page.goto(base);await page.getByRole('heading',{name:/Tu próximo viaje/}).waitFor();await page.screenshot({path:'/tmp/transmilenio-movil.png',fullPage:true});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Desbordamiento horizontal móvil');
 if(errors.length)throw Error(errors.join('\n'));
 console.log('Navegación, consultas, viaje, horarios, ranking, cierre/deshacer, simulación, rendimiento y vista móvil: OK; sin errores JS.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
