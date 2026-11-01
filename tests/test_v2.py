import csv
import inspect
import json
import random
import statistics
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from motor import Red,simular_fila
from motor.analisis_fila import AnalisisFila
from servicios.laboratorio import ejecutar,experimento,generar,LIMITE_ANIMADO
from tests.test_proyecto import escribir

ROOT=Path(__file__).resolve().parents[1]


class HorariosV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.red=Red(ROOT/'datos')

    def test_regresion_csv_original(self):
        with (ROOT/'datos/horarios.csv').open(newline='',encoding='utf8') as f:
            originales=sorted(r['hora'] for r in csv.DictReader(f)
                              if r['ruta']=='B10-1' and r['estacion']=='PORTAL NORTE')
        for consulta,esperado in [('08:00','08:18'),('08:18','08:18'),('09:25','11:33'),('11:33','11:33'),('11:34','11:41')]:
            self.assertEqual(next(h for h in originales if h>=consulta),esperado)
            self.assertEqual(self.red.proximo_bus('PORTAL NORTE','B10-1',consulta),esperado)
        self.assertEqual(self.red.siguientes_horarios('PORTAL NORTE','B10-1','09:25'),['11:33','11:41','11:49','11:57','12:06'])

    def test_rutas_sentido(self):
        for ruta,origen,destino in self.red.rutas_estacion('PORTAL NORTE'):
            recorrido=self.red.recorrido(ruta)
            self.assertIn('PORTAL NORTE',recorrido)
            self.assertEqual((origen,destino),(recorrido[0],recorrido[-1]))
        with self.assertRaises(ValueError):self.red.rutas_estacion('NO EXISTE')

    def test_eventos_duplicados_cierre_edicion(self):
        with tempfile.TemporaryDirectory() as d:
            escribir(d,['A','B','C'],[('R',2,'B'),('R',1,'A')],
                     [('R','A','25:10'),('R','A','09:00'),('R','A','09:00')])
            red=Red(d)
            self.assertEqual(red.siguientes_horarios('A','R','09:00'),['09:00','09:00','25:10'])
            self.assertEqual(red.siguientes_horarios('A','R','25:11'),[])
            with self.assertRaises(ValueError):red.siguientes_horarios('C','R','00:00')
            with self.assertRaises(ValueError):red.siguientes_horarios('A','R','0:00')
            red.cerrar('A');self.assertEqual(red.rutas_estacion('A'),[])
            with self.assertRaises(ValueError):red.siguientes_horarios('A','R','00:00')
            red.deshacer();red.quitar_parada('R','A')
            with self.assertRaises(ValueError):red.siguientes_horarios('A','R','00:00')
            red.deshacer();self.assertEqual(red.siguientes_horarios('A','R','24:00'),['25:10'])
            red.agregar_parada('R','C','A');self.assertEqual(red.siguientes_horarios('C','R','00:00'),[])

    def test_firmas_publicas(self):
        firmas={'estado':'(self, nombre)','autocompletar':'(self, prefijo, k)','rango':'(self, desde, hasta)',
                'proximo_bus':'(self, estacion, ruta, hora)','viaje':'(self, origen, destino)',
                'ranking':'(self, k)','agregar_parada':'(self, ruta, nueva, despues_de)',
                'quitar_parada':'(self, ruta, estacion)','recorrido':'(self, ruta, al_reves=False)',
                'cerrar':'(self, nombre)','reabrir':'(self, nombre)','deshacer':'(self)','rehacer':'(self)'}
        for nombre,firma in firmas.items():self.assertEqual(str(inspect.signature(getattr(Red,nombre))),firma)
        self.assertEqual(str(inspect.signature(simular_fila)),'(llegadas, frecuencia, capacidad)')


