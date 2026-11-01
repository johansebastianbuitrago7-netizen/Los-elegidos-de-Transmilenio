import ast
import csv
import io
import random
import tempfile
import unittest
import zipfile
from collections import deque
from pathlib import Path
from motor import Red, simular_fila
from motor.estructuras import TablaHash, ListaDoble, Pila, Cola, ordenar, limite
from herramientas.restricciones import auditar
from herramientas.rendimiento import generar, medir
from conversion.gtfs import convertir

ROOT=Path(__file__).resolve().parents[1]


def escribir(carpeta, estaciones, rutas, horarios):
    for nombre,header,rows in [('estaciones',['nombre'],[(e,) for e in estaciones]),
                              ('rutas',['ruta','orden','estacion'],rutas),
                              ('horarios',['ruta','estacion','hora'],horarios)]:
        with (Path(carpeta)/(nombre+'.csv')).open('w',encoding='utf8',newline='') as f:
            w=csv.writer(f);w.writerow(header);w.writerows(rows)


class CasoRed(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.rutas={'R':['A','B','C'],'S':['B','D','E'],'T':['A','F','G','E']}
        escribir(self.tmp.name,list('ABCDEFGH'),[(r,i,e) for r,es in self.rutas.items() for i,e in reversed(list(enumerate(es)))],
                 [('R','A','10:00'),('R','A','09:00'),('R','A','09:00'),('S','B','25:10'),('S','B','12:00')])
        self.red=Red(self.tmp.name)

    def test_estado_cierres(self):
        self.assertEqual(self.red.estado('X'),'inexistente')
        self.assertTrue(self.red.cerrar('B'));self.assertEqual(self.red.estado('B'),'cerrada')
        self.assertEqual(self.red.autocompletar('B',2),[])
        self.assertEqual(self.red.rango('B','C'),['C'])
        self.assertNotIn('B',[n for n,_ in self.red.ranking(99)])
        self.assertIsNone(self.red.proximo_bus('B','S','10:00'))
        self.assertIsNone(self.red.viaje('B','E'))
        self.assertTrue(self.red.reabrir('B'))

    def test_autocomplete_rango(self):
        r=self.red
        self.assertEqual(r.autocompletar('',3),['A','B','C'])
        self.assertEqual(r.autocompletar('X',4),[])
        self.assertEqual(r.autocompletar('',0),[])
        self.assertEqual(r.rango('AA','DD'),['B','C','D'])
        self.assertEqual(r.rango('D','A'),[])
        self.assertEqual(r.rango('B','B'),['B'])

    def test_horas_duplicadas(self):
        r=self.red
        self.assertEqual(r.proximo_bus('A','R','09:00'),'09:00')
        self.assertEqual(r.proximo_bus('A','R','09:01'),'10:00')
        self.assertIsNone(r.proximo_bus('A','R','10:01'))
        self.assertEqual(r.proximo_bus('B','S','24:00'),'25:10')
        self.assertEqual(r.ranking(1),[('A',3)])
        self.assertEqual(len(r._horas('R','A')),3)
        for hora in ['9:00','10:60','abc','-1:00']:
            with self.assertRaises(ValueError):r.proximo_bus('A','R',hora)

    def test_viajes(self):
        r=self.red
        self.assertEqual(r.viaje('A','C').estaciones,['A','B','C'])
        # Ambos caminos miden tres enlaces; gana el directo en el desempate.
        self.assertEqual(r.viaje('A','E').rutas,['T'])
        self.assertEqual(r.viaje('C','C').paradas,0)
        self.assertIsNone(r.viaje('C','A'));self.assertIsNone(r.viaje('A','H'))
        r.quitar_parada('T','E')
        v=r.viaje('A','E');self.assertEqual(v.transbordo,'B');self.assertEqual(v.paradas,3)
        r.cerrar('B');self.assertIsNone(r.viaje('A','E'))
        self.assertEqual(r.viaje('A','C').paradas,2)  # Puede atravesar B cerrada.

    def test_edicion_historial(self):
        r=self.red
        r.quitar_parada('R','A');self.assertEqual(r.ranking(1),[('B',2)])
        self.assertIsNone(r.proximo_bus('A','R','08:00'))
        r.deshacer();self.assertEqual(r.recorrido('R'),['A','B','C'])
        self.assertEqual(r.proximo_bus('A','R','08:00'),'09:00')
        r.agregar_parada('R','H','B');r.cerrar('H');r.quitar_parada('R','C')
        for _ in range(3):self.assertTrue(r.deshacer())
        self.assertEqual(r.recorrido('R'),['A','B','C'])
        for _ in range(3):self.assertTrue(r.rehacer())
        self.assertEqual(r.recorrido('R',True),['H','B','A'])
        r.deshacer();r.reabrir('H');self.assertFalse(r.rehacer())
        with self.assertRaises(ValueError):r.agregar_parada('R','B','A')
        with self.assertRaises(ValueError):r.quitar_parada('R','X')
        self.assertIsNone(r.proximo_bus('H','R','00:00'))

    def test_noops_no_historia(self):
        r=self.red
        self.assertFalse(r.reabrir('A'));self.assertFalse(r.deshacer())
        r.cerrar('A');r.deshacer();self.assertFalse(r.reabrir('A'));self.assertTrue(r.rehacer())
        with self.assertRaises(ValueError):r.cerrar('X')

    def test_remove_all(self):
        for n in ['A','B','C']:self.red.quitar_parada('R',n)
        self.assertEqual(self.red.recorrido('R'),[])
        for _ in range(3):self.red.deshacer()
        self.assertEqual(self.red.recorrido('R'),['A','B','C'])

    def test_mutaciones_referencia(self):
        rng=random.Random(49);r=self.red;esperado=['A','B','C'];hist=[];fut=[]
        for _ in range(200):
            op=rng.randrange(4)
            if op==0 and len(esperado)<8 and esperado:
                nueva=rng.choice([e for e in 'ABCDEFGH' if e not in esperado]);despues=rng.choice(esperado)
                hist.append(esperado[:]);fut=[]
                r.agregar_parada('R',nueva,despues);esperado.insert(esperado.index(despues)+1,nueva)
            elif op==1 and esperado:
                e=rng.choice(esperado);hist.append(esperado[:]);fut=[];esperado.remove(e);r.quitar_parada('R',e)
            elif op==2:
                self.assertEqual(r.deshacer(),bool(hist))
                if hist:fut.append(esperado[:]);esperado=hist.pop()
            elif op==3:
                self.assertEqual(r.rehacer(),bool(fut))
                if fut:hist.append(esperado[:]);esperado=fut.pop()
            self.assertEqual(r.recorrido('R'),esperado)
            self.assertEqual(r.recorrido('R',True),esperado[::-1])
            conteos={e:0 for e in 'ABCDEFGH'}
            conteos['B']=2
            if 'A' in esperado:conteos['A']=3
            self.assertEqual(r.ranking(99),sorted(conteos.items(),key=lambda x:(-x[1],x[0])))


class Algoritmos(unittest.TestCase):
    def test_hash_colisiones_resize(self):
        t=TablaHash(1)
        for i in range(1000):t.guardar(str(i),i)
        for i in range(1000):self.assertEqual(t.obtener(str(i)),i)
        for i in range(0,1000,2):self.assertTrue(t.borrar(str(i)))
        self.assertEqual(t.cantidad,500)
        t.guardar('1',500);self.assertEqual(t.obtener('1'),500)
        self.assertFalse(t.borrar('ausente'))

    def test_orden_binaria(self):
        rng=random.Random(3)
        for n in range(80):
            a=[rng.randrange(30) for _ in range(n)]
            self.assertEqual(ordenar(a),sorted(a))
            b=ordenar(a)
            for x in range(31):self.assertEqual(limite(b,x),sum(v<x for v in b))
        self.assertEqual(ordenar([(1,'A'),(1,'B')],lambda x:x[0]),[(1,'A'),(1,'B')])

    def test_pila_cola(self):
        p=Pila();c=Cola()
        for i in range(1000):p.apilar(i);c.poner(i)
        self.assertEqual([p.sacar() for _ in range(1000)],list(reversed(range(1000))))
        self.assertEqual([c.sacar() for _ in range(1000)],list(range(1000)))
        self.assertIsNone(c.sacar());self.assertIsNone(p.sacar());c.poner(2);self.assertEqual(c.sacar(),2)

    def test_simulacion(self):
        r=simular_fila([5,0,0,1],5,2)
        self.assertEqual(r.abordajes,[5,0,0,5]);self.assertEqual(r.esperas,[0,0,0,4])
        self.assertEqual(r.espera_media,1)
        self.assertEqual(simular_fila([],5,2).buses,0)
        self.assertEqual(simular_fila([1000000000],5,1).buses,1)
        for args in [([1],0,1),([1],1,0),([-1],1,1),([1.2],1,1)]:
            with self.assertRaises(ValueError):simular_fila(*args)

    def test_simulacion_grande(self):
        r=simular_fila([0]*200000,3,100)
        self.assertEqual(r.pasajeros,200000);self.assertEqual(r.buses,2000)
        self.assertEqual(r.abordajes[-1],5997)

    def test_restricciones(self):
        self.assertEqual(auditar(ROOT/'motor'),[])
        with tempfile.TemporaryDirectory() as d:
            Path(d,'m.py').write_text('x = {}\ny = sorted([2,1])\n')
            self.assertEqual(len(auditar(d)),2)

    def test_red_real(self):
        r=Red(ROOT/'datos')
        with (ROOT/'datos/estaciones.csv').open() as f:self.assertEqual(len(r.nombres),sum(1 for _ in csv.reader(f))-1)
        self.assertEqual(r.eventos,sum(e.buses for _,e in r.estaciones.elementos()))
        for ruta,lista in r.rutas.elementos():
            es=lista.valores()
            if len(es)>1:
                v=r.viaje(es[0],es[-1]);self.assertIsNotNone(v);self.assertLessEqual(v.paradas,len(es)-1)

    def test_rendimiento(self):
        data=medir(32,3)
        self.assertEqual(len(data['resultados']),52)
        self.assertNotIn('viaje',{x['operacion'] for x in data['resultados']})
        for r in data['resultados']:
            self.assertEqual(len(r['muestras_us']),3);self.assertGreater(r['mediana_us'],0)

    def test_viajes_oraculo(self):
        rng=random.Random(7)
        def distancia(rutas,abiertas,o,d):
            if o not in abiertas or d not in abiertas:return None
            if o==d:return 0
            q=deque();vistos=set()
            for r,es in rutas.items():
                if o in es:q.append((r,es.index(o),0,0))
            while q:
                r,i,c,p=q.popleft()
                clave=(r,i,c)
                if clave in vistos:continue
                vistos.add(clave)
                es=rutas[r]
                if es[i]==d:return p
                # Aristas de costo cero de cambio se procesan primero (0-1 BFS).
                if c==0 and es[i] in abiertas:
                    for r2,es2 in rutas.items():
                        if r2!=r and es[i] in es2:q.appendleft((r2,es2.index(es[i]),1,p))
                if i+1<len(es):q.append((r,i+1,c,p+1))
            return None
        for _ in range(12):
            estaciones=list('ABCDEFG')
            rutas={f'R{i}':rng.sample(estaciones,rng.randint(2,6)) for i in range(5)}
            with tempfile.TemporaryDirectory() as d:
                escribir(d,estaciones,[(r,i,e) for r,es in rutas.items() for i,e in enumerate(es)],[])
                red=Red(d);abiertas=set(estaciones)
                cerrada=rng.choice(estaciones);red.cerrar(cerrada);abiertas.remove(cerrada)
                for o in estaciones:
                    for dest in estaciones:
                        v=red.viaje(o,dest)
                        self.assertEqual(v.paradas if v else None,distancia(rutas,abiertas,o,dest),(rutas,o,dest))


class Conversion(unittest.TestCase):
    def test_gtfs(self):
        with tempfile.TemporaryDirectory() as d:
            zpath=Path(d,'test.zip');out=Path(d,'salida')
            with zipfile.ZipFile(zpath,'w') as z:
                z.writestr('stops.txt','stop_id,stop_name\n1,Árbol\n2,Bosque\n3,Casa\n')
                z.writestr('routes.txt','route_id\nR\n')
                z.writestr('trips.txt','route_id,service_id,trip_id,direction_id\nR,S,T,0\nR,S,U,1\nR,S,V,0\n')
                z.writestr('stop_times.txt','trip_id,arrival_time,departure_time,stop_id,stop_sequence\nT,25:10:20,25:10:20,1,1\nT,25:20:00,25:20:00,2,2\nU,12:00:00,12:00:00,2,1\nU,12:10:00,12:10:00,1,2\nV,10:00:00,10:00:00,1,1\nV,10:10:00,10:10:00,3,2\n')
            resumen=convertir(zpath,out);self.assertEqual(resumen['rutas'],3)
            r=Red(out);self.assertEqual(r.nombres,['ARBOL','BOSQUE','CASA'])
            ruta=next(n for n,v in r.rutas.elementos() if v.valores()==['ARBOL','BOSQUE'])
            self.assertEqual(r.proximo_bus('ARBOL',ruta,'24:00'),'25:10')
            with self.assertRaises(ValueError):convertir(zpath,out)


class Web(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import crear_app
        cls.app=crear_app();cls.app.testing=True
    def setUp(self):self.client=self.app.test_client()
    def test_paginas(self):
        self.assertEqual(self.client.get('/').status_code,200)
        with self.client.get('/static/js/app.js') as respuesta:
            self.assertEqual(respuesta.status_code,200)
        data=self.client.get('/api/red').get_json();self.assertTrue(data['estaciones']);self.assertTrue(data['rutas'])
    def test_operaciones(self):
        r=self.app.config['RED'];e=r.nombres[0];ruta=next(n for n,_ in r.rutas.elementos());rec=r.recorrido(ruta)
        cases=[('estado',{'nombre':e}),('autocompletar',{'prefijo':'','k':5}),('rango',{'desde':e,'hasta':e}),('proximo_bus',{'estacion':rec[0],'ruta':ruta,'hora':'08:00'}),('viaje',{'origen':rec[0],'destino':rec[-1]}),('ranking',{'k':5}),('recorrido',{'ruta':ruta,'al_reves':True}),('cerrar',{'nombre':e}),('deshacer',{}),('rehacer',{}),('reabrir',{'nombre':e}),('simular_fila',{'llegadas':[0,1,2],'frecuencia':5,'capacidad':2})]
        for op,args in cases:
            response=self.client.post('/api/operacion',json={'operacion':op,'argumentos':args})
            self.assertEqual(response.status_code,200,(op,response.get_json()))
        response=self.client.post('/api/rendimiento',json={'base':32,'repeticiones':3})
        self.assertEqual(response.status_code,200)
    def test_errores(self):
        for body in [{},{'operacion':'__dict__'},{'operacion':'estado','argumentos':{}},{'operacion':'ranking','argumentos':{'k':'a'}},{'operacion':'recorrido','argumentos':{'ruta':1,'al_reves':True}}]:
            self.assertEqual(self.client.post('/api/operacion',json=body).status_code,400)
        self.assertEqual(self.client.post('/api/rendimiento',json={'base':999}).status_code,400)

if __name__=='__main__':unittest.main()
