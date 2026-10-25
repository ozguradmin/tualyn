import sys, math, json; sys.path.insert(0,'.')
import kbsim, gait as G, numpy as np, mujoco, tarcin as T
rf=G.rest_feet()
def test(lift_leg, H, shift_y=0.0, lev=False, verbose=False):
    r=kbsim.Run(None,0,0,0); s=r.s; t0=s.d.time
    L=G.Leveler(0.5,1.5)
    pawg=r.paw_gid
    res=[]
    def tg(t):
        u1=min(1,max(0,t/0.8)); u2=min(1,max(0,(t-0.8)/0.6)); u3=min(1,max(0,(t-3.4)/0.6))
        sm=lambda u:u*u*(3-2*u)
        out={}
        lv=L(s,T.DT) if lev else {l:0 for l in T.LEGS}
        for leg in T.LEGS:
            y,z=rf[leg]; y-=shift_y*sm(u1); z+=lv[leg]
            if leg==lift_leg: z+=H*(sm(u2)-sm(u3))
            h,k=T.ik(leg,y,z); out['hip_'+leg]=h; out['knee_'+leg]=k
        out['tail']=0; out['neck_pan']=0
        return out
    mx=0
    for i in range(int(4.5/T.DT)):
        t=s.d.time-t0; s.step(tg(t))
        R=s.d.xmat[s.bid].reshape(3,3)
        roll=math.degrees(math.asin(R[2,0])); pitch=math.degrees(math.asin(R[2,1]))
        if 1.4<t<3.4: mx=max(mx, math.hypot(roll,pitch))
        if verbose and i%int(0.25/T.DT)==0:
            con=set()
            for k in range(s.d.ncon):
                cc=s.d.contact[k]
                for g in (cc.geom1,cc.geom2):
                    if g in pawg: con.add(T.LEGS[pawg.index(g)])
            print(f"  t{t:4.2f} roll {roll:5.1f} pitch {pitch:5.1f} con {''.join(sorted(con))} paws z {np.round(r.paws()[:,2]*1000,1)}")
    return round(mx,1), round(float(s.d.xmat[s.bid][8]),3)
for leg in ['fl','hl']:
    for H in [0.005,0.010,0.015]:
        for sh in [-0.010,0.0,0.010,0.015]:
            print(leg, H, 'shift', sh, test(leg,H,sh))
test('fl',0.015,0.010,verbose=True)
