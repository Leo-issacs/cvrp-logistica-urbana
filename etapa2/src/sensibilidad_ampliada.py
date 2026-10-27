"""Sensibilidad ampliada (ejecutar después del experimento principal; no cambia la configuración reportada).

Bloques:
  A) ACO en CVRP_10: diseño factorial alfa x beta x rho x hormigas, 30 semillas (200-229), 2000 evaluaciones.
  B) GA en CVRP_10: pm x tamaño de población, 100 semillas (300-399), 2000 evaluaciones;
     y pc con pm en {0.2, 0.4}.
  C) Instancias adicionales E10-a..e (óptimo certificado): GA con pm en {0.1, 0.2, 0.4, 0.6} y ACO, 30 semillas.
  D) Instancias mayores E20 y E30 (sin certificado): GA pm 0.2/0.4 y ACO, presupuestos 2000 y 10000, 10 semillas.
"""
import json, sys, time
from itertools import product
from multiprocessing import Pool
sys.path.insert(0, 'src')
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instancias_extra import EXTRA10, GRANDES
from instrumentado import ga_traza, aco_traza
from exacto_subconjuntos import cvrp_exacto

INST = {'CVRP_10': dict(dem=DEM, Q=Q, depot=DEPOT, d=D)}
INST.update(EXTRA10); INST.update(GRANDES)

def correr(tarea):
    metodo, inst, seed, cfg, zref = tarea
    I = INST[inst]
    t0 = time.perf_counter()
    if metodo == 'ga':
        r = ga_traza(I['dem'], I['Q'], I['depot'], I['d'], seed, z_opt=zref, con_diversidad=False, **cfg)
    else:
        r = aco_traza(I['dem'], I['Q'], I['depot'], I['d'], seed, z_opt=zref, con_diversidad=False,
                      con_feromona=False, **cfg)
    return dict(metodo=metodo, inst=inst, seed=seed, cfg=cfg, z=r['z'], primera_opt=r['primera_opt'],
                n_rutas=len(r['rutas']), t=time.perf_counter() - t0,
                mejoras=[(m[1], m[2]) for m in r['mejoras']])

if __name__ == '__main__':
    zopt = {'CVRP_10': Z_OPT}
    for k, I in EXTRA10.items():
        zopt[k] = cvrp_exacto(I['dem'], I['Q'], I['depot'], I['d'])[0]
    tareas = []
    for a, b, rho, h in product((.5, 1., 2.), (0., 1., 2., 5.), (.1, .2, .5), (10, 20, 40)):
        cfg = dict(alpha=a, beta=b, rho=rho, ants=h, steps=2000 // h)
        tareas += [('aco', 'CVRP_10', s, cfg, Z_OPT) for s in range(200, 230)]
    for pm, pop in product((0., .1, .2, .4, .6, .8, 1.), (10, 20, 40)):
        cfg = dict(pm=pm, pop=pop, steps=2000 // pop)
        tareas += [('ga', 'CVRP_10', s, cfg, Z_OPT) for s in range(300, 400)]
    for pc, pm in product((.5, .7, 1.), (.2, .4)):
        tareas += [('ga', 'CVRP_10', s, dict(pc=pc, pm=pm), Z_OPT) for s in range(300, 400)]
    for k in EXTRA10:
        for pm in (.1, .2, .4, .6):
            tareas += [('ga', k, s, dict(pm=pm), zopt[k]) for s in range(30)]
        tareas += [('aco', k, s, {}, zopt[k]) for s in range(30)]
    for k in GRANDES:
        for steps in (100, 500):
            for pm in (.2, .4):
                tareas += [('ga', k, s, dict(pm=pm, steps=steps), None) for s in range(10)]
            tareas += [('aco', k, s, dict(steps=steps), None) for s in range(10)]
    print(len(tareas), 'corridas', flush=True)
    t0 = time.time()
    with Pool(2) as pool:
        res = pool.map(correr, tareas, chunksize=20)
    print('listo en', round(time.time() - t0), 's')
    json.dump(dict(zopt=zopt, corridas=res), open('resultados/sensibilidad_ampliada.json', 'w'), default=float)
