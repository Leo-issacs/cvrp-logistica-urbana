# Atribuciones y licencias

Este repositorio **no declara una licencia general**. El código y los textos de análisis son trabajo académico del equipo; al no haber licencia, no se conceden derechos de reutilización. Tampoco se otorgan derechos sobre el material del curso ni de terceros listado abajo.

| Material | Origen | Tratamiento en el repositorio |
|---|---|---|
| `data/instancia.txt` (CVRP_10) | Archivo proporcionado en la actividad del curso *Diseño de algoritmos matemáticos bioinspirados* (el informe lo cita como «Material de la actividad»). | Incluido sin cambios solo para reproducir el análisis. Derechos del material: de su autor/curso. Si el docente no autoriza su redistribución, retirar el archivo. |
| PuLP / CBC | PuLP (licencia MIT, [coin-or/pulp](https://github.com/coin-or/pulp)); CBC (Eclipse Public License 2.0, [coin-or/Cbc](https://github.com/coin-or/Cbc)). | Se instalan como dependencia (`requirements.txt`); no se redistribuyen binarios. |
| matplotlib | Licencia basada en PSF. | Dependencia, no redistribuida. |
| Algoritmo de ahorros | Clarke y Wright (1964), *Operations Research* 12(4), 568–581. | Método publicado; su implementación está en `src/`. No se verificó contra implementaciones de terceros y este documento no afirma originalidad más allá de lo que consta aquí. |
| `etapa3/instancias/CMT1.vrp` a `CMT14.vrp` | Christofides, Mingozzi y Toth (1979), instancias CMT, obtenidas de CVRPLIB (http://vrp.galgos.inf.puc-rio.br). | Copiadas sin cambios en `etapa3/instancias/`. El BKS se toma del campo `COMMENT` de cada archivo. Derechos del material: de sus autores y de CVRPLIB; no se otorga ninguno. |
| `etapa3/instancias/X-n*.vrp` (diez instancias X) | Uchoa et al. (2017), conjunto X, obtenidas de CVRPLIB. | Copiadas sin cambios en `etapa3/instancias/`. Derechos del material: de sus autores y de CVRPLIB; no se otorga ninguno. |
| BKS de las instancias X | Vidal (2022), *Computers & Operations Research* 140, 105643 (tablas 5 y 6, según `etapa3/README.md`). | Solo valores numéricos de referencia para calcular el GAP; no se reproduce el artículo. |
| Bibliografía y referencias contextuales del informe (BBC, McKinsey, Foro Económico Mundial, etc.) | Ver sección *Referencias* del informe. | Solo citadas; no se reproducen sus contenidos. |

## Privacidad

- Los registros CBC y `resultados.json` que se conservan (históricos y de las mediciones nuevas) fueron editados únicamente para **omitir la ruta local** del equipo (línea `command line` del log y campo `entorno.solver`). Los valores numéricos no se tocaron.
- El informe vigente (`docs/Reto_CVRP_revisado.docx`) es el entregable del equipo y lleva en su portada los nombres e identificadores de los integrantes. El repositorio es **público** y esa portada se conserva por decisión expresa del autor.
