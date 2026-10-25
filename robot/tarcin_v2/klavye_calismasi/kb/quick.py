import sys, json; sys.path.insert(0,'.')
import kbd, kbsim, ctrl, rgait, batch
from multiprocessing import Pool
def one(a):
    name, sp, ter = a
    if ter=='flat': kb=None; hd,x0,y0,yj=0,0,0,0
    elif ter=='slope5': kb=kbd.Slope(5, mu=0.4); hd,x0,y0,yj=0,60,200,0
    elif ter=='up5': kb=kbd.Slope(5, mu=0.4); hd,x0,y0,yj=90,300,60,0
    else:
        k,mode,sd,mu=ter.split(':'); sd=int(sd); mu=float(mu)
        kb=kbd.Keyboard(k,"real" if mode=="rows" else "field",seed=sd,mu=mu); hd,x0,y0,yj,_=batch.start(k,mode,sd,kb)
    r=kbsim.Run(kb, hd, x0, y0, yaw_jitter_deg=yj, target_mm=250)
    c = ctrl.Baseline(**sp) if name.startswith('BASE') else rgait.Rough(sp)
    o=r.go(c, t_max=float(sp.get('tmax',20)) if isinstance(sp,dict) else 20, log_every=1.0)
    return f"{name:44s} {ter:14s} {o['result']:10s} t{o['t']:5.1f} prog {o['progress_mm']:6.1f} lat {o['lat_mm']:6.1f} yaw {o['yaw_err_deg']:6.1f} v {o['speed_cm_s']:5.2f} knee sat {o['knee']['sat']:.3f} hip sat {o['hip']['sat']:.3f} tilt {o['maxtilt_deg']}"
if __name__=='__main__':
    cases=json.loads(sys.argv[1]); ters=sys.argv[2].split(',')
    jobs=[(n,sp,t) for n,sp in cases for t in ters]
    with Pool(4) as P:
        for line in P.imap(one, jobs): print(line, flush=True)
