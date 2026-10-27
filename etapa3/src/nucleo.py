"""Núcleo numérico (numba) de la Etapa 3: Split, GA, ACO y 2-opt.

Mismo diseño que la Etapa 2 (permutación de clientes + decodificador Split), escalado a
instancias de 50 a 458 clientes. Nodo 0 = depósito; clientes 1..n.
"""
import numpy as np
from numba import njit

INF = 1e18


# ------------------------------------------------------------------ Split
@njit(cache=True)
def split_costo(p, d, q, Q, D, s):
    """Costo mínimo de partir el orden p en rutas que respetan capacidad Q y duración D."""
    n = p.shape[0]
    V = np.full(n + 1, INF)
    V[0] = 0.0
    for i in range(n):
        if V[i] >= INF:
            continue
        carga = 0
        largo = 0.0
        for j in range(i, n):
            c = p[j]
            carga += q[c]
            if carga > Q:
                break
            if j == i:
                largo = d[0, c]
            else:
                largo += d[p[j - 1], c]
            costo = largo + d[c, 0]
            if costo + s * (j - i + 1) > D + 1e-9:
                break
            v = V[i] + costo
            if v < V[j + 1] - 1e-12:
                V[j + 1] = v
    return V[n]


@njit(cache=True)
def split_pred(p, d, q, Q, D, s):
    n = p.shape[0]
    V = np.full(n + 1, INF)
    P = np.full(n + 1, -1, np.int64)
    V[0] = 0.0
    for i in range(n):
        if V[i] >= INF:
            continue
        carga = 0
        largo = 0.0
        for j in range(i, n):
            c = p[j]
            carga += q[c]
            if carga > Q:
                break
            if j == i:
                largo = d[0, c]
            else:
                largo += d[p[j - 1], c]
            costo = largo + d[c, 0]
            if costo + s * (j - i + 1) > D + 1e-9:
                break
            v = V[i] + costo
            if v < V[j + 1] - 1e-12:
                V[j + 1] = v
                P[j + 1] = i
    return V[n], P


def rutas_de(p, P):
    rutas, j = [], len(p)
    while j > 0:
        i = int(P[j])
        if i < 0:
            raise ValueError('orden sin partición factible')
        rutas.append([int(v) for v in p[i:j]])
        j = i
    return rutas[::-1]


# ------------------------------------------------------------------ 2-opt dentro de cada ruta
@njit(cache=True)
def dos_opt(r, d):
    """2-opt de mejor mejora sobre una ruta 0 -> r -> 0 (r sin depósitos). Devuelve r mejorada."""
    m = r.shape[0]
    t = np.empty(m + 2, np.int64)
    t[0] = 0
    t[m + 1] = 0
    t[1:m + 1] = r
    mejora = True
    while mejora:
        mejora = False
        mejor = -1e-9
        ba, bb = -1, -1
        for a in range(0, m):
            for b in range(a + 2, m + 1):
                delta = d[t[a], t[b]] + d[t[a + 1], t[b + 1]] - d[t[a], t[a + 1]] - d[t[b], t[b + 1]]
                if delta < mejor:
                    mejor, ba, bb = delta, a, b
        if ba >= 0:
            t[ba + 1:bb + 1] = t[ba + 1:bb + 1][::-1].copy()
            mejora = True
    return t[1:m + 1].copy()


# ------------------------------------------------------------------ operadores GA
@njit(cache=True)
def ox_dos_puntos(a, b):
    """OX clásico (Etapa 2): conserva a[lo..hi] y llena en el orden circular de b desde hi+1."""
    n = a.shape[0]
    lo = np.random.randint(n)
    hi = np.random.randint(n)
    if lo > hi:
        lo, hi = hi, lo
    hijo = np.empty(n, np.int64)
    usado = np.zeros(n + 1, np.bool_)
    for k in range(lo, hi + 1):
        hijo[k] = a[k]
        usado[a[k]] = True
    pos = (hi + 1) % n
    for t in range(n):
        v = b[(hi + 1 + t) % n]
        if not usado[v]:
            hijo[pos] = v
            pos = (pos + 1) % n
    return hijo


