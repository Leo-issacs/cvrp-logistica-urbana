"""Reúne en resultados/cifras.json todas las cifras citadas en el informe corregido (trazabilidad)."""
import json, math, statistics as st, sys
sys.path.insert(0, 'src')
from algoritmos import split
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instancias_extra import EXTRA10
from exacto_subconjuntos import cvrp_exacto
from instrumentado import aco_traza

P = json.load(open('resultados/principal.json'))
S = json.load(open('resultados/sensibilidad_ampliada.json'))
c = {}

# --- GA: diversidad de semillas exitosas y fallidas (generaciones 10-99)
def resumen_div(s):
    dv = P['ga'][s]['diversidad'][10:]
    return dict(unicos=st.mean(x[0] for x in dv), dist=st.mean(x[1] for x in dv), decod=st.mean(x[2] for x in dv),
                gen_decod_le3=next(g for g, x in enumerate(P['ga'][s]['diversidad']) if x[2] <= 3))
c['ga_div'] = {s: resumen_div(s) for s in map(str, range(10))}
exito = [s for s in map(str, range(10)) if P['ga'][s]['primera_opt']]
c['ga_div_grupos'] = {g: {k: st.mean(c['ga_div'][s][k] for s in ss) for k in ('unicos', 'dist', 'decod', 'gen_decod_le3')}
                      for g, ss in (('exitosas', exito), ('fallidas', ['4', '8']))}
c['ga_div_gen0'] = P['ga']['0']['diversidad'][0]

# --- GA: vecindario de inversión de los cromosomas estancados
def inv(p, i, j): return p[:i] + p[i:j + 1][::-1] + p[j + 1:]
c['ga_vecindario'] = {}
for s in ('4', '8'):
    p = P['ga'][s]['perm']; z0 = split(p, DEM, Q, DEPOT, D)[0]
    uno = [inv(p, i, j) for i in range(10) for j in range(i + 1, 10)]
    mejora1 = sum(split(x, DEM, Q, DEPOT, D)[0] < z0 - 1e-9 for x in uno)
    dos = [(x, i, j) for x in uno for i in range(10) for j in range(i + 1, 10)]
    mejora2 = sum(split(inv(x, i, j), DEM, Q, DEPOT, D)[0] < z0 - 1e-9 for x, i, j in dos)
    llega2 = sum(split(inv(x, i, j), DEM, Q, DEPOT, D)[0] <= Z_OPT + 1e-9 for x, i, j in dos)
    c['ga_vecindario'][s] = dict(perm=p, z=z0, mejora_1inv=mejora1, n1=len(uno), mejora_2inv=mejora2,
                                 optimo_2inv=llega2, n2=len(dos))

# --- primera evaluación con el óptimo (100 semillas)
for m in ('ga', 'aco'):
    ok = sorted(x['primera_opt'] for x in P['cien'][m] if x['primera_opt'])
    q1, q2, q3 = st.quantiles(ok, n=4)
    c[f'primera_{m}_100'] = dict(exitos=len(ok), mediana=q2, q1=q1, q3=q3, min=ok[0], max=ok[-1],
                                 le200=sum(o <= 200 for o in ok), le500=sum(o <= 500 for o in ok))
    c[f'primera_{m}_0_9'] = [P[m][str(s)]['primera_opt'] for s in range(10)]

# --- ACO: feromona
fr = [f['frac_fantasma'] for s in map(str, range(10)) for f in P['aco'][s]['feromona']]
c['aco_frac_fantasma'] = dict(media=st.mean(fr), min=min(fr), max=max(fr))
c['aco_tau_max_final'] = [P['aco'][s]['feromona'][-1]['max'] for s in map(str, range(10))]
c['aco_branching'] = dict(inicio=st.mean(P['aco'][s]['feromona'][0]['branching'] for s in map(str, range(10))),
                          fin=st.mean(P['aco'][s]['feromona'][-1]['branching'] for s in map(str, range(10))))
c['aco_unicos_fin'] = [P['aco'][s]['diversidad'][-1][0] for s in map(str, range(10))]
c['aco_cota_tau'] = 20 / (0.2 * Z_OPT)
c['aco_tau_min_sin_refuerzo_100it'] = 0.01 * 0.8 ** 100
r5 = aco_traza(DEM, Q, DEPOT, D, 0, rho=.5, z_opt=Z_OPT, con_diversidad=False)
c['aco_rho05_pisos'] = r5['pisos']
c['aco_rho05_iter_piso'] = math.ceil(math.log(1e-12 / 0.01) / math.log(0.5))
tau = {tuple(map(int, k.split('-'))): v for k, v in P['aco']['0']['tau_final'].items()}
p = P['aco']['0']['perm']; tour = [1] + p + [1]
rutas = [x['ruta'] for x in P['aco']['0']['rutas']]
arcos = {frozenset(e) for r in rutas for e in zip(r, r[1:])}
c['aco_tau_semilla0'] = dict(perm=p, adyacencias=[(i, j, tau[i, j], frozenset((i, j)) in arcos) for i, j in zip(tour, tour[1:])],
                             no_reforzados=sorted([(min(e), max(e), tau[min(e), max(e)]) for e in arcos
                                                   if e not in {frozenset(x) for x in zip(tour, tour[1:])}]))
