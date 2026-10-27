"""Certificación exacta por programación dinámica sobre subconjuntos (instancias de hasta ~12 clientes).

1) Held-Karp desde el depósito: g[S][j] = costo mínimo de salir del depósito, visitar S y terminar en j.
2) c(S) = min_j g[S][j] + d(j, depósito): mejor ruta que atiende exactamente S (si carga(S) <= Q).
3) f(S) = min_{T ⊆ S, T contiene al menor cliente de S, carga(T) <= Q} c(T) + f(S \\ T).
"""
def cvrp_exacto(q, Q, depot, d):
    cl = sorted(set(q) - {depot})
    n = len(cl)
    full = (1 << n) - 1
    INF = float('inf')
    carga = [0] * (1 << n)
    for S in range(1, 1 << n):
        b = (S & -S).bit_length() - 1
        carga[S] = carga[S & (S - 1)] + q[cl[b]]
    g = [[INF] * n for _ in range(1 << n)]
    for j in range(n):
        g[1 << j][j] = d[depot, cl[j]]
    for S in range(1, 1 << n):
        if carga[S] > Q:
            continue
        for j in range(n):
            v = g[S][j]
            if v == INF:
                continue
            for k in range(n):
                if S >> k & 1:
                    continue
                T = S | 1 << k
                if carga[T] <= Q and v + d[cl[j], cl[k]] < g[T][k]:
                    g[T][k] = v + d[cl[j], cl[k]]
    ruta = [INF] * (1 << n)
    for S in range(1, 1 << n):
        if carga[S] <= Q:
            ruta[S] = min(g[S][j] + d[cl[j], depot] for j in range(n) if S >> j & 1)
    f = [INF] * (1 << n)
    elec = [0] * (1 << n)
    f[0] = 0.
    for S in range(1, 1 << n):
        low = S & -S
        rest = S ^ low
        T = rest
        while True:
            sub = T | low
            if ruta[sub] < INF and ruta[sub] + f[S ^ sub] < f[S]:
                f[S], elec[S] = ruta[sub] + f[S ^ sub], sub
            if T == 0:
                break
            T = (T - 1) & rest
    grupos, S = [], full
    while S:
        grupos.append(sorted(cl[j] for j in range(n) if elec[S] >> j & 1))
        S ^= elec[S]
    return f[full], grupos
