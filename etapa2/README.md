# Etapa 2 corregida: GA y ACO para el CVRP

Esta carpeta contiene la versión corregida del Entregable 2 y todo lo necesario para reproducirla.

## Contenido

| Carpeta / archivo | Qué es |
|---|---|
| `latex/main.tex` | Informe completo corregido (mismo preámbulo que la etapa 1). Compilar con `pdflatex main.tex` dos veces. |
| `latex/portada_etapa2.pdf` | Portada original del entregable. |
| `latex/tablas/*.tex` | Tablas nuevas, generadas automáticamente por `src/tablas_latex.py`. |
| `latex/figuras/*.pdf` | Figuras del informe (generadas por `src/figuras_etapa2.py`). |
| `src/algoritmos.py` | Código del Anexo A **sin cambios de lógica** (sólo se normalizó la sangría al copiarlo del PDF). |
| `src/instrumentado.py` | Copias de `ga` y `aco` que registran diversidad, feromona y la primera evaluación con el óptimo. Usan las mismas llamadas a `random.Random`, por lo que reproducen exactamente las Tablas 7 y 9. |
| `src/*.py` | Análisis nuevos (ver orden de ejecución abajo). |
| `tests/test_etapa2.py` | 5 pruebas automatizadas (Split contra 512 cortes, OX, óptimo por subconjuntos, soluciones finales). |
| `resultados/*.json` | Resultados de todas las corridas; `cifras.json` reúne cada número citado en el texto. |
| `figuras/*.png` | Las mismas figuras en PNG. |

## Cómo reproducir

```bash
python -m pip install numpy matplotlib pytest
python -m pytest -q tests                 # ~1 s
python src/analisis_principal.py          # ~15 s
python src/ejemplos.py
python src/sensibilidad_ampliada.py       # ~4 min con 2 procesos
python src/aco_sin_feromona.py
python src/aco_cotas.py
python src/tiempos_componentes.py         # depende del equipo
python src/cifras.py
python src/tablas_latex.py
python src/figuras_etapa2.py
cd latex && pdflatex main.tex && pdflatex main.tex
```

Todo es determinista por semilla excepto los tiempos. Los tiempos de la Tabla 15 (i7-13620H, Windows) se conservaron del experimento del 20 de octubre; el desglose por componente y el tiempo hasta el óptimo se midieron en otro equipo (Linux) y así se indica en el texto. Si quieren reportarlos con su equipo, ejecuten `src/tiempos_componentes.py` y cambien esas cifras en la sección 4.4.
