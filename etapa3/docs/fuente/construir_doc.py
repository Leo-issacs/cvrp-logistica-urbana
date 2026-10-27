"""Genera Etapa3_CVRP.md a partir de los resultados y lo convierte a .docx con pandoc."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'resultados').exists())   # carpeta etapa3/
sys.path.insert(0, str(ROOT / 'src'))
from instancias import todas, leer

R = ROOT / 'resultados'
FIG = ROOT / 'figuras'
A = json.load(open(R / 'analisis.json'))
CW = {f['inst']: f for f in json.load(open(R / 'cw.json'))}
FIN = [json.loads(l) for l in open(R / 'final.jsonl')]
ESC = json.load(open(R / 'escalabilidad_modelo.json'))
NOM = todas()
INST = {n: leer(n) for n in NOM}
gi, ai = A['inst_ga'], A['inst_aco']


def f2(x, d=2):
    return f'{x:,.{d}f}'


def media(xs):
    return float(np.mean(list(xs)))


def tabla(enc, filas, alinear=None):
    out = ['| ' + ' | '.join(enc) + ' |']
    al = alinear or ['---'] * len(enc)
    out.append('| ' + ' | '.join(al) + ' |')
    out += ['| ' + ' | '.join(str(c) for c in f) + ' |' for f in filas]
    return '\n'.join(out)


# ------------------------------------------------------------------ tablas
def t_instancias():
    filas = []
    for n in NOM:
        I = INST[n]
        filas.append([n, I.n, I.Q, f2(I.D, 0) if I.con_duracion else '—', f2(I.s, 0) if I.s else '—',
                      int(-(-I.q.sum() // I.Q)), f2(I.bks, 2) if I.familia == 'CMT' else f'{int(I.bks):,}'])
    return ('**Tabla 1.** Instancias. n = clientes; Q = capacidad; D = duración máxima de ruta; '
            's = tiempo de servicio; k_min = ⌈Σq/Q⌉ (mínimo de vehículos por capacidad).\n\n' +
            tabla(['Instancia', 'n', 'Q', 'D', 's', 'k_min', 'BKS'], filas, ['---'] + ['---:'] * 6))


def nombre_ga(c):
    return f"OX {c[0]} punto{'s' if c[0] == 2 else ''}, p_m = {c[1]}, {c[2]}"


def corto_ga(c):
    return f"{c[0]} pto · {c[1]} · {c[2]}"


def nombre_aco(c):
    return f'α = {c[0]:g}, β = {c[1]:g}, ρ = {c[2]:g}'


def t_factorial(alg):
    celdas = sorted(A[alg]['celdas'], key=lambda f: (f['rango'], f['gap']))
    nom = corto_ga if alg == 'ga' else nombre_aco
    filas = [[k + 1, nom(f['celda']), f2(f['gap']), f2(f['gap_2opt']), f2(f['rango']), f['gana'],
              f2(f['tiempo']), f2(f['it_mejor'], 0)] for k, f in enumerate(celdas)]
    unidad = 'generación' if alg == 'ga' else 'iteración'
    return tabla(['#', 'Configuración', 'GAP medio (%)', 'GAP con 2-opt (%)', 'Rango medio',
                  'Instancias donde es la mejor', 'Tiempo medio (s)', f'{unidad.capitalize()} de la mejor solución'],
                 filas, ['---:', '---'] + ['---:'] * 6)


def t_efectos(alg, etiquetas):
    filas = []
    for f, et in etiquetas.items():
        e = A[alg]['efectos'][f]
        for lv, v in e['niveles'].items():
            filas.append([et, lv.replace('.0', '') if alg == 'aco' else lv, f2(v['gap']), f2(v['rango']),
                          f2(v['tiempo']), f2(v['it_mejor'], 0)])
    unidad = 'Generación' if alg == 'ga' else 'Iteración'
    return tabla(['Factor', 'Nivel', 'GAP medio (%)', 'Rango medio', 'Tiempo medio (s)',
                  f'{unidad} de la mejor solución'], filas, ['---', '---'] + ['---:'] * 4)


def p_txt(p):
    return 'p < 0.001' if p < 0.001 else f'p = {p:.3f}'


def t_comparacion():
    filas = []
    for n in NOM:
        filas.append([n, INST[n].n, f2(CW[n]['gap']), f2(CW[n]['tiempo'] * 1000, 1),
                      f2(gi[n]['gap']), f2(gi[n]['gap_2opt']), f2(gi[n]['tiempo']), f2(gi[n]['it_mejor'], 0),
                      f2(ai[n]['gap']), f2(ai[n]['gap_2opt']), f2(ai[n]['tiempo']), f2(ai[n]['it_mejor'], 0)])
    filas.append(['**Promedio**', '', f"**{f2(media(CW[n]['gap'] for n in NOM))}**",
                  f2(media(CW[n]['tiempo'] * 1000 for n in NOM), 1),
                  f"**{f2(media(gi[n]['gap'] for n in NOM))}**", f2(media(gi[n]['gap_2opt'] for n in NOM)),
                  f2(media(gi[n]['tiempo'] for n in NOM)), f2(media(gi[n]['it_mejor'] for n in NOM), 0),
                  f"**{f2(media(ai[n]['gap'] for n in NOM))}**", f2(media(ai[n]['gap_2opt'] for n in NOM)),
                  f2(media(ai[n]['tiempo'] for n in NOM)), f2(media(ai[n]['it_mejor'] for n in NOM), 0)])
    return tabla(['Instancia', 'n', 'CW GAP (%)', 'CW tiempo (ms)', 'GA GAP (%)', 'GA +2-opt (%)', 'GA tiempo (s)',
                  'GA generación', 'ACO GAP (%)', 'ACO +2-opt (%)', 'ACO tiempo (s)', 'ACO iteración'],
                 filas, ['---', '---:'] + ['---:'] * 10)


def t_inicial():
    I0 = A['inicial']
    filas = [[n, INST[n].n, f2(I0[n]['aleatoria'], 1), f2(I0[n]['heuristica'], 1)] for n in NOM]
    filas.append(['**Promedio**', '', f"**{f2(media(I0[n]['aleatoria'] for n in NOM), 1)}**",
                  f"**{f2(media(I0[n]['heuristica'] for n in NOM), 1)}**"])
    return tabla(['Instancia', 'n', 'Población aleatoria (Etapa 2): GAP (%)', 'Población heurística: GAP (%)'],
                 filas, ['---', '---:', '---:', '---:'])


def final_resumen():
    out = {}
    for alg, cel, ref in (('ga_final', A['mejor_ga'], gi), ('aco_final', A['mejor_aco'], ai)):
        F = [r for r in FIN if r['alg'] == alg]
        por = {n: [r for r in F if r['inst'] == n] for n in NOM}
        out[alg] = {n: dict(gap=media(r['gap'] for r in por[n]), gap_2opt=media(r['gap_2opt'] for r in por[n]),
                            tiempo=media(r['tiempo'] for r in por[n]), it=media(r['it_mejor'] for r in por[n]),
                            gap_min=min(r['gap'] for r in por[n]), sd=float(np.std([r['gap'] for r in por[n]], ddof=1)))
                    for n in NOM}
    return out


FR = final_resumen()


def t_final():
    filas = []
    for n in NOM:
        g, a = FR['ga_final'][n], FR['aco_final'][n]
        mejor = min((CW[n]['gap'], 'CW'), (g['gap_2opt'], 'GA'), (a['gap_2opt'], 'ACO'))[1]
        filas.append([n, f2(CW[n]['gap']), f"{f2(g['gap'])} ± {f2(g['sd'])}", f2(g['gap_2opt']),
                      f"{f2(a['gap'])} ± {f2(a['sd'])}", f2(a['gap_2opt']), mejor])
    filas.append(['**Promedio**', f"**{f2(media(CW[n]['gap'] for n in NOM))}**",
                  f"**{f2(media(FR['ga_final'][n]['gap'] for n in NOM))}**",
                  f2(media(FR['ga_final'][n]['gap_2opt'] for n in NOM)),
                  f"**{f2(media(FR['aco_final'][n]['gap'] for n in NOM))}**",
                  f2(media(FR['aco_final'][n]['gap_2opt'] for n in NOM)), ''])
    return tabla(['Instancia', 'CW + 2-opt GAP (%)', 'GA GAP (%) ± d.e.', 'GA + 2-opt (%)',
                  'ACO GAP (%) ± d.e.', 'ACO + 2-opt (%)', 'Mejor (con 2-opt)'], filas,
                 ['---', '---:', '---:', '---:', '---:', '---:', '---'])


def t_escalabilidad():
    filas = []
    for e in ESC:
        ok = e['estado'] == 'optimo_probado'
        est = 'Óptimo probado' if ok else ('Factible, sin prueba' if e['estado'] == 'factible_sin_prueba' else 'Sin solución')
        ref = e['objetivo'] if ok else None
        g = (lambda z: f2(max(0.0, 100 * (z - ref) / ref))) if ref else (lambda z: '—')
        cota = e.get('cota')
        brecha = f2(100 * (e['objetivo'] - cota) / e['objetivo']) if (not ok and e['objetivo'] and cota) else ('0.00' if ok else '—')
        filas.append([e['k'], f"{e['variables']:,}", f"{e['restricciones']:,}", est,
                      f2(e['objetivo']) if e['objetivo'] else '—', brecha, f2(e['tiempo_modelo'], 1),
                      g(e['cw']), g(e['ga']), g(e['aco'])])
    return tabla(['Clientes', 'Variables', 'Restricciones', 'Estado de CBC', 'Distancia del modelo',
                  'Brecha de CBC (%)', 'Tiempo del modelo (s)', 'GAP CW (%)', 'GAP GA (%)', 'GAP ACO (%)'],
                 filas, ['---:', '---:', '---:', '---', '---:', '---:', '---:', '---:', '---:', '---:'])


# ------------------------------------------------------------------ cifras para el texto
mg, ma = A['mejor_ga'], A['mejor_aco']
cw_med = media(CW[n]['gap'] for n in NOM)
ga_med, aco_med = media(gi[n]['gap'] for n in NOM), media(ai[n]['gap'] for n in NOM)
ga2_med, aco2_med = media(gi[n]['gap_2opt'] for n in NOM), media(ai[n]['gap_2opt'] for n in NOM)
eg, ea = A['ga']['efectos'], A['aco']['efectos']
cmt = [n for n in NOM if n.startswith('CMT')]
xs = [n for n in NOM if n.startswith('X')]
cw_gana = sum(CW[n]['gap'] <= min(gi[n]['gap_2opt'], ai[n]['gap_2opt']) for n in NOM)
ga_gana = [n for n in NOM if gi[n]['gap_2opt'] < min(CW[n]['gap'], ai[n]['gap_2opt'])]
aco_gana = [n for n in NOM if ai[n]['gap_2opt'] < min(CW[n]['gap'], gi[n]['gap_2opt'])]
ini = A['inicial']
opt = [e for e in ESC if e['estado'] == 'optimo_probado']
k_max_opt = max(e['k'] for e in opt) if opt else None
no_opt = [e for e in ESC if e['estado'] != 'optimo_probado']
cmt1 = [e for e in ESC if e['k'] == 50][0]
fg, fa = FR['ga_final'], FR['aco_final']
fin_cw = sum(CW[n]['gap'] <= min(fg[n]['gap_2opt'], fa[n]['gap_2opt']) for n in NOM)
fin_aco = [n for n in NOM if fa[n]['gap_2opt'] < min(CW[n]['gap'], fg[n]['gap_2opt'])]
fin_ga = [n for n in NOM if fg[n]['gap_2opt'] < min(CW[n]['gap'], fa[n]['gap_2opt'])]

partes = {}
partes['TABLA_INSTANCIAS'] = t_instancias()
estatica = (Path(__file__).parent / 'parte_estatica.md').read_text()
for k, v in partes.items():
    estatica = estatica.replace('{' + k + '}', v)

pmp = eg['pm']['pares_wilcoxon']
md = f"""---
title: "Reto CVRP de logística urbana — Etapa 3"
subtitle: "Modelo matemático, Clarke–Wright + 2-opt, algoritmo genético y colonia de hormigas en 24 instancias de referencia"
lang: es-MX
---

