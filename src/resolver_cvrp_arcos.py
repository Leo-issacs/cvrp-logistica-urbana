"""CVRP: modelo de arcos y carga fisica (PuLP/CBC), SEC y ahorros + 2-opt.
Uso: python src/resolver_cvrp_arcos.py data/instancia.txt --out results/reproduccion_<fecha>
Dependencias: pulp==3.3.0, matplotlib. Distancia euclidiana sin redondeo.

Cambios respecto del script que genero results/ (conservado en
archive/v2_arcos_script_de_la_revision/): el escenario de tres rutas ya no se
presenta como optimo por el solo hecho de que PuLP devuelva "Optimal"; se
registra si CBC probo optimalidad y el optimo de tres rutas se certifica por
particion (programacion dinamica). Ver docs/coherencia.md.
"""
import argparse, csv, datetime, itertools as it, json, math, platform, statistics, time
from pathlib import Path
import pulp

def leer(path):
    xy, q, mode, Q, depot = {}, {}, '', None, None
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        s=line.strip()
        if s.startswith('CAPACITY'): Q=int(s.split(':')[1])
        elif s in ('NODE_COORD_SECTION','DEMAND_SECTION','DEPOT_SECTION'): mode=s
        elif s in ('EOF','-1'): mode=''
        elif s and ':' not in s:
            a=s.split()
            if mode=='NODE_COORD_SECTION': xy[int(a[0])]=tuple(map(float,a[1:3]))
            elif mode=='DEMAND_SECTION': q[int(a[0])]=int(a[1])
            elif mode=='DEPOT_SECTION': depot=int(a[0])
    assert Q and depot in xy and set(q)==set(xy)
    assert q[depot]==0 and all(0 < q[i] <= Q for i in xy if i!=depot)
    return xy,q,Q,depot

def matriz(xy, rounded=False):
    return {(i,j): (math.floor(math.dist(xy[i],xy[j])+0.5) if rounded
                    else math.dist(xy[i],xy[j])) for i in xy for j in xy}

def costo(route,d): return sum(d[a,b] for a,b in zip(route,route[1:]))

def enumerar(q,Q,depot,d):
    """Una ruta optima por subconjunto factible: exhaustivo, no heuristico."""
    clients=sorted(set(q)-{depot}); cols=[]
    for k in range(1,len(clients)+1):
        for subset in it.combinations(clients,k):
            if sum(q[i] for i in subset)>Q: continue
            candidates=((depot,)+p+(depot,) for p in it.permutations(subset)
                        if len(p)==1 or p[0]<p[-1])
            route=min(candidates,key=lambda r:(costo(r,d),r))
            cols.append((subset,route,costo(route,d)))
    return cols

def exacto(q,Q,depot,d,log=None,fixed_k=None,limite=120,exigir_optimo=True):
    """Arcos x y carga fisica f; SEC explicitas para esta instancia pequena."""
    start=time.perf_counter()
    V=sorted(q); C=[i for i in V if i!=depot]
    A=[(i,j) for i in V for j in V if i!=j]
    model=pulp.LpProblem('CVRP_arcos_carga',pulp.LpMinimize)
    x=pulp.LpVariable.dicts('x',A,cat='Binary')
    f=pulp.LpVariable.dicts('f',A,lowBound=0)
    model += pulp.lpSum(d[i,j]*x[i,j] for i,j in A), 'distancia'
    for i in C:
        model += pulp.lpSum(x[j,i] for j in V if j!=i)==1, f'visita_{i}'
        model += pulp.lpSum(x[i,j] for j in V if j!=i)==pulp.lpSum(x[j,i] for j in V if j!=i), f'continuidad_{i}'
        model += pulp.lpSum(f[j,i] for j in V if j!=i)-pulp.lpSum(f[i,j] for j in V if j!=i)==q[i], f'entrega_{i}'
        model += f[i,depot]==0, f'regreso_vacio_{i}'
    m=pulp.lpSum(x[depot,j] for j in C)
    model += m==pulp.lpSum(x[i,depot] for i in C), 'balance_deposito'
    model += m>=math.ceil(sum(q.values())/Q), 'flota_minima_cota'
    model += m<=len(C), 'flota_maxima'
    model += pulp.lpSum(f[depot,j] for j in C)==sum(q.values()), 'carga_inicial_total'
    if fixed_k is not None: model += m==fixed_k, 'flota_fija'
    for i,j in A:
        model += f[i,j]<=Q*x[i,j], f'capacidad_{i}_{j}'
    n_sec=0
    for size in range(2,len(C)+1):
        for S in it.combinations(C,size):
            model += pulp.lpSum(x[i,j] for i in S for j in S if i!=j)<=len(S)-1, f'subtour_{n_sec}'
            n_sec+=1
    build=time.perf_counter()-start
    solver=pulp.PULP_CBC_CMD(msg=False,threads=0,gapRel=0,gapAbs=0,timeLimit=limite,
                            logPath=str(log) if log else None)
    ts=time.perf_counter();status=model.solve(solver);solve=time.perf_counter()-ts
    assert pulp.LpStatus[status]=='Optimal',pulp.LpStatus[status]
    # PuLP informa 'Optimal' tambien si CBC se detiene por tiempo con una solucion
    # entera; sol_status distingue el optimo probado de un incumbente.
    probado=model.sol_status==pulp.LpSolutionOptimal
    assert probado or not exigir_optimo,'CBC no probo optimalidad (limite de tiempo)'
    successor={i:j for i,j in A if i!=depot and x[i,j].value()>0.5}
    routes=[]
    for first in sorted(j for j in C if x[depot,j].value()>0.5):
        route=[depot,first]
        while route[-1]!=depot:
            assert len(route)<=len(V)
            route.append(successor[route[-1]])
        routes.append(route)
    total=time.perf_counter()-start
    # Verificacion fuera del cronometro: carga real en cada arco seleccionado.
    for route in routes:
        remaining=sum(q[i] for i in route)
        for i,j in zip(route,route[1:]):
            assert abs(f[i,j].value()-remaining)<1e-6
            remaining-=q[j]
    assert max(abs(c.value()) if c.sense==0 else max(0,-c.value()*c.sense)
               for c in model.constraints.values())<1e-5
    return routes,{'total_s':total,'build_s':build,'solve_s':solve,
                   'variables':len(model.variables()),'constraints':len(model.constraints),
                   'sec':n_sec,'status':pulp.LpStatus[status],'optimo_probado':probado,
                   'objetivo':pulp.value(model.objective)}

