"""Figuras del informe corregido de la etapa 2 (se guardan en figuras/ como PDF y PNG)."""
import json, math, statistics as st, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, 'src')
from instancia import COORD, DEM, Z_OPT

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.titlesize': 10, 'axes.labelsize': 9,
                     'legend.fontsize': 8, 'legend.frameon': False, 'savefig.bbox': 'tight'})
GA, ACO, FALLA, GRIS = '#1F5F8B', '#D9822B', '#C0392B', '#A9B0B7'
RUTA = ['#1F5F8B', '#D9822B', '#3C8D5A', '#8E5BA8']
P = json.load(open('resultados/principal.json'))
C = json.load(open('resultados/cifras.json'))


def guardar(fig, nombre):
    fig.savefig(f'figuras/{nombre}.pdf'); fig.savefig(f'figuras/{nombre}.png', dpi=200); plt.close(fig)


def dibujar_rutas(ax, rutas, titulo):
    for k, r in enumerate(rutas):
        xs = [COORD[v][0] for v in r]; ys = [COORD[v][1] for v in r]
        for a in range(len(r) - 1):
            ax.annotate('', xy=(xs[a + 1], ys[a + 1]), xytext=(xs[a], ys[a]),
                        arrowprops=dict(arrowstyle='-|>', color=RUTA[k % 4], lw=1.4, shrinkA=6, shrinkB=6))
        carga = sum(DEM[v] for v in r)
        ax.plot([], [], color=RUTA[k % 4], lw=1.6, label=f'R{k + 1}: {" → ".join(map(str, r))}  (carga {carga}/50)')
    for v, (x, y) in COORD.items():
        if v == 1:
            ax.scatter(x, y, marker='s', s=70, color='black', zorder=3)
        else:
            ax.scatter(x, y, s=46, color='white', edgecolor='black', zorder=3)
        ax.text(x + 1.6, y + 1.6, str(v), fontsize=8)
    ax.set_xlim(15, 92); ax.set_ylim(18, 88); ax.set_aspect('equal')
    ax.set_xlabel('Coordenada x'); ax.set_ylabel('Coordenada y'); ax.set_title(titulo)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=1, fontsize=7.5)


# Figuras 1 y 2: rutas óptimas de GA y ACO (semilla 0), como en la versión entregada
for m, nombre, tit in (('ga', 'fig1_rutas_ga', 'GA + Split · semilla 0 · Z = 318.989487'),
                       ('aco', 'fig2_rutas_aco', 'ACO + Split · semilla 0 · Z = 318.989487')):
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    dibujar_rutas(ax, [x['ruta'] for x in P[m]['0']['rutas']], tit)
    guardar(fig, nombre)

# Figura nueva: rutas de las semillas no óptimas del GA
fig, axs = plt.subplots(1, 2, figsize=(9.6, 5.0))
for ax, s in zip(axs, ('4', '8')):
    z = P['ga'][s]['z']
    dibujar_rutas(ax, [x['ruta'] for x in P['ga'][s]['rutas']],
                  f'GA semilla {s} · Z = {z:.6f} (GAP {100 * (z - Z_OPT) / Z_OPT:.2f} %)')
guardar(fig, 'fig_rutas_semillas_4_8')

# Figura 3 corregida: convergencia por evaluaciones con la primera evaluación en el óptimo
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.4), sharey=True)
for ax, m, col, nombre in ((axs[0], 'ga', GA, 'GA + Split'), (axs[1], 'aco', ACO, 'ACO + Split')):
    curvas = []
    for s in map(str, range(10)):
        h = P[m][s]['hist']
        ev = [20 * (g + 1) for g in range(len(h))]
        falla = P[m][s]['primera_opt'] is None
        ax.step(ev, h, where='post', color=FALLA if falla else col, alpha=.9 if falla else .28, lw=1.3 if falla else .9)
        if falla:
            ax.text(2010, h[-1], f's{s}', color=FALLA, va='center', fontsize=7.5)
        curvas.append(h)
        fo = P[m][s]['primera_opt']
        if fo:
            ax.plot(fo, Z_OPT, '|', color='black', ms=9, mew=1.1)
    ax.step(ev, np.median(curvas, axis=0), where='post', color=col, lw=2.2, label='Mediana (10 semillas)')
    ax.axhline(Z_OPT, color='black', ls='--', lw=.8, label='Óptimo exacto')
    ax.plot([], [], '|', color='black', ms=9, label='Primera evaluación con Z*')
    ax.set_title(nombre); ax.set_xlabel('Evaluaciones de soluciones'); ax.set_xlim(0, 2100); ax.set_ylim(315, 385)
    ax.legend(loc='upper right')