**Diseño de algoritmos matemáticos bioinspirados (MA2015), Gpo. 201**
Profesor: Fernando Elizalde

## Resumen

Se resolvieron 24 instancias de referencia del CVRP (CMT1–CMT14 y diez instancias X de 279 a 458 clientes) con el modelo matemático de la Etapa 1, la heurística propuesta (Clarke–Wright + 2-opt) y los algoritmos genético y de colonia de hormigas de la Etapa 2, con 5 corridas por caso. Contra la mejor solución conocida (BKS), el GAP medio fue de **{f2(cw_med)} %** para Clarke–Wright + 2-opt, **{f2(aco_med)} %** para la colonia de hormigas y **{f2(ga_med)} %** para el algoritmo genético, en sus mejores configuraciones. En el GA la mejor combinación fue **{nombre_ga(mg)}**; en la colonia de hormigas, **{nombre_aco(ma)}**. Clarke–Wright + 2-opt fue el mejor método en {cw_gana} de las 24 instancias y el más rápido: tarda milisegundos, contra segundos de los metaheurísticos. El modelo matemático probó el óptimo solo hasta {k_max_opt} clientes con un límite de 300 s.

{estatica}

## 5. Resultados del algoritmo genético

### 5.1 Las 12 combinaciones

La tabla 2 ordena las combinaciones por rango medio (1 = la mejor en todas las instancias). Las diferencias entre combinaciones son significativas (Friedman, {p_txt(A['ga']['friedman_p'])}).

