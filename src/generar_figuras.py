"""Regenera las figuras del informe a partir de un directorio de resultados.

Uso: python src/generar_figuras.py [results] [--salida figures]

- rutas_exactas.png, rutas_heuristica.png, rutas_tres.png: se trazan desde resultados.json.
- comparacion_<M>.png: distancia y tiempo medio, desde resultados.json (barras con los valores medidos).
- diagrama_variables[_A].png: diagrama explicativo del modelo; los numeros del ejemplo
  (ruta 1-3-2-6-1, carga inicial 44) salen de la solucion exacta documentada. El modelo B excluye las
  subrutas con el balance de producto (demandas positivas); el modelo A las prohibe con las restricciones (8).
- El modelo M (A o B) se toma de resultados.json (esquema 2) o es A en la evidencia historica;
  se puede forzar con --modelo. Nombres: B -> comparacion_B.png y diagrama_variables.png;
  A -> comparacion_A.png y diagrama_variables_A.png (las figuras historicas versionadas estan en figures/historicas/).
No se inventa ningun dato: cada barra y cada ruta proviene del JSON indicado.
"""
import argparse, json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from resolver_cvrp_arcos import particion_optima, matriz, plot_routes


def comparacion(R, destino, modelo='A'):
    ze = sum(r['distancia'] for r in R['exacto']); zh = sum(r['distancia'] for r in R['heuristica'])
    fig, axs = plt.subplots(1, 2, figsize=(8, 3.6)); etiquetas = [f'Exacto {modelo}' if modelo == 'B' else 'Exacto', 'Heurística']
    for ax, vals, titulo, eje in [(axs[0], [ze, zh], 'Distancia total' if modelo == 'B' else 'Calidad de solución', 'Unidades de distancia' if modelo == 'B' else 'Distancia total'),
                                  (axs[1], [R['total_s']['media'] * 1000, R['heuristica_s']['media'] * 1000],
                                   'Tiempo medio · diez ejecuciones' if modelo == 'B' else '10 ejecuciones por método',
                                   'Milisegundos (escala logarítmica)' if modelo == 'B' else 'Tiempo medio (ms, escala logarítmica)')]:
        ax.bar(etiquetas, vals, color=['#356b8c', '#d78235']); ax.set(title=titulo, ylabel=eje)
        if ax is axs[1]: ax.set_yscale('log'); ax.set_ylim(.05 if modelo == 'B' else .1, max(vals) * 4)
        else: ax.set_ylim(0, 390)
        for j, v in enumerate(vals): ax.text(j, v * 1.08, f'{v:.3f}' if ax is axs[1] else f'{v:.2f}', ha='center', fontsize=9)
    fig.tight_layout(); fig.savefig(destino, dpi=200); plt.close(fig)


