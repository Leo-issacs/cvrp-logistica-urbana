"""Lectura de instancias TSPLIB (CVRPLIB) y valores de referencia (BKS)."""
import math
from pathlib import Path
import numpy as np

DIR = Path(__file__).resolve().parent.parent / 'instancias'

# BKS de las instancias X: Vidal (2022), tablas 5 y 6. CMT: campo COMMENT del archivo
# (mejores soluciones conocidas de Christofides, Mingozzi y Toth, 1979).
BKS_X = {'X-n280-k17': 33503, 'X-n303-k21': 21736, 'X-n308-k13': 25859, 'X-n327-k20': 27532,
         'X-n336-k84': 139111, 'X-n401-k29': 66163, 'X-n411-k19': 19712, 'X-n429-k61': 65449,
         'X-n449-k29': 55233, 'X-n459-k26': 24139}


class Instancia:
    def __init__(self, nombre, xy, q, Q, D, s, redondeo, bks):
        self.nombre, self.xy, self.q, self.Q = nombre, xy, q, Q
        self.D = D if D is not None else np.inf          # duración máxima de ruta
        self.s = s                                       # tiempo de servicio por cliente
        self.redondeo, self.bks = redondeo, bks
        dif = xy[:, None, :] - xy[None, :, :]
        d = np.sqrt((dif ** 2).sum(-1))
        self.d = np.floor(d + 0.5) if redondeo else d
        self.n = len(q) - 1                               # clientes (el depósito es el nodo 0)

    @property
    def familia(self):
        return 'X' if self.nombre.startswith('X') else 'CMT'

    @property
    def con_duracion(self):
        return np.isfinite(self.D)


def leer(nombre):
    txt = (DIR / f'{nombre}.vrp').read_text().splitlines()
    cab, xy, q, modo, depot = {}, {}, {}, None, None
    for ln in txt:
        s = ln.strip()
        if not s:
            continue
        if s.split()[0] in ('NODE_COORD_SECTION', 'DEMAND_SECTION', 'DEPOT_SECTION'):
            modo = s.split()[0]; continue
        if s.startswith('EOF'):
            break
        if ':' in s and modo is None:
            k, v = s.split(':', 1); cab[k.strip()] = v.strip().strip('"'); continue
        a = s.split()
        if modo == 'NODE_COORD_SECTION':
            xy[int(a[0])] = (float(a[1]), float(a[2]))
        elif modo == 'DEMAND_SECTION':
            q[int(a[0])] = int(a[1])
        elif modo == 'DEPOT_SECTION' and int(a[0]) > 0:
            depot = int(a[0])
    nodos = [depot] + sorted(i for i in xy if i != depot)      # depósito -> índice 0
    XY = np.array([xy[i] for i in nodos]); Qv = np.array([q[i] for i in nodos], dtype=np.int64)
    assert Qv[0] == 0
    redondeo = nombre.startswith('X')
    bks = BKS_X[nombre] if redondeo else float(cab['COMMENT'])
    D = float(cab['DISTANCE']) if 'DISTANCE' in cab else None
    s = float(cab.get('SERVICE_TIME', 0))
    return Instancia(nombre, XY, Qv, int(cab['CAPACITY']), D, s, redondeo, bks)


def todas():
    cmt = sorted((p.stem for p in DIR.glob('CMT*.vrp')), key=lambda n: int(n[3:]))
    x = sorted((p.stem for p in DIR.glob('X-*.vrp')), key=lambda n: int(n.split('-')[1][1:]))
    return cmt + x


def subinstancia(inst, k):
    """Depósito + los primeros k clientes de la instancia (para el estudio de escalabilidad)."""
    sub = Instancia(f'{inst.nombre}-sub{k}', inst.xy[:k + 1], inst.q[:k + 1], inst.Q,
                    None if not inst.con_duracion else inst.D, inst.s, inst.redondeo, None)
    return sub
