import json, math, sys, numpy as np, tarcin as T, gait as G
base=json.load(open('out/gait_best_trot_calm.json'))['p']
X={mu:T.build(mu) for mu in (0.6,0.4)}
def go(mu, per, turn, h, lev):
    p=dict(base); p.update(period=per, height=h, turn=turn, fwd=0.0)
    s=T.Sim(X[mu],record=False); s.set_pose(T.rest_pose()); s.drop_to_floor(); s.hold(T.rest_pose(),0.5)
    rf=G.rest_feet(); t0=s.d.time; y0=G.yaw(s); L=G.Leveler(*lev) if lev else None; maxtilt=0
    while s.d.time-t0<4.4:
        t=s.d.time-t0; ramp=min(1.0,t/0.5)
        if t>3.9: ramp=max(0,(4.4-t)/0.5)
        tg=G.leg_targets(p,t,rf,ramp,L(s,T.DT) if L else None); tg['neck_pan']=22; tg['tail']=-15*ramp
        s.step(tg); maxtilt=max(maxtilt, math.degrees(math.acos(min(1,s.up()[2][2]))))
    return round(math.degrees(G.unwrap(G.yaw(s)-y0)),1), round(float(np.linalg.norm(s.d.qpos[:2]))*1000,1), round(maxtilt,1)
for per,turn,h,lev in [(0.42,0.016,0.0053,None),(0.42,0.016,0.0053,(0.3,1.0)),(0.42,0.022,0.0053,None),(0.42,0.022,0.0053,(0.3,1.0)),(0.524,0.022,0.008,None),(0.524,0.022,0.008,(0.3,1.0))]:
    print(per,turn,h,lev,[go(mu,per,turn,h,lev) for mu in (0.6,0.4)],flush=True)
