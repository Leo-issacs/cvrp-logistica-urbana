# Script de la revisión (modelo de arcos), versión original

`resolver_cvrp_arcos_original.py` es, byte a byte, el script que generó `results/` (revisión del 15/oct/2026). Se conserva porque contiene una lectura incorrecta del estado de CBC: con `fixed_k=3` aceptaba como óptima una solución detenida por límite de tiempo (361.0004). Detalles en [`../../docs/coherencia.md`](../../docs/coherencia.md).

Para ejecutar o reproducir use [`../../src/resolver_cvrp_arcos.py`](../../src/resolver_cvrp_arcos.py), que mantiene el mismo modelo y corrige esa comprobación.
