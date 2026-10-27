"""Genera las tablas nuevas del informe en latex/tablas/*.tex a partir de resultados/*.json (sin transcribir a mano)."""
import json, os, sys
sys.path.insert(0, 'src')
from algoritmos import split
from instancia import DEM, Q, DEPOT, D, Z_OPT

os.makedirs('latex/tablas', exist_ok=True)
E = json.load(open('resultados/ejemplos.json'))
P = json.load(open('resultados/principal.json'))
C = json.load(open('resultados/cifras.json'))
f6 = lambda x: f'{x:.6f}'
flecha = lambda r: r'$\to$'.join(map(str, r))


def escribir(nombre, texto):
    open(f'latex/tablas/{nombre}.tex', 'w').write(texto.strip() + '\n')


# --- Split: etiquetas D(b) y predecesores
sp = E['split']; p = sp['perm']
filas = []
for b in range(1, 11):
    a = sp['prev'][b] + 1
    seg = p[a - 1:b]
    w = D[DEPOT, seg[0]] + sum(D[x, y] for x, y in zip(seg, seg[1:])) + D[seg[-1], DEPOT]
    filas.append(f"{b} & {p[b-1]} & {DEM[p[b-1]]} & {f6(sp['dp'][b])} & {sp['prev'][b]} & "
                 f"$(\\pi_{{{a}}},\\dots,\\pi_{{{b}}})=({', '.join(map(str, seg))})$ & {sum(DEM[c] for c in seg)} & {f6(w)}\\\\")
