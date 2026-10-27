"""Desglose del tiempo por componente y tiempo real hasta el óptimo (observaciones pp. 4, 8-9 y 11).

Qué se cronometra (igual que en el informe): sólo la búsqueda (inicialización, operadores, Split,
actualización de feromona e historial). Quedan FUERA la lectura de la instancia, el cálculo de la matriz
de distancias, las verificaciones de factibilidad y la generación de figuras.

El desglose usa copias de ga() y aco() con relojes alrededor de cada bloque; los relojes añaden un
pequeño costo, por lo que los porcentajes describen la proporción del trabajo y no sustituyen la
medición de la Tabla 8. Los tiempos dependen del equipo donde se ejecute este script.
"""
import json, platform, random, statistics as st, sys, time
sys.path.insert(0, 'src')
from algoritmos import split, ox, ga, aco
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instrumentado import ga_traza, aco_traza

pc_ = time.perf_counter


def ga_cronometrado(seed, pop=20, steps=100, pc=.9, pm=.2):
    rng = random.Random(seed)
    T = dict(split=0., operadores=0., reemplazo=0.)
    clients = sorted(set(DEM) - {DEPOT})
    t = pc_(); population = [rng.sample(clients, 10) for _ in range(pop)]; T['operadores'] += pc_() - t
    t = pc_(); costs = [split(p, DEM, Q, DEPOT, D)[0] for p in population]; T['split'] += pc_() - t
    for _ in range(steps - 1):
        t = pc_()
        def tournament():
            inds = rng.sample(range(pop), 2)
            return population[min(inds, key=lambda i: costs[i])]
        children = []
        for _ in range(pop):
            a, b = tournament(), tournament()
            h = ox(a, b, rng) if rng.random() < pc else a[:]
            if rng.random() < pm:
                i, j = sorted(rng.sample(range(10), 2)); h[i:j + 1] = h[i:j + 1][::-1]
            children.append(h)
        T['operadores'] += pc_() - t
        t = pc_(); child_costs = [split(p, DEM, Q, DEPOT, D)[0] for p in children]; T['split'] += pc_() - t
        t = pc_()
        old = sorted(zip(costs, population), key=lambda x: x[0])[:2]
        new = sorted(zip(child_costs, children), key=lambda x: x[0])[:pop - 2]
        costs, population = map(list, zip(*sorted(old + new, key=lambda x: x[0])))
        T['reemplazo'] += pc_() - t
    return T


def aco_cronometrado(seed, ants=20, steps=100, alpha=1., beta=2., rho=.2, tau0=.01):
    rng = random.Random(seed)
    T = dict(construccion=0., split=0., feromona=0.)
    clients = sorted(set(DEM) - {DEPOT})
    tau = {(i, j): tau0 for i in DEM for j in DEM if i != j}
    for _ in range(steps):
        sols = []
        for _ in range(ants):
            t = pc_()
            left, p, cur = clients[:], [], DEPOT
            while left:
                w = [tau[cur, j] ** alpha * (1 / D[cur, j]) ** beta for j in left]
                nxt = rng.choices(left, weights=w, k=1)[0]
                p.append(nxt); left.remove(nxt); cur = nxt
            T['construccion'] += pc_() - t
            t = pc_(); z, _ = split(p, DEM, Q, DEPOT, D); T['split'] += pc_() - t
            sols.append((p, z))
        t = pc_()
        for e in tau:
            tau[e] = max(1e-12, (1 - rho) * tau[e])
        for p, z in sols:
            tour = [DEPOT] + p + [DEPOT]
            for i, j in zip(tour, tour[1:]):
                tau[i, j] += 1 / z; tau[j, i] += 1 / z
        T['feromona'] += pc_() - t
    return T


if __name__ == '__main__':
    for s in (999,):                       # calentamiento, como en el informe
        ga(DEM, Q, DEPOT, D, s); aco(DEM, Q, DEPOT, D, s)
    tot = dict(ga=[], aco=[])
    for s in range(10):
        t = pc_(); ga(DEM, Q, DEPOT, D, s); tot['ga'].append(1000 * (pc_() - t))
        t = pc_(); aco(DEM, Q, DEPOT, D, s); tot['aco'].append(1000 * (pc_() - t))
    comp = dict(ga=[ga_cronometrado(s) for s in range(10)], aco=[aco_cronometrado(s) for s in range(10)])
    hasta_opt = dict(ga=[], aco=[])
    for s in range(10):
        g = ga_traza(DEM, Q, DEPOT, D, s, z_opt=Z_OPT, con_diversidad=False)
        a = aco_traza(DEM, Q, DEPOT, D, s, z_opt=Z_OPT, con_diversidad=False, con_feromona=False)
        hasta_opt['ga'].append(None if g['t_opt'] is None else 1000 * g['t_opt'])
        hasta_opt['aco'].append(None if a['t_opt'] is None else 1000 * a['t_opt'])
    out = dict(entorno=f'{platform.processor() or platform.machine()} | {platform.system()} {platform.release()} | Python {platform.python_version()}',
               total_ms=tot, componentes=comp, hasta_opt_ms=hasta_opt)
    for m in ('ga', 'aco'):
        c = {k: st.mean(x[k] for x in comp[m]) for k in comp[m][0]}
        s_ = sum(c.values())
        print(m, 'total medio %.3f ms' % st.mean(tot[m]), 'por evaluación %.2f µs' % (1000 * st.mean(tot[m]) / 2000),
              {k: f'{100 * v / s_:.1f}%' for k, v in c.items()})
        print('  hasta óptimo (ms):', [None if x is None else round(x, 2) for x in hasta_opt[m]])
    json.dump(out, open('resultados/tiempos_componentes.json', 'w'), default=float)