**Tabla 2.** Algoritmo genético: promedio sobre las 24 instancias (5 corridas por instancia).

{t_factorial('ga')}

### 5.2 Efecto de cada hiperparámetro

![Efectos principales del GA: GAP medio (arriba) y tiempo medio (abajo) por nivel. El valor p es el de la prueba sobre las 24 instancias.]({FIG}/efectos_ga.png){{width=95%}}

**Tabla 3.** Algoritmo genético: promedio por nivel de cada factor (cada nivel promedia todas las combinaciones que lo contienen).

{t_efectos('ga', dict(puntos='Puntos de cruce', pm='Prob. de mutación', seleccion='Selección'))}

- **Selección.** El torneo binario es mejor que la ruleta en las 24 instancias (GAP medio {f2(eg['seleccion']['niveles']['torneo']['gap'])} % contra {f2(eg['seleccion']['niveles']['ruleta']['gap'])} %; Wilcoxon, {p_txt(eg['seleccion']['p'])}). Con aptitud 1/costo, todas las soluciones de la población tienen costos parecidos, así que la ruleta reparte casi la misma probabilidad a todas y la presión de selección es muy baja. El torneo solo compara dos individuos, sin importar cuánto difieren sus costos. La ruleta también encuentra su mejor solución antes (generación {f2(eg['seleccion']['niveles']['ruleta']['it_mejor'], 0)} contra {f2(eg['seleccion']['niveles']['torneo']['it_mejor'], 0)}), pero es porque se estanca, no porque converja mejor.
- **Puntos de cruce.** El OX de un punto es mejor que el de dos puntos en las 24 instancias (GAP medio {f2(eg['puntos']['niveles']['1']['gap'])} % contra {f2(eg['puntos']['niveles']['2']['gap'])} %; Wilcoxon, {p_txt(eg['puntos']['p'])}). El OX de un punto hereda un prefijo completo del primer padre, incluida su conexión con el depósito, y el resto en el orden relativo del segundo, así que conserva bloques largos de rutas ya formadas. El de dos puntos rota el relleno de forma circular y corta más adyacencias. También es un poco más rápido ({f2(eg['puntos']['niveles']['1']['tiempo'])} s contra {f2(eg['puntos']['niveles']['2']['tiempo'])} s).
- **Probabilidad de mutación.** El efecto es pequeño y depende del cruce. En promedio, p_m = 0.1 y p_m = 0.2 empatan ({f2(eg['pm']['niveles']['0.1']['gap'])} % y {f2(eg['pm']['niveles']['0.2']['gap'])} %; Wilcoxon, {p_txt(pmp['0.1 vs 0.2'])}) y ambas son mejores que 0.4 ({f2(eg['pm']['niveles']['0.4']['gap'])} %; {p_txt(pmp['0.1 vs 0.4'])} y {p_txt(pmp['0.2 vs 0.4'])}). El mejor nivel cambia según el cruce: con OX de un punto y torneo, 0.2 y 0.4 empatan como los mejores, y con OX de dos puntos y torneo el mejor es 0.1. Un cruce que ya rompe muchas adyacencias necesita menos mutación.
- **Número de iteraciones.** La mejor combinación encuentra su mejor solución, en promedio, en la generación {f2(A['inst_ga'] and media(gi[n]['it_mejor'] for n in NOM), 0)} de 1,000. El GA seguía mejorando al terminar: con más generaciones bajaría más el GAP, y el presupuesto, más que los hiperparámetros, es lo que lo limita.

