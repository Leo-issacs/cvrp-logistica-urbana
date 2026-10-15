# Reejecución del 15 de octubre de 2026

Salidas de `python src/resolver_cvrp_arcos.py data/instancia.txt --out results/reproduccion_2026-10-15`, ejecutado con `src/resolver_cvrp_arcos.py` (versión de este repositorio) en un entorno virtual nuevo.

| | |
|---|---|
| Sistema | Windows 11 (10.0.26300) |
| Python / PuLP | 3.12.10 / 3.3.0 |
| Procesador | Intel64 Family 6 Model 186 (véase `resultados.json → entorno`) |
| Solver | CBC incluido en PuLP, modo serial, `gapRel = gapAbs = 0`, límite 120 s |

**Es evidencia nueva y distinta de `../`**, que contiene las mediciones documentadas en el informe. No se sustituyeron las tablas ni las figuras del informe.

- Distancias, rutas y GAP: idénticos a los documentados (318.9894867478301; 339.252870136741; 6.352367 %).
- Tiempo exacto medio: **5.421 s** (documentado: 10.970 s). Causa no investigada.
- Escenario de 3 rutas: CBC (modelo de arcos) se detuvo a los 120 s con 339.1647 **sin probar optimalidad**; el óptimo se certifica por particiones.
- Las figuras de esta ejecución no se versionaron (se pueden regenerar con `python src/generar_figuras.py results/reproduccion_2026-10-15 --salida <carpeta>`).
