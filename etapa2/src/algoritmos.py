"""GA y ACO sobre permutaciones de clientes, con decodificador Split comun.
Solo biblioteca estandar; distancias continuas; flota no prefijada.
"""
import random


def split(p, q, Q, depot, d):
    """Particion de menor distancia para el orden p; O(n^2)."""
    n = len(p)
    dp, prev = [0.] + [float('inf')] * n, [-1] * (n + 1)
    for i in range(n):
        load, length = 0, 0.
        for j in range(i, n):
            load += q[p[j]]
            if load > Q:
                break
            length += d[depot, p[j]] if j == i else d[p[j-1], p[j]]
            value = dp[i] + length + d[p[j], depot]
            if value < dp[j+1] - 1e-12:
                dp[j+1], prev[j+1] = value, i
    routes, j = [], n
    while j:
        i = prev[j]
        if i < 0:
            raise ValueError('Demanda individual superior a la capacidad')
        routes.append([depot] + list(p[i:j]) + [depot])
        j = i
    return dp[n], routes[::-1]


def ox(a, b, rng):
    """Order crossover: conserva un segmento y el orden circular restante."""
    n = len(a)
    lo, hi = sorted(rng.sample(range(n), 2))
    hi += 1
    child = [None] * n
    child[lo:hi] = a[lo:hi]
    rest = [v for v in b[hi:] + b[:hi] if v not in child]
    for pos, value in zip(list(range(hi, n)) + list(range(lo)), rest):
        child[pos] = value
    return child


def ga(q, Q, depot, d, seed, pop=20, steps=100, pc=.9, pm=.2):
    rng = random.Random(seed)
    clients = sorted(set(q) - {depot})
    evaluate = lambda p: split(p, q, Q, depot, d)[0]
    population = [rng.sample(clients, len(clients)) for _ in range(pop)]
    costs = [evaluate(p) for p in population]
    history = [min(costs)]
    for _ in range(steps - 1):
        def tournament():
            inds = rng.sample(range(pop), 2)





            return population[min(inds, key=lambda i: costs[i])]
        children = []
        for _ in range(pop):
            a, b = tournament(), tournament()
            h = ox(a, b, rng) if rng.random() < pc else a[:]
            if rng.random() < pm:
                i, j = sorted(rng.sample(range(len(h)), 2))
                h[i:j+1] = h[i:j+1][::-1]
            children.append(h)
        child_costs = [evaluate(p) for p in children]
        # Dos elites anteriores y los 18 mejores hijos: siempre 20 individuos.
        old = sorted(zip(costs, population), key=lambda t: t[0])[:2]
        new = sorted(zip(child_costs, children), key=lambda t: t[0])[:pop-2]
        ranked = sorted(old + new, key=lambda t: t[0])
        costs, population = map(list, zip(*ranked))
        history.append(min(costs))
    best = population[min(range(pop), key=lambda i: costs[i])]
    z, routes = split(best, q, Q, depot, d)
    return z, routes, history


def aco(q, Q, depot, d, seed, ants=20, steps=100,
        alpha=1., beta=2., rho=.2, tau0=.01, deposit=1.):
    """Ant System sobre ordenes gigantes, no construccion capacitada voraz.
    La feromona aprende las adyacencias de la permutacion y Split fija retornos.
    """
    rng = random.Random(seed)
    clients = sorted(set(q) - {depot})
    tau = {(i, j): tau0 for i in q for j in q if i != j}
    best, best_routes, history = float('inf'), None, []
    for _ in range(steps):
        solutions = []
        for _ in range(ants):
            left, p, current = clients[:], [], depot
            while left:
                weights = [tau[current, j]**alpha * (1/d[current, j])**beta
                           for j in left]
                nxt = rng.choices(left, weights=weights, k=1)[0]
                p.append(nxt)
                left.remove(nxt)
                current = nxt
            z, routes = split(p, q, Q, depot, d)
            solutions.append((p, z))
            if z < best - 1e-12:
                best, best_routes = z, routes
        for edge in tau:
            tau[edge] = max(1e-12, (1-rho)*tau[edge])
        for p, z in solutions:
            # Transiciones del orden gigante, incluidas sus conexiones al deposito.
            tour = [depot] + p + [depot]
            for i, j in zip(tour, tour[1:]):
                tau[i, j] += deposit/z
                tau[j, i] += deposit/z
        history.append(best)
    return best, best_routes, history
