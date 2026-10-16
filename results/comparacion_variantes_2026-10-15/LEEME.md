# Comparación de los modelos A, B y C (15 de octubre de 2026)

Salidas de `python src/comparar_variantes.py --out results/comparacion_variantes_2026-10-15`.

Protocolo: un calentamiento descartado por variante y caso; 10 repeticiones por caso con el **orden de las variantes rotado** en cada repetición (ABC, BCA, CAB, …); tiempos separados `build_s`, `solve_s`, `reconstruct_s` y `total_s` (su suma); límite de 120 s por corrida; certificación independiente fuera del cronómetro. Mismo equipo y entorno que `../medicion_modelo_B_2026-10-15/` (Windows 11, Python 3.12.10, PuLP 3.3.0, CBC 2.10.3).

Comprobación: `python src/verificar_resultados.py results/comparacion_variantes_2026-10-15` → 13/13, con 8 avisos (las corridas del modelo A con tres rutas detenidas sin probar optimalidad; son evidencia, no errores).

## Sin flota fija (óptimo certificado 318.9894867478)

| Modelo | Restricciones | Probadas | Tiempo total medio ± σ | Nodos / iteraciones de CBC | Relajación inicial |
|---|---:|---:|---:|---:|---:|
| A (1 013 subrutas) | 1 167 | 10/10 | 5.49 ± 0.05 s | 218 / 15 377 | 286.92 |
| **B** (sin subrutas) | 154 | 10/10 | 2.07 ± 0.03 s | 240 / 20 066 | 276.46 |
| C (B + cotas de carga) | 264 | 10/10 | 1.78 ± 0.02 s | 168 / 15 725 | 291.14 |

## Exactamente 3 rutas (óptimo certificado 339.1646737616)

| Modelo | Probadas | Tiempo de ejecución medio ± σ (mín.–máx.) | Observación |
|---|---:|---|---|
| A | **2/10** | 113.5 ± 14.1 s (86.5–120.3) | 8 corridas se detuvieron en el límite: incumbentes de 361.0004 (3), 363.8579 (4) y 339.1647 sin prueba (1); cota inferior de CBC 299.712 (325.776 en una). **El promedio mezcla corridas probadas y detenidas: no es «tiempo hasta el óptimo».** |
| **B** | 10/10 | 17.4 ± 6.1 s (6.3–22.3) | 8 247 nodos / 204 300 iteraciones en todas las corridas |
| C | 10/10 | 23.4 ± 12.1 s (10.6–35.6) | 10 713 nodos / 341 329 iteraciones |

## Cómo leerlo

- **Sin flota fija**, B y C resuelven en menos de la mitad del tiempo de A en esta máquina. Con tres rutas, B probó el óptimo en las 10 corridas y A solo en 2; C también lo probó siempre, pero más lento que B.
- Los tiempos de tres rutas son **bimodales**: en las repeticiones 1–2 B tardó ≈ 6.3 s y de la 3 a la 10 ≈ 17–22 s con **idéntico** número de nodos e iteraciones, lo que indica deriva de rendimiento del equipo (carga, frecuencia) y no del modelo. Rotar el orden reparte ese sesgo, pero no lo elimina: compare las variantes dentro de una misma repetición y no confíe en los tiempos absolutos.
- Una corrida de A con tres rutas terminó con 339.1647 sin haberlo probado (cota 325.776): el valor coincide con el óptimo certificado, pero **solo la certificación por particiones lo demuestra**.
- Resultados de una sola instancia y un solo equipo; no prueban que quitar las subrutas sea mejor en general.
