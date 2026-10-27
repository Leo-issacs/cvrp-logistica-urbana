## 1. Introducción

Esta etapa cierra el reto del problema de ruteo de vehículos con capacidad (CVRP). En la Etapa 1 se formuló el modelo matemático de arcos y carga (modelo B) y se propuso la heurística de ahorros de Clarke–Wright con mejora 2-opt; en la Etapa 2 se diseñaron un algoritmo genético (GA) y un algoritmo de colonia de hormigas (ACO) sobre una instancia didáctica de 10 clientes. Aquí los cuatro métodos se aplican a 24 instancias de referencia de la literatura, de 50 a 458 clientes, y se responde:

1. ¿Qué nivel de cada hiperparámetro del GA (puntos de cruce, probabilidad de mutación y método de selección) y del ACO (α, β y ρ) da mejores resultados en calidad de la solución, tiempo de cómputo y número de iteraciones?
2. ¿Hasta qué tamaño es útil el modelo matemático y qué tan lejos quedan las heurísticas del óptimo que prueba (GAP)?
3. ¿Qué algoritmo obtiene los mejores resultados?

**Nota sobre las instrucciones.** El segundo bloque de combinaciones (α, β y ρ) aparece rotulado como "Algoritmo Genético", pero esos son los parámetros del algoritmo de colonia de hormigas; aquí se tratan como tales.

## 2. Instancias

Se usaron las 24 instancias proporcionadas, en formato TSPLIB de CVRPLIB:

- **CMT1–CMT14** (Christofides et al., 1979): de 50 a 199 clientes con distancia euclidiana real. Siete de ellas (CMT6–CMT10, CMT13 y CMT14) agregan una **duración máxima de ruta** D y un **tiempo de servicio** s por cliente: la suma de distancia recorrida y servicio de cada ruta no puede pasar de D. El objetivo sigue siendo la distancia total.
- **X-n280 a X-n459** (Uchoa et al., 2017): de 279 a 458 clientes, con distancia euclidiana redondeada al entero más cercano, como en la definición del conjunto.

La calidad se mide contra la **mejor solución conocida (BKS)**: para CMT, el valor que trae cada archivo; para X, el reportado por Vidal (2022).

{TABLA_INSTANCIAS}

## 3. Métodos

Los cuatro métodos resuelven el mismo problema: cada cliente se visita exactamente una vez, cada ruta empieza y termina en el depósito, la carga de cada ruta no supera Q y, cuando aplica, la duración de cada ruta no supera D. Toda solución reportada se verificó con una función independiente que revisa estas condiciones y recalcula la distancia.

### 3.1 Modelo matemático (modelo B de la Etapa 1)

Es el modelo de arcos y carga física de la Etapa 1, resuelto con PuLP y CBC. Con x_ij = 1 si un vehículo va de i a j y f_ij = carga que viaja por ese arco:

$$\min \sum_{(i,j)\in A} c_{ij}\,x_{ij}$$

sujeto a

$$\sum_{j\ne i} x_{ji} = 1,\qquad \sum_{j\ne i} x_{ij}=\sum_{j\ne i} x_{ji}\qquad \forall i\in C$$

$$\sum_{j\ne i} f_{ji}-\sum_{j\ne i} f_{ij}=q_i\qquad \forall i\in C$$

$$0\le f_{ij}\le Q\,x_{ij},\qquad \sum_{j\in C} f_{0j}=\sum_{i\in C} q_i,\qquad \sum_{j\in C}x_{0j}\ge k_{\min}$$

donde k_min es el mínimo de vehículos que exige la capacidad (demanda total entre Q, redondeada hacia arriba).

El balance de carga elimina las subrutas sin restricciones explícitas, porque toda demanda es positiva. El modelo tiene n(n+1) variables binarias y otras tantas continuas, así que crece con el cuadrado del número de clientes. No incluye la restricción de duración; por eso el estudio de escalabilidad (sección 8) se hace sobre subinstancias de CMT1, que no la tiene.

### 3.2 Algoritmo propuesto: Clarke–Wright + 2-opt

Es la heurística propuesta en la Etapa 1, sin cambios de lógica:

1. Cada cliente empieza en su propia ruta 0 → i → 0.
2. Se calculan los ahorros s_ij = c_0i + c_0j − c_ij y se ordenan de mayor a menor.
3. Se recorren los ahorros: si i y j son extremos de rutas distintas y la ruta unida respeta la capacidad (y la duración, en las instancias que la tienen), se unen.
4. Cada ruta final se mejora con 2-opt de mejor mejora hasta que ningún intercambio reduce la distancia.

Para la Etapa 3 solo se agregó la revisión de duración al unir rutas. Es determinista: una sola corrida por instancia; el tiempo reportado es la mediana de 5 ejecuciones.

### 3.3 Algoritmo genético

Se conserva el diseño de la Etapa 2: cada cromosoma es una permutación de los clientes (una "ruta gigante") y el decodificador **Split** (Prins, 2004) la parte de forma óptima en rutas factibles mediante programación dinámica. En esta etapa Split también corta una ruta cuando su duración excede D.

| Elemento | Diseño |
|---|---|
| Cromosoma | Permutación de los n clientes |
| Aptitud | Distancia total de la partición óptima que devuelve Split |
| Población | 50 individuos |
| Población inicial | Vecino más cercano aleatorizado: en cada paso se elige al azar uno de los 3 clientes no visitados más cercanos |
| Selección | **Torneo binario** o **ruleta** con aptitud 1/costo (factor del experimento) |
| Cruce (p_c = 0.9) | **OX de un punto** u **OX de dos puntos** (factor del experimento) |
| Mutación | Inversión de un segmento con probabilidad **p_m ∈ {0.1, 0.2, 0.4}** (factor del experimento) |
| Reemplazo | Elitista: las 2 mejores soluciones de la generación anterior más los 48 mejores hijos |
| Paro | 1,000 generaciones (50,000 soluciones evaluadas) |

