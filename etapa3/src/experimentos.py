"""Diseño factorial de la Etapa 3.

GA : puntos de cruce {1, 2} x prob. de mutación {0.1, 0.2, 0.4} x selección {torneo, ruleta}
ACO: alfa {1, 2} x beta {2, 5} x rho {0.1, 0.5}
Cada combinación se corre con 5 semillas en las 24 instancias. Mismo presupuesto en ambos
algoritmos: 50,000 soluciones evaluadas por corrida (GA 50 x 1000; ACO 25 x 2000).

Uso: python experimentos.py {ga|aco|cw|ga_aleatorio|final} [salida.jsonl]
"""
import itertools as it, json, os, sys, time
from multiprocessing import Pool
import numpy as np
from instancias import leer, todas
from algoritmos import correr_ga, correr_aco, clarke_wright

SEMILLAS = range(5)
GA_NIVELES = dict(puntos=(1, 2), pm=(0.1, 0.2, 0.4), seleccion=('torneo', 'ruleta'))
ACO_NIVELES = dict(alfa=(1.0, 2.0), beta=(2.0, 5.0), rho=(0.1, 0.5))
GA_FIJOS = dict(pop=50, gens=1000, pc=0.9)
ACO_FIJOS = dict(hormigas=25, iters=2000, k_cand=25)
_cache = {}


def inst(nombre):
    if nombre not in _cache:
        _cache[nombre] = leer(nombre)
    return _cache[nombre]


def resumen_hist(h, puntos=100):
    idx = np.linspace(0, len(h) - 1, puntos).round().astype(int)
    return [float(h[i]) for i in idx]


def tarea(args):
    alg, nombre, cfg, semilla = args
    I = inst(nombre)
    if alg in ('ga', 'ga_aleatorio', 'ga_final'):
        r = correr_ga(I, semilla, **GA_FIJOS, **cfg)
    else:
        r = correr_aco(I, semilla, **ACO_FIJOS, **cfg)
    return dict(alg=alg, inst=nombre, semilla=semilla, **{k: v for k, v in cfg.items()},
                z=float(r['z']), z_2opt=float(r['z_2opt']), bks=float(I.bks),
                gap=100 * (r['z'] - I.bks) / I.bks, gap_2opt=100 * (r['z_2opt'] - I.bks) / I.bks,
                it_mejor=r['it_mejor'], evals_mejor=r['evals_mejor'], tiempo=r['tiempo'],
                tiempo_2opt=r['tiempo_2opt'], rutas=len(r['rutas']), hist=resumen_hist(r['hist']))


def combinaciones(niveles):
    claves = list(niveles)
    return [dict(zip(claves, v)) for v in it.product(*niveles.values())]


def tareas(modo, semillas=SEMILLAS, cfg_final=None):
    nombres = todas()
    if modo == 'ga':
        return [('ga', n, c, s) for c in combinaciones(GA_NIVELES) for n in nombres for s in semillas]
    if modo == 'aco':
        return [('aco', n, c, s) for c in combinaciones(ACO_NIVELES) for n in nombres for s in semillas]
    if modo == 'ga_aleatorio':
        c = dict(puntos=2, pm=0.2, seleccion='torneo', inicial='aleatoria')
        return [('ga_aleatorio', n, c, s) for n in nombres for s in semillas]
    if modo == 'final':
        return ([('ga_final', n, cfg_final['ga'], s) for n in nombres for s in semillas] +
                [('aco_final', n, cfg_final['aco'], s) for n in nombres for s in semillas])
    raise ValueError(modo)


def correr(lista, salida, procesos=2):
    hechos = set()
    if os.path.exists(salida):
        for ln in open(salida):
            r = json.loads(ln)
            hechos.add((r['alg'], r['inst'], r['semilla'],
                        json.dumps({k: r[k] for k in sorted(r) if k in ('puntos', 'pm', 'seleccion', 'inicial', 'alfa', 'beta', 'rho')})))
    pend = [t for t in lista if (t[0], t[1], t[3], json.dumps(dict(sorted(t[2].items())))) not in hechos]
    # instancias grandes primero para balancear los procesos
    pend.sort(key=lambda t: -inst(t[1]).n)
    print(f'{len(pend)} corridas pendientes de {len(lista)}', flush=True)
    t0 = time.time()
    with Pool(procesos) as pool, open(salida, 'a') as f:
        for k, r in enumerate(pool.imap_unordered(tarea, pend, chunksize=1), 1):
            f.write(json.dumps(r) + '\n'); f.flush()
            if k % 50 == 0:
                print(f'{k}/{len(pend)}  {time.time() - t0:.0f}s', flush=True)


def correr_cw(salida, reps=5):
    filas = []
    for n in todas():
        I = inst(n)
        ts = []
        for _ in range(reps):
            r = clarke_wright(I); ts.append(r['tiempo'])
        filas.append(dict(alg='cw', inst=n, z=r['z'], z_sin_2opt=r['z_sin_2opt'], bks=float(I.bks),
                          gap=100 * (r['z'] - I.bks) / I.bks, tiempo=float(np.median(ts)),
                          rutas=len(r['rutas'])))
    json.dump(filas, open(salida, 'w'), indent=1)


if __name__ == '__main__':
    modo = sys.argv[1]
    if modo == 'cw':
        correr_cw(sys.argv[2] if len(sys.argv) > 2 else '../resultados/cw.json')
    elif modo == 'final':
        cfg = json.load(open('../resultados/mejores_config.json'))
        correr(tareas('final', semillas=range(5, 10), cfg_final=cfg), '../resultados/final.jsonl')
    else:
        correr(tareas(modo), sys.argv[2] if len(sys.argv) > 2 else f'../resultados/{modo}.jsonl')
