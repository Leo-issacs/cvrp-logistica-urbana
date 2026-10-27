"""Análisis estadístico de los experimentos de la Etapa 3 -> resultados/analisis.json"""
import json, itertools as it
from collections import defaultdict
import numpy as np
from scipy import stats
from instancias import todas, leer

R = '../resultados/'


def cargar(f):
    return [json.loads(l) for l in open(R + f)]


def clave_ga(r):
    return (r['puntos'], r['pm'], r['seleccion'])


def clave_aco(r):
    return (r['alfa'], r['beta'], r['rho'])


def por_celda(filas, clave):
    """celda -> instancia -> listas de métricas (5 semillas)"""
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in filas:
        for m in ('gap', 'gap_2opt', 'tiempo', 'it_mejor', 'evals_mejor', 'z'):
            T[clave(r)][r['inst']][m].append(r[m])
    return T


def matriz(T, metrica, celdas, inst):
    return np.array([[np.mean(T[c][i][metrica]) for c in celdas] for i in inst])


def resumen_factorial(T, celdas, nombres_factores):
    inst = todas()
    G = matriz(T, 'gap', celdas, inst)
    rangos = np.apply_along_axis(stats.rankdata, 1, G)
    fr = stats.friedmanchisquare(*G.T)
    filas = []
    for k, c in enumerate(celdas):
        filas.append(dict(celda=list(c), gap=float(G[:, k].mean()), gap_med=float(np.median(G[:, k])),
                          gap_2opt=float(matriz(T, 'gap_2opt', celdas, inst)[:, k].mean()),
                          rango=float(rangos[:, k].mean()),
                          tiempo=float(matriz(T, 'tiempo', celdas, inst)[:, k].mean()),
                          it_mejor=float(matriz(T, 'it_mejor', celdas, inst)[:, k].mean()),
                          gana=int((G[:, k] == G.min(1)).sum()),
                          sd_semillas=float(np.mean([np.std(T[c][i]['gap'], ddof=1) for i in inst]))))
    efectos = {}
    for f, nombre in enumerate(nombres_factores):
        niveles = sorted({c[f] for c in celdas}, key=str)
        por_nivel = {}
        for lv in niveles:
            idx = [k for k, c in enumerate(celdas) if c[f] == lv]
            por_nivel[str(lv)] = dict(
                gap=float(G[:, idx].mean()),
                tiempo=float(matriz(T, 'tiempo', celdas, inst)[:, idx].mean()),
                it_mejor=float(matriz(T, 'it_mejor', celdas, inst)[:, idx].mean()),
                rango=float(rangos[:, idx].mean()))
        # prueba pareada sobre instancias: promedio de las celdas de cada nivel por instancia
        M = np.array([G[:, [k for k, c in enumerate(celdas) if c[f] == lv]].mean(1) for lv in niveles]).T
        if len(niveles) == 2:
            w = stats.wilcoxon(M[:, 0], M[:, 1])
            prueba = dict(prueba='Wilcoxon', p=float(w.pvalue),
                          gana_nivel0=int((M[:, 0] < M[:, 1]).sum()), n=len(inst))
        else:
            fr2 = stats.friedmanchisquare(*M.T)
            pares = {}
            for a, b in it.combinations(range(len(niveles)), 2):
                pares[f'{niveles[a]} vs {niveles[b]}'] = float(stats.wilcoxon(M[:, a], M[:, b]).pvalue)
            prueba = dict(prueba='Friedman', p=float(fr2.pvalue), pares_wilcoxon=pares)
        efectos[nombre] = dict(niveles=por_nivel, **prueba)
    return dict(celdas=filas, friedman_p=float(fr.pvalue), efectos=efectos)


def por_instancia(T, celda):
    out = {}
    for i in todas():
        c = T[celda][i]
        out[i] = {m: float(np.mean(c[m])) for m in c} | {'gap_min': float(min(c['gap'])),
                                                          'gap_sd': float(np.std(c['gap'], ddof=1))}
    return out


if __name__ == '__main__':
    ga, aco = cargar('ga.jsonl'), cargar('aco.jsonl')
    Tg, Ta = por_celda(ga, clave_ga), por_celda(aco, clave_aco)
    cg = sorted(Tg, key=str); ca = sorted(Ta, key=str)
    A = dict(ga=resumen_factorial(Tg, cg, ['puntos', 'pm', 'seleccion']),
             aco=resumen_factorial(Ta, ca, ['alfa', 'beta', 'rho']))
    mejor_ga = min(A['ga']['celdas'], key=lambda f: (f['rango'], f['gap']))['celda']
    mejor_aco = min(A['aco']['celdas'], key=lambda f: (f['rango'], f['gap']))['celda']
    A['mejor_ga'], A['mejor_aco'] = mejor_ga, mejor_aco
    A['inst_ga'] = por_instancia(Tg, tuple(mejor_ga))
    A['inst_aco'] = por_instancia(Ta, tuple(mejor_aco))
    al = cargar('ga_aleatorio.jsonl')
    base = [r for r in ga if (r['puntos'], r['pm'], r['seleccion']) == (2, 0.2, 'torneo')]
    A['inicial'] = {i: dict(aleatoria=float(np.mean([r['gap'] for r in al if r['inst'] == i])),
                            heuristica=float(np.mean([r['gap'] for r in base if r['inst'] == i])),
                            t_aleatoria=float(np.mean([r['tiempo'] for r in al if r['inst'] == i])))
                    for i in todas()}
    mb = [r for r in ga if (r['puntos'], r['pm'], r['seleccion']) == tuple(mejor_ga)]
    A['ga_mejora_inicial'] = dict(gap_poblacion_inicial=float(np.mean([100 * (r['hist'][0] - r['bks']) / r['bks'] for r in mb])),
                                  gap_final=float(np.mean([r['gap'] for r in mb])))
    ma = [r for r in aco if (r['alfa'], r['beta'], r['rho']) == tuple(mejor_aco)]
    A['aco_mejora_inicial'] = dict(gap_primera_iteracion=float(np.mean([100 * (r['hist'][0] - r['bks']) / r['bks'] for r in ma])),
                                   gap_final=float(np.mean([r['gap'] for r in ma])))
    json.dump(dict(ga=dict(puntos=mejor_ga[0], pm=mejor_ga[1], seleccion=mejor_ga[2]),
                   aco=dict(alfa=mejor_aco[0], beta=mejor_aco[1], rho=mejor_aco[2])),
              open(R + 'mejores_config.json', 'w'), indent=1)
    json.dump(A, open(R + 'analisis.json', 'w'), indent=1)
    print('GA  mejor', mejor_ga, ' ACO mejor', mejor_aco)
    for alg in ('ga', 'aco'):
        print(alg, 'Friedman p =', A[alg]['friedman_p'])
        for f in sorted(A[alg]['celdas'], key=lambda f: f['rango']):
            print('  ', f['celda'], 'gap %.2f  2opt %.2f  rango %.2f  t %.2fs  it %.0f  gana %d  sd %.2f' % (
                f['gap'], f['gap_2opt'], f['rango'], f['tiempo'], f['it_mejor'], f['gana'], f['sd_semillas']))
        for k, e in A[alg]['efectos'].items():
            print('   efecto', k, {lv: round(v['gap'], 2) for lv, v in e['niveles'].items()}, e['prueba'], round(e['p'], 4))
