"""Figuras de la Etapa 3 (PNG para el documento)."""
import json
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from instancias import todas, leer

R, F = '../resultados/', '../figuras/'
AZUL, NARANJA, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
TXT, TXT2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.size': 9.5, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': TXT2, 'axes.labelcolor': TXT, 'xtick.color': TXT2,
                     'ytick.color': TXT2, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6,
                     'axes.axisbelow': True, 'legend.frameon': False, 'figure.dpi': 110})
A = json.load(open(R + 'analisis.json'))
CW = {f['inst']: f for f in json.load(open(R + 'cw.json'))}
NOM = todas()
N = {n: leer(n).n for n in NOM}


def cargar(f):
    return [json.loads(l) for l in open(R + f)]


def efectos(alg, factores, etiquetas, archivo):
    fig, ax = plt.subplots(2, len(factores), figsize=(2.6 * len(factores), 4.6), sharey='row')
    for k, (f, et) in enumerate(zip(factores, etiquetas)):
        niv = A[alg]['efectos'][f]['niveles']
        x = list(niv)
        ax[0, k].plot(range(len(x)), [niv[v]['gap'] for v in x], 'o-', color=NARANJA if alg == 'ga' else AQUA, lw=2, ms=7)
        ax[1, k].plot(range(len(x)), [niv[v]['tiempo'] for v in x], 'o-', color=TXT2, lw=2, ms=7)
        for r in (0, 1):
            ax[r, k].set_xticks(range(len(x)), [v.replace('.0', '') for v in x])
            ax[r, k].set_xlim(-0.4, len(x) - 0.6)
        ax[1, k].set_xlabel(et)
        p = A[alg]['efectos'][f]['p']
        ax[0, k].set_title(f'p = {p:.3g}', fontsize=8.5, color=TXT2)
    ax[0, 0].set_ylabel('GAP medio vs BKS (%)')
    ax[1, 0].set_ylabel('Tiempo medio (s)')
    fig.tight_layout(); fig.savefig(F + archivo, dpi=170); plt.close(fig)


def comparacion():
    gi, ai = A['inst_ga'], A['inst_aco']
    orden = sorted(NOM, key=lambda n: (n.startswith('X'), N[n]))
    y = np.arange(len(orden))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 7.4))
    for vals, col, lab, m in ((
            [CW[n]['gap'] for n in orden], AZUL, 'Clarke-Wright + 2-opt', 'o'),
            ([ai[n]['gap'] for n in orden], AQUA, 'ACO (mejor configuración)', 's'),
            ([gi[n]['gap'] for n in orden], NARANJA, 'GA (mejor configuración)', 'D')):
        ax.scatter(vals, y, s=42, color=col, label=lab, marker=m, edgecolor='white', linewidth=1, zorder=3)
    ax.set_yticks(y, [f'{n} ({N[n]})' for n in orden], fontsize=8)
    ax.set_xlabel('GAP vs mejor solución conocida (%) - promedio de 5 corridas')
    ax.legend(loc='lower right')
    ax.axhline(y[13] - .5, color=TXT2, lw=.8, ls='--')
    fig.tight_layout(); fig.savefig(F + 'comparacion_gap.png', dpi=170); plt.close(fig)


def tiempos():
    gi, ai = A['inst_ga'], A['inst_aco']
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    xs = [N[n] for n in NOM]
    for vals, col, lab, m in (([CW[n]['tiempo'] for n in NOM], AZUL, 'Clarke-Wright + 2-opt', 'o'),
                              ([ai[n]['tiempo'] for n in NOM], AQUA, 'ACO', 's'),
                              ([gi[n]['tiempo'] for n in NOM], NARANJA, 'GA', 'D')):
        ax.scatter(xs, vals, s=36, color=col, label=lab, marker=m, edgecolor='white', linewidth=1, zorder=3)
    ax.set_yscale('log'); ax.set_xlabel('Número de clientes n'); ax.set_ylabel('Tiempo por corrida (s, escala log)')
    ax.legend(); fig.tight_layout(); fig.savefig(F + 'tiempos.png', dpi=170); plt.close(fig)


def convergencia(instancias=('CMT5', 'X-n459-k26')):
    ga, aco = cargar('ga.jsonl'), cargar('aco.jsonl')
    mg, ma = tuple(A['mejor_ga']), tuple(A['mejor_aco'])
    peor_g = tuple(max(A['ga']['celdas'], key=lambda f: f['rango'])['celda'])
    peor_a = tuple(max(A['aco']['celdas'], key=lambda f: f['rango'])['celda'])
    fig, ax = plt.subplots(1, len(instancias), figsize=(7.2, 3.8))
    for k, n in enumerate(instancias):
        bks = leer(n).bks
        x = np.linspace(0, 100, 100)
        for filas, clave, cel, col, ls, lab in (
                (ga, lambda r: (r['puntos'], r['pm'], r['seleccion']), mg, NARANJA, '-', 'GA mejor'),
                (ga, lambda r: (r['puntos'], r['pm'], r['seleccion']), peor_g, NARANJA, ':', 'GA peor'),
                (aco, lambda r: (r['alfa'], r['beta'], r['rho']), ma, AQUA, '-', 'ACO mejor'),
                (aco, lambda r: (r['alfa'], r['beta'], r['rho']), peor_a, AQUA, ':', 'ACO peor')):
            H = np.array([r['hist'] for r in filas if r['inst'] == n and clave(r) == tuple(cel)])
            ax[k].plot(x, 100 * (H.mean(0) - bks) / bks, color=col, ls=ls, lw=2, label=lab)
        ax[k].axhline(CW[n]['gap'], color=AZUL, lw=1.4, ls='--', label='Clarke-Wright + 2-opt')
        ax[k].set_title(n, fontsize=9.5); ax[k].set_xlabel('% de iteraciones')
        ax[k].set_ylim(0, None)
    ax[0].set_ylabel('GAP vs BKS (%)')
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=5, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(F + 'convergencia.png', dpi=170); plt.close(fig)


def escalabilidad():
    E = json.load(open(R + 'escalabilidad_modelo.json'))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    k = [e['k'] for e in E]
    t = [e['tiempo_modelo'] for e in E]
    col = [AZUL if e['estado'] == 'optimo_probado' else NARANJA for e in E]
    ax.plot(k, t, color=GRID, lw=1.5, zorder=1)
    ax.scatter(k, t, c=col, s=50, zorder=3, edgecolor='white')
    ax.set_yscale('log'); ax.set_xlabel('Clientes en la subinstancia de CMT1'); ax.set_ylabel('Tiempo de CBC (s, log)')
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker='o', ls='', color=AZUL, label='óptimo probado'),
                       Line2D([], [], marker='o', ls='', color=NARANJA, label='detenido por tiempo')])
    fig.tight_layout(); fig.savefig(F + 'escalabilidad_modelo.png', dpi=170); plt.close(fig)


if __name__ == '__main__':
    import os, sys
    os.makedirs(F, exist_ok=True)
    efectos('ga', ['puntos', 'pm', 'seleccion'], ['Puntos de cruce', 'Prob. de mutación', 'Selección'], 'efectos_ga.png')
    efectos('aco', ['alfa', 'beta', 'rho'], ['α', 'β', 'ρ'], 'efectos_aco.png')
    comparacion(); tiempos(); convergencia()
    if 'modelo' in sys.argv:
        escalabilidad()
    print('ok')
