import itertools as it, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from instancias import leer, subinstancia
from nucleo import split_costo, ox_un_punto, ox_dos_puntos
from algoritmos import clarke_wright, correr_ga, correr_aco, verificar, costo_ruta


def split_fuerza_bruta(p, I):
    n, mejor = len(p), np.inf
    for cortes in it.product([0, 1], repeat=n - 1):
        rutas, act = [], [p[0]]
        for c, v in zip(cortes, p[1:]):
            if c: rutas.append(act); act = [v]
            else: act.append(v)
        rutas.append(act)
        if all(I.q[r].sum() <= I.Q and costo_ruta(r, I.d) + I.s * len(r) <= I.D + 1e-9 for r in rutas):
            mejor = min(mejor, sum(costo_ruta(r, I.d) for r in rutas))
    return mejor


def test_split_optimo_con_duracion():
    rng = np.random.default_rng(1)
    for nombre in ('CMT1', 'CMT6', 'CMT13'):
        I = subinstancia(leer(nombre), 10)
        for _ in range(20):
            p = rng.permutation(10) + 1
            assert abs(split_costo(p, I.d, I.q, I.Q, I.D, I.s) - split_fuerza_bruta(list(p), I)) < 1e-6


def test_ox_produce_permutaciones():
    np.random.seed(0)
    for _ in range(500):
        a, b = np.random.permutation(30) + 1, np.random.permutation(30) + 1
        for h in (ox_un_punto(a, b), ox_dos_puntos(a, b)):
            assert sorted(h) == list(range(1, 31))


def test_soluciones_factibles():
    for nombre in ('CMT6', 'CMT14', 'X-n336-k84'):
        I = leer(nombre)
        assert verificar(I, clarke_wright(I)['rutas']) > 0
        assert correr_ga(I, 0, gens=20)['z'] > 0
        assert correr_aco(I, 0, iters=10)['z'] > 0