prob = 1.
left = sorted(set(DEM) - {DEPOT}); cur = DEPOT
for nxt in p:
    w = {j: tau[cur, j] * (1 / D[cur, j]) ** 2 for j in left}
    prob *= w[nxt] / sum(w.values()); left.remove(nxt); cur = nxt
c['aco_prob_repetir_mejor'] = prob

# --- ACO en E10-b: ¿las fallas tienen la agrupación óptima?
I = EXTRA10['E10-b']; zb, gb = cvrp_exacto(I['dem'], I['Q'], 1, I['d'])
grupos_opt = {frozenset(g) for g in gb}
fallas = []
for s in range(30):
    r = aco_traza(I['dem'], I['Q'], 1, I['d'], s, z_opt=zb, con_diversidad=False)
    if r['z'] > zb + 1e-9:
        fallas.append(dict(seed=s, z=r['z'], misma_agrupacion={frozenset(x[1:-1]) for x in r['rutas']} == grupos_opt,
                           branching_fin=r['feromona'][-1]['branching']))
c['aco_E10b'] = dict(zopt=zb, grupos=gb, fallas=fallas,
                     branching_fin_medio=st.mean(f['branching_fin'] for f in fallas) if fallas else None)

# --- sensibilidad: tablas resumen
def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z * z / n; cc = p + z * z / (2 * n); s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (cc - s) / den, (cc + s) / den
aco = [x for x in S['corridas'] if x['metodo'] == 'aco' and x['inst'] == 'CVRP_10']
tab = {}
for a in (.5, 1., 2.):
    for b in (0., 1., 2., 5.):
        xs = [x for x in aco if x['cfg']['alpha'] == a and x['cfg']['beta'] == b]
        ok = [x['primera_opt'] for x in xs if x['primera_opt']]
        tab[f'{a}|{b}'] = dict(n=len(xs), exitos=len(ok), le200=sum(o <= 200 for o in ok),
                               mediana=st.median(ok) if ok else None)
c['aco_alfa_beta'] = tab
for nombre in ('rho', 'ants'):
    d_ = {}
    for lv in sorted({x['cfg'][nombre] for x in aco}):
        xs = [x for x in aco if x['cfg'][nombre] == lv and x['cfg']['beta'] in (1., 2.)]
        ok = [x['primera_opt'] for x in xs if x['primera_opt']]
        d_[str(lv)] = dict(n=len(xs), exitos=len(ok), le200=sum(o <= 200 for o in ok), mediana=st.median(ok))
    c[f'aco_{nombre}_beta12'] = d_
ga = [x for x in S['corridas'] if x['metodo'] == 'ga' and x['inst'] == 'CVRP_10']
gt = {}
for x in ga:
    k = f"{x['cfg'].get('pm', .2)}|{x['cfg'].get('pop', 20)}|{x['cfg'].get('pc', .9)}"
    gt.setdefault(k, []).append(x)
c['ga_tabla'] = {k: dict(n=len(v), exitos=sum(1 for x in v if x['primera_opt']),
                         ic=wilson(sum(1 for x in v if x['primera_opt']), len(v)),
                         media=st.mean(x['z'] for x in v)) for k, v in gt.items()}
inst = {}
best = {}
for x in S['corridas']:
    best[x['inst']] = min(best.get(x['inst'], 9e9), x['z'])
for x in S['corridas']:
    if x['inst'] == 'CVRP_10':
        continue
    k = f"{x['inst']}|{x['metodo']}|{json.dumps(x['cfg'], sort_keys=True)}"
    inst.setdefault(k, []).append(x)
c['instancias'] = {}
for k, v in inst.items():
    nombre = k.split('|')[0]; ref = S['zopt'].get(nombre, best[nombre])
    gaps = [100 * (x['z'] - ref) / ref for x in v]
    c['instancias'][k] = dict(n=len(v), exitos=sum(g <= 1e-7 for g in gaps), gap_medio=st.mean(gaps),
                              gap_peor=max(gaps), ref=ref, certificado=nombre in S['zopt'],
                              t_ms=1000 * st.mean(x['t'] for x in v))
c['zref'] = {k: S['zopt'].get(k, best[k]) for k in best}
c['aco_sin_feromona'] = json.load(open('resultados/aco_sin_feromona.json'))
c['aco_cotas'] = json.load(open('resultados/aco_cotas.json'))
c['tiempos'] = json.load(open('resultados/tiempos_componentes.json'))
json.dump(c, open('resultados/cifras.json', 'w'), indent=1, default=lambda o: list(o) if isinstance(o, (set, frozenset)) else float(o))
print(json.dumps({k: c[k] for k in ('ga_div_grupos', 'ga_vecindario', 'primera_ga_100', 'primera_aco_100', 'aco_frac_fantasma',
                                     'aco_branching', 'aco_unicos_fin', 'aco_rho05_pisos', 'aco_rho05_iter_piso', 'aco_prob_repetir_mejor', 'aco_E10b', 'aco_tau_semilla0')}, indent=0, default=str)[:4000])
