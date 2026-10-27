"""Interfaz de alto nivel: Clarke-Wright + 2-opt (algoritmo propuesto en la Etapa 1),
GA y ACO (Etapa 2) y verificación de soluciones."""
import time
import numpy as np
from nucleo import (split_costo, split_pred, rutas_de, dos_opt, ga as _ga, aco as _aco,
                    vecino_mas_cercano, listas_candidatos)


def costo_ruta(r, d):
    t = [0] + list(r) + [0]
    return float(sum(d[a, b] for a, b in zip(t, t[1:])))


def verificar(inst, rutas):
    """Cada cliente exactamente una vez, capacidad y duración. Devuelve la distancia total."""
    vis = sorted(v for r in rutas for v in r)
    assert vis == list(range(1, inst.n + 1)), 'clientes faltantes o repetidos'
    total = 0.0
    for r in rutas:
        assert inst.q[list(r)].sum() <= inst.Q, 'capacidad excedida'
        c = costo_ruta(r, inst.d)
        assert c + inst.s * len(r) <= inst.D + 1e-6, 'duración excedida'
        total += c
    return total


def pulir(inst, rutas):
    """2-opt dentro de cada ruta (mismo pulido que usa Clarke-Wright)."""
    return [list(dos_opt(np.array(r, np.int64), inst.d)) for r in rutas]


# ------------------------------------------------------------------ Clarke-Wright + 2-opt
def clarke_wright(inst):
    t0 = time.perf_counter()
    d, q, n = inst.d, inst.q, inst.n
    i_idx, j_idx = np.triu_indices(n, 1)
    i_idx, j_idx = i_idx + 1, j_idx + 1
    ahorro = d[0, i_idx] + d[0, j_idx] - d[i_idx, j_idx]
    orden = np.lexsort((j_idx, i_idx, -ahorro))
    ruta_de = list(range(n + 1))                       # id de ruta de cada cliente
    rutas = {i: [i] for i in range(1, n + 1)}
    carga = {i: int(q[i]) for i in range(1, n + 1)}
    largo = {i: 2.0 * d[0, i] for i in range(1, n + 1)}
    for k in orden:
        s = ahorro[k]
        if s <= 0:
            break
        i, j = int(i_idx[k]), int(j_idx[k])
        a, b = ruta_de[i], ruta_de[j]
        if a == b:
            continue
        ra, rb = rutas[a], rutas[b]
        if i not in (ra[0], ra[-1]) or j not in (rb[0], rb[-1]):
            continue
        if carga[a] + carga[b] > inst.Q:
            continue
        nuevo_largo = largo[a] + largo[b] - s
        if nuevo_largo + inst.s * (len(ra) + len(rb)) > inst.D + 1e-9:
            continue
        aa = ra if ra[-1] == i else ra[::-1]
        bb = rb if rb[0] == j else rb[::-1]
        rutas[a] = aa + bb
        carga[a] += carga[b]
        largo[a] = nuevo_largo
        for v in rb:
            ruta_de[v] = a
        del rutas[b], carga[b], largo[b]
    sin_pulir = list(rutas.values())
    z0 = sum(costo_ruta(r, d) for r in sin_pulir)
    rutas_f = pulir(inst, sin_pulir)
    t = time.perf_counter() - t0
    return dict(z=verificar(inst, rutas_f), z_sin_2opt=z0, rutas=rutas_f, tiempo=t)


# ------------------------------------------------------------------ GA y ACO
def correr_ga(inst, semilla, pop=50, gens=1000, pc=0.9, pm=0.2, seleccion='torneo', puntos=2,
              inicial='heuristica', k_cand=25):
    t0 = time.perf_counter()
    cand = listas_candidatos(inst.d, k_cand)
    p, z, g, hist = _ga(inst.d, inst.q, inst.Q, inst.D, inst.s, semilla, pop, gens, pc, pm,
                        0 if seleccion == 'torneo' else 1, puntos,
                        1 if inicial == 'heuristica' else 0, cand)
    t = time.perf_counter() - t0
    zz, P = split_pred(p, inst.d, inst.q, inst.Q, inst.D, inst.s)
    rutas = rutas_de(p, P)
    z_ver = verificar(inst, rutas)
    assert abs(z_ver - z) < 1e-6 * max(1, z)
    t1 = time.perf_counter(); rp = pulir(inst, rutas); t2 = time.perf_counter() - t1
    return dict(z=z, it_mejor=int(g), evals_mejor=int(pop * (g + 1)), tiempo=t, hist=hist,
                z_2opt=verificar(inst, rp), tiempo_2opt=t2, rutas=rutas)


def correr_aco(inst, semilla, hormigas=25, iters=2000, alfa=1.0, beta=2.0, rho=0.2, k_cand=25):
    t0 = time.perf_counter()
    cand = listas_candidatos(inst.d, k_cand)
    p_nn = vecino_mas_cercano(inst.d)
    c_nn = split_costo(p_nn, inst.d, inst.q, inst.Q, inst.D, inst.s)
    tau0 = hormigas / c_nn                                 # Dorigo y Stützle (2004), Ant System
    p, z, it, hist = _aco(inst.d, inst.q, inst.Q, inst.D, inst.s, semilla, hormigas, iters,
                          float(alfa), float(beta), float(rho), cand, tau0)
    t = time.perf_counter() - t0
    zz, P = split_pred(p, inst.d, inst.q, inst.Q, inst.D, inst.s)
    rutas = rutas_de(p, P)
    z_ver = verificar(inst, rutas)
    assert abs(z_ver - z) < 1e-6 * max(1, z)
    t1 = time.perf_counter(); rp = pulir(inst, rutas); t2 = time.perf_counter() - t1
    return dict(z=z, it_mejor=int(it), evals_mejor=int(hormigas * (it + 1)), tiempo=t, hist=hist,
                z_2opt=verificar(inst, rp), tiempo_2opt=t2, rutas=rutas)