class LaboratorioV2(unittest.TestCase):
    def test_educativo_obligatorio(self):
        r=ejecutar([0,0,1,2,5,5,9],5,3,True)
        self.assertEqual(r['abordajes'],[0,0,5,5,5,10,10])
        self.assertEqual(r['esperas'],[0,0,4,3,0,5,1])
        m=r['metricas'];self.assertEqual(m['espera_total'],13)
        self.assertAlmostEqual(m['espera_media'],13/7)
        self.assertEqual(m['cola_maxima'],4)
        self.assertEqual(m['espera_mediana'],1)
        self.assertEqual(m['espera_p95'],5)
        self.assertEqual(m['buses'],3)
        self.assertAlmostEqual(m['ocupacion_media'],7/9)
        self.assertEqual(m['ultimo_abordaje'],10)
        saturada=next(p for p in r['pasos'] if p['minuto']==5 and p['fase']=='abordaje')
        self.assertEqual(saturada['abordando'],[2,3,4]);self.assertEqual(saturada['fila'],[5])
        llegada=next(p for p in r['pasos'] if p['minuto']==5 and p['fase']=='llegadas')
        self.assertEqual(llegada['fila'],[2,3,4,5])

    def test_metricas_referencia(self):
        rng=random.Random(33)
        for _ in range(80):
            llegadas=[rng.randrange(40) for _ in range(rng.randrange(1,50))]
            f=rng.randrange(1,12);cap=rng.randrange(1,10)
            r=simular_fila(llegadas,f,cap);a=AnalisisFila(llegadas,r,f,cap)
            self.assertEqual(a.espera_mediana,statistics.median(r.esperas))
            self.assertEqual(a.espera_p95,sorted(r.esperas)[(95*len(llegadas)+99)//100-1])
            self.assertEqual(a.buses,len(Counter(r.abordajes)))
            self.assertEqual(a.ultimo_abordaje,max(r.abordajes))
            cola=max(sum(l<=t<=b for l,b in zip(llegadas,r.abordajes)) for t in set(llegadas+r.abordajes))
            self.assertEqual(a.cola_maxima,cola)
            self.assertEqual(sum(f[2] for f in a.distribucion),len(llegadas))
            self.assertEqual(sum(f[1] for f in a.ocupacion),len(llegadas))
            self.assertTrue(all(f[1]+f[2]==cap for f in a.ocupacion))

    def test_simultaneos_vacio_hueco(self):
        for llegadas,f,c,esperado in [([5,5],5,10,[5,5]),([0,0,0],10,1,[0,10,20]),([0,1],1,1,[0,1]),([],5,3,[]),([1000000000],1440,1,[1000000800])]:
            r=ejecutar(llegadas,f,c,True)
            self.assertEqual(r['abordajes'],esperado)
            if not llegadas:self.assertTrue(all(x==0 for x in r['metricas'].values()))

    def test_semilla_y_mismas_llegadas(self):
        cuerpo={'modo':'avanzado','cantidad':600,'duracion':60,'escenario':'intensa','semilla':44,
                'a':{'frecuencia':5,'capacidad':10},'b':{'frecuencia':5,'capacidad':10}}
        a=experimento(cuerpo);b=experimento(cuerpo)
        self.assertEqual(a,b);self.assertEqual(a['a'],a['b'])
        self.assertEqual(a['diferencias']['espera_media']['b_menos_a'],0)
        cuerpo['b']['capacidad']=20
        mejor=experimento(cuerpo)
        self.assertEqual(a['huella_llegadas'],mejor['huella_llegadas'])
        self.assertLessEqual(mejor['b']['metricas']['espera_media'],mejor['a']['metricas']['espera_media'])
        for tipo in ('baja','media','intensa'):
            self.assertEqual(generar(100,60,tipo,42),generar(100,60,tipo,42))

    def test_limites_y_grande(self):
        with self.assertRaises(ValueError):ejecutar([0]*41,5,3,True)
        r=ejecutar(list(range(100000)),5,20)
        self.assertNotIn('pasos',r);self.assertNotIn('abordajes',r);self.assertNotIn('esperas',r)
        self.assertLessEqual(len(r['series']['fila']),162)
        self.assertLess(len(json.dumps(r)),50000)
        self.assertEqual(r['metricas']['abordados'],100000)
        for args in [([-1],5,3),([0],0,3),([0],5,0),([0],True,3)]:
            with self.assertRaises(ValueError):ejecutar(*args)


class APIV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import crear_app
        cls.app=crear_app();cls.app.testing=True
    def setUp(self):self.c=self.app.test_client()
    def test_endpoints_horarios(self):
        r=self.c.get('/api/horarios',query_string={'estacion':'PORTAL NORTE','ruta':'B10-1','hora':'09:25'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['resultado']['diferencia_minutos'],128)
        self.assertEqual(r.json['presentacion']['origen'],'PORTAL 80')
        self.assertEqual(self.c.get('/api/ruta?ruta=B10-1').json['estaciones'][-1],'PORTAL NORTE')
        self.assertTrue(self.c.get('/api/estacion/rutas?estacion=PORTAL+NORTE').json['rutas'])
        self.app.config['RED'].cerrar('PORTAL NORTE')
        self.assertEqual(self.c.get('/api/estacion/rutas?estacion=PORTAL+NORTE').json['rutas'],[])
        self.assertEqual(self.c.get('/api/horarios',query_string={'estacion':'PORTAL NORTE','ruta':'B10-1','hora':'09:25'}).status_code,400)
        self.app.config['RED'].reabrir('PORTAL NORTE')
        self.assertEqual(self.c.get('/api/ruta?ruta=NO').status_code,400)
        self.assertEqual(self.c.get('/api/horarios?estacion=PORTAL+80&ruta=1-4&hora=09:25').status_code,400)
    def test_endpoint_laboratorio(self):
        self.assertEqual(self.c.post('/api/laboratorio',json={'modo':'educativo','llegadas':[0],'frecuencia':5,'capacidad':3}).status_code,200)
        for b in [None,[],{}, {'modo':'educativo','llegadas':[0]*41,'frecuencia':5,'capacidad':3}]:
            self.assertEqual(self.c.post('/api/laboratorio',json=b).status_code,400)