**Operadores de cruce.** El OX de dos puntos es el de la Etapa 2: copia del primer padre el segmento entre dos cortes y llena el resto en el orden circular del segundo padre. El OX de un punto copia el prefijo del primer padre hasta un solo corte y completa con los clientes faltantes en el orden en que aparecen en el segundo padre. Ambos producen siempre permutaciones válidas, así que no hace falta reparar.

**Por qué cambió la población inicial.** En la Etapa 2 la población era aleatoria, lo que funcionó con 10 clientes. Con cientos de clientes una permutación aleatoria está muy lejos de una buena solución, y 50,000 evaluaciones no alcanzan para recuperarse. Para comprobarlo se corrió la configuración exacta de la Etapa 2 (torneo, OX de dos puntos, p_m = 0.2, población aleatoria) en las 24 instancias; el resultado está en la sección 5.3. Sembrar la población con soluciones constructivas es la práctica de Prins (2004) para el GA con Split.

### 3.4 Colonia de hormigas

Se conserva el Ant System de la Etapa 2 (Dorigo et al., 1996): cada hormiga construye una ruta gigante desde el depósito, Split la parte en rutas, y todas las hormigas depositan feromona 1/costo en las adyacencias de su ruta gigante. La probabilidad de ir de i a j es

$$p_{ij}=\frac{\tau_{ij}^{\alpha}\,\eta_{ij}^{\beta}}{\sum_{l\in N_i}\tau_{il}^{\alpha}\,\eta_{il}^{\beta}},\qquad \eta_{ij}=\frac{1}{c_{ij}}$$

y la actualización es $\tau_{ij}\leftarrow(1-\rho)\,\tau_{ij}+\sum_k 1/L_k$ sobre los arcos usados por cada hormiga k.

| Elemento | Diseño |
|---|---|
| Hormigas | 25 |
| Iteraciones | 2,000 (50,000 soluciones evaluadas, igual que el GA) |
| α (peso de la feromona) | **1 o 2** (factor del experimento) |
| β (peso de la distancia) | **2 o 5** (factor del experimento) |
| ρ (evaporación) | **0.1 o 0.5** (factor del experimento) |
| Feromona inicial | τ₀ = m / C^nn, con C^nn el costo de la solución del vecino más cercano (Dorigo y Stützle, 2004) |
| Listas de candidatos | Cada hormiga elige entre los 25 clientes no visitados más cercanos; si todos ya fueron visitados, entre todos los restantes |

**Cambios para escalar.** Con 458 clientes, revisar todos los clientes en cada paso cuesta del orden de n² por hormiga; las listas de candidatos reducen ese costo a 25 operaciones por paso sin cambiar la regla de transición. La feromona inicial fija de la Etapa 2 (τ₀ = 0.01) dejaba de tener sentido con costos de decenas de miles: cada depósito 1/L sería de 5 a 1,400 veces menor que τ₀ (1/L va de 2×10⁻³ en CMT1 a 7×10⁻⁶ en X-n336-k84), y la feromona casi no cambiaría. Por eso se usa la regla estándar τ₀ = m / C^nn, que pone a τ₀ en la misma escala que los depósitos.

### 3.5 Pulido con 2-opt

Clarke–Wright incluye 2-opt y el GA y el ACO no. Para que la comparación sea justa, a la mejor solución de cada corrida del GA y del ACO también se le aplica el mismo 2-opt dentro de cada ruta, y se reportan ambos valores: el del algoritmo puro y el pulido. Los hiperparámetros se eligen con el valor puro, que es el que depende de ellos.

## 4. Diseño experimental

| | Algoritmo genético | Colonia de hormigas |
|---|---|---|
| Factores | Puntos de cruce {1, 2} × p_m {0.1, 0.2, 0.4} × selección {torneo, ruleta} | α {1, 2} × β {2, 5} × ρ {0.1, 0.5} |
| Combinaciones | 12 | 8 |
| Corridas por combinación e instancia | 5 (semillas 0–4) | 5 (semillas 0–4) |
| Total de corridas | 12 × 24 × 5 = 1,440 | 8 × 24 × 5 = 960 |
| Presupuesto por corrida | 50,000 soluciones evaluadas | 50,000 soluciones evaluadas |

**Métricas.**

- **Calidad:** GAP = 100 · (z − BKS) / BKS, promedio de las 5 corridas.
- **Tiempo de cómputo:** segundos de pared por corrida, sin contar la lectura de la instancia ni el pulido 2-opt.
- **Número de iteraciones:** generación (GA) o iteración (ACO) en la que apareció la mejor solución de la corrida. Como el paro es fijo, esta es la medida de qué tan rápido converge cada configuración; una iteración del GA evalúa 50 soluciones y una del ACO 25.

**Cómo se decide el mejor nivel.** Promediar GAP de instancias muy distintas deja que las difíciles dominen; por eso, además del GAP medio, se usa el **rango medio**: en cada instancia se ordenan las configuraciones de mejor a peor (1 = mejor) y se promedia ese lugar. La significancia se prueba sobre las 24 instancias emparejadas: prueba de Friedman para comparar todas las configuraciones o los tres niveles de p_m, y prueba de rangos con signo de Wilcoxon para los factores de dos niveles (Derrac et al., 2011). Se usa α = 0.05.

**Equipo.** Python 3.13 con NumPy y Numba (núcleos compilados), Intel Xeon a 2.8 GHz, Linux, dos corridas en paralelo. Todos los algoritmos se midieron en el mismo equipo y en las mismas condiciones, así que los tiempos son comparables entre sí, pero no con los de otro equipo.