**Mejor nivel de cada hiperparámetro:** **OX de un punto, p_m = 0.2 y torneo binario**. Es la combinación con mejor rango medio y la mejor en {[f for f in A['ga']['celdas'] if f['celda'] == mg][0]['gana']} de las 24 instancias. Empata en rango con p_m = 0.4, pero tiene menor GAP medio y menor tiempo.

### 5.3 Población inicial: aleatoria (Etapa 2) contra heurística

**Tabla 4.** GA con la configuración de la Etapa 2 (OX de dos puntos, p_m = 0.2, torneo), con población aleatoria y con población heurística. GAP medio de 5 corridas.

{t_inicial()}

Con población aleatoria el GAP medio es de {f2(media(ini[n]['aleatoria'] for n in NOM), 1)} %, y supera 100 % en {sum(ini[n]['aleatoria'] > 100 for n in NOM)} instancias; con la población heurística baja a {f2(media(ini[n]['heuristica'] for n in NOM), 1)} %. El GA sí aporta sobre su punto de partida: en la mejor configuración, la mejor solución de la población inicial está a {f2(A['ga_mejora_inicial']['gap_poblacion_inicial'])} % del BKS y la final a {f2(A['ga_mejora_inicial']['gap_final'])} %.

## 6. Resultados de la colonia de hormigas

### 6.1 Las 8 combinaciones

Las diferencias entre combinaciones son significativas (Friedman, {p_txt(A['aco']['friedman_p'])}).

**Tabla 5.** Colonia de hormigas: promedio sobre las 24 instancias (5 corridas por instancia).

{t_factorial('aco')}