def dos_opt(route,d):
    while True:
        best=route; bestcost=costo(route,d)
        for a in range(1,len(route)-2):
            for b in range(a+1,len(route)-1):
                candidate=route[:a]+list(reversed(route[a:b+1]))+route[b+1:]
                z=costo(candidate,d)
                if z < bestcost-1e-10: best,bestcost=candidate,z
        if best is route: return route
        route=best

def heuristica(q,Q,depot,d):
    clients=sorted(set(q)-{depot}); routes=[[i] for i in clients]
    savings=sorted(((d[depot,i]+d[depot,j]-d[i,j],i,j)
                    for i,j in it.combinations(clients,2)),key=lambda t:(-t[0],t[1],t[2]))
    for s,i,j in savings:
        if s<=0: continue
        a=next(r for r in routes if i in r); b=next(r for r in routes if j in r)
        if a is b or i not in (a[0],a[-1]) or j not in (b[0],b[-1]): continue
        if sum(q[v] for v in a+b)>Q: continue
        aa=a if a[-1]==i else a[::-1]; bb=b if b[0]==j else b[::-1]
        routes.remove(a); routes.remove(b); routes.append(aa+bb)
    return [dos_opt([depot]+r+[depot],d) for r in routes]

def verificar(routes,q,Q,depot,d):
    visited=[i for r in routes for i in r[1:-1]]
    assert sorted(visited)==sorted(set(q)-{depot})
    assert all(r[0]==r[-1]==depot and sum(q[i] for i in r)<=Q for r in routes)
    return [{'ruta':r,'carga':sum(q[i] for i in r),'distancia':costo(r,d),
             'desperdicio_pct':100*(Q-sum(q[i] for i in r))/Q} for r in routes]

def particion_optima(q,Q,depot,d,k=None):
    """Particion optima de clientes en rutas (DP sobre subconjuntos).
    Con k exige exactamente k rutas. Devuelve (distancia, rutas)."""
    cols=enumerar(q,Q,depot,d); clients=sorted(set(q)-{depot})
    idx={c:n for n,c in enumerate(clients)}
    enc=[(sum(1<<idx[i] for i in s),z,r) for s,r,z in cols]
    full=(1<<len(clients))-1
    dp=[{} for _ in range(full+1)]; dp[0][0]=(0.0,None)
    for mask in range(1,full+1):
        first=mask & -mask
        for m,z,r in enc:
            if m&first and m&mask==m:
                for j,(zz,_) in dp[mask^m].items():
                    if j+1 not in dp[mask] or zz+z<dp[mask][j+1][0]-1e-12: dp[mask][j+1]=(zz+z,(m,r))
    j=k if k is not None else min(dp[full],key=lambda t:dp[full][t][0])
    z=dp[full][j][0]; mask=full; routes=[]
    while mask:
        _,(m,r)=dp[mask][j]; routes.append(list(r)); mask^=m; j-=1
    return z,sorted(routes)

def certificar_dp(q,Q,depot,d):
    """Verificacion independiente del solver: particion por programacion dinamica."""
    return particion_optima(q,Q,depot,d)[0]

