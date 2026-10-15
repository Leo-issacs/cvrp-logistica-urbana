# Metodología

Este documento resume el modelo, los métodos y los supuestos. El análisis completo, con la discusión del problema y la bibliografía, está en el [informe vigente](Reto_CVRP_revisado.docx).

## 1. Problema

CVRP estático, determinista, simétrico y con flota homogénea: un depósito (nodo 1), 10 clientes con demanda conocida, vehículos de capacidad `Q = 50`. Cada cliente se atiende una sola vez, sin entregas divididas ni recargas intermedias, y cada ruta parte y termina en el depósito. El archivo de la instancia no fija el tamaño de la flota, horarios ni costos monetarios; por eso el caso principal **minimiza solo la distancia** y deja que el modelo decida cuántas rutas usar.

## 2. Modelo exacto vigente: arcos binarios y carga física

![Diagrama de variables y restricciones](../figures/diagrama_variables.png)

Conjuntos: $V = \{1,\dots,11\}$, clientes $C = V \setminus \{1\}$, arcos $A = \{(i,j) : i \ne j\}$ (110 arcos).
Variables: $x_{ij} \in \{0,1\}$ (se recorre el arco $i \to j$) y $f_{ij} \ge 0$ (producto que el vehículo aún lleva al recorrer ese arco).

$$\min \sum_{(i,j)\in A} c_{ij}\,x_{ij} \tag{1}$$

| Ec. | Restricción | Significado |
|---|---|---|
| (2) | $\sum_{j} x_{ji} = 1,\ \forall i \in C$ | cada cliente recibe una visita |
| (3) | $\sum_{j} x_{ij} = \sum_{j} x_{ji},\ \forall i \in C$ | continuidad: lo que entra, sale |
| (4) | $\sum_{j\in C} x_{1j} = \sum_{i\in C} x_{i1} = m,\quad \lceil 146/50\rceil \le m \le 10$ | balance de rutas en el depósito |
| (5) | $\sum_{j} f_{ji} - \sum_{j} f_{ij} = q_i,\ \forall i \in C$ | balance de producto: se entrega la demanda $q_i$ |
| (6) | $0 \le f_{ij} \le Q\,x_{ij}$ | capacidad y carga solo en arcos usados |
| (7) | $f_{i1} = 0,\ \forall i \in C$ | regreso vacío; con $\sum_j f_{1j} = 146$ |
| (8) | $\sum_{i,j\in S,\,i\ne j} x_{ij} \le \lvert S\rvert-1,\ \forall S\subseteq C,\ \lvert S\rvert\ge 2$ | eliminación de subrutas |

Con 10 clientes las restricciones (8) se **enumeran completas**: $2^{10}-10-1 = 1\,013$. El modelo tiene 220 variables (110 binarias, 110 continuas) y 1 167 restricciones, y se resuelve con CBC (incluido en PuLP) con `gapRel = 0` y `gapAbs = 0`. Esta enumeración no escala a instancias grandes; ahí haría falta separar las desigualdades dinámicamente o usar otra formulación.

## 3. Heurística: ahorros de Clarke–Wright + 2-opt

1. Cada cliente empieza en su propia ruta.
2. Se calculan los ahorros $s_{ij} = c_{1i} + c_{1j} - c_{ij}$ y se fusionan rutas en orden decreciente de ahorro si $i$ y $j$ son extremos de rutas distintas y la carga combinada no supera `Q`.
3. Cada ruta resultante se mejora con 2-opt.

Es determinista y factible por construcción, pero **no** garantiza optimalidad.

## 4. Verificación independiente del óptimo

`certificar_dp` y `particion_optima` (en [`src/resolver_cvrp_arcos.py`](../src/resolver_cvrp_arcos.py)) enumeran todos los subconjuntos de clientes que caben en un vehículo, hallan la mejor ruta de cada uno por fuerza bruta y combinan una partición óptima por programación dinámica. No comparte código con el modelo de CBC, de modo que coincidir en 318.9894867 es una comprobación cruzada real. Se usa también para el escenario de tres rutas (véase [`coherencia.md`](coherencia.md)).

## 5. Métrica: GAP de costo

$$\text{GAP}_{\text{costo}}(\%) = 100\cdot\frac{Z_{\text{heur}} - Z^{*}}{Z^{*}} = 100\cdot\frac{339.252870 - 318.989487}{318.989487} \approx 6.35\,\%$$

Mide cuánto más largo es el recorrido de la heurística respecto del óptimo probado. **No** es una cota ni una brecha de optimalidad reportada por el solver. La diferencia temporal entre métodos es otra cantidad y no se mezcla con el GAP.

## 6. Protocolo de medición

- `time.perf_counter()`, una ejecución de calentamiento descartada y diez repeticiones por método.
- El tiempo **exacto** incluye construir el modelo (incluidas las 1 013 SEC), lanzar CBC, resolver y reconstruir rutas. El tiempo **heurístico** incluye ahorros, fusiones y 2-opt.
- No se cronometran la lectura del archivo, la matriz de distancias, la validación posterior ni las figuras.
- Ambos métodos son deterministas: las repeticiones miden variación temporal, no diversidad de soluciones.
- Los tiempos dependen del equipo, la carga del sistema y la versión de CBC. **No** son comparables con los del modelo anterior por partición de rutas (otra formulación, otra relajación).

## 7. Supuestos y limitaciones

- Una sola instancia didáctica de 10 clientes: los resultados no prueban superioridad general de ningún método.
- Sin unidades físicas, costos monetarios ni emisiones: el objetivo es distancia, no dinero ni CO₂.
- Rutas inversas y su numeración son equivalentes (el problema es simétrico); las figuras muestran una orientación representativa.
- La razón de tiempos (exacto/heurística) depende de esta formulación por arcos y no generaliza a otras formulaciones exactas.
- Los tiempos documentados provienen de una sola máquina (véase `entorno` en `results/resultados.json`).

## 8. Fuentes

La bibliografía completa (Clarke y Wright 1964, Gillett y Miller 1974, Prins 2004, Vidal 2022, Reinelt/TSPLIB y otras) está en la sección *Referencias* del [informe vigente](Reto_CVRP_revisado.docx). Atribuciones de material de terceros: [`../ATRIBUCIONES.md`](../ATRIBUCIONES.md).
