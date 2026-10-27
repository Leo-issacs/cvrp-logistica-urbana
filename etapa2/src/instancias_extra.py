"""Instancias adicionales generadas con semilla fija (mismo formato que CVRP_10).

- E10-a ... E10-e: 10 clientes, coordenadas uniformes en [0, 100]^2, depósito en (50, 50),
  demandas enteras uniformes en [8, 20], Q = 50. Óptimo certificado con exacto_subconjuntos.
- E20 y E30: 20 y 30 clientes con la misma regla; sin certificado (se reporta la mejor conocida).
"""
import random
from instancia import distancias

def generar(n, semilla, Q=50):
    rng = random.Random(semilla)
    coord = {1: (50, 50)}
    dem = {1: 0}
    for k in range(2, n + 2):
        coord[k] = (rng.randint(0, 100), rng.randint(0, 100))
        dem[k] = rng.randint(8, 20)
    return dict(coord=coord, dem=dem, Q=Q, depot=1, d=distancias(coord))

EXTRA10 = {f'E10-{c}': generar(10, 1000 + i) for i, c in enumerate('abcde')}
GRANDES = {'E20': generar(20, 2020), 'E30': generar(30, 3030)}
