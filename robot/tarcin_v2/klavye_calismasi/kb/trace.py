import sys, math, json; sys.path.insert(0,'.')
import kbsim, rgait, numpy as np, mujoco, tarcin as T
def trace(sp, tmax=3.0, every=0.05, kb=None, hd=0, x0=0, y0=0):
    r=kbsim.Run(kb,hd,x0,y0)
    s=r.s; c=rgait.Rough(sp)
    pawg=set(r.paw_gid)
    t0=s.d.time
    for i in range(int(tmax/T.DT)):
        t=s.d.time-t0
        tg=c(t,s,r); s.step(tg)
        if i%int(every/T.DT)==0:
            R=s.d.xmat[s.bid].reshape(3,3)
            roll=math.degrees(math.asin(R[2,0])); pitch=math.degrees(math.asin(R[2,1]))
            con=set(); other=set()
            for k in range(s.d.ncon):
                cc=s.d.contact[k]
                n1,n2=s.m.geom(cc.geom1).name,s.m.geom(cc.geom2).name
                for g in (cc.geom1,cc.geom2):
                    if g in pawg: con.add(T.LEGS[r.paw_gid.index(g)])
                if cc.geom1 not in pawg and cc.geom2 not in pawg: other.add(n1.replace('_hull','')+'/'+n2.replace('_hull',''))
            PW=r.paws()
            print(f"t{t:5.2f} roll {roll:6.1f} pitch {pitch:6.1f} prog {r.progress()*1000:6.1f} paws z {np.round(PW[:,2]*1000,1)} con {''.join(sorted(con))} other {sorted(other)}")
            if R[2,2]<0.7: break
if __name__=='__main__':
    trace(json.loads(sys.argv[1]), float(sys.argv[2]) if len(sys.argv)>2 else 3.0)