def diagrama(destino, modelo='A'):
    azul, verde = '#164769', '#16756f'
    fig, ax = plt.subplots(figsize=(11, 7)); ax.set(xlim=(0, 11), ylim=(0, 7)); ax.axis('off')
    def caja(x, y, w, h, texto, col=azul):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=.08', fc='white', ec=col, lw=1.4))
        ax.text(x + w / 2, y + h / 2, texto, ha='center', va='center', fontsize=11, color='#18313f')
    caja(.1, 5.5, 3.4, 1.15, 'RECORRIDO: xᵢⱼ\nElegir el arco i → j\nCosto: cᵢⱼ xᵢⱼ en la FO (1)')
    caja(3.8, 5.5, 3.4, 1.15, 'VISITA Y CONTINUIDAD\nUna llegada y una salida\nEcuaciones (2) y (3)')
    caja(7.5, 5.5, 3.4, 1.15, 'DEPÓSITO Y FLOTA\nm salidas = m regresos\n3 ≤ m ≤ 10; ecuación (4)')
    nodos = [(.65, '1\nDepósito'), (3.1, '3\nq₃ = 18'), (5.5, '2\nq₂ = 12'), (7.9, '6\nq₆ = 14'), (10.3, '1\nDepósito')]
    for x, t in nodos:
        dep = t.startswith('1\n')
        ax.scatter(x, 3.8, s=950, marker='s' if dep else 'o', color=azul if dep else verde, zorder=3)
        ax.text(x, 3.8, t.split('\n')[0], ha='center', va='center', color='white', fontsize=13, zorder=4)
        ax.text(x, 3.32, t.split('\n')[1], ha='center', va='center', color=azul, fontsize=11)
    etiquetas = ['x₁₃ = 1\nf₁₃ = 44', 'x₃₂ = 1\nf₃₂ = 26', 'x₂₆ = 1\nf₂₆ = 14', 'x₆₁ = 1\nf₆₁ = 0']
    for k, (a, b) in enumerate(zip(nodos, nodos[1:])):
        ax.annotate('', xy=(b[0] - .32, 3.8), xytext=(a[0] + .32, 3.8), arrowprops=dict(arrowstyle='-|>', lw=2, color=azul))
        ax.text((a[0] + b[0]) / 2, 4.3, etiquetas[k], ha='center', fontsize=10)
    caja(.1, .5, 3.4, 1.6, 'CARGA FÍSICA: fᵢⱼ\n0 ≤ fᵢⱼ ≤ 50 xᵢⱼ  (6)\n44 ≤ 50 al salir\nf₆₁ = 0 al regresar  (7)', verde)
    caja(3.8, .5, 3.4, 1.6, 'ENTREGA EN EL CLIENTE\nCarga entrante − saliente\n= demanda qᵢ  (5)\nNodo 3: 44 − 26 = 18', verde)
    if modelo == 'B':
        caja(7.5, .5, 3.4, 1.6, 'SIN CICLOS AISLADOS\nBalance (5) y enlace (6)\nUn ciclo aislado exigiría\n0 = suma de demandas > 0', verde)
    else:
        caja(7.5, .5, 3.4, 1.6, 'SIN CICLOS AISLADOS\nArcos internos ≤ |S| − 1  (8)\nS = {2,3,6}: 2 ≤ 2\nConexión con el depósito', verde)
    for a, b in [((1.8, 5.45), (1.9, 4.65)), ((5.5, 5.45), (5.5, 4.18)), ((9.2, 5.45), (10.3, 4.18)),
                 ((1.8, 2.2), (1.8, 3.5)), ((5.5, 2.2), (3.1, 3.02)), ((9.2, 2.2), (7.9, 3.02))]:
        ax.annotate('', xy=b, xytext=a, arrowprops=dict(arrowstyle='->', lw=1.2, color='#6e8291'))
    fig.savefig(destino, dpi=200, bbox_inches='tight'); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('resultados', nargs='?', default='results')
    ap.add_argument('--salida', default='figures')
    ap.add_argument('--modelo', choices=['A', 'B'], help='modelo del diagrama y de la comparacion (por defecto, el del JSON)')
    args = ap.parse_args()
    R = json.loads((Path(args.resultados) / 'resultados.json').read_text(encoding='utf8'))
    modelo = args.modelo or (R.get('modelo', 'A') if R.get('esquema') == 2 else 'A')
    if R.get('esquema') == 2:  # resultados de la medicion nueva: se adaptan a las claves historicas
        est = R['estadisticas']
        R['total_s'] = {'media': est['exacto_libre']['total_s']['media']}
        R['heuristica_s'] = {'media': est['heuristica_s']['media']}
        R['tres_rutas_certificado_dp'] = R['certificacion_dp']['tres_rutas']
    xy = {int(k): tuple(v) for k, v in R['xy'].items()}; dep = R['deposito']
    out = Path(args.salida); out.mkdir(parents=True, exist_ok=True)
    plot_routes(R['exacto'], xy, dep, out / 'rutas_exactas.png', 'Solución exacta · CVRP de 10 clientes')
    plot_routes(R['heuristica'], xy, dep, out / 'rutas_heuristica.png', 'Ahorros de Clarke–Wright + 2-opt')
    tres = R['tres_rutas']
    if 'tres_rutas_certificado_dp' not in R:
        # resultados.json historicos guardan el incumbente de CBC (361.0004), no el optimo:
        # se recalcula el optimo de tres rutas por particion en vez de dibujar un dato no optimo.
        q = {int(k): v for k, v in R['demanda'].items()}; d = matriz(xy)
        _, rutas = particion_optima(q, R['capacidad'], dep, d, k=3)
        tres = [{'ruta': r, 'carga': sum(q[i] for i in r), 'distancia': sum(d[a, b] for a, b in zip(r, r[1:]))} for r in rutas]
    plot_routes(tres, xy, dep, out / 'rutas_tres.png', 'Escenario de flota mínima · 3 rutas')
    comparacion(R, out / f'comparacion_{modelo}.png', modelo)
    diagrama(out / ('diagrama_variables.png' if modelo == 'B' else 'diagrama_variables_A.png'), modelo)
    print('Figuras escritas en', out)


if __name__ == '__main__':
    main()
