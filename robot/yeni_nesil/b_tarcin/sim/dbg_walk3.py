import json, math, sys, numpy as np, tarcin as T, gait as G, clips as C
p=json.load(open('out/gait_best_trot_calm.json'))['p']
def go(mu, tail, kp, ki, push=None, dur=6.3):
    s=T.Sim(T.build(mu),record=False); s.set_pose(T.rest_pose()); s.drop_to_floor(); s.hold(T.rest_pose(),0.5)
    rf=G.rest_feet(); t0=s.d.time; ys=[]; L=G.Leveler(kp,ki); lev=None; maxroll=0
    while s.d.time-t0<dur:
        t=s.d.time-t0; ramp=min(1.0,t/0.6)
        if kp or ki: lev=L(s,T.DT)
        tg=G.leg_targets(p,t,rf,ramp,lev); tg['tail']=tail*math.sin(2*math.pi*t/p['period']/2); tg['neck_pan']=3*math.sin(2*math.pi*t/p['period']/2)
        if push and abs(t-push[0])<T.DT/2: s.d.qvel[3:6]+=np.array(push[1])
        s.step(tg)
        R=s.d.xmat[s.bid].reshape(3,3); maxroll=max(maxroll,abs(math.degrees(math.asin(R[2,0]))))
        if s.k%2000==0: ys.append(round(-s.d.qpos[1]*1000,1))
    return np.diff(ys).round(0).tolist(), round(maxroll,1), round(s.peak_tau,3)
for mu in (0.6,0.4):
  for tail,kp,ki,push in [(10,0,0,None),(10,0.5,1.5,None),(10,1.0,3,None),(0,0.5,1.5,(2.0,[1.5,0,0])),(0,0,0,(2.0,[1.5,0,0])),(10,0.5,1.5,(2.0,[0,1.5,0]))]:
    print(mu,tail,kp,ki,push,go(mu,tail,kp,ki,push),flush=True)