axs[0].set_ylabel('Mejor distancia acumulada')
guardar(fig, 'fig3_convergencia')

# Figura nueva: distribución de la primera evaluación con el óptimo (100 semillas) — curva de tiempo de ejecución
fig, ax = plt.subplots(figsize=(6.2, 3.4))
for m, col, nombre in (('ga', GA, 'GA'), ('aco', ACO, 'ACO')):
    xs = sorted(x['primera_opt'] for x in P['cien'][m] if x['primera_opt'])
    ys = [(k + 1) / 100 for k in range(len(xs))]
    ax.step([1] + xs + [2000], [0] + ys + [ys[-1]], where='post', color=col, lw=1.8,
            label=f'{nombre}: {len(xs)}/100 semillas; mediana {st.median(xs):g} evaluaciones')
    ax.axvline(st.median(xs), color=col, ls=':', lw=1)
ax.set_xscale('log'); ax.set_xlim(1, 2000); ax.set_ylim(0, 1.02)
ax.set_xlabel('Evaluaciones hasta alcanzar Z* (escala logarítmica)'); ax.set_ylabel('Fracción de semillas con Z*')
ax.set_title('ACO llega al óptimo unas 10 veces antes que GA (semillas 0–99)')
ax.legend(loc='upper left')
guardar(fig, 'fig_primera_evaluacion')

# Figura nueva: diversidad del GA y comparación con la colonia
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.4))
ax = axs[0]
exitos = [s for s in map(str, range(10)) if P['ga'][s]['primera_opt']]
M = np.array([[x[2] for x in P['ga'][s]['diversidad']] for s in exitos])
gen = np.arange(M.shape[1])
ax.fill_between(gen, M.min(axis=0), M.max(axis=0), color=GA, alpha=.15, lw=0)
ax.plot(gen, np.median(M, axis=0), color=GA, lw=1.6, label='Semillas con Z* (mediana y rango, n = 8)')
for s, ls, dy in (('4', '-', 9.5), ('8', '--', 13.5)):
    dv = [x[2] for x in P['ga'][s]['diversidad']]
    ax.plot(gen, dv, color=FALLA, lw=1.1, ls=ls, label=f'Semilla {s}')
    ultima = P['ga'][s]['mejoras'][-1][0]
    ax.annotate(f's{s}: última mejora en la gen. {ultima}', xy=(ultima, dv[ultima]), xytext=(30, dy),
                arrowprops=dict(arrowstyle='-', lw=.6, color=FALLA), color=FALLA, fontsize=7.5)
ax.set_ylim(0, 21); ax.set_xlabel('Generación'); ax.set_ylabel('Soluciones distintas tras Split (de 20)')
ax.set_title('GA: la población converge hacia la generación 18'); ax.legend(loc='upper right')
ax = axs[1]
for m, col, nombre in (('ga', GA, 'Población del GA'), ('aco', ACO, 'Colonia de ACO')):
    mat = np.array([[x[1] for x in P[m][s]['diversidad']] for s in map(str, range(10))])
    ev = [20 * (g + 1) for g in range(mat.shape[1])]
    ax.plot(ev, np.median(mat, axis=0), color=col, lw=1.8, label=nombre)
    ax.fill_between(ev, mat.min(axis=0), mat.max(axis=0), color=col, alpha=.15)
ax.set_xlabel('Evaluaciones de soluciones'); ax.set_ylabel('Distancia media de adyacencias')
ax.set_title('Diversidad de permutaciones (mediana y rango, 10 semillas)'); ax.set_ylim(0, .85)
ax.legend(loc='upper right')
guardar(fig, 'fig_diversidad')