### 6.2 Efecto de cada hiperparámetro

![Efectos principales del ACO: GAP medio (arriba) y tiempo medio (abajo) por nivel.]({FIG}/efectos_aco.png){{width=95%}}

**Tabla 6.** Colonia de hormigas: promedio por nivel de cada factor.

{t_efectos('aco', dict(alfa='α', beta='β', rho='ρ'))}

- **α (peso de la feromona).** α = 1 es mejor que α = 2 en las 24 instancias (GAP medio {f2(ea['alfa']['niveles']['1.0']['gap'])} % contra {f2(ea['alfa']['niveles']['2.0']['gap'])} %; Wilcoxon, {p_txt(ea['alfa']['p'])}). Con α = 2 las diferencias de feromona se elevan al cuadrado, la colonia sigue casi siempre los mismos arcos y se estanca: encuentra su mejor solución en la iteración {f2(ea['alfa']['niveles']['2.0']['it_mejor'], 0)} en promedio, contra {f2(ea['alfa']['niveles']['1.0']['it_mejor'], 0)} con α = 1. Además tarda {f2(ea['alfa']['niveles']['2.0']['tiempo'] / ea['alfa']['niveles']['1.0']['tiempo'], 1)} veces más, porque cada transición calcula una potencia en vez de usar τ directamente.
- **ρ (evaporación).** ρ = 0.1 es mejor que ρ = 0.5 en las 24 instancias ({f2(ea['rho']['niveles']['0.1']['gap'])} % contra {f2(ea['rho']['niveles']['0.5']['gap'])} %; Wilcoxon, {p_txt(ea['rho']['p'])}). Con ρ = 0.5 la feromona se olvida en pocas iteraciones, la información se concentra en las últimas soluciones y la búsqueda converge antes (iteración {f2(ea['rho']['niveles']['0.5']['it_mejor'], 0)} contra {f2(ea['rho']['niveles']['0.1']['it_mejor'], 0)}).
- **β (peso de la distancia).** En promedio no hay diferencia significativa ({f2(ea['beta']['niveles']['2.0']['gap'])} % con β = 2 y {f2(ea['beta']['niveles']['5.0']['gap'])} % con β = 5; Wilcoxon, {p_txt(ea['beta']['p'])}). El efecto depende de los otros dos: β = 5 solo es mejor en la combinación α = 1, ρ = 0.1, que resulta la mejor de todas; en las otras tres combinaciones de α y ρ, β = 2 es ligeramente mejor. Una evaporación lenta mantiene la diversidad que una regla más voraz (β alto) reduciría.

**Mejor nivel de cada hiperparámetro:** **α = 1, β = 5 y ρ = 0.1**. Es la combinación con mejor rango medio ({f2([f for f in A['aco']['celdas'] if f['celda'] == ma][0]['rango'])}), la mejor en {[f for f in A['aco']['celdas'] if f['celda'] == ma][0]['gana']} instancias y la de menor GAP medio ({f2(aco_med)} %), con un tiempo intermedio. La colonia sí aprende: la mejor solución de la primera iteración está a {f2(A['aco_mejora_inicial']['gap_primera_iteracion'])} % del BKS y la final a {f2(A['aco_mejora_inicial']['gap_final'])} %.

## 7. Comparación de los tres algoritmos

La tabla 7 compara, instancia por instancia, Clarke–Wright + 2-opt con la mejor configuración del GA y del ACO. GA y ACO son promedios de 5 corridas.

**Tabla 7.** GAP contra el BKS, tiempo y número de iteraciones por instancia.

{t_comparacion()}

![GAP de cada método por instancia (las instancias X están debajo de la línea punteada).]({FIG}/comparacion_gap.png){{width=85%}}

**Calidad de la solución.** Clarke–Wright + 2-opt tiene el menor GAP medio ({f2(cw_med)} %), seguido del ACO ({f2(aco_med)} %; {f2(aco2_med)} % con 2-opt) y del GA ({f2(ga_med)} %; {f2(ga2_med)} % con 2-opt). Aun con el mismo 2-opt aplicado a sus soluciones, CW es el mejor en {cw_gana} instancias; el GA gana en {len(ga_gana)} ({', '.join(ga_gana) or 'ninguna'}) y el ACO en {len(aco_gana)} ({', '.join(aco_gana) or 'ninguna'}). La ventaja de CW crece con el tamaño: en las instancias X su GAP medio es {f2(media(CW[n]['gap'] for n in xs))} %, contra {f2(media(ai[n]['gap'] for n in xs))} % del ACO y {f2(media(gi[n]['gap'] for n in xs))} % del GA. Las instancias agrupadas (CMT11–CMT14) son las más fáciles para todos.

