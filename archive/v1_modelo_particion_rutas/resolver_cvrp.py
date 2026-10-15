"""CVRP didactico: particion exacta de rutas (PuLP/CBC) y ahorros + 2-opt.
Uso: python resolver_cvrp.py instancia.txt --out resultados
Dependencias: pulp==3.3.0, matplotlib. Distancia euclidiana sin redondeo.
"""
import argparse, csv, itertools as it, json, math, platform, statistics, time
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

def exacto(q,Q,depot,d,log=None,fixed_k=None):
    start=time.perf_counter(); cols=enumerar(q,Q,depot,d)
    model=pulp.LpProblem('CVRP_particion',pulp.LpMinimize)
    y=pulp.LpVariable.dicts('ruta',range(len(cols)),cat='Binary')
    model += pulp.lpSum(c[2]*y[r] for r,c in enumerate(cols))
    for i in sorted(set(q)-{depot}):
        model += pulp.lpSum(y[r] for r,c in enumerate(cols) if i in c[0])==1
    if fixed_k is not None: model += pulp.lpSum(y.values())==fixed_k
    build=time.perf_counter()-start
    solver=pulp.PULP_CBC_CMD(msg=False,threads=0,gapRel=0,gapAbs=0,
                            logPath=str(log) if log else None)
    ts=time.perf_counter(); status=model.solve(solver); solve=time.perf_counter()-ts
    assert pulp.LpStatus[status]=='Optimal', pulp.LpStatus[status]
    routes=[list(c[1]) for r,c in enumerate(cols) if y[r].value()>0.5]
    return routes,{'total_s':time.perf_counter()-start,'build_s':build,
                   'solve_s':solve,'columns':len(cols),'status':pulp.LpStatus[status]}

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

def certificar_dp(q,Q,depot,d):
    """Verificacion independiente del solver: particion por programacion dinamica."""
    cols=enumerar(q,Q,depot,d); clients=sorted(set(q)-{depot})
    encoded=[(sum(1<<clients.index(i) for i in s),z) for s,_,z in cols]
    dp=[math.inf]*(1<<len(clients)); dp[0]=0
    for mask in range(1,len(dp)):
        first=mask & -mask
        dp[mask]=min(z+dp[mask^m] for m,z in encoded if m&first and m&mask==m)
    return dp[-1]

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
    ap=argparse.ArgumentParser(); ap.add_argument('instance'); ap.add_argument('--out',default='resultados'); args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    xy,q,Q,depot=leer(args.instance);d=matriz(xy)
    # Una ejecucion de calentamiento para cada metodo, no contabilizada.
    exacto(q,Q,depot,d); heuristica(q,Q,depot,d)
    trials=[]
    for run in range(10):
        routes,t=exacto(q,Q,depot,d,out/f'cbc_{run+1:02}.log')
        t0=time.perf_counter(); hr=heuristica(q,Q,depot,d); ht=time.perf_counter()-t0
        erows=verificar(routes,q,Q,depot,d); hrows=verificar(hr,q,Q,depot,d)
        trials.append({'repeticion':run+1,**t,'heuristica_s':ht,
                      'z_exacto':sum(r['distancia'] for r in erows),
                      'z_heuristica':sum(r['distancia'] for r in hrows)})
    assert abs(certificar_dp(q,Q,depot,d)-trials[0]['z_exacto'])<1e-7
    rounded=matriz(xy,True); rr,_=exacto(q,Q,depot,rounded)
    rounded_rows=verificar(rr,q,Q,depot,rounded)
    three,_=exacto(q,Q,depot,d,out/'cbc_3rutas.log',fixed_k=3)
    result={'xy':xy,'demanda':q,'capacidad':Q,'deposito':depot,'exacto':erows,'heuristica':hrows,
            'repeticiones':trials,'distancia_redondeada_sensibilidad':rounded_rows,
            'entorno':{'python':platform.python_version(),'pulp':pulp.__version__,'sistema':platform.platform(),
                       'procesador':platform.processor(),'solver':pulp.PULP_CBC_CMD().path},
            'dp_verificado':True,'tres_rutas':verificar(three,q,Q,depot,d)}
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
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