# Figura nueva: semillas 4 y 8 continuadas a 500 generaciones
fig, axs = plt.subplots(2, 1, figsize=(6.6, 4.4), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
for s, ls in (('4', '-'), ('8', '--')):
    h = P['ga_ext'][s]['hist']; ev = [20 * (g + 1) for g in range(len(h))]
    axs[0].step(ev, h, where='post', color=FALLA, ls=ls, label=f'Semilla {s}')
    axs[1].plot(ev, [x[2] for x in P['ga_ext'][s]['diversidad']], color=FALLA, ls=ls, lw=.9)
axs[0].axhline(Z_OPT, color='black', ls=':', lw=.8); axs[0].axvline(2000, color=GRIS, lw=1)
axs[0].text(2050, 352, 'fin del presupuesto\nde la Tabla 7', fontsize=7.5, color='#555')
fo = P['ga_ext']['4']['primera_opt']
axs[0].annotate(f'Z* en la evaluación {fo}', xy=(fo, Z_OPT), xytext=(fo - 3800, 326),
                arrowprops=dict(arrowstyle='->', lw=.8), fontsize=7.5)
axs[0].set_ylabel('Mejor distancia'); axs[0].set_ylim(315, 375); axs[0].legend(loc='upper right')
axs[0].set_title('Continuar 400 generaciones más rescata sólo a la semilla 4')
axs[1].set_ylabel('Soluciones\ndistintas'); axs[1].set_xlabel('Evaluaciones de soluciones'); axs[1].set_ylim(0, 21)
guardar(fig, 'fig_semillas_extendidas')

# Figura nueva: dinámica de la feromona
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.3))
it = np.arange(1, 101)
mx = np.array([[f['max'] for f in P['aco'][s]['feromona']] for s in map(str, range(10))])
br = np.array([[f['branching'] for f in P['aco'][s]['feromona']] for s in map(str, range(10))])
ax = axs[0]
ax.plot(it, np.median(mx, axis=0), color=ACO, lw=1.8, label='τ máxima (mediana)')
ax.axhline(C['aco_cota_tau'], color='black', ls='--', lw=.8, label=f'Cota implícita 20/(ρ·Z*) = {C["aco_cota_tau"]:.4f}')
ax.set_xlabel('Iteración'); ax.set_ylabel('Feromona'); ax.set_title('La feromona máxima se acerca a su cota implícita')
ax.legend(loc='lower right')
ax = axs[1]
ax.plot(it, np.median(br, axis=0), color=ACO, lw=1.8, label='Factor de ramificación λ = 0.05')
uq = np.array([[x[0] for x in P['aco'][s]['diversidad']] for s in map(str, range(10))])
ax2 = ax.twinx(); ax2.spines['right'].set_visible(True)
ax2.plot(it, np.median(uq, axis=0), color=GRIS, lw=1.4, label='Permutaciones distintas por iteración')
ax.set_xlabel('Iteración'); ax.set_ylabel('Arcos atractivos por nodo'); ax2.set_ylabel('Permutaciones distintas (de 20)')
ax.set_title('La colonia se concentra en 2–3 arcos por nodo')
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='upper right'); ax.set_ylim(0, 11); ax2.set_ylim(0, 21)
guardar(fig, 'fig_feromona')

# Figura nueva: sensibilidad de ACO (alfa x beta)
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.2))
A_, B_ = (.5, 1., 2.), (0., 1., 2., 5.)
for ax, campo, titulo, fmt in ((axs[0], 'exitos', 'Corridas con Z* en 2,000 evaluaciones (de 270)', '{:.0f}'),
                               (axs[1], 'mediana', 'Mediana de evaluaciones hasta Z*', '{:g}')):
    M = np.array([[C['aco_alfa_beta'][f'{a}|{b}'][campo] or np.nan for b in B_] for a in A_], dtype=float)
    vis = M / 270 if campo == 'exitos' else np.log10(M)
    ax.imshow(vis, cmap='Blues' if campo == 'exitos' else 'Oranges_r', aspect='auto')
    for i in range(3):
        for j in range(4):
            v = M[i, j]
            ax.text(j, i, '—' if np.isnan(v) else fmt.format(v), ha='center', va='center', fontsize=8.5,
                    color='white' if (campo == 'exitos' and v > 200) or (campo == 'mediana' and v < 30) else 'black',
                    fontweight='bold' if (A_[i], B_[j]) == (1., 2.) else 'normal')
    ax.set_xticks(range(4), [f'β = {b:g}' for b in B_]); ax.set_yticks(range(3), [f'α = {a:g}' for a in A_])
    ax.set_title(titulo)
    for s in ('left', 'bottom'):
        ax.spines[s].set_visible(False)
