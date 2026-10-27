"""Exploratorio: ACO con cota relativa de feromona (inspirada en MAX-MIN Ant System, Stützle y Hoos, 2000).

Después de cada actualización se impone tau >= r * max(tau): ninguna transición puede quedar más de 1/r
veces por debajo de la más reforzada. r = 0 reproduce el ACO original. No sustituye la configuración principal."""
import json, random, sys, statistics as st
sys.path.insert(0, 'src')
from algoritmos import split
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instancias_extra import EXTRA10
from exacto_subconjuntos import cvrp_exacto

def aco_cota(q, Qc, depot, d, seed, r=0., ants=20, steps=100, alpha=1., beta=2., rho=.2, tau0=.01, z_opt=None):
    rng = random.Random(seed)
    clients = sorted(set(q) - {depot})
    tau = {(i, j): tau0 for i in q for j in q if i != j}
    best, n_eval, primera = float('inf'), 0, None
    for _ in range(steps):
        sols = []
        for _ in range(ants):
            left, p, cur = clients[:], [], depot
            while left:
                w = [tau[cur, j] ** alpha * (1 / d[cur, j]) ** beta for j in left]
                nxt = rng.choices(left, weights=w, k=1)[0]
                p.append(nxt); left.remove(nxt); cur = nxt
            z, _ = split(p, q, Qc, depot, d); n_eval += 1
            sols.append((p, z)); best = min(best, z)
            if primera is None and z_opt is not None and z <= z_opt + 1e-9:
                primera = n_eval
        for e in tau:
            tau[e] = max(1e-12, (1 - rho) * tau[e])
        for p, z in sols:
            t = [depot] + p + [depot]
            for i, j in zip(t, t[1:]):
                tau[i, j] += 1 / z; tau[j, i] += 1 / z
        if r > 0:
            piso = r * max(tau.values())
            for e in tau:
                tau[e] = max(tau[e], piso)
    return best, primera

if __name__ == '__main__':
    casos = {'CVRP_10': (DEM, Q, DEPOT, D, Z_OPT)}
    I = EXTRA10['E10-b']; casos['E10-b'] = (I['dem'], I['Q'], 1, I['d'], cvrp_exacto(I['dem'], I['Q'], 1, I['d'])[0])
    out = {}
    for nombre, (q, Qc, dep, d, z) in casos.items():
        for r in (0., .01, .05, .1):
            rs = [aco_cota(q, Qc, dep, d, s, r=r, z_opt=z) for s in range(200, 230)]
            ok = [p for _, p in rs if p]
            out[f'{nombre}|r={r}'] = dict(exitos=len(ok), n=30, mediana_primera=st.median(ok) if ok else None,
                                          media_z=st.mean(b for b, _ in rs))
            print(nombre, r, out[f'{nombre}|r={r}'], flush=True)
    json.dump(out, open('resultados/aco_cotas.json', 'w'), indent=1)
