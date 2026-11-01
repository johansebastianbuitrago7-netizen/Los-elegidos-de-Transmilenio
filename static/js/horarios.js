window.PulsoHorarios = (() => {
  function html() {
    return `<section class="schedule-layout"><article class="card query-panel"><div class="section-code">CONSULTA / R04</div><h2>Una estación. Sus servicios.</h2><form id="horario-form">
      <label><span class="step-label">01 / ESTACIÓN</span><input name="estacion" list="estaciones" placeholder="Busca una estación" required autocomplete="off"></label>
      <p id="rutas-ayuda" class="field-help" role="status">Selecciona una estación para conocer sus rutas.</p>
      <label><span class="step-label">02 / RUTA Y SENTIDO</span><select name="ruta" disabled required aria-describedby="rutas-ayuda"><option value="">Primero elige una estación</option></select></label>
      <label><span class="step-label">03 / HORA DE SERVICIO</span><input name="hora" value="09:25" placeholder="HH:MM" required pattern="[0-9]{2,}:[0-5][0-9]" aria-describedby="hora-ayuda"></label>
      <p id="hora-ayuda" class="field-help">Formato HH:MM. 25:10 indica el minuto 1510 del servicio; no se transforma en 01:10.</p>
      <button>Consultar horarios →</button></form><details id="ruta-completa"><summary>Ver recorrido del servicio seleccionado</summary><div id="recorrido-horario">Selecciona una ruta.</div></details></article>
      <article class="schedule-result" id="horario-resultado" aria-live="polite"><div class="signal-icon">◷</div><h2>Lee el horario con contexto.</h2><p>Elige una estación y verás únicamente los servicios que pasan por ella. Los extremos provienen del recorrido cargado, sin deducirlos del identificador.</p><div class="note">Registros históricos · Julio 2021<br>No es información en tiempo real. Un evento no confirma llegada, salida ni posibilidad de abordar.</div></article></section>`;
  }
  function iniciar({fetchJSON,esc}) {
    const form=document.querySelector('#horario-form'),select=form.elements.ruta,station=form.elements.estacion;
    const ayuda=document.querySelector('#rutas-ayuda'),out=document.querySelector('#horario-resultado');
    let revision=0;
    const rutaDetalle=async()=>{
      if(!select.value)return;
      const actual=select.value;
      try { const r=await fetchJSON('/api/ruta?'+new URLSearchParams({ruta:actual}));
        if(select.value===actual)document.querySelector('#recorrido-horario').innerHTML=`<ol class="itinerary">${r.estaciones.map(e=>`<li>${esc(e)}</li>`).join('')}</ol>`;
      } catch(e){ayuda.textContent=e.message;}
    };
    async function cargar() {
      const version=++revision;
      select.disabled=true;select.innerHTML='<option value="">Cargando servicios…</option>';
      station.removeAttribute('aria-invalid');
      try {
        const data=await fetchJSON('/api/estacion/rutas?'+new URLSearchParams({estacion:station.value}));
        if(version!==revision)return;
        select.innerHTML=data.rutas.map(r=>`<option value="${esc(r.ruta)}">${esc(r.ruta)} · ${esc(r.origen)} → ${esc(r.destino)}</option>`).join('');
        select.disabled=!data.rutas.length;
        ayuda.textContent=data.estado==='cerrada'?'Esta estación está cerrada en la red de la sesión. Reábrela en Administración para consultar.':data.rutas.length?`${data.rutas.length} rutas disponibles en esta estación.`:'Esta estación no tiene rutas activas.';
        if(!data.rutas.length)select.innerHTML='<option value="">No hay servicios disponibles</option>';
        await rutaDetalle();
      } catch(e){if(version===revision){ayuda.textContent=e.message;station.setAttribute('aria-invalid','true');select.innerHTML='<option value="">Estación no disponible</option>';}}
    }
    station.addEventListener('change',cargar);
    station.addEventListener('input',()=>{revision++;select.disabled=true;select.innerHTML='<option value="">Confirma la estación con Tab o selección</option>';});
    select.addEventListener('change',rutaDetalle);
    form.addEventListener('submit',async e=>{
      e.preventDefault();if(select.disabled)return;
      const button=form.querySelector('button');button.disabled=true;out.setAttribute('aria-busy','true');out.innerHTML='<p class="loading">Buscando en los horarios registrados…</p>';
      try {
        const data=await fetchJSON('/api/horarios?'+new URLSearchParams(new FormData(form)));
        if(!out.isConnected)return;
        const r=data.resultado,p=data.presentacion,delta=r.diferencia_minutos;
        const duracion=m=>m>=60?`${Math.floor(m/60)} h ${String(m%60).padStart(2,'0')} min`:`${m} min`;
        const mensaje=delta===null?'No hay más horarios registrados para esta ruta en esta estación después de la hora seleccionada, dentro del día de servicio.':delta===0?'Hay un registro programado justo a la hora consultada. Diferencia: 0 minutos.':delta>=60?`El siguiente registro disponible está a ${duracion(delta)}. El archivo histórico no contiene eventos intermedios para esta combinación.`:`El siguiente registro está programado ${delta} minutos después de tu hora de consulta.`;
        const toMinutes=h=>{const [a,b]=h.split(':').map(Number);return a*60+b;}; // Solo posiciones gráficas; diferencia definitiva proviene de la API.
        const tiempos=[p.consulta,...r.eventos],ultimo=toMinutes(tiempos.at(-1)),primero=toMinutes(p.consulta),amplitud=Math.max(ultimo-primero,1);
        out.innerHTML=`<div class="section-code">REGISTRO HISTÓRICO / ${esc(p.ruta)}</div><h2>${esc(p.estacion)}</h2><p class="service-direction">${esc(p.origen)} → ${esc(p.destino)}</p><div class="departure-board"><div><span>HORA CONSULTADA</span><strong>${esc(p.consulta)}</strong></div><span class="board-arrow">→</span><div><span>PRÓXIMO REGISTRO</span><strong>${r.eventos.length?esc(r.eventos[0]):'—'}</strong></div></div>${delta!==null?`<p class="time-gap">${duracion(delta)} <small>de diferencia en el archivo (${delta} minutos)</small></p>`:''}<p class="${delta>=60?'note':'explanation'}">${mensaje}</p>
          ${r.eventos.length?`<div class="timeline"><h3>El tiempo entre registros</h3><svg viewBox="0 0 620 100" role="img" aria-label="Posiciones proporcionales al tiempo desde la consulta"><path d="M20 40H600" stroke="#aab6b8" stroke-width="2"/>${tiempos.map((h,i)=>`<circle tabindex="0" cx="${20+(toMinutes(h)-primero)/amplitud*580}" cy="40" r="${i===1?8:5}" fill="${i===0?'#196d70':'#d9233f'}"><title>${i===0?'Consulta':'Evento '+i}: ${h}</title></circle>`).join('')}<text x="20" y="80">${esc(p.consulta)}</text><text x="550" y="80">${esc(tiempos.at(-1))}</text></svg><p class="field-help">Escala proporcional al tiempo. Puntos coincidentes pueden superponerse; cada registro se conserva en la lista.</p><ol class="event-list">${r.eventos.map((h,i)=>`<li><b>${esc(h)}</b><span>Registro ${i+1}</span><small>${i?'Desde el registro anterior: '+duracion(toMinutes(h)-toMinutes(r.eventos[i-1])):'Primer registro desde tu consulta'}</small></li>`).join('')}</ol></div>`:''}<div class="note">${esc(p.tipo)}. La diferencia calculada no representa una espera real del TransMilenio actual.</div><details><summary>¿Cómo se encontró este resultado?</summary><p>El motor agrupa horarios por ruta y estación, mantiene sus minutos ordenados y aplica búsqueda binaria inclusiva. Una coincidencia exacta no se salta; los registros repetidos se conservan.</p></details>`;
      } catch(error){out.innerHTML=`<p class="error" role="alert">${esc(error.message)}. Comprueba la estación, la ruta y el formato HH:MM.</p>`;}
      finally {button.disabled=false;out.removeAttribute('aria-busy');}
    });
  }
  return {html,iniciar};
})();
