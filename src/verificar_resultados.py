"""Comprueba, sin volver a resolver, que un directorio de resultados es coherente.

Uso: python src/verificar_resultados.py [results] [--instancia data/instancia.txt]

Solo usa la biblioteca estandar. Recalcula distancias y cargas desde la instancia
y las contrasta con resultados.json, mediciones.csv, matriz_costos.csv y los
registros CBC. Termina con codigo 1 si alguna comprobacion falla.
"""
import argparse, csv, json, math, re, statistics, sys
from pathlib import Path

ESPERADO = {  # valores documentados en la revision del 15/oct/2026
    'optimo': 318.9894867478301, 'heuristica': 339.252870136741,
    'gap_pct': 6.352367, 'tiempo_exacto_s': 10.970079, 'tres_rutas': 339.1646737615703}


def leer(path):
    xy, q, Q, modo = {}, {}, None, ''
    for linea in Path(path).read_text(encoding='utf-8-sig').splitlines():
        s = linea.strip()
        if s.startswith('CAPACITY'): Q = int(s.split(':')[1])
        elif s in ('NODE_COORD_SECTION', 'DEMAND_SECTION', 'DEPOT_SECTION'): modo = s
        elif s in ('EOF', '-1'): modo = ''
        elif s and ':' not in s:
            a = s.split()
            if modo == 'NODE_COORD_SECTION': xy[int(a[0])] = (float(a[1]), float(a[2]))
            elif modo == 'DEMAND_SECTION': q[int(a[0])] = int(a[1])
    return xy, q, Q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('resultados', nargs='?', default='results')
    ap.add_argument('--instancia', default='data/instancia.txt')
    args = ap.parse_args()
    res = Path(args.resultados)
    xy, q, Q = leer(args.instancia)
    depot = 1
    clientes = sorted(set(q) - {depot})
    R = json.loads((res / 'resultados.json').read_text(encoding='utf8'))
    fallos, total = [], 0

    def check(nombre, cond, detalle=''):
        nonlocal total
        total += 1
        print(('OK    ' if cond else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
        if not cond: fallos.append(nombre)

    def dist(a, b): return math.dist(xy[a], xy[b])
    def largo(r): return sum(dist(a, b) for a, b in zip(r, r[1:]))

    def solucion(nombre, filas, esperado=None, rutas=None):
        rs = [f['ruta'] for f in filas]
        visitados = sorted(i for r in rs for i in r[1:-1])
        check(f'{nombre}: atiende cada cliente exactamente una vez', visitados == clientes)
        check(f'{nombre}: parte y termina en el deposito', all(r[0] == r[-1] == depot for r in rs))
        check(f'{nombre}: carga <= {Q} en cada ruta', all(sum(q[i] for i in r) <= Q for r in rs))
        check(f'{nombre}: cargas y distancias de cada ruta coinciden con la instancia',
              all(sum(q[i] for i in f['ruta']) == f['carga'] and abs(largo(f['ruta']) - f['distancia']) < 1e-9 for f in filas))
        z = sum(largo(r) for r in rs)
        if esperado is not None:
            check(f'{nombre}: distancia total = {esperado:.6f}', abs(z - esperado) < 1e-6, f'{z:.10f}')
        if rutas is not None:
            check(f'{nombre}: {rutas} rutas', len(rs) == rutas)
        return z

    check('instancia: 10 clientes + deposito, Q=50, demanda total 146',
          len(clientes) == 10 and Q == 50 and sum(q.values()) == 146)
    ze = solucion('exacto', R['exacto'], ESPERADO['optimo'], 4)
    zh = solucion('heuristica', R['heuristica'], ESPERADO['heuristica'])
    advertencias = []
    if 'tres_rutas_certificado_dp' in R:
        z3 = solucion('tres rutas', R['tres_rutas'], ESPERADO['tres_rutas'], 3)
    else:  # resultados.json historico: guardo el incumbente de CBC, no el optimo
        z3 = solucion('tres rutas (incumbente de CBC guardado en el JSON)', R['tres_rutas'], None, 3)
        if z3 > ESPERADO['tres_rutas'] + 1e-6:
            advertencias.append(f'resultados.json guarda tres rutas con {z3:.6f}, que NO es el optimo ({ESPERADO["tres_rutas"]:.6f}); ver docs/coherencia.md')
    try:  # certificacion independiente (requiere PuLP solo para importar el modulo)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from resolver_cvrp_arcos import matriz, particion_optima
        d = matriz(xy)
        z4, _ = particion_optima(q, Q, depot, d)
        z3dp, _ = particion_optima(q, Q, depot, d, k=3)
        check('DP independiente: optimo sin flota fija = 318.989487 (4 rutas)', abs(z4 - ESPERADO['optimo']) < 1e-6, f'{z4:.10f}')
        check('DP independiente: optimo con exactamente 3 rutas = 339.164674', abs(z3dp - ESPERADO['tres_rutas']) < 1e-6, f'{z3dp:.10f}')
    except ImportError:
        print('INFO  certificacion DP omitida (instale PuLP para ejecutarla)')
    gap = 100 * (zh - ze) / ze
    check('GAP de costo = (Z_heur - Z_exacto) / Z_exacto', abs(gap - R['gap_costo_pct']) < 1e-9 and abs(gap - ESPERADO['gap_pct']) < 1e-5, f'{gap:.6f}%')

    filas = list(csv.DictReader((res / 'mediciones.csv').open(encoding='utf8')))
    te = [float(f['total_s']) for f in filas]
    check('mediciones.csv: 10 repeticiones, todas Optimal con 220 variables, 1167 restricciones y 1013 SEC',
          len(filas) == 10 and all(f['status'] == 'Optimal' and (f['variables'], f['constraints'], f['sec']) == ('220', '1167', '1013') for f in filas))
    check('mediciones.csv: z_exacto y z_heuristica constantes y iguales a los de la solucion',
          all(abs(float(f['z_exacto']) - ze) < 1e-9 and abs(float(f['z_heuristica']) - zh) < 1e-9 for f in filas))
    check('tiempo exacto medio de mediciones.csv = resultados.json', abs(statistics.mean(te) - R['total_s']['media']) < 1e-9, f'{statistics.mean(te):.6f} s')
    check('tiempo exacto medio coincide con lo documentado (~10.970079 s)  [solo mediciones historicas]',
          abs(statistics.mean(te) - ESPERADO['tiempo_exacto_s']) < 1e-5 or 'reproduccion' in str(res),
          'una nueva ejecucion tendra otros tiempos' if 'reproduccion' in str(res) else '')

    matriz = list(csv.reader((res / 'matriz_costos.csv').open(encoding='utf8')))
    ids = [int(x) for x in matriz[0][1:]]
    check('matriz_costos.csv = distancias euclidianas sin redondeo de la instancia',
          all(abs(float(matriz[1 + a][1 + b]) - dist(i, j)) < 1e-9 for a, i in enumerate(ids) for b, j in enumerate(ids)))

    optimos = 0
    for k in range(1, 11):
        txt = (res / f'cbc_{k:02}.log').read_text(encoding='utf8', errors='replace')
        m = re.search(r'Objective value:\s+([\d.]+)', txt)
        optimos += 'Optimal solution found' in txt and m is not None and abs(float(m[1]) - ze) < 1e-6
    check('registros CBC 01-10: "Optimal solution found" con el objetivo exacto', optimos == 10, f'{optimos}/10')
    log3 = res / 'cbc_3rutas.log'
    if log3.exists():
        txt = log3.read_text(encoding='utf8', errors='replace')
        probado = 'Optimal solution found' in txt
        print(f'INFO  cbc_3rutas.log (modelo de arcos, m=3): {"optimo probado" if probado else "detenido por limite de tiempo, no probo optimalidad"}')
        if not probado:
            m = re.search(r'Objective value:\s+([\d.]+)', txt)
            advertencias.append(f'cbc_3rutas.log no probo optimalidad (objetivo del incumbente {m[1] if m else "?"}); el optimo de 3 rutas se certifica por particion')
    for a in advertencias: print('AVISO ' + a)
    print(f'\n{total - len(fallos)}/{total} comprobaciones superadas, {len(advertencias)} aviso(s) documentado(s)')
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