def plot_routes(rows,xy,depot,path,title):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.2,5.2))
    for k,row in enumerate(rows,1):
        r=row['ruta']; ax.plot([xy[i][0] for i in r],[xy[i][1] for i in r],
             '-o',label=f"R{k}: carga {row['carga']}, distancia {row['distancia']:.2f}")
        for a,b in zip(r,r[1:]):
            ax.annotate('',xy=xy[b],xytext=xy[a],arrowprops=dict(arrowstyle='->',color=ax.lines[-1].get_color(),lw=1))
    for i,(x,y) in xy.items(): ax.annotate(str(i),(x,y),xytext=(5,5),textcoords='offset points')
    ax.scatter(*xy[depot],marker='s',s=110,color='black',zorder=5,label='Depósito 1')
    ax.set(xlabel='Coordenada x',ylabel='Coordenada y',title=title); ax.set_aspect('equal')
    ax.grid(alpha=.18); ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.13),ncol=2)
    fig.tight_layout(); fig.savefig(path,dpi=180,bbox_inches='tight'); plt.close(fig)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('instance'); ap.add_argument('--out',default='resultados')
    ap.add_argument('--limite-tres-rutas',type=float,default=120,help='segundos de CBC para el escenario de tres rutas')
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    xy,q,Q,depot=leer(args.instance);d=matriz(xy)
    # Una ejecucion de calentamiento para cada metodo, no contabilizada.
    exacto(q,Q,depot,d); heuristica(q,Q,depot,d)
    trials=[]
    for run in range(10):
        routes,t=exacto(q,Q,depot,d,out/f'cbc_{run+1:02}.log')
        t0=time.perf_counter(); hr=heuristica(q,Q,depot,d); ht=time.perf_counter()-t0
        erows=verificar(routes,q,Q,depot,d); hrows=verificar(hr,q,Q,depot,d)
        print(f"Ejecucion {run+1}: exacto={t['total_s']:.6f}s, heuristica={ht:.6f}s",flush=True)
        trials.append({'repeticion':run+1,**t,'heuristica_s':ht,
                      'z_exacto':sum(r['distancia'] for r in erows),
                      'z_heuristica':sum(r['distancia'] for r in hrows)})
    assert abs(certificar_dp(q,Q,depot,d)-trials[0]['z_exacto'])<1e-7
    rounded=matriz(xy,True); rr,_=exacto(q,Q,depot,rounded)
    rounded_rows=verificar(rr,q,Q,depot,rounded)
    three_cbc,t3=exacto(q,Q,depot,d,out/'cbc_3rutas.log',fixed_k=3,limite=args.limite_tres_rutas,exigir_optimo=False)
    z3,three=particion_optima(q,Q,depot,d,k=3)
    assert t3['objetivo']>=z3-1e-7
    result={'xy':xy,'demanda':q,'capacidad':Q,'deposito':depot,'exacto':erows,'heuristica':hrows,
            'repeticiones':trials,'distancia_redondeada_sensibilidad':rounded_rows,
            'entorno':{'python':platform.python_version(),'pulp':pulp.__version__,'sistema':platform.platform(),
                       'procesador':platform.processor(),'solver':Path(pulp.PULP_CBC_CMD().path).name+' (incluido en PuLP)','fecha':datetime.date.today().isoformat()},
            'dp_verificado':True,'tres_rutas':verificar(three,q,Q,depot,d),'tres_rutas_certificado_dp':z3,
            'tres_rutas_cbc_arcos':{**t3,'rutas':verificar(three_cbc,q,Q,depot,d)}}
    for key in ('total_s','build_s','solve_s','heuristica_s'):
        vals=[t[key] for t in trials]
        result[key]={'media':statistics.mean(vals),'mediana':statistics.median(vals),'desv_est':statistics.stdev(vals),'min':min(vals),'max':max(vals)}
    result['gap_costo_pct']=100*(trials[0]['z_heuristica']-trials[0]['z_exacto'])/trials[0]['z_exacto']
    result['gap_tiempo_pct']=100*(result['heuristica_s']['media']-result['total_s']['media'])/result['total_s']['media']
    (out/'resultados.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    with (out/'matriz_costos.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['nodo']+list(xy));w.writerows([[i]+[d[i,j] for j in xy] for i in xy])
    with (out/'mediciones.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(trials[0]));w.writeheader();w.writerows(trials)
    plot_routes(erows,xy,depot,out/'rutas_exactas.png','Solución exacta · CVRP de 10 clientes')
    plot_routes(hrows,xy,depot,out/'rutas_heuristica.png','Ahorros de Clarke–Wright + 2-opt')
    plot_routes(result['tres_rutas'],xy,depot,out/'rutas_tres.png','Escenario de flota mínima · 3 rutas')
    print(json.dumps({k:result[k] for k in ('total_s','heuristica_s','gap_costo_pct','gap_tiempo_pct')},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
