# Etapa 3: comparación de métodos en instancias de referencia

Cierre del reto CVRP. Los cuatro métodos del proyecto se aplican a **24 instancias de referencia** de CVRPLIB (CMT1–CMT14 y diez instancias X de 279 a 458 clientes):

- el **modelo matemático** de la Etapa 1 (modelo B de arcos y carga, PuLP + CBC);
- el **algoritmo propuesto**, Clarke–Wright + 2-opt (Etapa 1);
- el **algoritmo genético** y la **colonia de hormigas** de la Etapa 2.

Informe: [`docs/Etapa3_CVRP.pdf`](docs/Etapa3_CVRP.pdf) (fuente LaTeX en [`docs/latex/`](docs/latex/), versión editable en [`docs/Etapa3_CVRP.docx`](docs/Etapa3_CVRP.docx)).

## Resultado en breve

GAP medio contra la mejor solución conocida (BKS), 24 instancias, 5 corridas por caso, mismo presupuesto de 50,000 soluciones evaluadas para GA y ACO:

| Método | Configuración | GAP medio | Tiempo por corrida |
|---|---|---:|---:|
| Clarke–Wright + 2-opt | determinista | **7.10 %** | 1–91 ms |
| Colonia de hormigas | α = 1, β = 5, ρ = 0.1 | 12.41 % (9.37 % con 2-opt final) | 3.0 s |
| Algoritmo genético | OX de 1 punto, p_m = 0.2, torneo | 18.04 % (13.74 % con 2-opt final) | 0.9 s |

- Clarke–Wright + 2-opt es el mejor en 21 de 24 instancias.
- El modelo matemático prueba el óptimo hasta 30 clientes (subinstancias de CMT1, límite de 300 s). En ese rango, GA y ACO quedan a ~2 % del óptimo y Clarke–Wright a 4.7 %.
- Diseño factorial: GA con 2 × 3 × 2 = 12 combinaciones (puntos de cruce, probabilidad de mutación, selección); ACO con 2 × 2 × 2 = 8 (α, β, ρ). Pruebas de Friedman y Wilcoxon sobre las 24 instancias.

## Estructura

| Ruta | Contenido |
|---|---|
| `src/instancias.py` | Lectura de las instancias TSPLIB y valores BKS |
| `src/nucleo.py` | Split con capacidad y duración, operadores del GA, GA, ACO y 2-opt (Numba) |
| `src/algoritmos.py` | Clarke–Wright + 2-opt, interfaz del GA y del ACO, verificación de soluciones |
| `src/experimentos.py` | Diseño factorial y corrida final |
| `src/modelo_exacto.py` | Modelo B (importado de `../../src/resolver_cvrp_arcos.py`) en subinstancias de CMT1 |
| `src/analisis.py`, `src/figuras.py` | Estadística y figuras |
| `tests/test_etapa3.py` | Split contra fuerza bruta, validez de los cruces, factibilidad |
| `instancias/` | Las 24 instancias `.vrp` (CVRPLIB) |
| `resultados/` | `ga.jsonl`, `aco.jsonl`, `ga_aleatorio.jsonl`, `final.jsonl` (una línea por corrida), `cw.json`, `analisis.json`, `mejores_config.json`, `escalabilidad_modelo.json` |
| `figuras/` | Figuras del informe |
| `docs/` | Informe (PDF, DOCX, LaTeX) y `fuente/` con los scripts que generan el DOCX y el LaTeX a partir de los resultados |

## Reproducir

Requiere Python 3.10+ (probado con 3.13).

```bash
pip install -r requirements.txt
python -m pytest -q tests          # 3 pruebas, segundos
cd src
python experimentos.py cw          # Clarke-Wright + 2-opt
python experimentos.py ga          # 1,440 corridas (~15 min con 2 núcleos)
python experimentos.py ga_aleatorio
python experimentos.py aco         # 960 corridas (~30 min con 2 núcleos)
python analisis.py                 # elige las mejores configuraciones
python experimentos.py final       # 5 semillas nuevas con las mejores configuraciones
python modelo_exacto.py 300        # modelo B en subinstancias de CMT1
python figuras.py modelo
```

Las semillas son fijas, así que los costos se reproducen; los tiempos dependen del equipo (los del informe son de un Intel Xeon a 2.8 GHz, Linux, dos corridas en paralelo).

## Fuentes de las instancias y valores de referencia

- CMT1–CMT14: Christofides, Mingozzi y Toth (1979); BKS tomado del campo `COMMENT` de cada archivo.
- X-n280 a X-n459: Uchoa et al. (2017); BKS de Vidal (2022), tablas 5 y 6.
- Archivos obtenidos de CVRPLIB (http://vrp.galgos.inf.puc-rio.br).
