# Revisión de coherencia

Contraste de las cifras de referencia de la revisión del 15 de octubre de 2026 con los archivos del repositorio. Lo marcado como **verificado** se recalculó con [`src/verificar_resultados.py`](../src/verificar_resultados.py) (solo recomputa desde la instancia; no confía en los totales del JSON) o se leyó directamente del archivo indicado.

## 1. Cifras de referencia

| Cifra de referencia | Estado | Evidencia |
|---|---|---|
| Distancia óptima 318.9894867478301 | **Verificada** | Recalculada desde las rutas y la instancia; CBC la reporta «Optimal solution found» en los 10 registros (`results/cbc_01.log … cbc_10.log`); coincide con la programación dinámica independiente y con la reejecución del 15/10/2026. |
| Cuatro rutas en la solución de menor distancia | **Verificada** | `results/resultados.json → exacto`: 4 rutas, cargas 44, 42, 47 y 13. |
| Distancia heurística ≈ 339.252870136741 | **Verificada** | Recalculada desde las rutas de `resultados.json → heuristica`. |
| GAP de costo ≈ 6.352367 % | **Verificado** | $100\,(339.252870-318.989487)/318.989487 = 6.352367\,\%$. |
| Tiempo exacto promedio ≈ 10.970079 s (10 ejecuciones) | **Verificado como medición histórica** | Media de `results/mediciones.csv` (columna `total_s`) = 10.970079 s, desv. est. 0.267 s. No se puede reproducir exactamente: ver §3. |
| Capacidad 50, demanda total 146, 10 clientes + depósito | **Verificado** | `data/instancia.txt`. |
| Distancias euclidianas sin redondeo; variante EUC_2D aparte | **Verificado** | `results/matriz_costos.csv` coincide con `math.dist` sin redondeo; la variante redondeada da óptimo **317** (`distancia_redondeada_sensibilidad`, 4 rutas), reproducido el 15/10/2026. |

## 2. Contradicción encontrada: escenario de tres rutas

**Qué decía el informe antes de la corrección.** La sección de flota mínima afirmaba que «el modelo de arcos y carga con *m* = 3 encontró una solución factible y óptima para esa flota: Z₃ = 339.164674» y la Figura 3 mostraba rutas con cargas 47, 50 y 49. La atribución se corrigió el 15 de octubre de 2026; las rutas y el valor certificado se mantienen.

**Qué muestra la evidencia de la revisión.**

| Fuente | Objetivo con exactamente 3 rutas | ¿Óptimo probado? |
|---|---|---|
| `results/cbc_3rutas.log` (modelo de arcos, 120 s) | **361.000366**, cota inferior 299.7, «Stopped on time limit» | **No** |
| `results/resultados.json → tres_rutas` | 361.000366 (el incumbente de CBC: rutas 1-3-5-11, 1-4-10-2-6 y 1-9-8-7) | **No**; guardado como si fuera el óptimo |
| `archive/v1_modelo_particion_rutas/results/cbc_3rutas.log` (modelo anterior) | **339.164674**, «Optimal solution found» | Sí |
| Programación dinámica por particiones (`particion_optima(k=3)`), ejecutada en esta revisión | **339.1646737615703**; rutas 1-2-3-11-1, 1-6-7-8-1, 1-9-5-4-10-1 | Sí (enumeración exhaustiva) |

**Causa.** El script usaba `timeLimit=120` y solo comprobaba `LpStatus == 'Optimal'`. PuLP devuelve ese estado también cuando CBC se detiene por tiempo con una solución entera, así que un incumbente de 361.0004 pasó por óptimo. El modelo de arcos con flota fija en 3 rutas es mucho más difícil para CBC que el caso sin flota fija (que sí se prueba en ≈ 5–11 s).

**Corrección.** El valor **339.164674 es correcto** y está certificado, pero **no proviene del modelo de arcos**: proviene del modelo por partición de rutas (antecedente) y de la programación dinámica. En el repositorio:

- `src/resolver_cvrp_arcos.py` ahora distingue el óptimo probado del incumbente (`sol_status`), registra ambos para `m = 3` y obtiene el óptimo de tres rutas por particiones. Guarda además `tres_rutas_cbc_arcos` con el estado de CBC.
- `results/` conserva **sin cambios** la evidencia histórica, incluido el 361.0004 equivocado; el verificador lo señala como aviso.
- `figures/rutas_tres.png` muestra la solución óptima de tres rutas (339.1647), no el incumbente.

**Corrección del informe completada el 15 de octubre de 2026.** Se corrigió el Google Doc y se actualizó `docs/Reto_CVRP_revisado.docx` desde una exportación nueva. La sección 6.2 distingue el incumbente histórico de 361.000366 del óptimo certificado de 339.164674. La Tabla 6, la Figura 3 y las conclusiones atribuyen ese óptimo a la programación dinámica por particiones y al registro del modelo anterior. El anexo contiene el control de `sol_status`, la función `particion_optima` y la separación entre incumbente y óptimo demostrado. Los promedios de tiempo se identifican como mediciones históricas del caso sin flota fija; el escenario de tres rutas no forma parte de ellos. Se conservó la portada y no se reincorporó el anexo B.

## 3. Mediciones históricas frente a una nueva ejecución

| | Histórica (`results/`) | Nueva (`results/reproduccion_2026-10-15/`) |
|---|---|---|
| Fecha | 15/10/2026 (revisión) | 15/10/2026, misma máquina, sesión posterior |
| Entorno | Windows 11 (10.0.26300), Python 3.12.14, PuLP 3.3.0 | Windows 11 (10.0.26300), Python 3.12.10, PuLP 3.3.0, entorno virtual nuevo |
| Distancia exacta / heurística | 318.9894867478301 / 339.252870136741 | **idénticas** |
| Tiempo exacto medio (10 ejec.) | 10.970 s (σ = 0.267) | 5.421 s (σ = 0.102) |
| Tiempo heurística medio | 0.487 ms | 0.124 ms |
| 3 rutas en CBC (120 s) | incumbente 361.0004, sin probar | incumbente 339.1647, **sin probar** |

Los **resultados** (rutas, distancias, GAP) se reproducen exactamente; los **tiempos** no: en esta ejecución el exacto tardó la mitad. No se ha investigado la causa (carga del sistema, versión de Python, planificación de hilos de CBC u otra); por eso los tiempos del informe se presentan como una medición de un equipo y un momento concretos, y no se reemplazaron. El incumbente de tres rutas en CBC también varía entre ejecuciones, lo que confirma que CBC no lo resuelve con garantía en 120 s.

## 4. Otras observaciones

- **Numeración de rutas.** El informe conserva la orientación y numeración representativas de sus tablas y figuras originales. `figures/rutas_exactas.png` usa el orden del modelo de arcos, que puede ser diferente. Los conjuntos de clientes y recorridos son equivalentes; los identificadores R1–R4 son etiquetas locales de cada presentación y no vehículos distintos.
- **Comparación de tiempos.** La figura de comparación de la versión anterior mostraba 35.005 ms (exacto, modelo por partición) frente a 0.128 ms; la vigente muestra 10 970 ms (modelo de arcos) frente a 0.487 ms. **No se pueden mezclar:** son formulaciones distintas. Solo se versionó la vigente.
- **Anexo B:** no existe en la revisión vigente y no se reincorporó.
- **Documento compartido:** se revisó y corrigió la versión en línea; se comprobó su exportación posterior en DOCX y PDF. La portada se comparó con la copia previa, tanto en texto como visualmente.

## 5. Modelo B y mediciones nuevas (15 de octubre de 2026)

A partir de un diagnóstico externo, revisado también por el equipo del informe, se integró en `src/` el **modelo B** (el modelo de arcos y carga sin las 1 013 restricciones explícitas de subrutas) como opción y como valor predeterminado. El modelo A se conserva (`--modelo A`) para reproducir la evidencia histórica y el modelo C queda como experimento opcional. Nada de `results/` ni de `results/reproduccion_2026-10-15/` se modificó.

