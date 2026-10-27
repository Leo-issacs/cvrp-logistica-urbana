"""Control: ACO con alfa = 0 (la feromona no influye; sólo la heurística 1/d^beta), mismo presupuesto.
Permite separar cuánto del éxito se debe a la información heurística y cuánto al aprendizaje por feromona."""
import json, sys, statistics as st
sys.path.insert(0, 'src')
from instancia import DEM, Q, DEPOT, D, Z_OPT
from instancias_extra import EXTRA10
from exacto_subconjuntos import cvrp_exacto
from instrumentado import aco_traza
out = {}
casos = {'CVRP_10': (DEM, Q, DEPOT, D, Z_OPT)}
for k in ('E10-b',):
    I = EXTRA10[k]; casos[k] = (I['dem'], I['Q'], 1, I['d'], cvrp_exacto(I['dem'], I['Q'], 1, I['d'])[0])
for nombre, (q, Qc, dep, d, z) in casos.items():
    for alpha in (0., 1.):
        rs = [aco_traza(q, Qc, dep, d, s, alpha=alpha, z_opt=z, con_diversidad=False, con_feromona=False)
              for s in range(200, 230)]
        ok = [r['primera_opt'] for r in rs if r['primera_opt']]
        out[f'{nombre}|alpha={alpha}'] = dict(exitos=len(ok), n=30, mediana_primera=st.median(ok) if ok else None,
                                              media_z=st.mean(r['z'] for r in rs))
        print(nombre, alpha, out[f'{nombre}|alpha={alpha}'])
json.dump(out, open('resultados/aco_sin_feromona.json', 'w'), indent=1)
