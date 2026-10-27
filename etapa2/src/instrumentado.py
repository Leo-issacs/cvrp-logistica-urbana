"""Versiones instrumentadas de ga() y aco() de algoritmos.py.

Reproducen exactamente la misma secuencia de números aleatorios que las funciones
originales (mismas llamadas a rng en el mismo orden), por lo que para una semilla dada
obtienen el mismo resultado. Solo agregan registros: evaluación en que mejora el mejor
costo, diversidad de la población o de la colonia y estadísticas de feromona.
"""
import random
import time
from itertools import combinations

from algoritmos import split, ox

TOL = 1e-9


# ---------------------------------------------------------------- diversidad
def adyacencias(p, depot):
    """Aristas no dirigidas del ciclo gigante depósito -> p -> depósito."""
    t = [depot] + list(p) + [depot]
    return frozenset(frozenset(e) for e in zip(t, t[1:]))


def diversidad(perms, depot):
    """Devuelve (únicos, distancia media de adyacencias entre pares).

    Distancia entre dos permutaciones = 1 - |A ∩ B| / |A|, donde A y B son sus
    11 adyacencias del ciclo gigante. 0 = mismo ciclo; 1 = no comparten aristas.
    """
    ads = [adyacencias(p, depot) for p in perms]
    unicos = len(set(tuple(p) for p in perms))
    n = len(ads[0])
    pares = list(combinations(range(len(ads)), 2))
    dist = sum(1 - len(ads[i] & ads[j]) / n for i, j in pares) / len(pares)
    return unicos, dist


def soluciones_distintas(perms, q, Q, depot, d):
    """Número de conjuntos de rutas distintos después de Split (sin importar orden/sentido)."""
    vistos = set()
    for p in perms:
        _, rutas = split(p, q, Q, depot, d)
        vistos.add(frozenset(frozenset(r[1:-1]) for r in rutas))
    return len(vistos)


# ---------------------------------------------------------------- GA
def ga_traza(q, Q, depot, d, seed, pop=20, steps=100, pc=.9, pm=.2,
             z_opt=None, con_diversidad=True):
    rng = random.Random(seed)
    clients = sorted(set(q) - {depot})
    evaluate = lambda p: split(p, q, Q, depot, d)[0]
    t0 = time.perf_counter()
    population = [rng.sample(clients, len(clients)) for _ in range(pop)]
    costs = [evaluate(p) for p in population]
    n_eval = pop
    mejor = min(costs)
    mejoras = [(0, costs.index(mejor) + 1, mejor, list(population[costs.index(mejor)]))]
    for k, c in enumerate(costs):          # evaluación exacta del mejor inicial
        if c == mejor:
            mejoras[0] = (0, k + 1, mejor, list(population[k]))
            break
    primera_opt = None
    if z_opt is not None and mejor <= z_opt + TOL:
        primera_opt = mejoras[0][1]
    t_opt = time.perf_counter() - t0 if primera_opt else None
    hist = [min(costs)]
    div = [diversidad(population, depot) + (soluciones_distintas(population, q, Q, depot, d),)] \
        if con_diversidad else []
    for g in range(1, steps):
        def tournament():
            inds = rng.sample(range(pop), 2)
            return population[min(inds, key=lambda i: costs[i])]
        children = []
        for _ in range(pop):
            a, b = tournament(), tournament()
            h = ox(a, b, rng) if rng.random() < pc else a[:]
            if rng.random() < pm:
                i, j = sorted(rng.sample(range(len(h)), 2))
                h[i:j + 1] = h[i:j + 1][::-1]
            children.append(h)
        child_costs = []
        for h in children:
            c = evaluate(h)
            n_eval += 1
            child_costs.append(c)
            if c < mejor - 1e-12:
                mejor = c
                mejoras.append((g, n_eval, c, list(h)))
            if primera_opt is None and z_opt is not None and c <= z_opt + TOL:
                primera_opt = n_eval
                t_opt = time.perf_counter() - t0
        old = sorted(zip(costs, population), key=lambda t: t[0])[:2]
        new = sorted(zip(child_costs, children), key=lambda t: t[0])[:pop - 2]
        ranked = sorted(old + new, key=lambda t: t[0])
        costs, population = map(list, zip(*ranked))
        hist.append(min(costs))
        if con_diversidad:
            div.append(diversidad(population, depot) + (soluciones_distintas(population, q, Q, depot, d),))
    best = population[min(range(pop), key=lambda i: costs[i])]
    z, routes = split(best, q, Q, depot, d)
    return dict(z=z, rutas=routes, hist=hist, mejoras=mejoras, primera_opt=primera_opt,
                t_opt=t_opt, n_eval=n_eval, diversidad=div, mejor_perm=best)


