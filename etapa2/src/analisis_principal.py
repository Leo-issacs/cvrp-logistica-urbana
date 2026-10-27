"""Análisis de la configuración principal (semillas 0-9 y ampliación a 0-99).

Genera resultados/principal.json con:
- trazas completas de GA y ACO (semillas 0-9): diversidad por generación/iteración, mejoras del mejor
  cromosoma, primera evaluación con el óptimo, estadísticas de feromona;
- semillas fallidas 4 y 8 del GA continuadas hasta 500 etapas (la secuencia aleatoria de las primeras 100
  es idéntica, así que es una continuación exacta de la corrida reportada);
- primera evaluación con el óptimo para 100 semillas (0-99) de cada método.
"""
import json, sys, time
sys.path.insert(0, 'src')
from algoritmos import split
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instrumentado import ga_traza, aco_traza

def rutas_info(rutas):
    return [dict(ruta=r, carga=sum(DEM[c] for c in r), dist=sum(D[a, b] for a, b in zip(r, r[1:])))
            for r in rutas]

res = dict(ga={}, aco={}, ga_ext={}, ga_pm04={}, cien=dict(ga=[], aco=[]))
for s in range(10):
    g = ga_traza(DEM, Q, DEPOT, D, s, z_opt=Z_OPT)
    a = aco_traza(DEM, Q, DEPOT, D, s, z_opt=Z_OPT)
    res['ga'][s] = dict(z=g['z'], rutas=rutas_info(g['rutas']), hist=g['hist'], mejoras=g['mejoras'],
                        primera_opt=g['primera_opt'], diversidad=g['diversidad'], perm=g['mejor_perm'])
    res['aco'][s] = dict(z=a['z'], rutas=rutas_info(a['rutas']), hist=a['hist'], mejoras=a['mejoras'],
                         primera_opt=a['primera_opt'], diversidad=a['diversidad'], feromona=a['feromona'],
                         pisos=a['pisos'], perm=a['mejor_perm'],
                         tau_final={f'{i}-{j}': v for (i, j), v in a['tau'].items()})
    print('semilla', s, round(g['z'], 6), g['primera_opt'], round(a['z'], 6), a['primera_opt'], flush=True)
for s in (4, 8):
    g = ga_traza(DEM, Q, DEPOT, D, s, steps=500, z_opt=Z_OPT)
    res['ga_ext'][s] = dict(z=g['z'], rutas=rutas_info(g['rutas']), hist=g['hist'], mejoras=g['mejoras'],
                            primera_opt=g['primera_opt'], diversidad=g['diversidad'])
    g4 = ga_traza(DEM, Q, DEPOT, D, s, pm=.4, z_opt=Z_OPT)
    res['ga_pm04'][s] = dict(z=g4['z'], primera_opt=g4['primera_opt'], diversidad=g4['diversidad'])
    print('ext', s, round(g['z'], 6), g['primera_opt'], 'pm0.4:', round(g4['z'], 6), g4['primera_opt'])
for s in range(100):
    g = ga_traza(DEM, Q, DEPOT, D, s, z_opt=Z_OPT, con_diversidad=False)
    a = aco_traza(DEM, Q, DEPOT, D, s, z_opt=Z_OPT, con_diversidad=False, con_feromona=False)
    res['cien']['ga'].append(dict(semilla=s, z=g['z'], primera_opt=g['primera_opt']))
    res['cien']['aco'].append(dict(semilla=s, z=a['z'], primera_opt=a['primera_opt']))
json.dump(res, open('resultados/principal.json', 'w'), default=float)
print('ok')
