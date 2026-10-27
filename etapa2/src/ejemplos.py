"""Ejemplos trabajados para el informe: Split con predecesores, OX, inversión y construcción de una hormiga."""
import json, random, sys
sys.path.insert(0, 'src')
from algoritmos import split, ox
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instrumentado import ga_traza

def split_tabla(p, q=DEM, Qc=Q, depot=DEPOT, d=D):
    """Igual que split(), pero devuelve todas las etiquetas D(b), predecesores y segmentos evaluados."""
    n = len(p)
    dp, prev = [0.] + [float('inf')] * n, [-1] * (n + 1)
    evaluados = []
    for i in range(n):
        load, length = 0, 0.
        for j in range(i, n):
            load += q[p[j]]
            if load > Qc:
                evaluados.append((i + 1, j + 1, load, None, None))
                break
            length += d[depot, p[j]] if j == i else d[p[j - 1], p[j]]
            w = length + d[p[j], depot]
            value = dp[i] + w
            evaluados.append((i + 1, j + 1, load, w, value))
            if value < dp[j + 1] - 1e-12:
                dp[j + 1], prev[j + 1] = value, i
    return dp, prev, evaluados

def greedy_split(p, q=DEM, Qc=Q, depot=DEPOT, d=D):
    """Corte voraz: llenar cada vehículo hasta que el siguiente cliente no cabe (para contrastar)."""
    rutas, act, carga = [], [], 0
    for c in p:
        if carga + q[c] > Qc:
            rutas.append(act); act, carga = [], 0
        act.append(c); carga += q[c]
    rutas.append(act)
    z = sum(d[depot, r[0]] + sum(d[a, b] for a, b in zip(r, r[1:])) + d[r[-1], depot] for r in rutas)
    return z, rutas

if __name__ == '__main__':
    out = {}
    r0 = ga_traza(DEM, Q, DEPOT, D, 0, z_opt=Z_OPT, con_diversidad=False)
    p = r0['mejor_perm']
    dp, prev, ev = split_tabla(p)
    out['split'] = dict(perm=p, dp=dp, prev=prev, evaluados=ev, z=split(p, DEM, Q, DEPOT, D)[0],
                        rutas=split(p, DEM, Q, DEPOT, D)[1], greedy=greedy_split(p))
    print('perm', p, [DEM[c] for c in p])
    for b in range(1, 11):
        print(b, p[b-1], round(dp[b], 6), prev[b])
    print('greedy', greedy_split(p))
    # OX: dos individuos de la población inicial de la semilla 0 y un corte fijo (lo, hi) = (3, 6)
    rng = random.Random(0)
    clients = sorted(set(DEM) - {DEPOT})
    popu = [rng.sample(clients, 10) for _ in range(20)]
    a, b = popu[0], popu[1]
    class Fijo:                      # rng de juguete que devuelve el corte elegido
        def sample(self, rango, k): return [3, 6]
    h = ox(a, b, Fijo())
    out['ox'] = dict(a=a, b=b, lo=3, hi=6, hijo=h, za=split(a, DEM, Q, DEPOT, D)[0],
                     zb=split(b, DEM, Q, DEPOT, D)[0], zh=split(h, DEM, Q, DEPOT, D)[0],
                     rutas_h=split(h, DEM, Q, DEPOT, D)[1])
    print('OX', a, b, h, sorted(h) == clients)
    inv = h[:]; i, j = 1, 4; inv[i:j+1] = inv[i:j+1][::-1]
    out['inv'] = dict(antes=h, i=i, j=j, despues=inv, z=split(inv, DEM, Q, DEPOT, D)[0],
                      rutas=split(inv, DEM, Q, DEPOT, D)[1])
    print('INV', inv, sorted(inv) == clients, out['inv']['z'])
    # Hormiga: primera hormiga de la semilla 0 con feromona inicial
    rng = random.Random(0)
    tau = {(i, j): .01 for i in DEM for j in DEM if i != j}
    left, perm, cur, pasos = clients[:], [], DEPOT, []
    while left:
        w = [tau[cur, j] * (1 / D[cur, j]) ** 2 for j in left]
        tot = sum(w)
        nxt = rng.choices(left, weights=w, k=1)[0]
        top = sorted(zip(left, [x / tot for x in w]), key=lambda t: -t[1])[:3]
        pasos.append(dict(desde=cur, elegido=nxt, p_elegido=w[left.index(nxt)] / tot, top3=top,
                          carga_acumulada=sum(DEM[c] for c in perm) + DEM[nxt]))
        perm.append(nxt); left.remove(nxt); cur = nxt
    z, rutas = split(perm, DEM, Q, DEPOT, D)
    out['hormiga'] = dict(perm=perm, pasos=pasos, z=z, rutas=rutas)
    for s in pasos: print(s['desde'], '->', s['elegido'], round(s['p_elegido'], 3), s['carga_acumulada'])
    print('hormiga', perm, z, rutas)
    json.dump(out, open('resultados/ejemplos.json', 'w'), indent=1, default=float)
