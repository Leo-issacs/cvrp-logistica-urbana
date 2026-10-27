"""Pruebas automatizadas de la etapa 2. Ejecutar desde la carpeta del proyecto:  python -m pytest -q tests

Cómo se eligen los casos (observación pp. 8-9): las 50 permutaciones de Split y los 1,000 cruces OX
se generan con random.Random(2026), una semilla distinta de las usadas en los experimentos, de modo
que los casos no se escogen a mano ni dependen de las corridas evaluadas. Además se incluye un caso
fijo, verificable a mano, tomado del ejemplo del informe (§1.3).
"""
import random, sys
from itertools import product
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from algoritmos import split, ox, ga, aco
from instancia import DEM, Q, DEPOT, D, Z_OPT
from exacto_subconjuntos import cvrp_exacto

CLIENTES = sorted(set(DEM) - {DEPOT})


def costo_rutas(rutas):
    return sum(D[a, b] for r in rutas for a, b in zip(r, r[1:]))


def fuerza_bruta_cortes(p):
    """Recorre las 2^9 = 512 formas de cortar una permutación de 10 clientes."""
    mejor = float('inf')
    for cortes in product((0, 1), repeat=len(p) - 1):
        rutas, act = [], [p[0]]
        for c, v in zip(cortes, p[1:]):
            if c:
                rutas.append(act); act = []
            act.append(v)
        rutas.append(act)
        if all(sum(DEM[v] for v in r) <= Q for r in rutas):
            mejor = min(mejor, costo_rutas([[DEPOT] + r + [DEPOT] for r in rutas]))
    return mejor


def verificar_solucion(z, rutas):
    visitados = [c for r in rutas for c in r[1:-1]]
    assert sorted(visitados) == CLIENTES, 'cada cliente exactamente una vez'
    assert all(r[0] == DEPOT and r[-1] == DEPOT for r in rutas), 'salida y regreso al depósito'
    assert all(sum(DEM[c] for c in r[1:-1]) <= Q for r in rutas), 'capacidad'
    assert abs(costo_rutas(rutas) - z) < 1e-9, 'la distancia reportada coincide con la suma de arcos'


def test_split_caso_fijo_del_informe():
    p = [4, 5, 11, 6, 2, 3, 10, 7, 8, 9]
    z, rutas = split(p, DEM, Q, DEPOT, D)
    assert rutas == [[1, 4, 5, 11, 1], [1, 6, 2, 3, 1], [1, 10, 1], [1, 7, 8, 9, 1]]
    assert abs(z - Z_OPT) < 1e-9
    assert abs(fuerza_bruta_cortes(p) - z) < 1e-9


def test_split_contra_512_cortes():
    rng = random.Random(2026)
    for _ in range(50):
        p = rng.sample(CLIENTES, 10)
        z, rutas = split(p, DEM, Q, DEPOT, D)
        assert abs(z - fuerza_bruta_cortes(p)) < 1e-9
        verificar_solucion(z, rutas)
        assert [c for r in rutas for c in r[1:-1]] == p, 'Split no reordena la permutación'


def test_ox_e_inversion_conservan_permutacion():
    rng = random.Random(2026)
    for _ in range(1000):
        a, b = rng.sample(CLIENTES, 10), rng.sample(CLIENTES, 10)
        h = ox(a, b, rng)
        assert sorted(h) == CLIENTES
        i, j = sorted(rng.sample(range(10), 2))
        h[i:j + 1] = h[i:j + 1][::-1]
        assert sorted(h) == CLIENTES


def test_optimo_por_subconjuntos():
    z, grupos = cvrp_exacto(DEM, Q, DEPOT, D)
    assert abs(z - Z_OPT) < 1e-9
    assert sorted(map(sorted, grupos)) == [[2, 3, 6], [4, 5, 11], [7, 8, 9], [10]]


REPORTADO_GA = {0: 318.989487, 1: 318.989487, 2: 318.989487, 3: 318.989487, 4: 330.957278,
                5: 318.989487, 6: 318.989487, 7: 318.989487, 8: 336.713769, 9: 318.989487}


def test_soluciones_finales_incluidas_las_no_optimas():
    for s in range(10):
        z, rutas, hist = ga(DEM, Q, DEPOT, D, s)
        verificar_solucion(z, rutas)
        assert abs(z - REPORTADO_GA[s]) < 1e-6, 'reproduce la Tabla 7'
        assert all(x >= y - 1e-12 for x, y in zip(hist, hist[1:])), 'historial no creciente'
        assert z >= Z_OPT - 1e-9
        z, rutas, hist = aco(DEM, Q, DEPOT, D, s)
        verificar_solucion(z, rutas)
        assert abs(z - Z_OPT) < 1e-6
