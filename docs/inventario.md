# Inventario de lo incorporado y lo excluido

Rutas relativas al directorio de trabajo original (`work/…`, `outputs/…`), que **no se modificó**: todo se copió. Las huellas son los 12 primeros caracteres del SHA-256 del archivo **tal como está en este repositorio**.

## Incorporado

| Ruta en el repositorio | Origen | Qué es | Por qué / observaciones |
|---|---|---|---|
| `src/resolver_cvrp_arcos.py` | `work/cvrp_revision/resolver_cvrp_arcos.py` | Código principal (modelo de arcos y carga + Clarke–Wright + 2-opt) | Modificado: distingue óptimo probado de incumbente y certifica 3 rutas por particiones (ver docs/coherencia.md). El original está en archive/. |
| `src/verificar_resultados.py` | `— (nuevo)` | Verificador de coherencia | Recalcula distancias/cargas desde la instancia; no existía en los materiales. |
| `src/generar_figuras.py` | `work/cvrp_revision/editar_informe.py (solo código de las dos figuras) + resolver_cvrp_arcos.py` | Regenera las figuras desde un JSON de resultados | Extrae el código de figuras del script de edición del informe; evita publicar el script que manipula el DOCX. |
| `data/instancia.txt` | `work/cvrp_revision/instancia.txt` | Instancia CVRP_10 (material del curso) | Idéntica por hash a work/cvrp/instancia.txt y work/cvrp/entrega/instancia.txt. |
| `results/cbc_01.log … cbc_10.log` | `work/cvrp_revision/resultados/` | Registros CBC de las 10 mediciones vigentes | Evidencia de las tablas del informe. Solo se sustituyó la ruta local en la línea `command line`. |
| `results/cbc_3rutas.log` | `work/cvrp_revision/resultados/cbc_3rutas.log` | Registro CBC del modelo de arcos con m = 3 | Detenido por límite de tiempo (361.0004, sin probar). Se conserva como evidencia de la contradicción. |
| `results/matriz_costos.csv` | `work/cvrp_revision/resultados/` | Matriz de distancias 11 × 11 | Idéntica por hash a la del modelo anterior (misma instancia). |
| `results/mediciones.csv` | `work/cvrp_revision/resultados/` | Diez mediciones del modelo de arcos y de la heurística | Fuente de las Tablas 8 y 9 y de la Figura 5 del informe. |
| `results/resultados.json` | `work/cvrp_revision/resultados/` | Resultados completos y entorno | Solo se sustituyó la ruta local del solver. Su campo tres_rutas guarda el incumbente 361.0004. |
| `results/reproduccion_2026-10-15/` | `Generado en esta tarea` | Reejecución completa con entorno nuevo | Evidencia nueva, separada de la histórica. |
| `figures/rutas_exactas.png` | `work/cvrp_revision/resultados/rutas_exactas.png` | Figura de rutas de la solución exacta (4 rutas) | Generada por el script de la revisión; numeración del modelo de arcos. |
| `figures/rutas_heuristica.png` | `work/cvrp_revision/resultados/rutas_heuristica.png` | Figura de rutas de Clarke–Wright + 2-opt | Idéntica por hash a la del modelo anterior (la heurística no cambió). |
| `figures/rutas_tres.png` | `Regenerada con src/generar_figuras.py` | Figura de la solución óptima con 3 rutas | Sustituye a la copia del modelo anterior; mismo contenido (339.1647). |
| `figures/comparacion.png` | `work/cvrp_revision/assets/comparacion_actualizada.png` | Distancia y tiempo medio, modelo de arcos vs heurística | Versión vigente (10 970 ms). La anterior (35 ms, otro modelo) solo está en archive/. |
| `figures/diagrama_variables.png` | `Regenerada con src/generar_figuras.py (original: work/cvrp_revision/assets/diagrama_variables.png)` | Diagrama de variables y restricciones | Mismo contenido; se movieron dos flechas que cruzaban etiquetas. |
| `docs/Reto_CVRP_revisado.docx` | `outputs/cvrp_revision/Reto_CVRP_revisado.docx` | Informe vigente | Idéntico por hash a work/cvrp_revision/despues.docx. |
| `docs/metodologia.md, docs/coherencia.md, docs/inventario.md` | `— (nuevos)` | Documentación | Escritos para el repositorio. |
| `archive/v1_modelo_particion_rutas/` | `work/cvrp/ (resolver_cvrp.py, resultados/, entrega/requirements.txt) + outputs/cvrp/Reto_CVRP_Etapa1.docx` | Antecedente: modelo por partición de rutas | Una sola copia (work/cvrp/entrega/ era un duplicado exacto). Es válido pero NO es el modelo vigente. |
| `archive/v2_arcos_script_de_la_revision/resolver_cvrp_arcos_original.py` | `work/cvrp_revision/resolver_cvrp_arcos.py` | Script exacto que generó results/ | Trazabilidad: es el que acepta como óptimo un incumbente por límite de tiempo. |

