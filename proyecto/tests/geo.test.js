// Pruebas de la geometría de "crear estación" (mismas funciones que usa el HTML). Correr: node tests/geo.test.js
const fs=require('fs'),assert=require('assert');
eval(fs.readFileSync(__dirname+'/geo_script.js','utf8')+';global.dseg=dseg;global.candidatos=candidatos;global.corridas=corridas');
const COORD={A:[0,0],B:[100,0],C:[200,0],D:[100,100],E:[100,-100]};
const PAR={R:['A','B','C'],S:['D','B','E'],T:['A','B','C']};const RUTAS=['R','S','T'];
// 1) exactamente sobre la línea
let c=candidatos([50,0],RUTAS,PAR,COORD);assert.strictEqual(c[0].d,0);assert.deepStrictEqual([c[0].r,c[0].a,c[0].b],['R','A','B']);
// 2) ligeramente alejada
c=candidatos([150,12],RUTAS,PAR,COORD);assert.strictEqual(Math.round(c[0].d),12);assert.deepStrictEqual([c[0].a,c[0].b],['B','C']);
// 3) entre dos estaciones: inserta entre A y B (a=A, b=B)
c=candidatos([30,-8],RUTAS,PAR,COORD);assert.deepStrictEqual([c[0].a,c[0].b],['A','B']);
// 5) cerca de dos rutas distintas: ambas aparecen, ordenadas por cercanía y luego por nombre
c=candidatos([100,40],RUTAS,PAR,COORD);assert.strictEqual(c[0].r,'S');assert.ok(c.some(x=>x.r==='R')&&c.some(x=>x.r==='T'));
// ruta de una sola estación o estación sin coordenadas: no rompe
assert.deepStrictEqual(candidatos([0,0],['X'],{X:['A']},COORD),[]);
// 4) varias consecutivas: forman UNA corrida entre A y C (sin tramos sueltos)
let nu=new Set(['N1','N2']);let k=corridas(['A','N1','N2','C'],nu);assert.deepStrictEqual(k,[{i:1,e:2,A:'A',B:'C'}]);
// separadas: dos corridas; al inicio o final de ruta: sin A o sin B
k=corridas(['A','N1','B','N2'],nu);assert.strictEqual(k.length,2);assert.strictEqual(k[1].B,undefined);
assert.strictEqual(corridas(['A','B'],nu).length,0);
console.log('geo OK');
