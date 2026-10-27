"""Instancia CVRP_10 (etapa 1 y 2): depósito 1, clientes 2-11, Q = 50, distancias euclidianas continuas."""
import math

COORD = {1: (50, 50), 2: (20, 70), 3: (30, 80), 4: (60, 75), 5: (80, 70), 6: (25, 45),
         7: (40, 30), 8: (65, 25), 9: (85, 40), 10: (45, 60), 11: (70, 55)}
DEM = {1: 0, 2: 12, 3: 18, 4: 10, 5: 15, 6: 14, 7: 20, 8: 16, 9: 11, 10: 13, 11: 17}
Q = 50
DEPOT = 1
Z_OPT = 318.9894867478301


def distancias(coord):
    return {(i, j): math.hypot(coord[i][0] - coord[j][0], coord[i][1] - coord[j][1])
            for i in coord for j in coord}


D = distancias(COORD)
