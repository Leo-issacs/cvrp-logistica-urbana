# Atribuciones y licencias

Este repositorio **no declara una licencia general**. El código y los textos de análisis son trabajo académico del equipo; al no haber licencia, no se conceden derechos de reutilización. Tampoco se otorgan derechos sobre el material del curso ni de terceros listado abajo.

| Material | Origen | Tratamiento en el repositorio |
|---|---|---|
| `data/instancia.txt` (CVRP_10) | Archivo proporcionado en la actividad del curso *Diseño de algoritmos matemáticos bioinspirados* (el informe lo cita como «Material de la actividad»). | Incluido sin cambios solo para reproducir el análisis. Derechos del material: de su autor/curso. Si el docente no autoriza su redistribución, retirar el archivo antes de compartir el repositorio. |
| PuLP / CBC | PuLP (licencia MIT, [coin-or/pulp](https://github.com/coin-or/pulp)); CBC (Eclipse Public License 2.0, [coin-or/Cbc](https://github.com/coin-or/Cbc)). | Se instalan como dependencia (`requirements.txt`); no se redistribuyen binarios. |
| matplotlib | Licencia basada en PSF. | Dependencia, no redistribuida. |
| Algoritmo de ahorros | Clarke y Wright (1964), *Operations Research* 12(4), 568–581. | Implementación propia del método publicado. |
| Bibliografía y referencias contextuales del informe (BBC, McKinsey, Foro Económico Mundial, etc.) | Ver sección *Referencias* del informe. | Solo citadas; no se reproducen sus contenidos. |

## Privacidad

- Los registros CBC y `resultados.json` que se conservan fueron editados únicamente para **omitir la ruta local** del equipo (campo `command line` del log y campo `entorno.solver`). Los valores numéricos no se tocaron.
- El informe vigente (`docs/Reto_CVRP_revisado.docx`) es el entregable del equipo y lleva en su portada los nombres e identificadores de los integrantes. El repositorio es **privado**; antes de hacerlo público, revisar esa portada.
