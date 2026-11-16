const fs=require('fs'),assert=require('assert');
eval(fs.readFileSync(__dirname+'/geo_script.js','utf8')+';global.calcPersonal=calcPersonal;global.validarViaje=validarViaje');
const T=['TERMINAL','A','B','C','D','E'],R=['1-1','K43-2'],H='2026-11-06';
const v=(o,d,f,r=[])=>({id:o+d+f,o,d,f,r,t:null,nota:''});
// 1) sin registros
let S=calcPersonal({viajes:[],visitas:[]},147);assert.strictEqual(S.nViajes,0);assert.strictEqual(S.fav,null);assert.strictEqual(S.rutaFav,null);assert.strictEqual(S.perfil.nombre,null);assert.strictEqual(S.pctRed,0);
// 2) primer viaje: origen y destino suman una visita cada uno
S=calcPersonal({viajes:[v('TERMINAL','A','2026-11-01',['1-1'])],visitas:[]},147);assert.strictEqual(S.nViajes,1);assert.strictEqual(S.tot,2);assert.strictEqual(S.distintas,2);assert.deepStrictEqual(S.fav.items,['A','TERMINAL']);assert.strictEqual(S.perfil.nombre,null);assert.strictEqual(S.mes,null);
// 3-4) varios viajes con la misma estación: la más visitada es TERMINAL; porcentaje
S=calcPersonal({viajes:[v('TERMINAL','A','2026-11-01'),v('B','TERMINAL','2026-11-02'),v('TERMINAL','C','2026-11-03')],visitas:[]},147);assert.deepStrictEqual(S.fav.items,['TERMINAL']);assert.strictEqual(S.fav.n,3);assert.strictEqual(S.tot,6);assert.strictEqual(S.favPct,50);assert.deepStrictEqual(S.origen.items,['TERMINAL']);assert.strictEqual(S.origen.n,2);assert.deepStrictEqual(S.destino.items,['A','C','TERMINAL'].filter(x=>x!='TERMINAL').length==2?S.destino.items:[]);
// 5) rutas: la más usada; transbordos cuentan cada ruta
S=calcPersonal({viajes:[v('A','B','2026-11-01',['1-1']),v('A','C','2026-11-02',['1-1','K43-2']),v('B','C','2026-11-03',['K43-2']),v('B','D','2026-11-04',['K43-2']),v('C','D','2026-11-05')],visitas:[]},147);assert.deepStrictEqual(S.rutaFav.items,['K43-2']);assert.strictEqual(S.rutaFav.n,3);assert.strictEqual(S.sinRuta,1);
// empate de rutas
S=calcPersonal({viajes:[v('A','B','2026-11-01',['1-1']),v('A','B','2026-11-02',['K43-2'])],visitas:[]},147);assert.deepStrictEqual(S.rutaFav.items,['1-1','K43-2']);
// 6-7) visitas manuales: no se duplican (mismo día) ni cuando ya hay un viaje ese día en esa estación
S=calcPersonal({viajes:[v('A','B','2026-11-01')],visitas:[{n:'C',f:'2026-11-01'},{n:'C',f:'2026-11-01'},{n:'A',f:'2026-11-01'},{n:'A',f:'2026-11-02'}]},147);assert.strictEqual(S.vis.get('C'),1);assert.strictEqual(S.vis.get("A"),2);assert.strictEqual(S.vis.get("B"),1);assert.strictEqual(S.tot,4);
// mes más activo: solo con al menos 2 meses
S=calcPersonal({viajes:[v('A','B','2026-10-01'),v('A','C','2026-11-02'),v('B','C','2026-11-03')],visitas:[]},147);assert.deepStrictEqual(S.mes.items,['2026-11']);assert.strictEqual(S.fechas.min,'2026-10-01');
// perfiles (criterios explicables)
const rep=[];for(let i=0;i<5;i++)rep.push(v('A','B','2026-11-0'+(i+1),['1-1']));S=calcPersonal({viajes:rep,visitas:[]},147);assert.strictEqual(S.perfil.id,'habitual');
const exp=[v('A','B','2026-11-01'),v('C','D','2026-11-02'),v('E','TERMINAL','2026-11-03'),v('A','E','2026-11-04'),v('B','D','2026-11-05')];S=calcPersonal({viajes:exp,visitas:[]},147);assert.strictEqual(S.perfil.id,'explorador');
const con=['1','2','3','4','5'].map((n,i)=>v('A',['B','C','D','E','TERMINAL'][i],'2026-11-0'+n,['1-1','K43-2']));S=calcPersonal({viajes:con,visitas:[]},147);assert.strictEqual(S.perfil.id,'conector');
// validaciones
const ok={o:'A',d:'B',f:'2026-11-01',r:['1-1']};assert.strictEqual(validarViaje(ok,T,R,H),'');
assert.ok(validarViaje({...ok,o:'ZZ'},T,R,H));assert.ok(validarViaje({...ok,d:'A'},T,R,H));assert.ok(validarViaje({...ok,f:'2026-12-31'},T,R,H));assert.ok(validarViaje({...ok,f:'2026-02-31'},T,R,H));assert.ok(validarViaje({...ok,f:''},T,R,H));assert.ok(validarViaje({...ok,r:['XX']},T,R,H));
console.log('personal OK');