escribir('split_dp', r'''
\begin{tabular}{rrrrrlrr}\toprule
$b$ & $\pi_b$ & $q_{\pi_b}$ & $D(b)$ & $\mathrm{pred}(b)$ & Último segmento que da $D(b)$ & Carga & $w_{ab}$\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')

# candidatos evaluados para b = 7 (ilustra la minimización)
cands = [e for e in sp['evaluados'] if e[1] == 7]
filas = []
for a, b, carga, w, val in cands:
    if w is None:
        filas.append(f'{a} & {carga} & \\multicolumn{{2}}{{l}}{{excede $Q=50$: no se evalúa}}\\\\')
    else:
        marca = r' $\leftarrow$ mínimo' if abs(val - sp['dp'][7]) < 1e-9 else ''
        filas.append(f"{a} & {carga} & $D({a-1})+w_{{{a},7}}={f6(sp['dp'][a-1])}+{f6(w)}$ & {f6(val)}{marca}\\\\")
escribir('split_b7', r'''
\begin{tabular}{rrlr}\toprule
$a$ & $L_{a7}$ & Candidato & Valor\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')

# --- OX e inversión
ox = E['ox']; inv = E['inv']
celda = lambda v, resaltar: f'\\textbf{{{v}}}' if resaltar else str(v)
lo, hi = ox['lo'], ox['hi']
def fila(nombre, vec, rango=None):
    return nombre + ' & ' + ' & '.join(celda(v, rango and rango[0] <= k <= rango[1]) for k, v in enumerate(vec)) + r'\\'
escribir('ox', r'''
\begin{tabular}{l*{10}{c}}\toprule
Posición & 1 & 2 & 3 & 4 & 5 & 6 & 7 & 8 & 9 & 10\\\midrule
''' + fila('Padre $a$', ox['a'], (lo, hi)) + '\n' + fila('Padre $b$', ox['b']) + '\n' +
r'Orden circular de $b$ desde la posición 8 & \multicolumn{10}{l}{' + ', '.join(map(str, ox['b'][hi+1:] + ox['b'][:hi+1])) + r'}\\' + '\n' +
r'Sin los genes ya copiados & \multicolumn{10}{l}{' + ', '.join(str(v) for v in ox['b'][hi+1:] + ox['b'][:hi+1] if v not in ox['a'][lo:hi+1]) + r'}\\' + '\n' +
fila('Hijo OX', ox['hijo'], (lo, hi)) + '\n' +
fila(f"Hijo invertido ($i={inv['i']+1}$, $j={inv['j']+1}$)", inv['despues'], (inv['i'], inv['j'])) + r'''
\bottomrule\end{tabular}''')

# --- hormiga: construcción paso a paso
h = E['hormiga']
filas = []
for k, s in enumerate(h['pasos'], 1):
    top = ', '.join(f'{j} ({pp:.3f})' for j, pp in s['top3'])
    filas.append(f"{k} & {s['desde']} & {top} & {s['elegido']} & {s['p_elegido']:.3f} & {s['carga_acumulada']}\\\\")
escribir('hormiga', r'''
\begin{tabular}{rrlrrr}\toprule
Paso & Desde $i$ & Tres opciones más probables ($p_{ij}$) & Elegido & $p_{ij}$ & Demanda acumulada\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')

# --- evolución del mejor cromosoma en las semillas 4 y 8
filas = []
for s in ('4', '8'):
    for g, ev, z, perm in P['ga'][s]['mejoras']:
        _, rutas = split(perm, DEM, Q, DEPOT, D)
        grupos = ' $|$ '.join(','.join(map(str, r[1:-1])) for r in rutas)
        filas.append(f"{s} & {g} & {ev} & {f6(z)} & {100*(z-Z_OPT)/Z_OPT:.2f} & {grupos}\\\\")
    filas.append(r'\addlinespace')
escribir('mejoras_4_8', r'''
\begin{tabular}{rrrrrl}\toprule
Semilla & Generación & Evaluación & Mejor $Z$ & GAP (\%) & Rutas después de Split (clientes)\\\midrule
''' + '\n'.join(filas[:-1]) + r'''
\bottomrule\end{tabular}''')

# --- rutas de semillas 4 y 8
filas = []
for s in ('4', '8'):
    for k, r in enumerate(P['ga'][s]['rutas'], 1):
        filas.append(f"{s} & R{k} & {flecha(r['ruta'])} & {f6(r['dist'])} & {r['carga']} & {round(100*(50-r['carga'])/50)}\\\\")
    filas.append(r'\addlinespace')
escribir('rutas_4_8', r'''
\begin{tabular}{rllrrr}\toprule
Semilla & Ruta & Recorrido & Distancia & Carga / 50 & Libre (\%)\\\midrule
''' + '\n'.join(filas[:-1]) + r'''
\bottomrule\end{tabular}''')

# --- feromona en las 11 adyacencias del mejor ciclo gigante de ACO, semilla 0
t = C['aco_tau_semilla0']
filas = [f"({i},{j}) & {v:.4f} & {'Sí' if usada else r'\textbf{No}: une el final de una ruta con el inicio de la siguiente'}\\\\"
         for i, j, v, usada in t['adyacencias']]
filas2 = [f"({i},{j}) & {v:.2e} & Sí, pero no es adyacencia del ciclo gigante\\\\" for i, j, v in t['no_reforzados']]
escribir('tau_semilla0', r'''
\begin{tabular}{lrl}\toprule
Par $\{i,j\}$ & $\tau_{ij}$ final & ¿Es arco de las rutas finales?\\\midrule
''' + '\n'.join(filas) + r'\midrule' + '\n' + '\n'.join(filas2) + r'''
\bottomrule\end{tabular}''')

# --- sensibilidad ACO: alfa x beta
AB = C['aco_alfa_beta']
filas = []
for a in (.5, 1., 2.):
    celdas = []
    for b in (0., 1., 2., 5.):
        x = AB[f'{a}|{b}']
        med = '--' if x['mediana'] is None else f"{x['mediana']:g}"
        txt = f"{x['exitos']}/270 · {x['le200']} · {med}"
        celdas.append(r'\textbf{' + txt + '}' if (a, b) == (1., 2.) else txt)
    filas.append(f'$\\alpha={a:g}$ & ' + ' & '.join(celdas) + r'\\')
escribir('sens_aco', r'''
\begin{tabular}{lcccc}\toprule
 & $\beta=0$ & $\beta=1$ & $\beta=2$ & $\beta=5$\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')

# rho y hormigas (beta en {1, 2})
filas = []
for nombre, clave, fmt in (('rho', 'aco_rho_beta12', '{:g}'), ('Hormigas', 'aco_ants_beta12', '{:g}')):
    for lv, x in C[clave].items():
        etiqueta = (f'$\\rho = {float(lv):g}$' if nombre == 'rho' else f'{float(lv):g} hormigas, {2000 // int(float(lv))} iteraciones')
        filas.append(f"{etiqueta} & {x['exitos']}/{x['n']} & {x['le200']}/{x['n']} & {x['mediana']:g}\\\\")
escribir('sens_aco_rho', r'''
\begin{tabular}{lrrr}\toprule
Nivel (resto de factores combinados, $\beta\in\{1,2\}$) & Con $Z^*$ en 2000 eval. & Con $Z^*$ en 200 eval. & Mediana hasta $Z^*$\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')

# --- sensibilidad GA
G = C['ga_tabla']
filas = []
for pm in (0., .1, .2, .4, .6, .8, 1.):
    celdas = []
    for pop in (10, 20, 40):
        x = G[f'{pm}|{pop}|0.9']
        txt = f"{x['exitos']} [{100*x['ic'][0]:.0f}, {100*x['ic'][1]:.0f}]"
        celdas.append(r'\textbf{' + txt + '}' if (pm, pop) == (.2, 20) else txt)
    filas.append(f'{pm:g} & ' + ' & '.join(celdas) + r'\\')
escribir('sens_ga', r'''
\begin{tabular}{lccc}\toprule
$p_m$ & Población 10 (199 gen.) & Población 20 (99 gen.) & Población 40 (49 gen.)\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')
filas = []
for pc in (.5, .7, .9, 1.):
    a, b = G[f'0.2|20|{pc}'], G[f'0.4|20|{pc}']
    filas.append(f"{pc:g} & {a['exitos']}/100 & {a['media']:.3f} & {b['exitos']}/100 & {b['media']:.3f}\\\\")
escribir('sens_ga_pc', r'''
\begin{tabular}{lrrrr}\toprule
$p_c$ & Éxitos, $p_m=0.2$ & Media $Z$ & Éxitos, $p_m=0.4$ & Media $Z$\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')

# --- instancias adicionales
I = C['instancias']
filas = []
for k in ('E10-a', 'E10-b', 'E10-c', 'E10-d', 'E10-e'):
    cel = [f"{I[f'{k}|ga|{json.dumps({chr(112)+chr(109): pm})}']['exitos']}" for pm in (.1, .2, .4, .6)]
    a = I[f'{k}|aco|{{}}']
    filas.append(f"{k} & {C['zref'][k]:.3f} & " + ' & '.join(cel) + f" & {a['exitos']} & {abs(a['gap_medio']):.3f}\\\\")
escribir('instancias10', r'''
\begin{tabular}{lrrrrrrr}\toprule
 & & \multicolumn{4}{c}{GA: corridas con $Z^*$ (de 30)} & \multicolumn{2}{c}{ACO principal}\\\cmidrule(lr){3-6}\cmidrule(lr){7-8}
Instancia & $Z^*$ certificado & $p_m=0.1$ & $0.2$ & $0.4$ & $0.6$ & Con $Z^*$ & GAP medio (\%)\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')
filas = []
for k in ('E20', 'E30'):
    for steps, ev in ((100, 2000), (500, 10000)):
        g2 = I[f'{k}|ga|{json.dumps({"pm": .2, "steps": steps})}']
        g4 = I[f'{k}|ga|{json.dumps({"pm": .4, "steps": steps})}']
        a = I[f'{k}|aco|{json.dumps({"steps": steps})}']
        filas.append(f"{k} & {ev:,} & {g2['gap_medio']:.2f} ({g2['gap_peor']:.2f}) & {g4['gap_medio']:.2f} ({g4['gap_peor']:.2f}) & "
                     f"{a['gap_medio']:.2f} ({a['gap_peor']:.2f}) & {g2['t_ms']:.0f} / {a['t_ms']:.0f}\\\\")
escribir('instancias_grandes', r'''
\begin{tabular}{lrrrrr}\toprule
Instancia & Evaluaciones & GA $p_m=0.2$ & GA $p_m=0.4$ & ACO & Tiempo medio GA / ACO (ms)\\\midrule
''' + '\n'.join(filas) + r'''
\bottomrule\end{tabular}''')
print('tablas listas:', sorted(os.listdir('latex/tablas')))