# ---------------------------------------------------------------- ACO
def aco_traza(q, Q, depot, d, seed, ants=20, steps=100, alpha=1., beta=2., rho=.2,
              tau0=.01, deposit=1., z_opt=None, con_diversidad=True, con_feromona=True):
    rng = random.Random(seed)
    clients = sorted(set(q) - {depot})
    tau = {(i, j): tau0 for i in q for j in q if i != j}
    best, best_routes, best_perm, history = float('inf'), None, None, []
    n_eval, primera_opt, t_opt = 0, None, None
    div, fer, mejoras = [], [], []
    pisos = 0
    t0 = time.perf_counter()
    for it in range(steps):
        solutions = []
        for _ in range(ants):
            left, p, current = clients[:], [], depot
            while left:
                weights = [tau[current, j] ** alpha * (1 / d[current, j]) ** beta for j in left]
                nxt = rng.choices(left, weights=weights, k=1)[0]
                p.append(nxt)
                left.remove(nxt)
                current = nxt
            z, routes = split(p, q, Q, depot, d)
            n_eval += 1
            solutions.append((p, z, routes))
            if z < best - 1e-12:
                best, best_routes, best_perm = z, routes, p
                mejoras.append((it, n_eval, z, list(p)))
            if primera_opt is None and z_opt is not None and z <= z_opt + TOL:
                primera_opt, t_opt = n_eval, time.perf_counter() - t0
        for edge in tau:
            v = (1 - rho) * tau[edge]
            if v < 1e-12:
                pisos += 1
            tau[edge] = max(1e-12, v)
        dep_fantasma = dep_total = 0.
        for p, z, routes in solutions:
            tour = [depot] + p + [depot]
            arcos_rutas = {frozenset(e) for r in routes for e in zip(r, r[1:])}
            for i, j in zip(tour, tour[1:]):
                tau[i, j] += deposit / z
                tau[j, i] += deposit / z
                dep_total += 2 * deposit / z
                if frozenset((i, j)) not in arcos_rutas:
                    dep_fantasma += 2 * deposit / z
        history.append(best)
        if con_diversidad:
            perms = [s[0] for s in solutions]
            div.append(diversidad(perms, depot) + (soluciones_distintas(perms, q, Q, depot, d),))
        if con_feromona:
            vals = list(tau.values())
            fer.append(dict(max=max(vals), min=min(vals), frac_fantasma=dep_fantasma / dep_total,
                            branching=branching(tau, q, depot)))
    return dict(z=best, rutas=best_routes, hist=history, mejoras=mejoras, primera_opt=primera_opt,
                t_opt=t_opt, n_eval=n_eval, diversidad=div, feromona=fer, tau=tau,
                mejor_perm=best_perm, pisos=pisos)


def branching(tau, q, depot, lam=0.05):
    """Factor de ramificación lambda medio (Gambardella y Dorigo): número de arcos de cada nodo
    cuya feromona supera min + lam * (max - min). Vale n-1 al inicio y tiende a 1-2 al converger."""
    nodos = list(q)
    tot = 0
    for i in nodos:
        v = [tau[i, j] for j in nodos if j != i]
        lo, hi = min(v), max(v)
        tot += sum(1 for x in v if x >= lo + lam * (hi - lo))
    return tot / len(nodos)
