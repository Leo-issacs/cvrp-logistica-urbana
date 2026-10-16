"""CVRP: modelo de arcos y carga fisica (PuLP/CBC) y ahorros de Clarke-Wright + 2-opt.
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

class ResultadoNoOptimo(RuntimeError):
    """El solver no entrego un optimo probado y el llamador lo exigio."""
    def __init__(self, estado, mensaje):
        super().__init__(f'{estado}: {mensaje}'); self.estado = estado

MODELOS = {'A': 'vigente historico: 1 013 restricciones de subrutas (8) + f <= Q x',
           'B': 'sin restricciones explicitas de subrutas; f <= Q x',
           'C': 'experimental: como B con q_j x <= f <= (Q - q_i) x'}

def clasificar_estado(status, sol_status):
    """Estado de la corrida a partir de PuLP. LpStatus por si solo NO certifica nada:
    PuLP informa 'Optimal' tambien cuando CBC se detiene por tiempo con una solucion entera.
    Devuelve (estado, causa)."""
    if status == pulp.LpStatusOptimal and sol_status == pulp.LpSolutionOptimal:
        return 'optimo_probado', None
    if sol_status == pulp.LpSolutionIntegerFeasible:
        return 'factible_sin_prueba', 'limite de tiempo con solucion entera'
    if status == pulp.LpStatusInfeasible or sol_status == pulp.LpSolutionInfeasible:
        return 'sin_solucion_factible', 'modelo infactible'
    if status == pulp.LpStatusNotSolved and sol_status == pulp.LpSolutionNoSolutionFound:
        return 'sin_solucion_factible', 'sin solucion entera al terminar el limite'
    return 'fallo_solver', f'LpStatus={pulp.LpStatus.get(status, status)}, sol_status={sol_status}'

def construir_modelo(q,Q,depot,d,modelo='B',fixed_k=None):
    """Modelo de arcos x y carga fisica f. modelo: A, B o C (ver MODELOS).
    Eliminar las subrutas explicitas (B, C) es valido solo si toda demanda de cliente es
    positiva: sumando el balance de producto (5) sobre un conjunto aislado S los flujos
    internos se cancelan y queda 0 = suma de q_i en S > 0, imposible. Con una demanda nula
    un ciclo aislado de clientes sin demanda seria factible: en ese caso se exige modelo A."""
    if modelo not in MODELOS: raise ValueError(f'modelo desconocido: {modelo}')
    V=sorted(q); C=[i for i in V if i!=depot]
    if modelo!='A' and any(q[i]<=0 for i in C):
        raise ValueError('el modelo '+modelo+' requiere demandas de clientes positivas; use el modelo A (con subrutas)')
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
        if modelo=='C':
            model += f[i,j]<=(Q-q[i])*x[i,j], f'capacidad_{i}_{j}'
            model += f[i,j]>=q[j]*x[i,j], f'carga_minima_{i}_{j}'
        else:
            model += f[i,j]<=Q*x[i,j], f'capacidad_{i}_{j}'
    n_sec=0
    if modelo=='A':
        for size in range(2,len(C)+1):
            for S in it.combinations(C,size):
                model += pulp.lpSum(x[i,j] for i in S for j in S if i!=j)<=len(S)-1, f'subtour_{n_sec}'
                n_sec+=1
    return model,x,f,A,C,n_sec

def reconstruir(x,A,C,depot,n_nodos,tol=1e-6):
    """Rutas a partir de x. Rechaza valores ausentes o fraccionarios en vez de redondearlos."""
    vals={a:x[a].value() for a in A}
    if any(v is None or min(abs(v),abs(v-1))>tol for v in vals.values()):
        raise ValueError('el solver devolvio valores ausentes o fraccionarios en x')
    successor={i:j for i,j in A if i!=depot and vals[i,j]>0.5}
    routes=[]
    for first in sorted(j for j in C if vals[depot,j]>0.5):
        route=[depot,first]
        while route[-1]!=depot:
            if len(route)>n_nodos: raise ValueError('ciclo que no regresa al deposito')
            route.append(successor[route[-1]])
        routes.append(route)
    return routes

def leer_log_cbc(path):
    """Cota inferior, brecha, nodos, iteraciones y estado textual del registro de CBC."""
    import re
    t=Path(path).read_text(errors='replace')
    g=lambda p:(re.search(p,t) or [None,None])[1]
    num=lambda s:None if s is None else float(s)
    return {'resultado_cbc':g(r'Result - (.+)'),'objetivo_log':num(g(r'Objective value:\s+(\S+)')),
            'cota_inferior':num(g(r'Lower bound:\s+(\S+)')),'brecha_cbc':num(g(r'Gap:\s+(\S+)')),
            'nodos':num(g(r'Enumerated nodes:\s+(\S+)')),'iteraciones':num(g(r'Total iterations:\s+(\S+)')),
            'relajacion_inicial':num(g(r'Continuous objective value is (\S+)'))}

def exacto(q,Q,depot,d,log=None,fixed_k=None,limite=120,exigir_optimo=True,modelo='B'):
    """Resuelve con CBC. Devuelve (rutas | None, info). info['estado'] es uno de:
    optimo_probado, factible_sin_prueba, sin_solucion_factible, fallo_solver.
    Si exigir_optimo y el estado no es optimo_probado se lanza ResultadoNoOptimo.
    Tiempos: build_s (modelo), solve_s (CBC), reconstruct_s (rutas) y total_s = suma,
    el mismo tramo que cronometra el script historico. La verificacion posterior queda fuera."""
    start=time.perf_counter()
    model,x,f,A,C,n_sec=construir_modelo(q,Q,depot,d,modelo,fixed_k)
    t_build=time.perf_counter()
    build=t_build-start
    info={'modelo':modelo,'fixed_k':fixed_k,'limite_s':limite,'build_s':build,'solve_s':None,'reconstruct_s':None,
          'variables':len(model.variables()),'constraints':len(model.constraints),'sec':n_sec,
          'estado':None,'causa':None,'status':None,'sol_status':None,'optimo_probado':False,'objetivo':None}
    solver=pulp.PULP_CBC_CMD(msg=False,threads=0,gapRel=0,gapAbs=0,timeLimit=limite,
                            logPath=str(log) if log else None)
    routes=None
    try:
        status=model.solve(solver)
    except (pulp.PulpSolverError,OSError) as e:
        info.update(estado='fallo_solver',causa=f'{type(e).__name__}: {e}',solve_s=time.perf_counter()-t_build)
    else:
        info['solve_s']=time.perf_counter()-t_build
        info['status']=pulp.LpStatus[status]; info['sol_status']=model.sol_status
        info['estado'],info['causa']=clasificar_estado(status,model.sol_status)
        if info['estado'] in ('optimo_probado','factible_sin_prueba'):
            t_rec=time.perf_counter()
            try:
                routes=reconstruir(x,A,C,depot,len(q))
                info['objetivo']=pulp.value(model.objective)
            except (ValueError,KeyError) as e:
                routes=None; info.update(estado='fallo_solver',causa=str(e))
            info['reconstruct_s']=time.perf_counter()-t_rec
    info['optimo_probado']=info['estado']=='optimo_probado'
    info['total_s']=sum(info[k] or 0.0 for k in ('build_s','solve_s','reconstruct_s'))  # = tramo medido, sin verificacion
    if log and Path(log).exists(): info.update(leer_log_cbc(log))
    if info['estado'] in ('optimo_probado','factible_sin_prueba'):
        # Verificacion fuera del cronometro: carga real en cada arco seleccionado y restricciones.
        for route in routes:
            remaining=sum(q[i] for i in route)
            for i,j in zip(route,route[1:]):
                assert abs(f[i,j].value()-remaining)<1e-6
                remaining-=q[j]
        assert max(abs(c.value()) if c.sense==0 else max(0,-c.value()*c.sense)
                   for c in model.constraints.values())<1e-5
    if exigir_optimo and info['estado']!='optimo_probado':
        raise ResultadoNoOptimo(info['estado'],info['causa'] or 'sin detalle')
    return routes,info

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

def resumen(vals):
    if not vals: return None
    return {'n':len(vals),'media':statistics.mean(vals),'mediana':statistics.median(vals),
            'desv_est':statistics.stdev(vals) if len(vals)>1 else 0.0,'min':min(vals),'max':max(vals)}

def main():
    ap=argparse.ArgumentParser(description='CVRP: modelo de arcos y carga (CBC) frente a Clarke-Wright + 2-opt')
    ap.add_argument('instance'); ap.add_argument('--out',default='resultados')
    ap.add_argument('--modelo',choices=sorted(MODELOS),default='B',
                    help='B (predeterminado): sin subrutas explicitas; A: reproduce la evidencia historica; C: experimental')
    ap.add_argument('--repeticiones',type=int,default=10,help='repeticiones medidas por caso (tras el calentamiento)')
    ap.add_argument('--limite-libre',type=float,default=120,help='segundos de CBC por corrida sin flota fija')
    ap.add_argument('--limite-tres-rutas',type=float,default=120,help='segundos de CBC por corrida con exactamente tres rutas')
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    xy,q,Q,depot=leer(args.instance);d=matriz(xy);mod=args.modelo
    # Certificacion independiente (fuera de todo cronometro).
    z_dp=certificar_dp(q,Q,depot,d); z3_dp,_=particion_optima(q,Q,depot,d,k=3)
    # Calentamiento descartado: un caso libre, uno de tres rutas y la heuristica.
    exacto(q,Q,depot,d,modelo=mod,limite=args.limite_libre,exigir_optimo=False)
    exacto(q,Q,depot,d,modelo=mod,fixed_k=3,limite=args.limite_tres_rutas,exigir_optimo=False); heuristica(q,Q,depot,d)
    filas=[]; libre_rows=heur_rows=tres_rows=None
    for caso,k,lim in (('libre',None,args.limite_libre),('tres_rutas',3,args.limite_tres_rutas)):
        for rep in range(1,args.repeticiones+1):
            routes,t=exacto(q,Q,depot,d,out/(f'cbc_{caso}_{rep:02}.log'),fixed_k=k,limite=lim,exigir_optimo=False,modelo=mod)
            rows=verificar(routes,q,Q,depot,d) if routes else None
            z=sum(r['distancia'] for r in rows) if rows else None
            hz=None
            if caso=='libre':
                t0=time.perf_counter(); hr=heuristica(q,Q,depot,d); hz=time.perf_counter()-t0
                hrows=verificar(hr,q,Q,depot,d)
                heur_rows=hrows
            print(f"{caso} {rep}: {t['estado']} z={z} total={t['total_s']:.3f}s"+(f" heuristica={hz*1000:.3f}ms" if hz is not None else ''),flush=True)
            filas.append({'caso':caso,'repeticion':rep,**{k2:t.get(k2) for k2 in ('modelo','estado','causa','status','sol_status','optimo_probado',
                          'objetivo','cota_inferior','brecha_cbc','nodos','iteraciones','relajacion_inicial','build_s','solve_s','reconstruct_s','total_s',
                          'limite_s','variables','constraints','sec')},'z_exacto':z,'heuristica_s':hz,'z_heuristica':sum(r['distancia'] for r in hrows) if hz is not None else None})
            if rep==1:
                if caso=='libre': libre_rows=rows
                else: tres_rows=rows
    with (out/'mediciones.csv').open('w',newline='',encoding='utf8') as fh:  # la evidencia se guarda siempre
        w=csv.DictWriter(fh,fieldnames=list(filas[0]));w.writeheader();w.writerows(filas)
    sin_solucion=[f"{f['caso']} {f['repeticion']}: {f['estado']} ({f['causa']})" for f in filas if f['z_exacto'] is None]
    if sin_solucion:
        raise SystemExit('CBC no entrego solucion en algunas corridas (ver mediciones.csv y cbc_*.log); no se calculan estadisticas ni porcentajes:\n  '+'\n  '.join(sin_solucion))
    rounded=matriz(xy,True); rr,rt=exacto(q,Q,depot,rounded,modelo=mod,exigir_optimo=False)
    redondeada=verificar(rr,q,Q,depot,rounded) if rr else None
    libre=[f for f in filas if f['caso']=='libre']; tres=[f for f in filas if f['caso']=='tres_rutas']
    def stats(grupo):
        s={k2:resumen([f[k2] for f in grupo if f[k2] is not None]) for k2 in ('build_s','solve_s','reconstruct_s','total_s')}
        s['optimo_probado']=f"{sum(1 for f in grupo if f['estado']=='optimo_probado')}/{len(grupo)}"
        s['estados']={e:sum(1 for f in grupo if f['estado']==e) for e in sorted({f['estado'] for f in grupo})}
        return s
    est_libre,est_tres=stats(libre),stats(tres)
    est_h=resumen([f['heuristica_s'] for f in libre])
    ze=libre[0]['z_exacto']; zh=libre[0]['z_heuristica']; z3=z3_dp  # el sobrecosto usa el optimo certificado de 3 rutas
    te,th=est_libre['total_s']['media'],est_h['media']
    result={'esquema':2,'modelo':mod,'descripcion_modelo':MODELOS[mod],
            'configuracion':{'calentamiento':'1 corrida libre + 1 de tres rutas + 1 heuristica, descartadas','repeticiones':args.repeticiones,
                             'limite_libre_s':args.limite_libre,'limite_tres_rutas_s':args.limite_tres_rutas,
                             'cbc':{'threads':0,'gapRel':0,'gapAbs':0},
                             'tiempo_exacto':'build_s + solve_s + reconstruct_s; sin lectura, matriz, verificacion, certificacion ni figuras',
                             'tiempo_heuristica':'ahorros + fusiones + 2-opt'},
            'entorno':{'python':platform.python_version(),'pulp':pulp.__version__,'sistema':platform.platform(),
                       'procesador':platform.processor(),'solver':Path(pulp.PULP_CBC_CMD().path).name+' (incluido en PuLP)','fecha':datetime.date.today().isoformat()},
            'xy':xy,'demanda':q,'capacidad':Q,'deposito':depot,
            'exacto':libre_rows,'heuristica':heur_rows,'tres_rutas':tres_rows,'tres_rutas_estado_primera_repeticion':tres[0]['estado'],
            'distancia_redondeada_sensibilidad':redondeada,
            'certificacion_dp':{'libre':z_dp,'tres_rutas':z3_dp},
            'estadisticas':{'exacto_libre':est_libre,'exacto_tres_rutas':est_tres,'heuristica_s':est_h},
            'porcentajes':{
                'gap_costo_pct':{'valor':100*(zh-ze)/ze,'formula':'100 (Z_heur - Z_exacto) / Z_exacto','denominador':'Z_exacto = %.10f'%ze},
                'reduccion_distancia_vs_heuristica_pct':{'valor':100*(zh-ze)/zh,'formula':'100 (Z_heur - Z_exacto) / Z_heur','denominador':'Z_heur = %.10f'%zh},
                'reduccion_tiempo_heuristica_pct':{'valor':100*(te-th)/te,'formula':'100 (t_exacto - t_heur) / t_exacto','denominador':'t_exacto medio = %.6f s'%te},
                'razon_tiempos_exacto_sobre_heuristica':te/th,
                'sobrecosto_tres_rutas_pct':{'valor':100*(z3-ze)/ze,'formula':'100 (Z_3_certificado - Z_libre) / Z_libre','denominador':'Z_exacto = %.10f'%ze}}}
    (out/'resultados.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    with (out/'matriz_costos.csv').open('w',newline='',encoding='utf8') as fh:
        w=csv.writer(fh);w.writerow(['nodo']+list(xy));w.writerows([[i]+[d[i,j] for j in xy] for i in xy])
    plot_routes(libre_rows,xy,depot,out/'rutas_exactas.png','Solución exacta · CVRP de 10 clientes')
    plot_routes(heur_rows,xy,depot,out/'rutas_heuristica.png','Ahorros de Clarke–Wright + 2-opt')
    plot_routes(tres_rows,xy,depot,out/'rutas_tres.png','Escenario de flota mínima · 3 rutas')
    print(json.dumps({'estadisticas':{'libre_total_s':est_libre['total_s'],'tres_total_s':est_tres['total_s'],'heuristica_s':est_h},'porcentajes':result['porcentajes']},ensure_ascii=False,indent=1))

if __name__=='__main__': main()
