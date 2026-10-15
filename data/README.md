# Datos

| Archivo | Contenido |
|---|---|
| [`instancia.txt`](instancia.txt) | Instancia didáctica **CVRP_10** en formato tipo TSPLIB: 1 depósito (nodo 1) + 10 clientes, capacidad de vehículo `Q = 50`, `EDGE_WEIGHT_TYPE: EUC_2D`. |

- **Demanda total:** 146 unidades (`⌈146 / 50⌉ = 3` rutas como cota inferior).
- **Origen:** archivo proporcionado en la actividad del curso (*Diseño de algoritmos matemáticos bioinspirados*). Se incluye sin modificaciones, únicamente para que el análisis sea reproducible; véase [`../ATRIBUCIONES.md`](../ATRIBUCIONES.md).
- **Unidades:** el archivo no declara unidades físicas (ni km ni kg). Se habla de «unidades de distancia» y «unidades de carga».
- **Distancia:** aunque la etiqueta es `EUC_2D` (que en TSPLIB redondea al entero más cercano), el caso principal usa distancia euclidiana **sin redondeo**. La variante redondeada se evalúa aparte como análisis de sensibilidad (`distancia_redondeada_sensibilidad` en `results/resultados.json`).

## Coordenadas y demandas

| Nodo | x | y | Demanda |
|---:|---:|---:|---:|
| 1 (depósito) | 50 | 50 | 0 |
| 2 | 20 | 70 | 12 |
| 3 | 30 | 80 | 18 |
| 4 | 60 | 75 | 10 |
| 5 | 80 | 70 | 15 |
| 6 | 25 | 45 | 14 |
| 7 | 40 | 30 | 20 |
| 8 | 65 | 25 | 16 |
| 9 | 85 | 40 | 11 |
| 10 | 45 | 60 | 13 |
| 11 | 70 | 55 | 17 |