**Tiempo de cómputo.** CW + 2-opt tarda de {f2(min(CW[n]['tiempo'] for n in NOM) * 1000, 1)} a {f2(max(CW[n]['tiempo'] for n in NOM) * 1000, 1)} ms por instancia. El GA tarda {f2(media(gi[n]['tiempo'] for n in NOM))} s en promedio y el ACO {f2(media(ai[n]['tiempo'] for n in NOM))} s, con el mismo número de soluciones evaluadas: construir una solución con hormigas cuesta más que cruzar dos permutaciones.

![Tiempo por corrida contra número de clientes.]({FIG}/tiempos.png){{width=80%}}

**Número de iteraciones.** El GA encuentra su mejor solución cerca del final (generación {f2(media(gi[n]['it_mejor'] for n in NOM), 0)} de 1,000 en promedio) y el ACO a la mitad (iteración {f2(media(ai[n]['it_mejor'] for n in NOM), 0)} de 2,000). En la figura de convergencia, el GA sigue bajando al terminar, mientras que la colonia se aplana: el GA está limitado por el presupuesto y el ACO por su propia convergencia. CW no itera: construye su solución en una sola pasada.

![Convergencia media (5 corridas) de la mejor y la peor configuración de cada algoritmo, en CMT5 y X-n459-k26. La línea discontinua es Clarke–Wright + 2-opt.]({FIG}/convergencia.png){{width=95%}}

## 8. Comparación con el modelo matemático

El modelo matemático da el óptimo, pero no escala. Se resolvió con CBC (límite de 300 s por corrida) en subinstancias de CMT1 con el depósito y los primeros k clientes, y en CMT1 completa. En cada subinstancia se corrieron también CW + 2-opt y la mejor configuración del GA y del ACO (5 corridas). El GAP de esta tabla se mide contra el **óptimo probado por el modelo**, no contra el BKS.

**Tabla 8.** Escalabilidad del modelo y GAP de los algoritmos contra el óptimo.

{t_escalabilidad()}

![Tiempo de CBC contra número de clientes.]({FIG}/escalabilidad_modelo.png){{width=80%}}

{{TEXTO_MODELO}}

## 9. Corrida final con los mejores hiperparámetros

Para confirmar la elección se corrieron de nuevo el GA ({nombre_ga(mg)}) y el ACO ({nombre_aco(ma)}) en las 24 instancias con 5 semillas nuevas (5 a 9), que no se usaron para elegir los hiperparámetros.

**Tabla 9.** Corrida final: GAP medio de 5 corridas nuevas.

{t_final()}

Con las semillas nuevas, el GAP medio fue de {f2(media(fg[n]['gap'] for n in NOM))} % en el GA y {f2(media(fa[n]['gap'] for n in NOM))} % en el ACO, frente a {f2(ga_med)} % y {f2(aco_med)} % en el experimento factorial. La diferencia es menor a {f2(max(abs(media(fg[n]['gap'] for n in NOM) - ga_med), abs(media(fa[n]['gap'] for n in NOM) - aco_med)) + 0.005)} puntos, así que la elección no dependió de las semillas. La desviación estándar entre corridas es de {f2(media(fg[n]['sd'] for n in NOM))} puntos en el GA y {f2(media(fa[n]['sd'] for n in NOM))} en el ACO: la colonia es más estable. Con las semillas nuevas, CW + 2-opt sigue siendo el mejor método en {fin_cw} de 24 instancias; el ACO con 2-opt lo supera en {', '.join(fin_aco)}. Son instancias de 50 a 150 clientes donde la diferencia entre métodos es menor a 4 puntos y depende de la semilla: en la tabla 7, con las semillas 0–4, CW ganaba en CMT4 y el GA en CMT1 y CMT6.

## 10. ¿Qué algoritmo tiene los mejores resultados?

**Clarke–Wright + 2-opt, el algoritmo propuesto en la Etapa 1.** Tiene el menor GAP medio ({f2(cw_med)} %), es el mejor en {cw_gana} de 24 instancias aun cuando a GA y ACO se les aplica el mismo 2-opt, es determinista y tarda milisegundos. Entre los bioinspirados, **la colonia de hormigas es mejor que el GA**: menor GAP ({f2(aco_med)} % contra {f2(ga_med)} %), menos variación entre corridas y mejor escalamiento a las instancias X. El GA solo le gana a los otros dos en instancias pequeñas ({', '.join(ga_gana) or '—'}).

Este resultado depende del diseño, no solo del algoritmo. GA y ACO se usan aquí como se diseñaron en la Etapa 2, sin búsqueda local durante la evolución, y con 50,000 evaluaciones. Los métodos que alcanzan el BKS en estas instancias, como la búsqueda genética híbrida de Vidal (2022), combinan el GA con Split y búsqueda local intensiva. El siguiente paso natural sería aplicar 2-opt y movimientos entre rutas dentro del ciclo del GA o del ACO, no solo al final.

