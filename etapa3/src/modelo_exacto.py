"""Escalabilidad del modelo matemático (modelo B de la Etapa 1: arcos + carga, PuLP/CBC) y
GAP de las heurísticas respecto del óptimo probado.

Subinstancias de CMT1 (depósito + primeros k clientes, sin límite de duración) de tamaño
creciente, más la instancia completa CMT1 (50 clientes) con límite de tiempo.
Uso: python modelo_exacto.py [limite_s]
"""
import json, sys, time
from pathlib import Path
import numpy as np

# Modelo B de la Etapa 1: src/resolver_cvrp_arcos.py en la raíz del repositorio (etapa3/src -> ../../src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from resolver_cvrp_arcos import exacto                      # modelo B del repositorio del equipo
from instancias import leer, subinstancia
from algoritmos import clarke_wright, correr_ga, correr_aco, verificar

import os
TAMANOS = [int(x) for x in os.environ["TAMANOS"].split(",")] if "TAMANOS" in os.environ else [5, 8, 10, 12, 15, 20, 25, 30, 50]


def a_dicts(I):
    q = {i: int(I.q[i]) for i in range(I.n + 1)}
    d = {(i, j): float(I.d[i, j]) for i in range(I.n + 1) for j in range(I.n + 1)}
    return q, d


def resolver(I, limite):
    q, d = a_dicts(I)
    log = Path(f'../resultados/cbc_{I.nombre}.log')
    rutas, info = exacto(q, I.Q, 0, d, log=log, limite=limite, exigir_optimo=False, modelo='B')
    if rutas:
        rr = [r[1:-1] for r in rutas]
        info['z_verificado'] = verificar(I, rr)
    return info


if __name__ == '__main__':
    limite = float(sys.argv[1]) if len(sys.argv) > 1 else 600
    cfg = json.load(open('../resultados/mejores_config.json'))
    base = leer('CMT1')
    previo = Path('../resultados/escalabilidad_modelo.json')
    filas = [f for f in json.load(open(previo)) if f['k'] not in TAMANOS] if previo.exists() else []
    for k in TAMANOS:
        I = base if k == base.n else subinstancia(base, k)
        I.nombre = 'CMT1' if k == base.n else f'CMT1-sub{k}'
        info = resolver(I, limite)
        cw = clarke_wright(I)
        ga = [correr_ga(I, s, **cfg['ga']) for s in range(5)]
        aco = [correr_aco(I, s, **cfg['aco']) for s in range(5)]
        fila = dict(k=k, estado=info['estado'], objetivo=info['objetivo'], cota=info.get('cota_inferior'),
                    tiempo_modelo=info['total_s'], variables=info['variables'], restricciones=info['constraints'],
                    cw=cw['z'], t_cw=cw['tiempo'],
                    ga=float(np.mean([r['z'] for r in ga])), ga_min=float(min(r['z'] for r in ga)),
                    t_ga=float(np.mean([r['tiempo'] for r in ga])),
                    aco=float(np.mean([r['z'] for r in aco])), aco_min=float(min(r['z'] for r in aco)),
                    t_aco=float(np.mean([r['tiempo'] for r in aco])))
        filas.append(fila)
        print(json.dumps(fila), flush=True)
        json.dump(sorted(filas, key=lambda f: f['k']), open('../resultados/escalabilidad_modelo.json', 'w'), indent=1)
