"""Compara los modelos A (historico), B (sin subrutas explicitas) y C (experimental) con el mismo protocolo.

Uso: python src/comparar_variantes.py [--out results/comparacion_variantes_<fecha>] [--repeticiones 10]

- Un calentamiento descartado por variante y caso (libre y exactamente tres rutas).
- El orden de las variantes rota en cada repeticion (ABC, BCA, CAB, ...) para repartir la deriva del equipo.
- Tiempos separados (build_s, solve_s, reconstruct_s) y total_s comparable con el historico.
- La certificacion independiente por particiones queda fuera de todo cronometro.
- Una corrida detenida por limite de tiempo se registra con su estado; su tiempo NO es "tiempo hasta el optimo".
"""
import argparse, csv, datetime, json, platform, statistics
from pathlib import Path
import pulp
from resolver_cvrp_arcos import (leer, matriz, exacto, verificar, particion_optima, certificar_dp, MODELOS)

CAMPOS = ('estado', 'causa', 'status', 'sol_status', 'optimo_probado', 'objetivo', 'cota_inferior', 'brecha_cbc', 'nodos',
          'iteraciones', 'relajacion_inicial', 'build_s', 'solve_s', 'reconstruct_s', 'total_s', 'limite_s',
          'variables', 'constraints', 'sec')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--instancia', default='data/instancia.txt')
    ap.add_argument('--out', default='results/comparacion_variantes')
    ap.add_argument('--repeticiones', type=int, default=10)
    ap.add_argument('--limite', type=float, default=120, help='segundos de CBC por corrida')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    xy, q, Q, depot = leer(args.instancia); d = matriz(xy)
    z_libre = certificar_dp(q, Q, depot, d); z_tres, _ = particion_optima(q, Q, depot, d, k=3)
    variantes = sorted(MODELOS)
    casos = (('libre', None), ('tres_rutas', 3))
    for caso, k in casos:  # calentamiento descartado
        for v in variantes: exacto(q, Q, depot, d, fixed_k=k, limite=args.limite, exigir_optimo=False, modelo=v)
    filas = []
    for caso, k in casos:
        for rep in range(1, args.repeticiones + 1):
            orden = variantes[(rep - 1) % 3:] + variantes[:(rep - 1) % 3]
            for pos, v in enumerate(orden, 1):
                routes, t = exacto(q, Q, depot, d, out / f'cbc_{caso}_{v}_{rep:02}.log', fixed_k=k, limite=args.limite,
                                   exigir_optimo=False, modelo=v)
                z = sum(r['distancia'] for r in verificar(routes, q, Q, depot, d)) if routes else None
                filas.append({'caso': caso, 'variante': v, 'repeticion': rep, 'posicion_en_el_orden': pos,
                              **{c: t.get(c) for c in CAMPOS}, 'z_recalculado': z})
                print(caso, rep, v, t['estado'], z, f"{t['total_s']:.2f}s", flush=True)
    resumen = {}
    for caso, k in casos:
        for v in variantes:
            g = [f for f in filas if f['caso'] == caso and f['variante'] == v]
            tt = [f['total_s'] for f in g]
            resumen[f'{caso}_{v}'] = {
                'n': len(g), 'estados': {e: sum(1 for f in g if f['estado'] == e) for e in sorted({f['estado'] for f in g})},
                'probadas': f"{sum(1 for f in g if f['estado'] == 'optimo_probado')}/{len(g)}",
                'tiempo_total_s': {'media': statistics.mean(tt), 'mediana': statistics.median(tt),
                                   'desv_est': statistics.stdev(tt), 'min': min(tt), 'max': max(tt)},
                'nota_tiempo': 'promedio de corridas con estados mixtos' if any(f['estado'] != 'optimo_probado' for f in g)
                               else 'todas las corridas probaron optimalidad',
                'solve_s_media': statistics.mean(f['solve_s'] for f in g),
                'nodos_media': statistics.mean(f['nodos'] for f in g if f['nodos'] is not None),
                'iteraciones_media': statistics.mean(f['iteraciones'] for f in g if f['iteraciones'] is not None),
                'objetivos_probados': sorted({round(f['z_recalculado'], 9) for f in g if f['estado'] == 'optimo_probado'})}
    res = {'esquema': 'comparacion', 'certificacion_dp': {'libre': z_libre, 'tres_rutas': z_tres},
           'configuracion': {'repeticiones': args.repeticiones, 'limite_s': args.limite,
                             'orden': 'rotativo: ABC, BCA, CAB, ...', 'calentamiento': '1 corrida descartada por variante y caso'},
           'entorno': {'python': platform.python_version(), 'pulp': pulp.__version__, 'sistema': platform.platform(),
                       'procesador': platform.processor(), 'fecha': datetime.date.today().isoformat()},
           'resumen': resumen}
    (out / 'resultados.json').write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding='utf8')
    with (out / 'mediciones.csv').open('w', newline='', encoding='utf8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