## 11. Conclusiones

1. **El modelo matemático solo es práctico en instancias pequeñas.** Probó el óptimo hasta {k_max_opt} clientes; en CMT1 completa (50 clientes) {('terminó con una brecha de ' + f2(100 * (cmt1['objetivo'] - cmt1['cota']) / cmt1['objetivo']) + ' % en 300 s') if (cmt1['objetivo'] and cmt1.get('cota')) else 'no llegó a una solución útil en 300 s'}. Para las instancias X, con hasta 458 clientes y unas 210,000 variables binarias, no es aplicable. Donde sí prueba el óptimo, sirve para medir el GAP real de las heurísticas.
2. **El mejor algoritmo es Clarke–Wright + 2-opt**, con un GAP medio de {f2(cw_med)} % contra el BKS y tiempos de milisegundos.
3. **En el GA, los mejores niveles son OX de un punto, p_m = 0.2 y torneo binario.** La selección es el factor con más efecto; la ruleta con aptitud 1/costo casi no discrimina. La mutación tiene efecto pequeño y depende del cruce.
4. **En el ACO, los mejores niveles son α = 1, β = 5 y ρ = 0.1.** α = 2 y ρ = 0.5 aceleran la convergencia pero la vuelven prematura; β no tiene efecto significativo por sí solo.
5. **La población inicial importa más que cualquier hiperparámetro del GA.** Pasar de población aleatoria a heurística bajó el GAP medio de {f2(media(ini[n]['aleatoria'] for n in NOM), 1)} % a {f2(media(ini[n]['heuristica'] for n in NOM), 1)} %.
6. **Limitaciones.** Hubo 5 corridas por caso, un solo presupuesto de evaluaciones y un solo equipo. El GA no había convergido al terminar, así que con más tiempo su GAP bajaría. El modelo exacto no incluye la restricción de duración, por eso el estudio de escalabilidad usa CMT1.

## Referencias

- Bullnheimer, B., Hartl, R. F., & Strauss, C. (1999). An improved ant system algorithm for the vehicle routing problem. *Annals of Operations Research, 89*, 319–328. https://doi.org/10.1023/A:1018940026670
- Christofides, N., Mingozzi, A., & Toth, P. (1979). The vehicle routing problem. En N. Christofides, A. Mingozzi, P. Toth, & C. Sandi (Eds.), *Combinatorial optimization* (pp. 315–338). Wiley.
- Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot to a number of delivery points. *Operations Research, 12*(4), 568–581. https://doi.org/10.1287/opre.12.4.568
- Derrac, J., García, S., Molina, D., & Herrera, F. (2011). A practical tutorial on the use of nonparametric statistical tests as a methodology for comparing evolutionary and swarm intelligence algorithms. *Swarm and Evolutionary Computation, 1*(1), 3–18. https://doi.org/10.1016/j.swevo.2011.02.002
- Dorigo, M., Maniezzo, V., & Colorni, A. (1996). Ant system: Optimization by a colony of cooperating agents. *IEEE Transactions on Systems, Man, and Cybernetics, Part B, 26*(1), 29–41. https://doi.org/10.1109/3477.484436
- Dorigo, M., & Stützle, T. (2004). *Ant colony optimization*. MIT Press.
- Goldberg, D. E. (1989). *Genetic algorithms in search, optimization, and machine learning*. Addison-Wesley.
- Prins, C. (2004). A simple and effective evolutionary algorithm for the vehicle routing problem. *Computers & Operations Research, 31*(12), 1985–2002. https://doi.org/10.1016/S0305-0548(03)00158-8
- Toth, P., & Vigo, D. (Eds.). (2014). *Vehicle routing: Problems, methods, and applications* (2nd ed.). SIAM.
- Uchoa, E., Pecin, D., Pessoa, A., Poggi, M., Vidal, T., & Subramanian, A. (2017). New benchmark instances for the capacitated vehicle routing problem. *European Journal of Operational Research, 257*(3), 845–858. https://doi.org/10.1016/j.ejor.2016.08.012
- Vidal, T. (2022). Hybrid genetic search for the CVRP: Open-source implementation and SWAP* neighborhood. *Computers & Operations Research, 140*, 105643. https://doi.org/10.1016/j.cor.2021.105643

## Anexo A. Reproducibilidad

El código, las instancias, los resultados de cada corrida y las figuras de esta etapa están en el repositorio del equipo, <https://github.com/Leo-issacs/cvrp-logistica-urbana>, en la carpeta `etapa3/`. El modelo matemático se importa del código de la Etapa 1 (`src/resolver_cvrp_arcos.py`), en la raíz del mismo repositorio.