## Huellas SHA-256 (datos, resultados, figuras e informe; los scripts y textos se normalizan a LF al confirmar y no se listan)

| Archivo | SHA-256 (12) |
|---|---|
| `data/instancia.txt` | `a76ebd6059d7` |
| `docs/Reto_CVRP_revisado.docx` | `91fa118455a0` |
| `figures/comparacion.png` | `e39492bd4679` |
| `figures/diagrama_variables.png` | `e33720fade91` |
| `figures/rutas_exactas.png` | `0badd1e6990a` |
| `figures/rutas_heuristica.png` | `cae31d31eca5` |
| `figures/rutas_tres.png` | `f43d78ba3cae` |
| `results/cbc_01.log` | `d697eba359a4` |
| `results/cbc_02.log` | `06659653bf91` |
| `results/cbc_03.log` | `acee5c2e1ef0` |
| `results/cbc_04.log` | `47dcea0d4792` |
| `results/cbc_05.log` | `8a96b3c91f0a` |
| `results/cbc_06.log` | `3f49cdd5239b` |
| `results/cbc_07.log` | `69fe4fbb9878` |
| `results/cbc_08.log` | `0ebfb3b0b64c` |
| `results/cbc_09.log` | `4b237b83e4fd` |
| `results/cbc_10.log` | `5ee7c38b5033` |
| `results/cbc_3rutas.log` | `17ef6a4b596c` |
| `results/matriz_costos.csv` | `7576c2357214` |
| `results/mediciones.csv` | `5c494d812924` |
| `results/resultados.json` | `b56684be847a` |

## Excluido y por qué

| Material | Motivo |
|---|---|
| outputs/cvrp_revision/Respaldo_CVRP_revision.zip, outputs/cvrp/*.zip, outputs/cvrp_latex/*.zip, work/cvrp_latex/CVRP_Etapa_1.zip | Paquetes comprimidos que duplican archivos ya incluidos. |
| work/cvrp_latex/, outputs/cvrp_latex/ (main.tex, Reto_CVRP_Etapa1.pdf, figuras, scripts de conversión, capturas) | La versión LaTeX está pendiente de actualización y aprobación; no se modificó ni se presenta como vigente. Sigue intacta en el directorio de origen. |
| work/cvrp/original.docx, original.pdf | Documento original de partida; está superado por el informe vigente. |
| work/cvrp/revision.docx/.pdf, work/cvrp_latex/aprobado.*, work/cvrp_revision/antes.*, despues.* | Estados intermedios del informe; el vigente es una copia de despues.docx. |
| work/cvrp/render/, work/cvrp_revision/renders/, work/cvrp_latex/pagina-*.png, contacto-*.png, portada.png, cover.png | Renders y hojas de contacto de comprobación visual; artefactos regenerables. |
| outputs/**/*.png de verificación en Google Docs / Prism, verificacion.json, manifest_sha256.json, cobertura.json | Evidencia de automatización de navegador y del flujo LaTeX; no necesaria para reproducir el análisis. |
| work/cvrp_revision/editar_informe.py, preparar_modelo.py, verificar_documento.py; work/cvrp/crear_reporte.py; work/cvrp_latex/convertir.py, verificar.py; contenido*.json, estructura.json, cuerpo*.html | Scripts y datos intermedios que fabrican o comprueban los DOCX/LaTeX; no son necesarios para reproducir resultados (la parte de figuras se llevó a src/generar_figuras.py). |
| work/cvrp_revision/referencia_modelo_exacto.py | Copia de código de otro autor (repositorio de referencia sin licencia). No se redistribuye; se cita. |
| work/cvrp_revision/assets/e01–e09.png, rId7–rId11.png | Imágenes de ecuaciones y figuras incrustadas en los DOCX (el informe ya las contiene) y duplicados por hash. |
| work/cvrp/entrega/ (duplicado exacto de work/cvrp/) | Duplicado por hash. |
| work/cvrp_revision/resultados/rutas_*.png | Ya copiadas a figures/ (no se duplican en results/). |

## Duplicados detectados por hash

- `instancia.txt`: 3 copias idénticas (`work/cvrp/`, `work/cvrp/entrega/`, `work/cvrp_revision/`).
- `matriz_costos.csv` y `rutas_heuristica.png`: idénticos entre el modelo anterior y la revisión (misma instancia; la heurística no cambió).
- Todos los archivos de `work/cvrp/resultados/` están duplicados byte a byte en `work/cvrp/entrega/resultados/`.
- `outputs/cvrp/Reto_CVRP_Etapa1.docx` = `work/cvrp/entrega/Reto_CVRP_Etapa1.docx`; `outputs/cvrp_revision/Reto_CVRP_revisado.docx` = `work/cvrp_revision/despues.docx`.
- `rId7–rId11.png` de la revisión = figuras del proyecto LaTeX anterior.

## Mediciones de dos modelos distintos

El modelo por partición de rutas (`archive/`, 35.005 ms de media para el exacto) y el modelo de arcos vigente (`results/`, 10 970.079 ms) **no se mezclan** en ninguna tabla ni figura del repositorio.
