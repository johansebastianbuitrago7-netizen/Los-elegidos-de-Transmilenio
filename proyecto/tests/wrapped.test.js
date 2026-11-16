const fs=require('fs');eval(fs.readFileSync(__dirname+'/geo_script.js','utf8')+';global.calcWrapped=calcWrapped');
const D=calcWrapped(JSON.parse(fs.readFileSync(__dirname+'/_w.json','utf8')));
console.log(JSON.stringify({nEst:D.nEst,nRut:D.nRut,nCon:D.nCon,top3:D.topEst.slice(0,3).map(e=>e.n),topRutas:D.topEst.slice(0,3).map(e=>e.rutas),larga:D.largas[0][1],corta:D.cortas[0][1],solo1:D.solo1,comp_max:D.compartido.k,redes:D.comp,prom:+D.prom.toFixed(2),horarios:D.horarios}));