| Archivo en `etapa3/` | Contenido |
|---|---|
| `src/instancias.py` | Lectura de las instancias TSPLIB y valores BKS |
| `src/nucleo.py` | Split con capacidad y duración, operadores del GA, GA, ACO y 2-opt (compilados con Numba) |
| `src/algoritmos.py` | Clarke–Wright + 2-opt, interfaz del GA y del ACO, verificación de soluciones |
| `src/experimentos.py` | Diseño factorial y corrida final |
| `src/modelo_exacto.py` | Modelo B con CBC en subinstancias de CMT1 |
| `src/analisis.py`, `src/figuras.py` | Estadística (Friedman, Wilcoxon) y figuras |
| `tests/test_etapa3.py` | Split contra fuerza bruta (con duración), validez de los cruces y factibilidad |
| `resultados/` | Una línea por corrida (`*.jsonl`): configuración, semilla, costo, GAP, tiempo e iteración; resúmenes en `analisis.json` |

Para reproducir, desde `etapa3/src`: `python experimentos.py cw`, `python experimentos.py ga`, `python experimentos.py ga_aleatorio`, `python experimentos.py aco`, `python analisis.py`, `python experimentos.py final`, `python modelo_exacto.py 300` y `python figuras.py modelo`. Las corridas usan semillas fijas; los tiempos dependen del equipo.
"""
def texto_modelo():
    g = lambda e, a: 100 * (e[a] - e['objetivo']) / e['objetivo']
    medias = {a: media(g(e, a) for e in opt) for a in ('cw', 'ga', 'aco')}
    exactos = {a: sum(abs(e[a + '_min'] - e['objetivo']) < 1e-6 for e in opt) for a in ('ga', 'aco')}
    t_opt = [e for e in opt]
    primero_lento = max(t_opt, key=lambda e: e['tiempo_modelo'])
    txt = (f"**Hasta dónde escala.** CBC probó el óptimo en todas las subinstancias de hasta {k_max_opt} clientes. "
           f"El tiempo creció de {f2(opt[0]['tiempo_modelo'], 2)} s con {opt[0]['k']} clientes a {f2(primero_lento['tiempo_modelo'], 1)} s "
           f"con {primero_lento['k']}; no crece de forma monótona porque depende de qué tan rápido la ramificación y acotamiento cierra la brecha. ")
    for e in no_opt:
        if e['objetivo'] and e['cota']:
            comp = 'mejor' if e['objetivo'] < e['cw'] else 'peor'
            txt += (f"Con {e['k']} clientes se detuvo a los 300 s con una solución de {f2(e['objetivo'])} ({comp} que la de CW, {f2(e['cw'])}) "
                    f"y una cota inferior de {f2(e['cota'])}: brecha de {f2(100 * (e['objetivo'] - e['cota']) / e['objetivo'])} %. ")
        else:
            txt += f"Con {e['k']} clientes no encontró una solución entera en 300 s. "
    txt += (f"El número de variables crece con el cuadrado de n: una instancia X de 458 clientes tendría unas 420,000 variables, "
            f"la mitad binarias, así que el modelo no es aplicable en ese tamaño.\n\n")
    txt += (f"**GAP contra el óptimo.** En las {len(opt)} subinstancias con óptimo probado, el GAP medio fue de "
            f"{f2(medias['cw'])} % para CW + 2-opt, {f2(medias['ga'])} % para el GA y {f2(medias['aco'])} % para el ACO "
            f"(promedios de 5 corridas). En estos tamaños pequeños el orden se invierte respecto de las instancias grandes: "
            f"los dos metaheurísticos superan a CW, y la mejor de sus 5 corridas alcanzó el óptimo en {exactos['ga']} subinstancias (GA) y "
            f"{exactos['aco']} (ACO). Con pocos clientes, 50,000 evaluaciones bastan para explorar bien el espacio; con cientos, no.")
    if cmt1['objetivo'] and cmt1['cota']:
        txt += (f"\n\nEn CMT1 completa, la solución que CBC tenía a los 300 s ({f2(cmt1['objetivo'])}) fue mejor que la de CW ({f2(cmt1['cw'])}), "
                f"el GA ({f2(cmt1['ga'])}) y el ACO ({f2(cmt1['aco'])}), pero sigue {f2(100 * (cmt1['objetivo'] - INST['CMT1'].bks) / INST['CMT1'].bks)} % arriba del BKS (524.61) "
                f"y no trae garantía de optimalidad. Con 40 clientes pasó lo contrario: la solución del solver fue peor que la de CW. "
                f"Detenido por tiempo, el modelo es una heurística más, sin certeza de su calidad.")
    return txt


md = md.replace('{TEXTO_MODELO}', texto_modelo())
(Path(__file__).parent / 'Etapa3_CVRP.md').write_text(md)
print('md ok')