@njit(cache=True)
def ox_un_punto(a, b):
    """OX de un punto: conserva el prefijo a[0..c-1] y completa en el orden de b."""
    n = a.shape[0]
    c = 1 + np.random.randint(n - 1)
    hijo = np.empty(n, np.int64)
    usado = np.zeros(n + 1, np.bool_)
    for k in range(c):
        hijo[k] = a[k]
        usado[a[k]] = True
    pos = c
    for t in range(n):
        v = b[t]
        if not usado[v]:
            hijo[pos] = v
            pos += 1
    return hijo


@njit(cache=True)
def seleccion(costos, metodo, acum):
    """0 = torneo binario; 1 = ruleta con aptitud 1/costo (acum = probabilidades acumuladas)."""
    if metodo == 0:
        i = np.random.randint(costos.shape[0])
        j = np.random.randint(costos.shape[0])
        return i if costos[i] <= costos[j] else j
    u = np.random.random()
    k = np.searchsorted(acum, u)
    return min(k, costos.shape[0] - 1)


@njit(cache=True)
def vmc_aleatorizado(d, cand, r):
    """Vecino más cercano aleatorizado: en cada paso elige al azar uno de los r clientes
    no visitados más cercanos (según la lista de candidatos; si se agota, el más cercano)."""
    n = d.shape[0] - 1
    usado = np.zeros(n + 1, np.bool_)
    usado[0] = True
    p = np.empty(n, np.int64)
    cur = 0
    opciones = np.empty(r, np.int64)
    for k in range(n):
        m = 0
        for c in range(cand.shape[1]):
            j = cand[cur, c]
            if not usado[j]:
                opciones[m] = j
                m += 1
                if m == r:
                    break
        if m > 0:
            nxt = opciones[np.random.randint(m)]
        else:
            best, nxt = INF, -1
            for j in range(1, n + 1):
                if not usado[j] and d[cur, j] < best:
                    best, nxt = d[cur, j], j
        p[k] = nxt
        usado[nxt] = True
        cur = nxt
    return p


@njit(cache=True)
def ga(d, q, Q, D, s, semilla, pop, gens, pc, pm, metodo_sel, puntos, init_heur, cand):
    """GA de la Etapa 2 con hiperparámetros variables. init_heur=1 siembra la población con
    vecino más cercano aleatorizado (r=3); 0 = permutaciones aleatorias (Etapa 2).
    Devuelve mejor permutación, costo, generación en que se encontró e historial."""
    np.random.seed(semilla)
    n = d.shape[0] - 1
    P = np.empty((pop, n), np.int64)
    C = np.empty(pop)
    for k in range(pop):
        if init_heur == 1:
            P[k] = vmc_aleatorizado(d, cand, 3)
        else:
            P[k] = np.random.permutation(n) + 1
        C[k] = split_costo(P[k], d, q, Q, D, s)
    hist = np.empty(gens)
    ib = np.argmin(C)
    mejor, gen_mejor = C[ib], 0
    hist[0] = mejor
    H = np.empty((pop, n), np.int64)
    CH = np.empty(pop)
    acum = np.empty(pop)
    for g in range(1, gens):
        if metodo_sel == 1:
            apt = 1.0 / C
            acum[:] = np.cumsum(apt) / apt.sum()
        for k in range(pop):
            a = P[seleccion(C, metodo_sel, acum)]
            b = P[seleccion(C, metodo_sel, acum)]
            if np.random.random() < pc:
                h = ox_un_punto(a, b) if puntos == 1 else ox_dos_puntos(a, b)
            else:
                h = a.copy()
            if np.random.random() < pm:                       # mutación por inversión
                i = np.random.randint(n)
                j = np.random.randint(n)
                if i > j:
                    i, j = j, i
                h[i:j + 1] = h[i:j + 1][::-1].copy()
            H[k] = h
            CH[k] = split_costo(h, d, q, Q, D, s)
        # Reemplazo de la Etapa 2: 2 élites de la generación anterior + los pop-2 mejores hijos
        oe = np.argsort(C)[:2]
        oh = np.argsort(CH)[:pop - 2]
        NP = np.empty((pop, n), np.int64)
        NC = np.empty(pop)
        NP[0], NC[0] = P[oe[0]], C[oe[0]]
        NP[1], NC[1] = P[oe[1]], C[oe[1]]
        for k in range(pop - 2):
            NP[k + 2], NC[k + 2] = H[oh[k]], CH[oh[k]]
        P, C = NP, NC
        ib = np.argmin(C)
        if C[ib] < mejor - 1e-9:
            mejor, gen_mejor = C[ib], g
        hist[g] = mejor
    ib = np.argmin(C)
    return P[ib].copy(), C[ib], gen_mejor, hist