guardar(fig, 'fig_sensibilidad_aco')

# Figura nueva: sensibilidad del GA (pm x población) con intervalos de Wilson
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.3))
ax = axs[0]
pms = (0., .1, .2, .4, .6, .8, 1.)
for pop, col, mk in ((10, '#8FB3CF', 's'), (20, GA, 'o'), (40, '#0B2E45', '^')):
    ks = [C['ga_tabla'][f'{pm}|{pop}|0.9'] for pm in pms]
    y = [k['exitos'] / k['n'] for k in ks]
    lo = [y_ - k['ic'][0] for y_, k in zip(y, ks)]; hi = [k['ic'][1] - y_ for y_, k in zip(y, ks)]
    ax.errorbar(pms, y, yerr=[lo, hi], color=col, marker=mk, ms=4, capsize=2, lw=1.2, label=f'Población {pop}')
ax.set_xlabel('Probabilidad de mutación pm'); ax.set_ylabel('Fracción de corridas con Z*')
ax.set_title('CVRP_10, 100 semillas (300–399), 2,000 evaluaciones'); ax.set_ylim(0, 1.05); ax.legend(loc='lower right')
ax = axs[1]
inst = ['CVRP_10', 'E10-a', 'E10-b', 'E10-c', 'E10-d', 'E10-e']
for pm, col in ((.1, '#C9D9E6'), (.2, '#8FB3CF'), (.4, GA), (.6, '#0B2E45')):
    ys = []
    for k in inst:
        if k == 'CVRP_10':
            t = C['ga_tabla'][f'{pm}|20|0.9']; ys.append(t['exitos'] / t['n'])
        else:
            t = C['instancias'][f'{k}|ga|{json.dumps({"pm": pm})}']; ys.append(t['exitos'] / t['n'])
    off = {.1: -.3, .2: -.1, .4: .1, .6: .3}[pm]
    ax.bar(np.arange(len(inst)) + off, ys, width=.19, color=col, label=f'GA pm = {pm:g}')
ys = [1.0 if k == 'CVRP_10' else C['instancias'][f'{k}|aco|{{}}']['exitos'] / 30 for k in inst]
ax.scatter(np.arange(len(inst)), ys, marker='D', color=ACO, zorder=3, s=22, label='ACO (configuración principal)')
ax.set_xticks(range(len(inst)), inst); ax.set_ylabel('Fracción de corridas con Z*'); ax.set_ylim(0, 1.12)
ax.set_title('Instancias de 10 clientes con óptimo certificado'); ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7.5)
guardar(fig, 'fig_sensibilidad_ga')

# Figura 4 (sin cambios de datos): distancia y tiempo medios reportados el 20 de octubre
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.3))
met = ['Exacto', 'CW+2opt', 'GA', 'ACO']; dist = [318.989487, 339.252870, 321.958694, 318.989487]
tms = [2162.488, 0.116, 29.555, 59.324]; cols = ['#555555', '#999999', GA, ACO]
axs[0].bar(met, dist, color=cols); axs[0].axhline(Z_OPT, color='black', ls='--', lw=.8)
for i, v in enumerate(dist):
    axs[0].text(i, v + 4, f'{v:.3f}', ha='center', fontsize=8)
axs[0].set_ylabel('Distancia media'); axs[0].set_ylim(0, 370)
axs[1].bar(met, tms, color=cols); axs[1].set_yscale('log')
for i, v in enumerate(tms):
    axs[1].text(i, v * 1.25, f'{v:g}', ha='center', fontsize=8)
axs[1].set_ylabel('Tiempo medio (ms; escala logarítmica)'); axs[1].set_ylim(.05, 8000)
guardar(fig, 'fig4_distancia_tiempo')
print('figuras listas')
