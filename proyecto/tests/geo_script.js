function dseg(p,A,B){const vx=B[0]-A[0],vy=B[1]-A[1],l=vx*vx+vy*vy||1;let t=((p[0]-A[0])*vx+(p[1]-A[1])*vy)/l;t=Math.max(0,Math.min(1,t));return Math.hypot(p[0]-(A[0]+t*vx),p[1]-(A[1]+t*vy))}
function candidatos(p,RUTAS,PAR,COORD){const o={};RUTAS.forEach(r=>{const a=PAR[r]||[];for(let i=0;i<a.length-1;i++){const A=COORD[a[i]],B=COORD[a[i+1]];if(!A||!B)continue;const d=dseg(p,A,B);if(!o[r]||d<o[r].d)o[r]={r,a:a[i],b:a[i+1],d}}});return Object.values(o).sort((x,y)=>x.d-y.d||(x.r<y.r?-1:1))}
function corridas(a,nu){const c=[];for(let i=0;i<a.length;i++){if(!nu.has(a[i])||(i>0&&nu.has(a[i-1])))continue;let e=i;while(e+1<a.length&&nu.has(a[e+1]))e++;c.push({i,e,A:a[i-1],B:a[e+1]})}return c}
function calcWrapped(W){const R=W.rutas,rs=Object.keys(R),rutasDe=new Map(),ady=new Map(),tramo=new Map();
 const add=(m,k,v)=>{if(!m.has(k))m.set(k,new Set());m.get(k).add(v)};
 rs.forEach(r=>R[r].forEach((s,i)=>{add(rutasDe,s,r);if(i>0){const a=R[r][i-1];add(ady,a,s);add(ady,s,a);add(tramo,a<s?a+'|'+s:s+'|'+a,r)}}));
 const pa=new Map();rutasDe.forEach((_,s)=>pa.set(s,s));const f=x=>{while(pa.get(x)!==x){pa.set(x,pa.get(pa.get(x)));x=pa.get(x)}return x};
 tramo.forEach((_,k)=>{const [a,b]=k.split('|');pa.set(f(a),f(b))});
 const cmp=(x,y)=>y[1]-x[1]||(x[0]<y[0]?-1:1),len=rs.map(r=>[r,R[r].length]).sort(cmp),
  conex=rs.map(r=>[r,R[r].filter(s=>rutasDe.get(s).size>1).length]).sort(cmp),
  top=[...rutasDe].map(([s,t])=>({n:s,rutas:t.size,vec:ady.has(s)?ady.get(s).size:0})).sort((a,b)=>b.rutas-a.rutas||b.vec-a.vec||(a.n<b.n?-1:1));
 let comp=null;tramo.forEach((t,k)=>{if(!comp||t.size>comp.k||(t.size==comp.k&&k<comp.key)){const [a,b]=k.split('|');comp={a,b,k:t.size,key:k}}});
 return{nEst:W.estaciones.length,conRuta:rutasDe.size,nRut:rs.length,nCon:tramo.size,comp:new Set([...rutasDe.keys()].map(f)).size,
  prom:rs.reduce((s,r)=>s+R[r].length,0)/rs.length,horarios:W.horarios,largas:len,cortas:[...len].reverse(),conex,topEst:top.slice(0,5),
  maxVec:[...top].sort((a,b)=>b.vec-a.vec||(a.n<b.n?-1:1))[0],solo1:top.filter(e=>e.rutas==1).length,compartido:comp}}
function validarViaje(v,TODAS,RUTAS,hoy){if(!v.o||!TODAS.includes(v.o))return 'Elige una estación de origen válida.';if(!v.d||!TODAS.includes(v.d))return 'Elige una estación de destino válida.';if(v.o===v.d)return 'El origen y el destino no pueden ser la misma estación.';
 if(!/^\d{4}-\d{2}-\d{2}$/.test(v.f||''))return 'Escribe una fecha válida.';const d=new Date(v.f+'T00:00:00');if(isNaN(d)||d.toISOString().slice(0,10)!==v.f)return 'Esa fecha no existe.';if(v.f>hoy)return 'La fecha no puede ser futura.';
 for(const r of v.r||[])if(!RUTAS.includes(r))return 'La ruta '+r+' no existe.';return ''}