# ------------------------------------------------------------------ ACO
@njit(cache=True)
def vecino_mas_cercano(d):
    n = d.shape[0] - 1
    usado = np.zeros(n + 1, np.bool_)
    usado[0] = True
    p = np.empty(n, np.int64)
    cur = 0
    for k in range(n):
        best, bj = INF, -1
        for j in range(1, n + 1):
            if not usado[j] and d[cur, j] < best:
                best, bj = d[cur, j], j
        p[k] = bj
        usado[bj] = True
        cur = bj
    return p


@njit(cache=True)
def aco(d, q, Q, D, s, semilla, hormigas, iters, alfa, beta, rho, cand, tau0):
    """Ant System de la Etapa 2 (orden gigante + Split, depósito de todas las hormigas),
    con listas de candidatos para escalar la construcción. Devuelve mejor permutación,
    costo, iteración en que se encontró e historial."""
    np.random.seed(semilla)
    n = d.shape[0] - 1
    N = n + 1
    tau = np.full((N, N), tau0)
    eta = np.empty((N, N))
    for i in range(N):
        for j in range(N):
            eta[i, j] = 0.0 if i == j else (1.0 / max(d[i, j], 1e-9)) ** beta
    K = cand.shape[1]
    hist = np.empty(iters)
    mejor, it_mejor = INF, 0
    mejor_p = np.empty(n, np.int64)
    rutas_it = np.empty((hormigas, n), np.int64)
    costos_it = np.empty(hormigas)
    w = np.empty(N)
    for it in range(iters):
        for h in range(hormigas):
            visit = np.zeros(N, np.bool_)
            visit[0] = True
            cur = 0
            for k in range(n):
                tot = 0.0
                for c in range(K):
                    j = cand[cur, c]
                    if not visit[j]:
                        t = tau[cur, j] if alfa == 1.0 else tau[cur, j] ** alfa
                        w[c] = t * eta[cur, j]
                        tot += w[c]
                    else:
                        w[c] = 0.0
                nxt = -1
                if tot > 0.0:
                    u = np.random.random() * tot
                    acc = 0.0
                    for c in range(K):
                        acc += w[c]
                        if acc >= u and w[c] > 0.0:
                            nxt = cand[cur, c]
                            break
                    if nxt < 0:                                   # redondeo numérico
                        for c in range(K - 1, -1, -1):
                            if w[c] > 0.0:
                                nxt = cand[cur, c]
                                break
                else:                                             # lista agotada: ruleta sobre todos
                    tot = 0.0
                    for j in range(1, N):
                        if not visit[j]:
                            t = tau[cur, j] if alfa == 1.0 else tau[cur, j] ** alfa
                            tot += t * eta[cur, j]
                    u = np.random.random() * tot
                    acc = 0.0
                    for j in range(1, N):
                        if not visit[j]:
                            t = tau[cur, j] if alfa == 1.0 else tau[cur, j] ** alfa
                            acc += t * eta[cur, j]
                            nxt = j
                            if acc >= u:
                                break
                rutas_it[h, k] = nxt
                visit[nxt] = True
                cur = nxt
            costos_it[h] = split_costo(rutas_it[h], d, q, Q, D, s)
            if costos_it[h] < mejor - 1e-9:
                mejor, it_mejor = costos_it[h], it
                mejor_p[:] = rutas_it[h]
        for i in range(N):                                        # evaporación
            for j in range(N):
                v = (1.0 - rho) * tau[i, j]
                tau[i, j] = v if v > 1e-12 else 1e-12
        for h in range(hormigas):                                 # depósito (todas las hormigas)
            dep = 1.0 / costos_it[h]
            a = 0
            for k in range(n):
                b = rutas_it[h, k]
                tau[a, b] += dep
                tau[b, a] += dep
                a = b
            tau[a, 0] += dep
            tau[0, a] += dep
        hist[it] = mejor
    return mejor_p, mejor, it_mejor, hist


def listas_candidatos(d, k):
    N = d.shape[0]
    k = min(k, N - 2)
    dd = d.copy()
    np.fill_diagonal(dd, np.inf)
    dd[:, 0] = np.inf                                             # el depósito nunca es candidato
    return np.argsort(dd, axis=1)[:, :k].astype(np.int64)