| Comprobación | Resultado |
|---|---|
| B devuelve el óptimo libre y el de tres rutas | 318.9894867478 y 339.1646737616 en las 20 corridas, con `optimo_probado`; coinciden con la certificación por particiones |
| B excluye subrutas aisladas | por el balance de producto con demandas positivas ([`metodologia.md`](metodologia.md)); todas las soluciones de B y C se verificaron factibles; con demandas nulas se exige el modelo A |
| Tamaño | A: 1 167 restricciones; B: 154; C: 264 (más una con tres rutas) |
| Relajación lineal inicial | A 286.92; B 276.46; C 291.14 |
| Tiempo, sin flota fija | A 5.49 s, B 2.07 s, C 1.78 s (comparación con orden rotado) |
| Tiempo, tres rutas | A: 2/10 probadas; B: 10/10, media 17.4 s en la comparación y 10.98 s en la medición propia; C: 10/10, 23.4 s |
| Verificadores | 38/38 (medición B) y 13/13 con 8 avisos (comparación) |

**Lectura prudente.** Que (8) fortalezca la relajación lineal (276.46 → 286.92) no implica que mejore el tiempo de CBC: en esta instancia, con esta versión de CBC y en este equipo, quitarlas redujo el tiempo sin flota fija y permitió probar siempre el caso de tres rutas dentro de 120 s. No es una propiedad general. Las cotas de carga adicionales (C) mejoraron la relajación y el tiempo sin flota fija, pero no el de tres rutas respecto de B.

**Los tiempos varían con el momento del equipo.** El mismo modelo B tardó 2.98 s (medición propia), 2.07 s (comparación) y 2.08 s (experimento exploratorio previo) en el caso libre, y en la comparación sus corridas de tres rutas pasaron de ≈ 6.3 s a ≈ 17–22 s con idéntico número de nodos e iteraciones. Esto apoya que parte de la diferencia 10.97 s / 5.42 s observada con el modelo A es variación del equipo, pero **no demuestra la causa** de aquella diferencia.

**Un experimento exploratorio previo tenía un defecto de protocolo:** su cronómetro terminaba antes de reconstruir las rutas, mientras que el tiempo histórico sí las incluye. Sus números no se versionan; la comparación del repositorio mide `build_s`, `solve_s` y `reconstruct_s`, y su total es el mismo tramo que el del script histórico.

## 6. Informe vigente: revisión editorial del 16 de octubre de 2026

El informe presenta el modelo de arcos y flujo de producto como formulación principal. Las variantes A, B y C se definen y comparan en la sección 7.2; la bitácora de depuración queda en la documentación del repositorio.

- Las nueve tablas conservan sus valores. La Tabla 8 corresponde a la medición principal del modelo B del 15 de octubre: tiempo medio exacto de 2.975 s, heurística de 0.198 ms y GAP de distancia de 6.352 %.
- La solución de tres rutas conserva 339.164674, probado por CBC en las diez ejecuciones de la medición principal y confirmado por particiones.
- El marco de costos se presenta formalmente y las cinco figuras incluyen interpretación. Se eliminaron aclaraciones defensivas y referencias a archivos históricos del cuerpo del informe.
- Las funciones `construir_modelo`, `costo`, `dos_opt` y `heuristica` del Anexo A LaTeX coinciden con `src/`. No se modificaron código, instancia ni resultados.
- La exportación de Google Docs conserva la portada original y no reincorpora el Anexo B. El PDF de LaTeX tiene 19 páginas; se revisaron numeración, referencias y maquetación. La portada se incorpora desde la página original, con el mismo contenido y disposición.
- `docs/latex/main.tex` coincide por SHA-256 con la fuente descargada de Prism. El paquete de entrega contiene los ocho archivos requeridos y se verificó su integridad.

En el PDF LaTeX, (4.8) es la contradicción que demuestra conectividad, no una restricción adicional. En el DOCX se conserva la numeración simple (8). Las referencias del diagrama están adaptadas a cada formato.
