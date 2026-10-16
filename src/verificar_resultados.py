"""Comprueba, sin volver a resolver, que un directorio de resultados es coherente.

Uso: python src/verificar_resultados.py [results] [--instancia data/instancia.txt]

Recalcula distancias y cargas desde la instancia
y las contrasta con resultados.json, mediciones.csv, matriz_costos.csv y los
registros CBC. Reconoce tres formatos: la evidencia historica (modelo A), las mediciones
nuevas (esquema 2, src/resolver_cvrp_arcos.py) y la comparacion de variantes. La certificacion
independiente y el tamano de cada modelo requieren PuLP. Termina con codigo 1 si alguna comprobacion falla.
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


AVISOS = []


def verificar_comparacion(R, res, q, Q, check):
    """Comparacion de variantes A/B/C (src/comparar_variantes.py): recalcula todo desde mediciones.csv y los registros."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import resolver_cvrp_arcos as M
    filas = list(csv.DictReader((res / 'mediciones.csv').open(encoding='utf8')))
    n = R['configuracion']['repeticiones']
    check(f'{len(filas)} filas = 2 casos x 3 variantes x {n} repeticiones', len(filas) == 6 * n)
    check('certificacion_dp: 318.989487 (libre) y 339.164674 (tres rutas)',
          abs(R['certificacion_dp']['libre'] - ESPERADO['optimo']) < 1e-6 and abs(R['certificacion_dp']['tres_rutas'] - ESPERADO['tres_rutas']) < 1e-6)
    ok_obj = ok_log = ok_tam = ok_tot = 0
    certificado = {'libre': R['certificacion_dp']['libre'], 'tres_rutas': R['certificacion_dp']['tres_rutas']}
    for f in filas:
        if f['estado'] == 'optimo_probado': ok_obj += abs(float(f['z_recalculado']) - certificado[f['caso']]) < 1e-6
        else: ok_obj += f['z_recalculado'] == '' or float(f['z_recalculado']) >= certificado[f['caso']] - 1e-6
        log = res / f"cbc_{f['caso']}_{f['variante']}_{int(f['repeticion']):02}.log"
        txt = log.read_text(encoding='utf8', errors='replace') if log.exists() else ''
        ok_log += bool(txt) and (('Optimal solution found' in txt) == (f['estado'] == 'optimo_probado'))
        ok_tot += abs(float(f['total_s']) - sum(float(f[k]) for k in ('build_s', 'solve_s', 'reconstruct_s') if f[k])) < 1e-6
        if f['estado'] != 'optimo_probado':
            AVISOS.append(f"{f['caso']} modelo {f['variante']} repeticion {f['repeticion']}: {f['estado']} (objetivo {float(f['objetivo']):.6f}); tiempo no es 'hasta el optimo'")
    check('objetivo de cada fila: igual al certificado si fue probada; nunca inferior al certificado si no', ok_obj == len(filas), f'{ok_obj}/{len(filas)}')
    check('registro CBC de cada fila: "Optimal solution found" si y solo si optimo_probado', ok_log == len(filas), f'{ok_log}/{len(filas)}')
    check('total_s = build_s + solve_s + reconstruct_s en cada fila', ok_tot == len(filas))
    libre = [f for f in filas if f['caso'] == 'libre']
    check('caso libre: las 30 corridas probaron optimalidad', all(f['estado'] == 'optimo_probado' for f in libre))
    for v in sorted(M.MODELOS):
        g = [f for f in filas if f['variante'] == v]
        r = R['resumen'][f"libre_{v}"]['tiempo_total_s']['media']
        check(f'modelo {v}: media libre del JSON = mediciones.csv',
              abs(statistics.mean(float(f['total_s']) for f in g if f['caso'] == 'libre') - r) < 1e-9)
    for v, n_filas in (('A', (1167, 1168)), ('B', (154, 155)), ('C', (264, 265))):
        g = [f for f in filas if f['variante'] == v]
        check(f'modelo {v}: restricciones = {n_filas[0]} (libre) y {n_filas[1]} (tres rutas)',
              all(int(f['constraints']) == n_filas[0 if f['caso'] == 'libre' else 1] for f in g))
    for a in AVISOS: print('AVISO ' + a)