function calcPersonal(P,nEst){const V=P.viajes||[],M=P.visitas||[],cnt=a=>{const m=new Map();a.forEach(x=>m.set(x,(m.get(x)||0)+1));return m},
 top=m=>{let n=0;m.forEach(v=>{if(v>n)n=v});return n?{n,items:[...m].filter(e=>e[1]==n).map(e=>e[0]).sort()}:null},
 ord=m=>[...m].sort((a,b)=>b[1]-a[1]||(a[0]<b[0]?-1:1)),vis=new Map(),add=s=>vis.set(s,(vis.get(s)||0)+1),dia=new Set(),seen=new Set();
 V.forEach(v=>{add(v.o);add(v.d);dia.add(v.o+'|'+v.f);dia.add(v.d+'|'+v.f)});
 M.forEach(x=>{const k=x.n+'|'+x.f;if(seen.has(k)||dia.has(k))return;seen.add(k);add(x.n)});
 let tot=0;vis.forEach(v=>tot+=v);
 const fe=V.map(v=>v.f).concat(M.map(x=>x.f)).sort(),meses=cnt(V.map(v=>v.f.slice(0,7))),fav=top(vis),oc=cnt(V.map(v=>v.o)),dc=cnt(V.map(v=>v.d)),
  rutas=cnt([].concat(...V.map(v=>v.r||[]))),rec=top(cnt(V.map(v=>v.o+' → '+v.d))),par=top(cnt(V.map(v=>v.o<v.d?v.o+' ↔ '+v.d:v.d+' ↔ '+v.o))),
  conR=V.filter(v=>(v.r||[]).length),trans=conR.filter(v=>v.r.length>1).length,pc=x=>Math.round(100*x);
 let perfil={id:null,nombre:null,motivo:'Aún no hay suficientes registros: se necesitan al menos 5 viajes.'};
 if(V.length>=5){const rep=rec.n/V.length,vari=vis.size/tot,dir=conR.length?(conR.length-trans)/conR.length:0;
  if(conR.length>=5&&trans/conR.length>=.4)perfil={id:'conector',nombre:'El Conector',motivo:pc(trans/conR.length)+'% de tus viajes con ruta usaron más de una ruta (se asigna desde 40%).'};
  else if(rec.n>=3&&rep>=.4)perfil={id:'habitual',nombre:'El Habitual',motivo:'Tu recorrido más repetido ('+rec.items[0]+') suma '+rec.n+' de tus '+V.length+' viajes: '+pc(rep)+'% (se asigna desde 40%).'};
  else if(vari>=.6)perfil={id:'explorador',nombre:'El Explorador',motivo:'Visitaste '+vis.size+' estaciones distintas en '+tot+' visitas: '+pc(vari)+' de cada 100 visitas fue a una estación diferente (se asigna desde 60%).'};
  else if(conR.length>=5&&dir>=.7)perfil={id:'directo',nombre:'El Viajero Directo',motivo:pc(dir)+'% de tus viajes con ruta fueron directos, sin transbordo (se asigna desde 70%).'};
  else perfil={id:'equilibrado',nombre:'El Viajero Equilibrado',motivo:'Ningún patrón domina tus registros: ni repites mucho un recorrido, ni exploras casi siempre estaciones nuevas, ni predominan los transbordos.'}}
 return{nViajes:V.length,nMarcas:M.length,tot,distintas:vis.size,pctRed:nEst?Math.round(1000*vis.size/nEst)/10:null,fechas:{min:fe[0]||null,max:fe[fe.length-1]||null,n:new Set(fe).size},
  fav,favPct:fav&&tot?Math.round(1000*fav.n/tot)/10:null,origen:top(oc),destino:top(dc),oTop:ord(oc),dTop:ord(dc),rutaFav:top(rutas),sinRuta:V.length-conR.length,rec,par,mes:meses.size>=2?top(meses):null,nMeses:meses.size,perfil,vis}}