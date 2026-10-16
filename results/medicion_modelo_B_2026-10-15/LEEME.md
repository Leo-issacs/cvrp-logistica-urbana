# Medición nueva con el modelo B (15 de octubre de 2026)

Salidas de

```
python src/resolver_cvrp_arcos.py data/instancia.txt --out results/medicion_modelo_B_2026-10-15 --modelo B
```

Es evidencia **nueva y separada** de `../` (mediciones históricas del modelo A, 10.970 s) y de `../reproduccion_2026-10-15/`. No sustituye ninguna tabla ni figura del informe, que sigue basado en las mediciones históricas.

| | |
|---|---|
| Modelo | B: arcos y carga física, **sin** restricciones explícitas de subrutas (154 restricciones en el caso libre, 155 con tres rutas; 220 variables) |
| Entorno | Windows 11 (10.0.26300), Python 3.12.10, PuLP 3.3.0, CBC 2.10.3 (incluido en PuLP), un solo equipo |
| CBC | `threads = 0`, `gapRel = gapAbs = 0`, límite de 120 s por corrida |
| Protocolo | calentamiento descartado (un caso libre, uno de tres rutas y la heurística) y 10 repeticiones por caso; tiempo = construcción + CBC + reconstrucción de rutas; certificación independiente y verificación fuera del cronómetro |
| Comprobación | `python src/verificar_resultados.py results/medicion_modelo_B_2026-10-15` → 38/38, sin avisos |

## Resultados

| | Libre (sin flota fija) | Exactamente 3 rutas | Heurística (C–W + 2-opt) |
|---|---:|---:|---:|
| Distancia | 318.9894867478 (4 rutas) | 339.1646737616 | 339.2528701367 |
| Estado de CBC | `optimo_probado` 10/10 | `optimo_probado` 10/10 | — |
| Tiempo total medio ± σ | 2.975 ± 0.097 s | 10.979 ± 0.641 s | 0.198 ± 0.080 ms |
| Mín.–máx. | 2.812–3.167 s | 9.611–11.570 s | 0.107–0.354 ms |
| Nodos / iteraciones de CBC | 240 / 20 066 | 8 247 / 204 300 | — |
| Relajación lineal inicial | 276.462 | 276.462 | — |

- Construcción ≈ 0.004 s; reconstrucción ≈ 0.0001 s; el resto es `solve_s`.
- Certificación independiente por particiones: 318.9894867478301 y 339.1646737615703; coinciden con CBC.
- Variante con distancias enteras (EUC_2D redondeado): óptimo 317.
- Como todas las corridas de ambos casos probaron optimalidad, el tiempo medio sí corresponde a «tiempo hasta el óptimo» **para estas 20 corridas**; no sería válido llamarlo así si alguna se hubiera detenido por límite.

## Porcentajes (cada uno con su denominador)

| Cantidad | Fórmula | Valor |
|---|---|---:|
| GAP de costo | 100 (Z_heur − Z\*) / Z\* , Z\* = 318.9894867478 | 6.352 % |
| Reducción de distancia del exacto respecto de la heurística | 100 (Z_heur − Z\*) / Z_heur , Z_heur = 339.2528701367 | 5.973 % |
| Sobrecosto de tres rutas respecto del óptimo libre | 100 (Z₃ − Z\*) / Z\* | 6.325 % |
| Reducción de tiempo de la heurística | 100 (t_E − t_H) / t_E , t_E = 2.9754 s | 99.993 % |
| Razón de tiempos t_E / t_H | | ≈ 15 008 |

## Cautelas

- Misma máquina que las otras mediciones, pero **otro momento**: en una comparación hecha poco después (`../comparacion_variantes_2026-10-15/`) el mismo modelo B tardó 2.07 s en el caso libre. Los tiempos absolutos varían entre ejecuciones y no son comparables con los históricos (10.970 s, modelo A). Los nodos e iteraciones de CBC se repiten exactamente; solo cambia el reloj.
- Una sola instancia, un solo equipo, una sola versión de CBC.
- Las figuras de esta ejecución no se versionaron; se regeneran con `python src/generar_figuras.py results/medicion_modelo_B_2026-10-15 --salida <carpeta>`.
- Esta medición se generó con `src/resolver_cvrp_arcos.py` antes de dos correcciones posteriores de robustez (guardar `mediciones.csv` y salir con un mensaje si una corrida no entrega solución, y añadir el campo `tres_rutas_estado_primera_repeticion` al JSON nuevo). La ruta de ejecución sin fallos no cambió y esta carpeta no se regeneró; por eso su `resultados.json` no incluye ese campo y el verificador lo deduce de `mediciones.csv`.
