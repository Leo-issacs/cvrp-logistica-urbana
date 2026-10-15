# v1 · Modelo por partición de rutas (antecedente)

**Formulación.** Se enumeran todas las rutas factibles (una ruta óptima por subconjunto de clientes que cabe en un vehículo: 177 columnas) y CBC elige la partición de costo mínimo (cobertura exacta, `y_r ∈ {0,1}`, minimizar Σ c_r y_r). Es una formulación válida y da el mismo óptimo, **318.9894867478301**, y el mismo escenario de tres rutas, **339.1646737615703**, que el modelo vigente.

**Por qué está en `archive/`.** El modelo vigente es el de arcos binarios y carga física (ver [`../../docs/metodologia.md`](../../docs/metodologia.md)). Los tiempos de esta carpeta (media del exacto: **35.005 ms**) corresponden a *otra formulación* y **no deben compararse ni mezclarse** con los del modelo vigente (10 970.079 ms en la medición histórica).

| Archivo | Contenido |
|---|---|
| `resolver_cvrp.py` | Código completo de esta versión (no se reejecutó en esta tarea). |
| `requirements.txt` | Dependencias de la época. |
| `results/` | Registros CBC, matriz, mediciones, `resultados.json` y figuras de esa ejecución (14/oct/2026). |
| `Reto_CVRP_Etapa1.docx` | Informe de la Etapa 1 basado en este modelo (**superado**). |

Nota: `results/cbc_3rutas.log` de esta carpeta sí probó el óptimo de tres rutas (339.16467376); es la fuente histórica de ese valor.