def verificar_v2(R, res, q, Q, check, solucion, dist):
    """Comprobaciones de una medicion con esquema 2: recalcula todo desde la instancia y las filas."""
    depot = 1
    ze = solucion('libre', R['exacto'], ESPERADO['optimo'], 4)
    zh = solucion('heuristica', R['heuristica'], ESPERADO['heuristica'])
    f3 = next(f for f in csv.DictReader((res / 'mediciones.csv').open(encoding='utf8')) if f['caso'] == 'tres_rutas' and f['repeticion'] == '1')
    prob3 = f3['estado'] == 'optimo_probado'  # la solucion guardada es la de la repeticion 1
    z3 = solucion('tres rutas' + ('' if prob3 else ' (incumbente sin prueba de optimalidad)'), R['tres_rutas'],
                  ESPERADO['tres_rutas'] if prob3 else None, 3)
    if not prob3:
        check('tres rutas: el incumbente no es mejor que el optimo certificado', z3 >= ESPERADO['tres_rutas'] - 1e-6, f'{z3:.6f}')
        AVISOS.append(f'la primera repeticion de tres rutas no probo optimalidad (incumbente {z3:.6f}); el optimo certificado es {ESPERADO["tres_rutas"]:.6f}')
    esperado_filas = None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import resolver_cvrp_arcos as M
        xy = {int(k): tuple(v) for k, v in R['xy'].items()}
        d = M.matriz(xy)
        z4, _ = M.particion_optima(q, Q, depot, d); z3dp, _ = M.particion_optima(q, Q, depot, d, k=3)
        check('DP independiente: optimo sin flota fija = 318.989487', abs(z4 - ESPERADO['optimo']) < 1e-6, f'{z4:.10f}')
        check('DP independiente: optimo con exactamente 3 rutas = 339.164674', abs(z3dp - ESPERADO['tres_rutas']) < 1e-6, f'{z3dp:.10f}')
        check('resultados.json: certificacion_dp coincide con el recalculo',
              abs(R['certificacion_dp']['libre'] - z4) < 1e-9 and abs(R['certificacion_dp']['tres_rutas'] - z3dp) < 1e-9)
        esperado_filas = {k: len(M.construir_modelo(q, Q, depot, d, R['modelo'], k)[0].constraints) for k in (None, 3)}
    except ImportError:
        print('INFO  certificacion DP y tamano del modelo omitidos (instale PuLP)')
    pct = R['porcentajes']
    gap = 100 * (zh - ze) / ze; red = 100 * (zh - ze) / zh
    check('GAP de costo (base Z_exacto) recalculado',
          abs(pct['gap_costo_pct']['valor'] - gap) < 1e-9 and abs(gap - ESPERADO['gap_pct']) < 1e-5, f'{gap:.6f}%')
    check('reduccion respecto de la heuristica (base Z_heur) recalculada',
          abs(pct['reduccion_distancia_vs_heuristica_pct']['valor'] - red) < 1e-9, f'{red:.6f}%')
    check('sobrecosto de tres rutas (base Z_exacto) recalculado',
          abs(pct['sobrecosto_tres_rutas_pct']['valor'] - 100 * (R['certificacion_dp']['tres_rutas'] - ze) / ze) < 1e-9,
          f"{100 * (R['certificacion_dp']['tres_rutas'] - ze) / ze:.6f}%")

    filas = list(csv.DictReader((res / 'mediciones.csv').open(encoding='utf8')))
    n = R['configuracion']['repeticiones']
    por = {c: [f for f in filas if f['caso'] == c] for c in ('libre', 'tres_rutas')}
    nsec = 1013 if R['modelo'] == 'A' else 0
    check(f'mediciones.csv: {n} repeticiones por caso', all(len(v) == n for v in por.values()) and len(filas) == 2 * n)
    check('mediciones.csv: modelo declarado en todas las filas', {f['modelo'] for f in filas} == {R['modelo']})
    check(f'mediciones.csv: 220 variables y {nsec} restricciones de subrutas',
          all(f['variables'] == '220' and f['sec'] == str(nsec) for f in filas))
    if esperado_filas:
        check('mediciones.csv: restricciones = las del modelo %s (libre %d, tres rutas %d)' % (R['modelo'], esperado_filas[None], esperado_filas[3]),
              all(int(f['constraints']) == esperado_filas[None if f['caso'] == 'libre' else 3] for f in filas))
    check('caso libre: estado optimo_probado y sol_status 1 en todas las repeticiones',
          all(f['estado'] == 'optimo_probado' and f['sol_status'] == '1' and f['optimo_probado'] == 'True' for f in por['libre']))
    check('caso libre: objetivo y heuristica constantes e iguales a los de la solucion',
          all(abs(float(f['z_exacto']) - ze) < 1e-9 and abs(float(f['z_heuristica']) - zh) < 1e-9 for f in por['libre']))
    probadas = [f for f in por['tres_rutas'] if f['estado'] == 'optimo_probado']
    check('tres rutas: toda repeticion con optimo_probado tiene el objetivo certificado',
          all(abs(float(f['z_exacto']) - ESPERADO['tres_rutas']) < 1e-6 for f in probadas), f'{len(probadas)}/{n} probadas')
    for f in por['tres_rutas']:
        if f['estado'] != 'optimo_probado':
            AVISOS.append(f"tres rutas, repeticion {f['repeticion']}: {f['estado']} ({f['causa']}); no cuenta como optimo probado")
    check('tiempos: total_s = build_s + solve_s + reconstruct_s en cada fila',
          all(abs(float(f['total_s']) - sum(float(f[k]) for k in ('build_s', 'solve_s', 'reconstruct_s') if f[k])) < 1e-6 for f in filas))
    est = R['estadisticas']
    check('estadisticas: media del tiempo total libre = mediciones.csv',
          abs(statistics.mean(float(f['total_s']) for f in por['libre']) - est['exacto_libre']['total_s']['media']) < 1e-9)
    check('estadisticas: media del tiempo total tres rutas = mediciones.csv',
          abs(statistics.mean(float(f['total_s']) for f in por['tres_rutas']) - est['exacto_tres_rutas']['total_s']['media']) < 1e-9)
    th = statistics.mean(float(f['heuristica_s']) for f in por['libre'])
    check('estadisticas: media del tiempo de la heuristica = mediciones.csv', abs(th - est['heuristica_s']['media']) < 1e-12, f'{th * 1000:.4f} ms')
    te = est['exacto_libre']['total_s']['media']
    check('porcentajes de tiempo: reduccion (base t_exacto) y razon recalculadas',
          abs(pct['reduccion_tiempo_heuristica_pct']['valor'] - 100 * (te - th) / te) < 1e-9
          and abs(pct['razon_tiempos_exacto_sobre_heuristica'] - te / th) < 1e-6)
    matriz = list(csv.reader((res / 'matriz_costos.csv').open(encoding='utf8')))
    ids = [int(x) for x in matriz[0][1:]]
    check('matriz_costos.csv = distancias euclidianas sin redondeo de la instancia',
          all(abs(float(matriz[1 + a][1 + b]) - dist(i, j)) < 1e-9 for a, i in enumerate(ids) for b, j in enumerate(ids)))
    bien = 0
    for f in filas:
        log = res / f"cbc_{f['caso']}_{int(f['repeticion']):02}.log"
        txt = log.read_text(encoding='utf8', errors='replace') if log.exists() else ''
        m = re.search(r'Objective value:\s+([\d.]+)', txt)
        if f['estado'] == 'optimo_probado':
            bien += 'Optimal solution found' in txt and m is not None and abs(float(m[1]) - float(f['z_exacto'])) < 1e-6
        else:
            bien += 'Optimal solution found' not in txt and bool(txt)
    check('registros CBC: "Optimal solution found" con el objetivo de la fila si y solo si el estado es optimo_probado',
          bien == len(filas), f'{bien}/{len(filas)}')
    for a in AVISOS: print('AVISO ' + a)


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
    if R.get('esquema') == 'comparacion':
        verificar_comparacion(R, res, q, Q, check)
        print(f'\n{total - len(fallos)}/{total} comprobaciones superadas, {len(AVISOS)} aviso(s)')
        sys.exit(1 if fallos else 0)
    if R.get('esquema') == 2:  # resultados de la medicion nueva (resolver_cvrp_arcos.py, esquema 2)
        verificar_v2(R, res, q, Q, check, solucion, dist)
        print(f'\n{total - len(fallos)}/{total} comprobaciones superadas, {len(AVISOS)} aviso(s)')
        sys.exit(1 if fallos else 0)
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
    check('mediciones.csv (esquema historico, modelo A): 10 repeticiones, todas Optimal con 220 variables, 1167 restricciones y 1013 SEC',
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
